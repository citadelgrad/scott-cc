---
description: Run linting and fix code quality issues
model: claude-sonnet-4-5
---

Run linting and fix code quality issues in the codebase.

## Target

$ARGUMENTS

## Lint Strategy for Solo Developers

### 1. **Run Linting Commands**

**JavaScript/TypeScript**
```bash
# ESLint
npm run lint
npx eslint . --fix

# TypeScript Compiler
npx tsc --noEmit

# Prettier (formatting)
npx prettier --write .
```

**Python**
```bash
# pylint
pylint src/

# flake8
flake8 src/

# black (formatting)
black src/

# mypy (type checking)
mypy src/
```

**Go**
```bash
# golangci-lint
golangci-lint run

# gofmt (formatting)
gofmt -w .

# go vet
go vet ./...
```

**Rust**
```bash
# cargo clippy
cargo clippy --fix

# rustfmt (formatting)
cargo fmt
```

**Other Languages**
- Use idiomatic linters and formatters for your language
- Configure according to your project's style guide

### 2. **Common Linting Issues**

**Type Safety Errors** (where applicable)
- Missing type annotations
- `any`/untyped data structures used
- Unused variables
- Missing return types

**Code Quality**
- Unused imports
- Console.log/print statements (in production code)
- Debugger statements
- TODO comments
- Dead code

**Best Practices**
- No var (use const/let in JS/TS)
- Prefer const over let/mutable
- No nested ternaries (if complex)
- Consistent return statements
- Proper error handling

**Framework-Specific** (adapt to your framework)
- Missing keys in lists (React, Vue, etc.)
- Unsafe hook dependencies
- Unescaped entities in templates
- Missing alt text on images
- Accessibility issues

### 3. **Auto-Fix What You Can**

**Safe Auto-Fixes**
```bash
# Formatting (most languages have formatters)
# ESLint auto-fix
eslint --fix .

# Black (Python)
black src/

# gofmt (Go)
gofmt -w .

# rustfmt (Rust)
cargo fmt
```

**Manual Fixes Needed**
- Type annotations
- Logic errors
- Missing error handling
- Accessibility issues
- Security vulnerabilities

### 4. **Lint Configuration**

**ESLint Config** (`.eslintrc.json` for JS/TS)
```json
{
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended"
  ],
  "rules": {
    "@typescript-eslint/no-explicit-any": "error",
    "@typescript-eslint/no-unused-vars": "error",
    "no-console": "warn"
  }
}
```

**Prettier Config** (`.prettierrc` for JS/TS)
```json
{
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5"
}
```

**pyproject.toml** (Python - Black, pylint, etc.)
```toml
[tool.black]
line-length = 100
target-version = ['py39']

[tool.pylint]
max-line-length = 100
```

**golangci.yml** (Go)
```yaml
linters:
  enable:
    - errcheck
    - gosimple
    - govet
    - ineffassign
    - staticcheck
```

### 5. **Priority Fixes**

**High Priority** (fix immediately)
- Type errors blocking build
- Security vulnerabilities
- Runtime errors
- Broken accessibility

**Medium Priority** (fix before commit)
- Missing type annotations
- Unused variables
- Code style violations
- TODO comments

**Low Priority** (fix when convenient)
- Formatting inconsistencies
- Comment improvements
- Minor refactoring opportunities

### 6. **Pre-Commit Hooks** (Recommended)

**Install pre-commit hooks** (adapt to your setup)
```bash
# For Node.js projects
npm install -D husky lint-staged
npx husky init

# For Python projects
pip install pre-commit
pre-commit install

# For Go projects
# Use git hooks directly or tools like pre-commit
```

**Configure** (adapt to your language/tools)
```bash
# .husky/pre-commit (Node.js)
npx lint-staged

# .pre-commit-config.yaml (Python)
repos:
  - repo: local
    hooks:
      - id: black
        name: black
        entry: black
        language: system
        types: [python]
```

**lint-staged config** (`package.json` for JS/TS)
```json
{
  "lint-staged": {
    "*.{js,jsx,ts,tsx}": [
      "eslint --fix",
      "prettier --write"
    ]
  }
}
```

### 7. **Editor Integration**

**VSCode Settings** (`.vscode/settings.json`)
```json
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true
  },
  "[go]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

## What to Generate

1. **Lint Report** - All issues found
2. **Auto-Fix Results** - What was automatically fixed
3. **Manual Fix Suggestions** - Issues requiring manual intervention
4. **Priority List** - Ordered by severity
5. **Configuration Recommendations** - Improve lint setup

## Common Fixes

**Remove Unused Imports**
```python
# Before
from lib import A, B, C

# After
from lib import A, C  # B was unused
```

**Add Type Annotations**
```python
# Before
def process(data):
    return data.map(x => x.value)

# After
def process(data: List[DataItem]) -> List[int]:
    return [x.value for x in data]
```

**Fix Missing Keys** (React/Vue)
```typescript
// Before
{items.map(item => <div>{item.name}</div>)}

// After
{items.map(item => <div key={item.id}>{item.name}</div>)}
```

Focus on fixes that improve code quality and prevent bugs. Run linting before every commit. Use the linters and formatters appropriate for your language and framework.
