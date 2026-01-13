---
description: List recent Process Engine executions
model: claude-sonnet-4-5
---

# List Process Executions

List recent Process Engine executions with their status.

## Arguments

$ARGUMENTS

Parse arguments:
- `--limit N`: Number of processes to show (default: 10)
- `--status <status>`: Filter by status (running, completed, failed, awaiting_gate)

## Action

```bash
curl -s "http://localhost:8001/api/v1/process?limit=<limit>&status_filter=<status>" | jq
```

## Output Format

Present as a table:

```
Recent Process Executions
=========================

| ID (short) | Epic ID | Title | Status | Phase | Started |
|------------|---------|-------|--------|-------|---------|
| abc123... | baseball-v3-63d | Two-way players | completed | phase_5 | 2h ago |
| def456... | baseball-v3-PE1 | Process Engine | running | phase_3 | 10m ago |
| ghi789... | baseball-v3-nk8 | Fix admin auth | failed | phase_4 | 1d ago |

Total: X processes (Y running, Z completed, W failed)
```

## Quick Actions

Based on the list, suggest relevant actions:

**If there are RUNNING processes:**
```
Active processes: X

Monitor the most recent: /process status <id>
```

**If there are AWAITING_GATE processes:**
```
Processes awaiting approval: X

Approve: /process approve <id>
```

**If there are FAILED processes:**
```
Failed processes: X

Retry: /process retry <id>
Or view details: /process status <id>
```
