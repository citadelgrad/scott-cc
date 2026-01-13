---
event: PostToolUse
match_tool: Bash
match_pattern: "bd close"
---

# Process Engine Auto-Suggestion Hook

This hook triggers after closing Beads tasks to suggest running the Process Engine when an epic is complete.

## Trigger Conditions
- Tool: Bash
- Command contains: `bd close`

## Logic

When a Beads task is closed, check if it completes an epic:

1. **Extract the closed task ID** from the command output
2. **Check if the task is part of an epic** (format: `epic-id.N`)
3. **List remaining open tasks in the epic**
4. **If all tasks are closed**, suggest running the Process Engine

## Implementation

After `bd close` completes successfully:

```bash
# Get the epic ID from the closed task (e.g., baseball-v3-63d.1 → baseball-v3-63d)
TASK_ID="<from command>"
EPIC_ID=$(echo "$TASK_ID" | sed 's/\.[0-9]*$//')

# Check if this looks like a subtask (has .N suffix)
if [[ "$TASK_ID" =~ \.[0-9]+$ ]]; then
  # List open tasks for this epic
  OPEN_TASKS=$(bd list --status=open --epic="$EPIC_ID" 2>/dev/null | wc -l)

  if [ "$OPEN_TASKS" -eq 0 ]; then
    # All tasks complete - suggest process validation
    echo "SUGGEST_PROCESS: $EPIC_ID"
  fi
fi
```

## Suggestion Message

When all epic tasks are closed:

```
All tasks in epic <epic-id> are complete!

Would you like to run the 5-phase Process Engine validation?
This will:
1. Verify infrastructure standards
2. Run code review and security audit
3. Execute tests and linter
4. Get secondary LLM review
5. Complete sign-off verification

Start validation: /process start <epic-id>
```

## User Response Handling

- **If user says "yes", "sure", "go ahead"**: Run `/process start <epic-id>`
- **If user declines**: Acknowledge and continue
- **If user asks questions**: Explain the Process Engine phases

## Notes

- Only suggest for epics (tasks with subtasks)
- Don't suggest if process already running for this epic
- Don't interrupt urgent work - suggestion should be non-blocking
