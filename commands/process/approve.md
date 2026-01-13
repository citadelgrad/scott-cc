---
description: Approve Phase 1 architecture gate
model: claude-sonnet-4-5
---

# Approve Architecture Gate

Approve the Phase 1 architecture gate to allow the process to continue.

## Arguments

$ARGUMENTS

Parse arguments:
- `process_id`: Required process ID to approve

## Context

Phase 1 creates research tasks and sets up the Beads epic. Before proceeding to
implementation phases (2-5), the architecture must be reviewed and approved.

This gate ensures that:
- Architecture design is finalized
- All research tasks are reviewed
- Implementation plan is approved

## Action

1. First, verify the process is in AWAITING_GATE status:
```bash
curl -s http://localhost:8001/api/v1/process/<process_id>/status | jq -r '.status'
```

2. If status is "awaiting_gate", approve the architecture:
```bash
curl -X POST http://localhost:8001/api/v1/process/<process_id>/approve-architecture \
  -H "Content-Type: application/json" \
  -d '{"approved": true}'
```

## Output

On success:
```
Architecture Approved

Process <process_id> is now continuing to Phase 2: Infrastructure & Standards.

The remaining phases will run automatically:
- Phase 2: Infrastructure validation
- Phase 3: Quality Gate (code review + security audit)
- Phase 4: Validation (tests + commits)
- Phase 5: Final Audit (secondary LLM review)

Monitor progress: /process status <process_id>
```

On error (wrong status):
```
Cannot approve - process is not awaiting architecture approval.

Current status: <status>
Current phase: <phase>

Use /process status <process_id> for more details.
```
