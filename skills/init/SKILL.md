---
name: init
description: >-
  Use when initializing a new project with standard scaffolding. Sets up git
  repo, CLAUDE.md, AGENTS.md symlink, beads, .envrc, Makefile, pre-commit hooks,
  and foundry.yaml. All components are optional — pick what you need.
license: MIT
metadata:
  category: technique
  triggers: [project-setup, scaffolding, templates]
uses:
  templates:
    - ${CLAUDE_PLUGIN_ROOT}/templates/CLAUDE.md
    - ${CLAUDE_PLUGIN_ROOT}/templates/pre-commit-config.yaml
  tools:
    - beads (bd init)
    - direnv
    - pre-commit
---

# Project Init

Interactive scaffolding for a new project. Detects what already exists, presents a menu, and sets up only what you select.

## When to Use
- Starting a brand-new project from scratch
- Adding missing scaffolding pieces (CLAUDE.md, Makefile, .envrc, etc.) to an existing project
- Setting up beads issue tracking, pre-commit hooks, or foundry.yaml for the first time
- Onboarding a project to the standard toolchain

## Step 1: Detect Current State

Run the detection checks in the current working directory. See [bash-helpers.md](references/bash-helpers.md) for the complete detection logic and tool availability checks.

Detect the **project type**: Python (`pyproject.toml`), Node/TS (`package.json` or `tsconfig.json`), or unknown. This determines the Makefile template in Step 3.

## Step 2: Present a Menu

Show the user a **numbered** status list with ✓ for items that exist and ○ for items not yet set up:

```
Project init — select what to set up:

  1. git            ○  git repository (git init)
  2. CLAUDE.md      ○  project-level Claude instructions
  3. AGENTS.md      ○  symlink → CLAUDE.md (for Codex)
  4. beads          ○  issue tracking (bd init)
  5. .envrc         ○  direnv environment stub
  6. Makefile       ○  service management targets
  7. pre-commit     ○  commit hooks (.pre-commit-config.yaml)
  8. foundry.yaml   ○  scheduling/automation control layer

Which would you like to set up? (enter numbers, "all", or "none")
```

**Dependency check:** Pre-commit (7) requires beads (4) for hook chaining. If the user selects pre-commit without beads, ask: "pre-commit requires beads for hook chaining. Add beads? (y/n)" and auto-add if yes.

Print a pre-execution summary before proceeding:
> "Will create: git, CLAUDE.md, AGENTS.md, beads. Will skip (already exists): .envrc."

## Step 3: Execute Selected Components

Execute each selected component in order. For detailed implementation instructions, including bash helpers, tool checks, and idempotency patterns, see [components.md](references/components.md).

The execution order is:

1. **git** — Initialize git repository (only if `.git/` doesn't exist)
2. **CLAUDE.md** — Copy project instructions from templates
3. **AGENTS.md** — Create symlink to CLAUDE.md for Codex compatibility
4. **beads** — Initialize issue tracking and set `validation.on-create=warn`
5. **.envrc** — Create direnv stub for environment variables
6. **Makefile** — Create service targets (template varies by project type; see [makefile-templates.md](references/makefile-templates.md))
7. **pre-commit** — Chain pre-commit hooks into `.beads/hooks/pre-commit` (see [pre-commit-setup.md](references/pre-commit-setup.md))
8. **foundry.yaml** — Create automation control layer (see [foundry-template.md](references/foundry-template.md))

For bash detection commands and tool availability checks, refer to [bash-helpers.md](references/bash-helpers.md).
For beads configuration details, see [beads-config.md](references/beads-config.md).

## Step 4: Report Results

After all components are processed, print a summary:

```
Done. Here's what was set up:

  ✓ git           — git init ran successfully
  ✓ CLAUDE.md     — copied from scott-cc template
  ✓ AGENTS.md     — symlinked to CLAUDE.md
  ✓ beads         — bd init ran successfully, validation.on-create=warn set
  ✓ .envrc        — created, direnv allow ran
  ✓ Makefile      — created (Python project: includes test + lint targets)
  ✓ pre-commit    — config copied, hook chain written to .beads/hooks/pre-commit
                    (hook envs install lazily on first commit)
  ✓ foundry.yaml  — created (empty profiles/schedules skeleton, two examples commented)

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
  Would stage: Makefile, .pre-commit-config.yaml, foundry.yaml, .gitignore
  Message: "chore: initial project scaffolding"
```

If yes:
```bash
git add Makefile .pre-commit-config.yaml foundry.yaml .gitignore
git commit -m "chore: initial project scaffolding"
```

## Available Skills

Mention these scott-cc skills after setup completes, so the user knows what's available:

```
Available skills for common workflows:

  /scott-cc:pas-pipeline    — run, resume, and manage PAS AI pipelines
  /scott-cc:reck-factory    — register repos and run tasks in the software factory
  /scott-cc:c4-diagram      — generate C4 architecture diagrams with Mermaid
  /scott-cc:cli-design      — design or audit CLIs for agent compatibility
```

Only list skills that are relevant to the project type detected in Step 1:
- Python or unknown project: list all four
- Node/TS project: omit `pas-pipeline` and `reck-factory` unless `pas.toml` or `foundry.yaml` is present

## Limitations
- Use this skill only when the task clearly matches the scope described above.
- Templates are opinionated — they reflect this project's conventions, not universal best practices.
- Does not install system dependencies (git, direnv, pre-commit) — assumes they are already available.
- Does not configure CI/CD pipelines; use foundry.yaml for local automation only.
- Stop and ask for clarification if the project type, language, or desired components are unclear.
