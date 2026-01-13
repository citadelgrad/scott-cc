---
description: Retry a failed Process Engine execution
model: claude-sonnet-4-5
---

# Retry Failed Process

Retry a Process Engine execution that has failed.

## Arguments

$ARGUMENTS

Parse arguments:
- `process_id`: Required process ID to retry

## Context

Processes can fail at various phases:
- **Phase 2**: Infrastructure checks failed (Makefile missing, logging not configured)
- **Phase 3**: Code review or security audit found critical issues
- **Phase 4**: Tests failed or linter errors
- **Phase 5**: Secondary audit or sign-off failed

The retry will restart from the current (failed) phase.

## Action

1. First, verify the process is in FAILED status:
```bash
curl -s http://localhost:8001/api/v1/process/<process_id>/status | jq
```

2. If status is "failed", show the error and retry:
```bash
# Show what failed
curl -s http://localhost:8001/api/v1/process/<process_id> | jq -r '.last_error'

# Retry
curl -X POST http://localhost:8001/api/v1/process/<process_id>/retry \
  -H "Content-Type: application/json"
```

## Output

On success:
```
Process Retry Started

Process <process_id> is retrying from <current_phase>.

Previous error: <last_error>

The process will attempt to complete the failed phase again.
Monitor progress: /process status <process_id>
```

On error (wrong status):
```
Cannot retry - process is not in failed status.

Current status: <status>

Retry is only available for failed processes.
Use /process status <process_id> for more details.
```

## Common Failure Scenarios

**Phase 2 failures (Infrastructure):**
- Missing Makefile targets → Add required targets (up, down, logs)
- JSON logging not configured → Update logging config

**Phase 3 failures (Quality Gate):**
- Code review issues → Address the findings
- Security vulnerabilities → Fix the security issues

**Phase 4 failures (Validation):**
- Test failures → Fix failing tests
- Linter errors → Run `uv run ruff check --fix`

**Phase 5 failures (Final Audit):**
- Secondary audit issues → Address the findings
- Sign-off gaps → Complete the missing requirements
