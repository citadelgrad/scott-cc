# browser-automation

> Complete browser testing and validation suite

## What's Included

### Agents (2)
- **browser-validator** - Validate UI implementations using browser automation with Playwright
- **e2e-runner** - End-to-end testing with AI automation, handles authenticated flows and 2FA

### Skills (2)
- **browser-use** - Automate browser interactions for testing, screenshots, and data extraction
- **browser-use-e2e** - Generate and run E2E tests using AI-powered browser control

## When to Use

**Install this if you**:
- Build web applications or websites
- Need automated UI testing
- Want to validate design implementations
- Test authenticated user flows

**Don't install if you**:
- Only build backend APIs (no UI)
- Don't need browser automation

## Use Cases

### 1. UI Validation
```
User: "Verify this component matches the Figma design"
browser-validator: Takes screenshots, compares with design
Output: Visual diff with discrepancies highlighted
```

### 2. E2E Test Generation
```
User: "Generate tests for the checkout flow"
e2e-runner: Records user journey, generates Python test
Output: Executable test script with assertions
```

### 3. Browser Automation
```
/browser-use open https://app.example.com
/browser-use click "Login"
/browser-use input email "test@example.com"
/browser-use screenshot
```

### 4. Authenticated Testing
```
User: "Test the user dashboard after login"
e2e-runner: Handles login, 2FA, navigates dashboard
Output: Test validation report
```

## Quick Start

```bash
# Validate UI implementation
Ask: "Check if my hero section matches the design specs"

# Generate E2E tests
Ask: "Create tests for the user registration flow"

# Automate browser tasks
/browser-use open https://example.com
/browser-use state  # See clickable elements
/browser-use click 5  # Click element by index
```

## Skills Overview

### /browser-use
Fast, persistent browser automation via CLI.

**Modes**:
- `chromium` - Headless browser (fast)
- `real` - Your Chrome with login sessions
- `remote` - Cloud browser with proxy support

**Commands**:
- `open <url>` - Navigate
- `state` - Get clickable elements
- `click <index>` - Click element
- `screenshot` - Take screenshot
- `eval "code"` - Run JavaScript

### /browser-use-e2e
Generate executable E2E tests from natural language.

**Features**:
- Authenticated flows with secure credential injection
- Persistent browser profiles for 2FA
- Python test script generation
- Critical user journey validation

## Recommended Combinations

**Frontend development**:
- browser-automation ✅
- scott-cc ✅ (main plugin for refactoring)
- mutation-testing ✅ (to verify tests work)

**QA automation**:
- browser-automation ✅
- process-engine ✅ (to track test coverage)
