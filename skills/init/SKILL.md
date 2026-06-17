---
name: init
description: Initialize a new project with standard scaffolding. Sets up git repo, CLAUDE.md, AGENTS.md symlink, beads, .envrc, Makefile, and pre-commit hooks. All components are optional — pick what you need.
license: MIT
tags: [project-setup, scaffolding, templates]
uses:
  templates:
    - templates/CLAUDE.md
    - templates/.pre-commit-config.yaml
  tools:
    - beads (bd init)
    - direnv
    - pre-commit
---

# Project Init

Interactive scaffolding for a new project. Detects what already exists, presents a menu, and sets up only what you select.

## Step 1: Detect Current State

Run these checks in the current working directory:

```bash
# Git repo check
ls -d .git/ 2>/dev/null

# Project type detection
ls pyproject.toml package.json tsconfig.json 2>/dev/null

# Existing scaffolding
ls CLAUDE.md AGENTS.md .envrc Makefile .pre-commit-config.yaml 2>/dev/null
ls -d .beads/ 2>/dev/null
```

Record which project files exist as the **detected project type**: Python (`pyproject.toml`), Node/TS (`package.json` or `tsconfig.json`), or unknown. This is used to customize the Makefile in Step 3.

## Step 2: Present a Menu

Show the user a **numbered** status list. Use ✓ for items that already exist and ○ for items not yet set up:

```
Project init — select what to set up:

  ✓ already exists   ○ not yet set up

  1. git            ○  git repository (git init)
  2. CLAUDE.md      ○  project-level Claude instructions
  3. AGENTS.md      ○  symlink → CLAUDE.md (for Codex)
  4. beads          ○  issue tracking (bd init)
  5. .envrc         ○  direnv environment stub
  6. Makefile       ○  service management targets
  7. pre-commit     ○  commit hooks (.pre-commit-config.yaml)

Which would you like to set up? (enter numbers, "all", or "none")
```

Replace ○ with ✓ for items that already exist, and note them as "(already exists — will skip or confirm overwrite)".

Accept a comma-separated list of numbers, "all", or "none".

**Dependency check:** If the user selects pre-commit (7) but neither selects beads (4) nor has `.beads/` already initialized, warn:
> "pre-commit requires beads for hook chaining. Add beads to your selection? (y/n)"

Auto-add beads if yes. Skip pre-commit setup if no.

**Pre-execution preview:** Before running anything, print a one-line summary of what will happen:
> "Will create: git, CLAUDE.md, AGENTS.md, beads. Will skip (already exists): .envrc. Will ask before overwriting: pre-commit."

## Step 3: Execute Selected Components

Execute each selected component in this order. For each one, print what you're doing.

### git

Condition: `.git/` directory does not exist.

```bash
git init
```

If `.git/` already exists, skip and note it. All other components that touch `.git/` (beads, pre-commit) depend on this running first.

### CLAUDE.md

Source: `~/projects/oss/scott-cc/templates/CLAUDE.md`
Destination: `./CLAUDE.md`

Steps:
1. If `CLAUDE.md` already exists, ask the user: "CLAUDE.md already exists — overwrite? (y/n)"
2. Copy the file:
   ```bash
   cp ~/projects/oss/scott-cc/templates/CLAUDE.md ./CLAUDE.md
   ```
3. Add `CLAUDE.md`, `AGENTS.md`, and `.envrc` to `.gitignore` if not already present (all three are personal/local config, not project config). The `||` branch creates `.gitignore` if it doesn't exist:
   ```bash
   grep -qxF 'CLAUDE.md' .gitignore 2>/dev/null || echo 'CLAUDE.md' >> .gitignore
   grep -qxF 'AGENTS.md' .gitignore 2>/dev/null || echo 'AGENTS.md' >> .gitignore
   grep -qxF '.envrc'    .gitignore 2>/dev/null || echo '.envrc'    >> .gitignore
   ```

### AGENTS.md symlink

Verify the current state with:
```bash
[ -L AGENTS.md ] && [ "$(readlink AGENTS.md)" = "CLAUDE.md" ]
```

- If that check passes, AGENTS.md is already a correct symlink — skip.
- If `AGENTS.md` exists as a regular file (not a symlink), ask before replacing it.
- Otherwise, create the symlink:
  ```bash
  ln -sf CLAUDE.md AGENTS.md
  ```

### beads

Check tool availability first:
```bash
command -v bd >/dev/null 2>&1 || { echo "bd not found — install beads before continuing"; exit 1; }
```

Condition: `.beads/` directory does not exist.

```bash
bd init
```

If `.beads/` already exists, skip and note it.

### .envrc

Condition: `.envrc` does not exist.

Create the file with this exact content:
```
# Environment variables for this project
# Run: direnv allow

# dotenv .env
```

Then run `direnv allow` if direnv is available:
```bash
command -v direnv >/dev/null 2>&1 && direnv allow
```

If `.envrc` already exists, skip and note it.

### Makefile

Condition: `Makefile` does not exist (never overwrite an existing Makefile).

Create the Makefile based on the **detected project type** from Step 1. Use tabs for recipe indentation, not spaces.

**Python project** (`pyproject.toml` detected):
```makefile
.PHONY: up down restart status logs test lint

up:
	docker compose up -d

down:
	docker compose down

restart: down up

status:
	docker compose ps

logs:
	docker compose logs -f

test:
	uv run pytest

lint:
	uv run ruff check .
```

**Node/TS project** (`package.json` or `tsconfig.json` detected):
```makefile
.PHONY: up down restart status logs test lint

up:
	docker compose up -d

down:
	docker compose down

restart: down up

status:
	docker compose ps

logs:
	docker compose logs -f

test:
	npm test

lint:
	npx biome check .
```

**Unknown project type** (none of the above detected):
```makefile
.PHONY: up down restart status logs

up:
	docker compose up -d

down:
	docker compose down

restart: down up

status:
	docker compose ps

logs:
	docker compose logs -f
```

Note: `logs` intentionally streams (`-f`). Do not chain it from other targets.

If `Makefile` already exists, skip it — do not overwrite, do not ask.

### pre-commit

Source: `~/projects/oss/scott-cc/templates/.pre-commit-config.yaml`
Destination: `./.pre-commit-config.yaml`

Check tool availability first:
```bash
command -v pre-commit >/dev/null 2>&1 || { echo "pre-commit not found — install with: pip install pre-commit"; exit 1; }
```

**Why `pre-commit install` is NOT used:** beads sets `core.hooksPath = .beads/hooks/`, which overrides `.git/hooks/` entirely. `pre-commit install` detects `core.hooksPath` and refuses to run (exits 1 with "Cowardly refusing to install hooks with `core.hooksPath` set"). Do not run it. Hook environments install lazily on the first commit that triggers `pre-commit run`.

Steps:
1. If `.pre-commit-config.yaml` already exists, ask: "`.pre-commit-config.yaml` already exists — overwrite? (y/n)"
2. Copy the template:
   ```bash
   cp ~/projects/oss/scott-cc/templates/.pre-commit-config.yaml ./.pre-commit-config.yaml
   ```
3. Write the chain into `.beads/hooks/pre-commit` using this decision tree:
   - **Already chained:** `grep -q 'pre-commit run' .beads/hooks/pre-commit 2>/dev/null` → if true, skip (idempotent).
   - **File exists, not yet chained:** append only these two lines (no shebang):
     ```bash
     # Chain into pre-commit framework
     exec pre-commit run --hook-stage pre-commit
     ```
   - **File does not exist:** create it with:
     ```bash
     #!/usr/bin/env bash
     set -euo pipefail

     # Chain pre-commit framework against staged files only
     exec pre-commit run --hook-stage pre-commit
     ```
4. Make it executable:
   ```bash
   chmod +x .beads/hooks/pre-commit
   ```

**Caveat:** If `bd init` is re-run later, it may overwrite `.beads/hooks/pre-commit`. Re-apply step 3 after any beads upgrade.

## Step 4: Report Results

After all components are processed, print a summary:

```
Done. Here's what was set up:

  ✓ git           — git init ran successfully
  ✓ CLAUDE.md     — copied from scott-cc template
  ✓ AGENTS.md     — symlinked to CLAUDE.md
  ✓ beads         — bd init ran successfully
  ✓ .envrc        — created, direnv allow ran
  ✓ Makefile      — created (Python project: includes test + lint targets)
  ✓ pre-commit    — config copied, hook chain written to .beads/hooks/pre-commit
                    (hook envs install lazily on first commit)

Skipped:
  — (none)

Next steps:
  - Add your project's env vars to .envrc and run: direnv allow
  - Customize Makefile with your actual services and ports
```

List skipped items with a reason (e.g., "already exists", "user declined").

Then offer an initial commit:
```
Make an initial commit? (y/n)
  Would stage: AGENTS.md, Makefile, .pre-commit-config.yaml, .gitignore
  Message: "chore: initial project scaffolding"
```

If yes:
```bash
git add AGENTS.md Makefile .pre-commit-config.yaml .gitignore
git commit -m "chore: initial project scaffolding"
```
