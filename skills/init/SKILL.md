---
name: init
description: Initialize a new project with standard scaffolding. Sets up beads, CLAUDE.md, AGENTS.md symlink, .envrc, Makefile, and pre-commit hooks. All components are optional — pick what you need.
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
# Project type detection
ls pyproject.toml package.json tsconfig.json 2>/dev/null

# Existing scaffolding
ls CLAUDE.md AGENTS.md .envrc Makefile .pre-commit-config.yaml 2>/dev/null
ls -d .beads/ 2>/dev/null
```

Collect the results so you know what already exists vs. what needs to be created.

## Step 2: Present a Menu

Show the user a status list of all available components. Use checkmarks for items that already exist and circles for items not yet set up:

```
Project init — select what to set up:

  ✓ already exists   ○ not yet set up

  [ ] beads          ○  issue tracking (bd init)
  [ ] CLAUDE.md      ○  project-level Claude instructions
  [ ] AGENTS.md      ○  symlink → CLAUDE.md (for Codex)
  [ ] .envrc         ○  direnv environment stub
  [ ] Makefile       ○  service management targets
  [ ] pre-commit     ○  commit hooks (.pre-commit-config.yaml)

Which would you like to set up? (enter numbers, "all", or "none")
```

Replace ○ with ✓ for items that already exist, and note them as "(already exists — will skip or confirm overwrite)".

Ask the user which components they want. Accept a comma-separated list of numbers, "all", or "none".

## Step 3: Execute Selected Components

Execute each selected component in order. For each one, print what you're doing.

### beads

Condition: `.beads/` directory does not exist.

```bash
bd init
```

If `.beads/` already exists, skip and note it.

### CLAUDE.md

Source: `~/projects/oss/scott-cc/templates/CLAUDE.md`
Destination: `./CLAUDE.md`

Steps:
1. If `CLAUDE.md` already exists, ask the user: "CLAUDE.md already exists — overwrite? (y/n)"
2. Copy the file:
   ```bash
   cp ~/projects/oss/scott-cc/templates/CLAUDE.md ./CLAUDE.md
   ```
3. Add `CLAUDE.md` to `.gitignore` if not already present (it's personal config, not project config):
   ```bash
   grep -qxF 'CLAUDE.md' .gitignore 2>/dev/null || echo 'CLAUDE.md' >> .gitignore
   ```

### AGENTS.md symlink

Condition: `AGENTS.md` does not exist, OR exists but is not a symlink pointing to `CLAUDE.md`.

Create a relative symlink so Codex reads the same instructions as Claude:
```bash
ln -sf CLAUDE.md AGENTS.md
```

If `AGENTS.md` already exists and is already `ln -sf CLAUDE.md AGENTS.md`, skip.
If `AGENTS.md` exists as a regular file (not a symlink), ask before replacing it.

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

Create the file with this exact content (use tabs for recipe indentation, not spaces):
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

If `Makefile` already exists, skip it — do not overwrite, do not ask.

### pre-commit

Source: `~/projects/oss/scott-cc/templates/.pre-commit-config.yaml`
Destination: `./.pre-commit-config.yaml`

Steps:
1. If `.pre-commit-config.yaml` already exists, ask: "`.pre-commit-config.yaml` already exists — overwrite? (y/n)"
2. Copy the template:
   ```bash
   cp ~/projects/oss/scott-cc/templates/.pre-commit-config.yaml ./.pre-commit-config.yaml
   ```
3. Install the hooks:
   ```bash
   pre-commit install
   ```

## Step 4: Report Results

After all components are processed, print a summary:

```
Done. Here's what was set up:

  ✓ beads         — bd init ran successfully
  ✓ CLAUDE.md     — copied from scott-cc template
  ✓ AGENTS.md     — symlinked to CLAUDE.md
  ✓ .envrc        — created, direnv allow ran
  ✓ Makefile      — created with up/down/restart/status/logs
  ✓ pre-commit    — config copied, hooks installed

Skipped:
  — (none)

Next steps:
  - Add your project's env vars to .envrc
  - Run: direnv allow  (if you haven't already)
  - Customize Makefile with your actual services and ports
```

List skipped items with a reason (e.g., "already exists", "user declined").
