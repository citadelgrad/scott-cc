---
description: >-
  Detailed execution instructions for each init component: git, CLAUDE.md,
  AGENTS.md, beads, .envrc, Makefile, pre-commit, and foundry.yaml.
metadata:
  tags: [init, components, scaffolding, execution-details]
---

Execute each selected component in this order. For each one, print what you're doing.

### git

Condition: `.git/` directory does not exist.

```bash
git init
```

If `.git/` already exists, skip and note it. All other components that touch `.git/` (beads, pre-commit) depend on this running first.

### CLAUDE.md

Source: `templates/CLAUDE.md` in the scott-cc repo
Destination: `./CLAUDE.md`

First, locate the scott-cc repo on this machine:
```bash
SCOTT_CC_DIR=$(fd -HI -t d -g 'scott-cc' ~ 2>/dev/null | grep -E '/scott-cc$' | head -1)
```

Steps:
1. If `CLAUDE.md` already exists, ask the user: "CLAUDE.md already exists — overwrite? (y/n)"
2. Copy the file:
   ```bash
   cp "$SCOTT_CC_DIR/templates/CLAUDE.md" ./CLAUDE.md
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
bd config set validation.on-create warn
```

`validation.on-create warn` makes `bd create` nag when the description is missing its required sections (e.g. Acceptance Criteria for task/feature/bug) — a technical backstop for the global CLAUDE.md rule that acceptance criteria must be generated via the `acceptance-criteria` skill before `bd create`. This setting is per-repo (stored in `.beads/config.yaml`); there is no global bd config for it, which is why it's wired into every `bd init` here instead.

If `.beads/` already exists, skip and note it. If `.beads/` already exists but `validation.on-create` is unset, still run `bd config set validation.on-create warn` (idempotent, safe to re-run).

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
.PHONY: up down restart status logs logs-tail test lint

up:
	docker compose up -d

down:
	docker compose down

restart: down up

status:
	docker compose ps

logs:
	docker compose logs -f

logs-tail:
	docker compose logs --tail=20

test:
	uv run pytest

lint:
	uv run ruff check .
```

**Node/TS project** (`package.json` or `tsconfig.json` detected):
```makefile
.PHONY: up down restart status logs logs-tail test lint

up:
	docker compose up -d

down:
	docker compose down

restart: down up

status:
	docker compose ps

logs:
	docker compose logs -f

logs-tail:
	docker compose logs --tail=20

test:
	npm test

lint:
	npx biome check .
```

**Unknown project type** (none of the above detected):
```makefile
.PHONY: up down restart status logs logs-tail

up:
	docker compose up -d

down:
	docker compose down

restart: down up

status:
	docker compose ps

logs:
	docker compose logs -f

logs-tail:
	docker compose logs --tail=20
```

Note: `logs` intentionally streams (`-f`) and shows every container's output combined — do not chain it from other targets. `logs-tail` is the non-blocking counterpart: it prints a recent snapshot from all containers and returns, so it's safe to run right after `make up` to verify startup without hanging the terminal.

If `Makefile` already exists, skip it — do not overwrite, do not ask.

### pre-commit

Source: `templates/.pre-commit-config.yaml` in the scott-cc repo (use `$SCOTT_CC_DIR` from the CLAUDE.md step above)
Destination: `./.pre-commit-config.yaml`

Check tool availability first:
```bash
command -v pre-commit >/dev/null 2>&1 || { echo "pre-commit not found — install with: uv tool install pre-commit"; exit 1; }
```

**Why `pre-commit install` is NOT used:** beads sets `core.hooksPath = .beads/hooks/`, which overrides `.git/hooks/` entirely. `pre-commit install` detects `core.hooksPath` and refuses to run (exits 1 with "Cowardly refusing to install hooks with `core.hooksPath` set"). Do not run it. Hook environments install lazily on the first commit that triggers `pre-commit run`.

Steps:
1. If `.pre-commit-config.yaml` already exists, ask: "`.pre-commit-config.yaml` already exists — overwrite? (y/n)"
2. Copy the template:
   ```bash
   cp "$SCOTT_CC_DIR/templates/.pre-commit-config.yaml" ./.pre-commit-config.yaml
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

### foundry.yaml

Condition: `foundry.yaml` does not exist (never overwrite an existing one).

Create the file with this exact content:
```yaml
# foundry.yaml — scheduling & automation control layer for this project.
# See CLAUDE.md's "Scheduling & Automation" section for the full schema.
# `foundry run <profile>` runs one locally; `foundry run <profile> --dry-run`
# previews its gates; `foundry schedule install <name>` installs its cron entry.

version: 1

# Example 1: unattended code review via the review-panel skill's mode:agent
# JSON contract, run as a post-feature gate. Reckoner calls `foundry run
# post-feature` automatically after every successful PR — no other wiring
# needed. See plugins/review-panel/skills/review-panel/references/dual-mode-contract.md
# for the full contract (status values, escalation handling, etc).
# profiles:
#   post-feature:
#     gates:
#       - id: review-panel
#         run: |
#           claude -p "/review-panel $(git merge-base origin/main HEAD)..HEAD --mode=agent" \
#             --dangerously-skip-permissions --output-format json \
#             > "$FOUNDRY_RUN_DIR/claude-cli.json"
#           jq -r '.result' "$FOUNDRY_RUN_DIR/claude-cli.json" \
#             > "$FOUNDRY_RUN_DIR/review-panel.json"
#           status=$(jq -r '.status' "$FOUNDRY_RUN_DIR/review-panel.json")
#           # converged/escalated pass; circuit_broken/error fail (escalated
#           # must never block unattended automation — see OQ4 in the
#           # dual-mode-contract.md doc above)
#           [ "$status" = "converged" ] || [ "$status" = "escalated" ]
#         timeout: 20m
#         allow_failure: false
#         decision_on_failure: fail

# Example 2: a scheduled agent gate that invokes a single review skill
# directly (not the full panel) — e.g. a nightly adversarial pass over
# recent changes, reported but never blocking on its own
# profiles:
#   adversarial-nightly:
#     gates:
#       - id: adversarial-review
#         run: |
#           claude -p "Use the adversarial-reviewer skill to review changes
#           from the last 24h and report findings." \
#             --dangerously-skip-permissions --output-format json \
#             > "$FOUNDRY_RUN_DIR/adversarial-review.json"
#         timeout: 15m
#         allow_failure: true
#         decision_on_failure: warn
#
# schedules:
#   nightly-adversarial-review:
#     profile: adversarial-nightly
#     cron: '0 3 * * *'

profiles: {}

schedules: {}
```

If `foundry.yaml` already exists, skip and note it.
