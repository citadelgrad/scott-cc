---
name: handoff
description: Generate a compact session handoff before clearing context. Captures git state, active work, key files, and concrete next actions for a fast reload.
allowed-tools: Bash, Read, Glob, Grep
---

# /handoff — Session reload document

Generate a compact handoff document the user can paste into a fresh session.

## Arguments

`$ARGUMENTS`

Optional focus text. If provided, emphasize that repo, feature, incident, or workflow in the handoff.

## Collect context

Run these read-only checks and continue if any nonessential command fails:

```bash
git status --short
git branch --show-current
git log --oneline -10
git diff --stat
```

If the repo uses a task tracker and the CLI is available, collect active/open work without creating or modifying tasks. Examples:

```bash
command -v bd >/dev/null 2>&1 && bd list --status=in_progress || true
command -v bd >/dev/null 2>&1 && bd list --status=open || true
```

Do not initialize or configure a new task tracker. Missing task tooling is not a blocker; note it briefly in the output only if it affects next actions.

Review modified/created files from `git status` and `git diff --stat`. Read only the specific files needed to describe current state accurately.

## Output

Produce only this fenced block. No prose before or after.

```markdown
## Handoff — YYYY-MM-DD

### Completed this session
- ...

### In progress
- ...

### Open / next
- ...

### Key files touched
- path: one-line reason

### Next actions
- exact command or concrete physical action

### Context that would be lost
- decision, constraint, blocker, or rationale
```

## Rules

- Keep it under 50 lines.
- Make next actions concrete: commands, URLs, files, or exact decisions needed.
- Prefer facts from the repo over memory.
- Preserve blockers and uncertainty explicitly.
- Do not paste raw logs unless one line is essential evidence.
