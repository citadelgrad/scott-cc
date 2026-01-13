---
description: Check Process Engine execution status
model: claude-sonnet-4-5
---

# Check Process Status

Check the status of a Process Engine execution.

## Arguments

$ARGUMENTS

Parse arguments:
- `process_id`: Optional process ID. If not provided, show most recent process.

## Action

1. If no process_id provided, list recent processes and use the most recent:
```bash
curl -s http://localhost:8001/api/v1/process?limit=1 | jq -r '.processes[0].id'
```

2. Get detailed status:
```bash
curl -s http://localhost:8001/api/v1/process/<process_id> | jq
```

## Output Format

Present the status in a clear format:

```
Process: <id>
Epic: <beads_epic_id>
Title: <title>

Status: <status>
Current Phase: <current_phase>

Phase History:
- Phase 1: Research & Epic Setup [status]
- Phase 2: Infrastructure [status]
- Phase 3: Quality Gate [status] (attempts: X)
- Phase 4: Validation [status]
- Phase 5: Final Audit [status]

<conditional sections based on status>
```

## Status-Specific Actions

**If AWAITING_GATE:**
```
Action Required: Architecture approval needed

The Process Engine has completed Phase 1 setup and is waiting for you to approve
the architecture before proceeding. Review the research tasks created and approve:

/process approve <process_id>
```

**If FAILED:**
```
Process Failed at <phase>

Error: <last_error>

Options:
1. Fix the issue and retry: /process retry <process_id>
2. Cancel the process: curl -X DELETE http://localhost:8001/api/v1/process/<process_id>
```

**If RUNNING:**
```
Process is running Phase <X>...

This phase typically takes 1-5 minutes. Check back with:
/process status <process_id>
```

**If COMPLETED:**
```
Process COMPLETED

All 5 phases passed:
- Phase 1: Research & Epic Setup
- Phase 2: Infrastructure & Standards
- Phase 3: Quality Gate (X attempts)
- Phase 4: Validation & Commits
- Phase 5: Final Audit

Feature is validated and ready for deployment.
```
