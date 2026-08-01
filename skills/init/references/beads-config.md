# Beads Configuration

Setup and validation configuration for beads issue tracking.

## Initialization

Run these commands to initialize beads:
```bash
bd init
bd config set validation.on-create warn
```

## Validation Setting: `validation.on-create warn`

This setting makes `bd create` nag when the description is missing required sections:
- **For tasks/features/bugs:** Missing Acceptance Criteria
- **General:** Missing description details

### Purpose

This is a technical backstop for the global CLAUDE.md rule that acceptance criteria must be generated via the `acceptance-criteria` skill before `bd create`. The warning reminds users to generate acceptance criteria first.

### Configuration Scope

This setting is **per-repository** (stored in `.beads/config.yaml`), not global. There is no global bd config for this behavior, so it must be wired into every `bd init` to enforce consistency across projects.

### Setting Idempotency

Running `bd config set validation.on-create warn` multiple times is safe and idempotent. It's safe to re-run after beads is already initialized.

## Skipping Beads If Already Present

If `.beads/` directory already exists:
1. Skip the `bd init` command
2. Still run `bd config set validation.on-create warn` to ensure the validation setting is in place (safe to re-run)

Note in the final report: "beads — already initialized, validation.on-create=warn confirmed"

## Tool Availability Check

Before attempting beads setup:
```bash
command -v bd >/dev/null 2>&1 || { echo "bd not found — install beads before continuing"; exit 1; }
```

If bd is not available, the component fails with a clear error message.

## Dependency: Git Must Exist First

Beads initialization requires a `.git/` repository to already exist or to be initialized in the same workflow. When presenting the menu, if the user selects beads (4) but git is not yet set up, auto-add git to the selection.
