---
name: browser-use-e2e
description: Generate and run E2E tests using browser-use AI automation. This skill should be used when creating automated browser tests, testing authenticated flows, generating test scripts from natural language, or validating user journeys with AI-powered browser control. Handles credentials securely via .env.test with domain-prefixed variables.
---

# browser-use E2E Testing

## Overview

Generate and execute end-to-end tests using browser-use, an AI-powered browser automation library. Tests are written in natural language and the AI agent figures out the specific interactions.

## Quick Start

### 1. Setup

```bash
# Install browser-use
uv add browser-use python-dotenv
uvx browser-use install
```

### 2. Configure Credentials

Create `.env.test` with domain-prefixed credentials:

```bash
# Format: SERVICENAME_USER, SERVICENAME_PASS, SERVICENAME_DOMAIN (optional)

GITHUB_USER=your-username
GITHUB_PASS=your-password

GMAIL_EMAIL=you@gmail.com
GMAIL_PASS=your-app-password

# Custom app
MYAPP_USER=admin
MYAPP_PASS=secret
MYAPP_DOMAIN=https://app.example.com
```

### 3. Credential Loader

```python
# tests/e2e/conftest.py
import os
from dotenv import load_dotenv

load_dotenv('.env.test')

DOMAIN_MAP = {
    'GITHUB': 'https://*.github.com',
    'GMAIL': 'https://*.google.com',
    'GOOGLE': 'https://*.google.com',
}

def build_sensitive_data() -> dict:
    """Build browser-use sensitive_data from .env.test vars."""
    credentials = {}

    for key in os.environ:
        if key.endswith('_USER') or key.endswith('_EMAIL'):
            prefix = key.rsplit('_', 1)[0]
            user_val = os.getenv(key)
            pass_key = f'{prefix}_PASS'
            pass_val = os.getenv(pass_key)

            if not pass_val:
                continue

            # Determine domain
            domain_key = f'{prefix}_DOMAIN'
            domain = os.getenv(domain_key) or DOMAIN_MAP.get(prefix)

            if not domain:
                continue

            # Build credential entry
            placeholder_user = f'{prefix.lower()}_user'
            placeholder_pass = f'{prefix.lower()}_pass'

            credentials[domain] = {
                placeholder_user: user_val,
                placeholder_pass: pass_val,
            }

    return credentials
```

## Test Patterns

### Simple Test

```python
from browser_use import Agent, Browser, ChatBrowserUse
import asyncio

async def test_login():
    from conftest import build_sensitive_data

    agent = Agent(
        task='''
        Go to github.com
        Log in with github_user and github_pass
        Verify the dashboard loads successfully
        ''',
        llm=ChatBrowserUse(),
        browser=Browser(headless=True),
        sensitive_data=build_sensitive_data(),
        use_vision=False,  # Security: no screenshots with creds
    )

    result = await agent.run()
    assert result.is_successful()

asyncio.run(test_login())
```

### With Pytest

```python
# tests/e2e/test_auth.py
import pytest
from browser_use import Agent, Browser, ChatBrowserUse

@pytest.fixture
def sensitive_data():
    from conftest import build_sensitive_data
    return build_sensitive_data()

@pytest.fixture
async def browser():
    b = Browser(headless=True)
    yield b
    await b.close()

@pytest.mark.asyncio
async def test_github_login(browser, sensitive_data):
    agent = Agent(
        task='Log into github.com with github_user/github_pass, verify repos page',
        llm=ChatBrowserUse(),
        browser=browser,
        sensitive_data=sensitive_data,
        use_vision=False,
    )
    result = await agent.run()
    assert result.is_successful()
```

### Persistent Profile (2FA Sites)

```python
from pathlib import Path

async def test_with_2fa_profile():
    profile_dir = Path.home() / '.browser-use-profiles' / 'github-2fa'

    browser = Browser(
        headless=False,
        user_data_dir=str(profile_dir),
    )

    agent = Agent(
        task='Go to github.com/settings/security, verify 2FA is enabled',
        llm=ChatBrowserUse(),
        browser=browser,
        # No credentials needed - profile has active session
    )

    result = await agent.run()
    assert result.is_successful()
```

### Setup Profile Script

```bash
# Run once interactively to save 2FA session
python scripts/setup_profile.py --service github --profile-name github-2fa
```

```python
# scripts/setup_profile.py
import argparse
import asyncio
from pathlib import Path
from browser_use import Browser

async def setup_profile(service: str, profile_name: str):
    profile_dir = Path.home() / '.browser-use-profiles' / profile_name
    profile_dir.mkdir(parents=True, exist_ok=True)

    urls = {
        'github': 'https://github.com/login',
        'google': 'https://accounts.google.com',
        'gitlab': 'https://gitlab.com/users/sign_in',
    }

    browser = Browser(headless=False, user_data_dir=str(profile_dir))
    ctx = await browser.new_context()
    page = await ctx.new_page()
    await page.goto(urls.get(service, service))

    input(f'Complete {service} login (including 2FA), then press Enter...')
    await browser.close()
    print(f'Profile saved to {profile_dir}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--service', required=True)
    parser.add_argument('--profile-name', required=True)
    args = parser.parse_args()
    asyncio.run(setup_profile(args.service, args.profile_name))
```

## Running Tests

```bash
# Run all E2E tests
pytest tests/e2e/ -v

# Run specific test
pytest tests/e2e/test_auth.py::test_github_login -v

# Run with visible browser
HEADLESS=false pytest tests/e2e/ -v

# Generate HTML report
pytest tests/e2e/ --html=report.html
```

## Domain Restriction

```python
# Limit where the agent can navigate (security)
browser = Browser(
    allowed_domains=['github.com', 'app.example.com']
)
```

## Tips

1. **Credential placeholders**: Use descriptive names like `github_user` not `x_user`
2. **Disable vision** when handling credentials to prevent screenshot leaks
3. **Use profiles** for 2FA - browser-use can't solve CAPTCHAs
4. **Domain restriction** prevents agent from navigating to unexpected sites
5. **Headless in CI** - set `headless=True` for automated pipelines
6. **Test idempotency** - clean up test data or use unique identifiers

## File Structure

```
project/
├── .env.test                    # Credentials (git-ignored)
├── tests/
│   └── e2e/
│       ├── conftest.py          # Fixtures, credential loader
│       ├── test_auth.py         # Authentication tests
│       └── test_journeys.py     # User journey tests
└── scripts/
    └── setup_profile.py         # Profile setup for 2FA
```
