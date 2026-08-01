# Pre-Commit Hook Setup

Details on how pre-commit integration works with beads hook chaining.

## Why Not `pre-commit install`?

Beads sets `core.hooksPath = .beads/hooks/`, which overrides `.git/hooks/` entirely. When `pre-commit install` detects `core.hooksPath` is set, it refuses to run with an error:

```
Cowardly refusing to install hooks with `core.hooksPath` set
```

This is intentional. The beads hook chain takes precedence, and we manually append pre-commit into that chain instead.

## Hook Chaining Logic

The pre-commit hook is wired into `.beads/hooks/pre-commit` via a decision tree:

### 1. Already Chained (No Action)
Check if pre-commit is already in the chain:
```bash
grep -q 'pre-commit run' .beads/hooks/pre-commit 2>/dev/null
```
If true, skip (idempotent).

### 2. File Exists, Not Yet Chained (Append)
If `.beads/hooks/pre-commit` exists but doesn't have the pre-commit chain, append these two lines (no shebang):
```bash
# Chain into pre-commit framework
exec pre-commit run --hook-stage pre-commit
```

### 3. File Does Not Exist (Create)
Create `.beads/hooks/pre-commit` with full initialization:
```bash
#!/usr/bin/env bash
set -euo pipefail

# Chain pre-commit framework against staged files only
exec pre-commit run --hook-stage pre-commit
```

### 4. Make Executable
```bash
chmod +x .beads/hooks/pre-commit
```

## Important: Hook Environments Install Lazily

When `.pre-commit-config.yaml` is first copied, the hook environments (e.g., node, python, system) do NOT install immediately. They install lazily on the first commit that triggers `pre-commit run`. This is expected behavior.

## Caveat: Beads Upgrades

If `bd init` is re-run later (e.g., after a beads upgrade), it may overwrite `.beads/hooks/pre-commit`. Re-apply the chaining logic after any beads upgrade.

## Dependency: Beads Must Exist First

Pre-commit setup requires:
- `.beads/` directory to already exist (created via `bd init` in the beads component)
- `core.hooksPath` to be already set to `.beads/hooks/` (set by `bd init`)

If pre-commit is selected without beads, the skill prompts to add beads to the selection.

## Tool Availability Check

Before attempting pre-commit setup:
```bash
command -v pre-commit >/dev/null 2>&1 || { echo "pre-commit not found — install with: uv tool install pre-commit"; exit 1; }
```

If pre-commit is not available, the component fails with a clear error message.
