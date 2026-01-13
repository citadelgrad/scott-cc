---
description: Start Process Engine validation for a Beads epic
model: claude-sonnet-4-5
---

# Start Process Engine Validation

Start the 5-phase validation process for the given Beads epic.

## Arguments

$ARGUMENTS

Parse the arguments to extract:
- `epic_id`: The Beads epic ID (e.g., baseball-v3-63d)
- `title`: Optional title override (default: use epic title from Beads)

## Process Engine Phases

The process will run through 5 mandatory phases:
1. **Phase 1: Research & Epic Setup** - Creates research tasks, requires architecture approval
2. **Phase 2: Infrastructure & Standards** - Validates Podman, Makefile, logging
3. **Phase 3: Quality Gate** - Code review + DRY analysis + security audit (primary LLM)
4. **Phase 4: Validation & Commits** - Run tests, linter, auto-commit
5. **Phase 5: Final Audit** - Secondary LLM audit + sign-off verification

## Action

1. First, verify the Jobs API is running:
```bash
curl -sf http://localhost:8001/api/v1/health || echo "Jobs API not running - start with: make jobs-all"
```

2. Get epic details from Beads (for title if not provided):
```bash
bd show <epic_id>
```

3. Start the process:
```bash
curl -X POST http://localhost:8001/api/v1/process \
  -H "Content-Type: application/json" \
  -d '{
    "beads_epic_id": "<epic_id>",
    "title": "<title or epic title>",
    "description": "Process Engine validation for <epic_id>",
    "config": {
      "architecture_finalized": false,
      "auto_commit": true,
      "require_signoff": true
    }
  }'
```

## Output

Report the following:
- Process ID (for tracking)
- Initial status
- Current phase
- Next action needed (usually: wait for Phase 1 to request architecture approval)

Example output:
```
Process started: abc123-def456
Status: RUNNING
Phase: phase_1_research_setup

Phase 1 will create research tasks and then request architecture approval.
Monitor with: /process status abc123-def456
```
