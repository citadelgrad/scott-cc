---
description: Build a complete feature from a beads epic with architecture review, implementation, and validation
model: claude-sonnet-4-5
---

# Build Feature

Orchestrate complete feature development for a beads epic.

## Arguments

$ARGUMENTS

Parse the arguments to extract:
- `epic_id`: The beads epic ID (required)

## Action

You are now operating as the **feature-builder** agent. Read the full agent instructions from:
`/Users/scott/projects/scott-cc/agents/feature-builder.md`

Execute the 6-phase workflow:

1. **Phase 1: Epic Setup** - Verify epic, mark in-progress
2. **Phase 2: Architecture Review** - Run system-architect (always), frontend-architect (if needed), backend-architect (if needed)
3. **Phase 3: Implementation** - Loop through ready tasks, implement following standards
4. **Phase 4: Quality Review** - DRY/KISS review via simplifier skills
5. **Phase 5: Validation** - Tests, lint, types, security, migrations, docs
6. **Phase 6: Final Review** - Verify complete, commit, close epic

## Before Starting

Confirm with the user:
1. The epic ID is correct
2. Any preferences for the implementation approach
3. Whether to pause at architecture review for approval (recommended for large epics)

## Progress Reporting

After each phase, report:
- Phase completed
- Key outcomes/changes
- Any issues encountered
- Next phase starting

## Example Usage

```
/build-feature my-epic-123
```

This will:
1. Load epic `my-epic-123` from beads
2. Run architecture review with relevant architects
3. Implement all tasks following code quality standards
4. Validate with tests, security, and documentation
5. Commit and close the epic
