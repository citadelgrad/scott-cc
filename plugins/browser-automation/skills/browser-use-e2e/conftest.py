"""
Pytest fixtures and credential loader for browser-use E2E tests.

Copy this file to your project's tests/e2e/ directory.

Credentials are loaded from .env.test using domain-prefixed naming:
  GITHUB_USER, GITHUB_PASS
  GMAIL_EMAIL, GMAIL_PASS
  MYAPP_USER, MYAPP_PASS, MYAPP_DOMAIN
"""

import os
from pathlib import Path
from typing import Dict, Optional

import pytest
from dotenv import load_dotenv

# Load test credentials
load_dotenv('.env.test')

# Map service prefixes to their domains
DOMAIN_MAP = {
    'GITHUB': 'https://*.github.com',
    'GITLAB': 'https://*.gitlab.com',
    'GMAIL': 'https://*.google.com',
    'GOOGLE': 'https://*.google.com',
    'BITBUCKET': 'https://*.bitbucket.org',
    'AZURE': 'https://*.azure.com',
    'AWS': 'https://*.aws.amazon.com',
}


def build_sensitive_data() -> Dict[str, Dict[str, str]]:
    """
    Build browser-use sensitive_data dict from environment variables.

    Looks for patterns:
      - SERVICENAME_USER + SERVICENAME_PASS (+ optional SERVICENAME_DOMAIN)
      - SERVICENAME_EMAIL + SERVICENAME_PASS (for email-based logins)

    Returns dict mapping domains to credential placeholders.
    The LLM sees only the placeholder names (e.g., 'github_user'),
    while real values are injected directly into form fields.
    """
    credentials = {}
    processed_prefixes = set()

    for key in os.environ:
        # Find user/email keys
        if not (key.endswith('_USER') or key.endswith('_EMAIL')):
            continue

        prefix = key.rsplit('_', 1)[0]
        if prefix in processed_prefixes:
            continue
        processed_prefixes.add(prefix)

        # Get user value
        user_val = os.getenv(key)
        if not user_val:
            continue

        # Get password
        pass_key = f'{prefix}_PASS'
        pass_val = os.getenv(pass_key)
        if not pass_val:
            continue

        # Determine domain (explicit or mapped)
        domain_key = f'{prefix}_DOMAIN'
        domain = os.getenv(domain_key) or DOMAIN_MAP.get(prefix)
        if not domain:
            # Skip if no domain can be determined
            continue

        # Create placeholder names (lowercase prefix)
        prefix_lower = prefix.lower()
        placeholder_user = f'{prefix_lower}_user'
        placeholder_pass = f'{prefix_lower}_pass'

        credentials[domain] = {
            placeholder_user: user_val,
            placeholder_pass: pass_val,
        }

    return credentials


def get_profile_path(profile_name: str) -> Path:
    """Get path to a persistent browser profile."""
    return Path.home() / '.browser-use-profiles' / profile_name


@pytest.fixture
def sensitive_data() -> Dict[str, Dict[str, str]]:
    """Fixture providing credentials for browser-use agents."""
    return build_sensitive_data()


@pytest.fixture
async def browser():
    """Fixture providing a browser-use Browser instance."""
    from browser_use import Browser

    headless = os.getenv('HEADLESS', 'true').lower() == 'true'
    browser = Browser(headless=headless)
    yield browser
    await browser.close()


@pytest.fixture
async def browser_with_profile(request):
    """
    Fixture providing browser with persistent profile.

    Usage:
        @pytest.mark.parametrize('browser_with_profile', ['github-2fa'], indirect=True)
        async def test_something(browser_with_profile):
            ...
    """
    from browser_use import Browser

    profile_name = request.param
    profile_path = get_profile_path(profile_name)

    if not profile_path.exists():
        pytest.skip(f"Profile '{profile_name}' not found. Run setup_profile.py first.")

    browser = Browser(
        headless=False,  # Profiles usually need visible browser
        user_data_dir=str(profile_path),
    )
    yield browser
    await browser.close()


def get_llm():
    """Get the default LLM for browser-use agents."""
    from browser_use import ChatBrowserUse
    return ChatBrowserUse()
