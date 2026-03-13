---
name: epic-swarm
description: Build all tasks in a beads epic using parallel worker agents in isolated worktrees, with CE code review after
argument-hint: "<epic-id> [--max-parallel 3] [--no-review] [--dry-run]"
---

# Epic Swarm Builder

Execute all tasks in a beads epic by spawning parallel worker agents in isolated git worktrees, then run a comprehensive code review.

## Arguments

$ARGUMENTS

Parse arguments:
- `epic_id` (required): The beads epic ID
- `--max-parallel N`: Max concurrent workers per wave (default: 3)
- `--no-review`: Skip the CE code review phase
- `--dry-run`: Show the wave plan without executing

---

## Checkpoint System

**This is critical.** The orchestrator context will fill up on large epics. Checkpointing lets you survive context compaction and resume mid-epic.

### Checkpoint File

After every phase boundary AND after every wave, write state to `.claude/epic-swarm/<epic-id>/checkpoint.json`:

```json
{
  "epic_id": "<epic-id>",
  "epic_title": "<title>",
  "branch": "<feature-branch-name>",
  "default_branch": "<main or master>",
  "max_parallel": 3,
  "skip_review": false,
  "current_phase": "waves",
  "wave_plan": {
    "total_waves": 3,
    "waves": {
      "1": ["task-aaa", "task-bbb"],
      "2": ["task-ccc"],
      "3": ["task-ddd", "task-eee"]
    }
  },
  "current_wave": 2,
  "completed_waves": [1],
  "tasks_completed": ["task-aaa", "task-bbb"],
  "tasks_failed": [],
  "tasks_remaining": ["task-ccc", "task-ddd", "task-eee"],
  "merged_branches": ["worktree-abc", "worktree-def"],
  "review_findings": null,
  "updated_at": "<ISO timestamp>"
}
```

### On Every Invocation — Check for Checkpoint FIRST

**Before doing anything else**, check if a checkpoint exists:

```bash
cat .claude/epic-swarm/<epic-id>/checkpoint.json 2>/dev/null
```

**If checkpoint exists:**
1. Read it
2. Report current state to the user: "Resuming epic `<id>` — Wave <N> of <total>, <X> tasks done, <Y> remaining"
3. Skip to the appropriate phase/wave based on `current_phase` and `current_wave`
4. Do NOT re-load the epic or re-plan waves — use the wave plan from the checkpoint

**If no checkpoint:**
1. This is a fresh run — proceed to Phase 1
2. Create the output directory: `mkdir -p .claude/epic-swarm/<epic-id>`

### When to Write Checkpoint

Write/update the checkpoint at these moments:
- After Phase 1 (wave plan created)
- After each wave completes in Phase 2
- After Phase 3 (review complete)
- After Phase 4 (shipped)

**Always update `updated_at` with the current timestamp.**

---

## Phase 1: Load Epic & Plan Waves

### Step 1.1: Load Epic

```bash
bd show <epic_id>
```

If the epic doesn't exist, stop and tell the user.

### Step 1.2: Load All Tasks

```bash
bd list --status=open
```

Filter for tasks that are children of this epic. For each task, run `bd show <task-id>` to get:
- Title, description, notes (these contain the implementation details)
- Dependencies (what blocks this task)
- Status

If no open tasks exist, tell the user the epic has no work to do.

### Step 1.3: Build Wave Plan

Group tasks into sequential **waves** based on dependencies:

```
Wave 1: Tasks with NO unfinished blockers (can start immediately)
Wave 2: Tasks whose blockers are ALL in Wave 1
Wave 3: Tasks whose blockers are ALL in Waves 1-2
...continue until all tasks assigned
```

**Rules:**
- Tasks within the same wave run in parallel
- A wave starts only after ALL tasks in the previous wave are complete
- If `--max-parallel N` is set, limit each wave to N concurrent agents
- Tasks with circular dependencies are flagged as errors

### Step 1.4: Present Wave Plan

Show the user:

```markdown
## Epic Swarm Plan: <epic-title>

### Wave 1 (parallel - N tasks)
- [ ] <task-id>: <title>
- [ ] <task-id>: <title>

### Wave 2 (parallel - N tasks, after Wave 1)
- [ ] <task-id>: <title> (depends on: <task-ids>)

### Wave 3 ...

**Total tasks:** N
**Estimated waves:** N
**Max parallel per wave:** N
**Code review after:** Yes/No
```

If `--dry-run`, stop here. Otherwise, ask: "Ready to start building? (yes/no)"

### Step 1.5: Create Feature Branch

```bash
current_branch=$(git branch --show-current)
default_branch=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
if [ -z "$default_branch" ]; then
  default_branch=$(git rev-parse --verify origin/main >/dev/null 2>&1 && echo "main" || echo "master")
fi
```

If already on a feature branch, ask whether to continue on it.
If on the default branch, create a new branch:

```bash
git checkout -b feat/<epic-id>
```

### Step 1.6: Write Initial Checkpoint

```bash
mkdir -p .claude/epic-swarm/<epic-id>
```

Write checkpoint with `current_phase: "waves"`, `current_wave: 1`, the full wave plan, and all tasks in `tasks_remaining`.

---

## Phase 2: Execute Waves

For each wave, execute all tasks in parallel using isolated worktrees.

### Step 2.1: Mark Tasks In-Progress

For each task in the current wave:
```bash
bd update <task-id> --status=in_progress
```

### Step 2.2: Spawn Worker Agents

For each task in the wave, spawn an Agent with `isolation: "worktree"`:

```
Agent(
  description: "Implement <task-id>",
  subagent_type: "general-purpose",
  isolation: "worktree",
  mode: "auto",
  prompt: "<worker prompt - see below>"
)
```

**Launch all agents for the wave in a SINGLE message** so they run in parallel.

If the wave has more tasks than `--max-parallel`, split into sub-batches:
- Launch first N agents
- Wait for them to complete
- Launch next N agents
- Repeat

### Worker Agent Prompt Template

For each task, construct this prompt:

```
You are a CODE IMPLEMENTER. Your ONLY job is to write production code for one task.

## Your Task

**ID:** <task-id>
**Title:** <title>
**Description:**
<full description from bd show>

**Implementation Notes:**
<full notes field from bd show - this contains the actual code/specs to implement>

## Instructions

1. Read the task description and notes carefully - they contain what to build
2. Explore the codebase briefly to understand existing patterns (spend at most 2-3 file reads for orientation)
3. IMPLEMENT the code changes described in the task
4. Write tests for your changes if the task involves testable logic
5. Run the project's test command to verify nothing is broken
6. Fix any test failures before finishing

## Rules

- IMPLEMENT, don't research. The task notes tell you what to build.
- Follow existing code patterns and conventions in the project
- Do NOT refactor code unrelated to your task
- Do NOT create planning documents or research notes
- Do NOT install new dependencies unless the task explicitly requires it
- Keep changes focused and minimal - only what the task requires
- If the task notes contain code snippets, use them as your starting point

## You Are Done When

- The code changes described in the task are complete
- Tests pass (or new tests are written and pass)
- Your changes are committed in the worktree
```

**Important:** Include the FULL task description and notes in the prompt. Workers have no access to beads commands or the parent conversation. They need all context embedded in their prompt.

### Step 2.3: Collect Results

After all agents in the wave complete, for each agent result:

1. **If the agent made changes** (worktree path and branch returned):
   - Note the branch name for merging
2. **If the agent made no changes:**
   - Log that the task may not have needed code changes
   - Investigate if the task was supposed to produce changes

### Step 2.4: Merge Worktree Branches

For each completed worktree branch with changes, merge into the feature branch:

```bash
git merge <worktree-branch> --no-edit
```

**If merge conflicts occur:**
1. List the conflicting files
2. Read the conflict markers
3. Resolve conflicts intelligently (both agents' changes should be kept if they're in different parts of the file)
4. If conflicts are too complex, tell the user and ask for guidance

**After merging each branch:**
```bash
git branch -d <worktree-branch>  # Clean up the temporary branch
```

### Step 2.5: Verify & Close Tasks

After merging all branches for the wave:

```bash
# Run tests to verify merged code works
# Use project's test command (pytest, npm test, vitest, etc.)
```

If tests pass, close all tasks in the wave:
```bash
bd close <task-id-1> <task-id-2> ...
```

If tests fail:
1. Identify which merge caused the failure
2. Fix the issue
3. Re-run tests
4. Only close tasks whose code is working

### Step 2.6: Write Wave Checkpoint

**After every wave**, update the checkpoint:
- Move completed task IDs from `tasks_remaining` to `tasks_completed`
- Add any failed task IDs to `tasks_failed`
- Increment `current_wave`
- Add the wave number to `completed_waves`
- Record merged branch names in `merged_branches`
- Update `updated_at`

This is the most important checkpoint write. If context compacts between waves, the orchestrator can read this file and know exactly where to resume.

### Step 2.7: Report Wave Progress

After each wave, report:

```markdown
## Wave N Complete

**Tasks completed:** N/N
- [x] <task-id>: <title> - <brief summary of changes>
- [x] <task-id>: <title> - <brief summary of changes>

**Tests:** PASS/FAIL
**Merge conflicts:** None / Resolved N conflicts
**Next wave:** Wave N+1 (N tasks)
```

### Step 2.8: Repeat for Next Wave

Continue to the next wave. The dependencies from completed waves are now satisfied.

Loop until all waves are complete.

After the final wave, update checkpoint: `current_phase: "review"`.

---

## Phase 3: Code Review

**Skip this phase if `--no-review` was passed.** Update checkpoint to `current_phase: "ship"` and jump to Phase 4.

After all tasks are implemented, run a comprehensive code review using CE's review agents.

### Step 3.1: Determine Review Agents

Check if `compound-engineering.local.md` exists in the project root.
- If yes: read `review_agents` from its YAML frontmatter
- If no: use these defaults:
  - `compound-engineering:review:architecture-strategist`
  - `compound-engineering:review:code-simplicity-reviewer`
  - `compound-engineering:review:security-sentinel`
  - `compound-engineering:review:performance-oracle`

### Step 3.2: Launch Review Agents in Parallel

Get the diff of all changes:
```bash
git diff <default-branch>...HEAD
```

Spawn all review agents in parallel:

```
Agent(
  description: "Architecture review",
  subagent_type: "compound-engineering:review:architecture-strategist",
  prompt: "Review the following code changes for architectural concerns.

<git diff output>

Focus on:
- Pattern compliance and design integrity
- Cross-cutting concerns
- Coupling and cohesion issues

Return a concise list of findings with severity (CRITICAL/IMPORTANT/NICE-TO-HAVE).",
  run_in_background: true
)

Agent(
  description: "Simplicity review",
  subagent_type: "compound-engineering:review:code-simplicity-reviewer",
  prompt: "Review the following code changes for unnecessary complexity.

<git diff output>

Focus on:
- YAGNI violations
- Over-engineering
- Simplification opportunities

Return a concise list of findings with severity.",
  run_in_background: true
)

// ... same pattern for security-sentinel, performance-oracle, etc.
```

### Step 3.3: Collect & Apply Review Findings

After all review agents complete:

1. **Categorize findings:**
   - **CRITICAL:** Fix immediately before proceeding
   - **IMPORTANT:** Fix now, they matter
   - **NICE-TO-HAVE:** Note for later, don't block shipping

2. **For CRITICAL and IMPORTANT findings:**
   - Fix the issues directly
   - Run tests again after fixes

3. **Present review summary to user:**

```markdown
## Code Review Results

**Review agents used:** architecture-strategist, code-simplicity-reviewer, security-sentinel, performance-oracle

### Findings
| Severity | Finding | Status |
|----------|---------|--------|
| CRITICAL | <description> | Fixed |
| IMPORTANT | <description> | Fixed |
| NICE-TO-HAVE | <description> | Noted |

### Actions Taken
- Fixed N critical issues
- Fixed N important issues
- N nice-to-have items noted for follow-up
```

### Step 3.4: Write Review Checkpoint

Update checkpoint:
- `current_phase: "ship"`
- `review_findings`: summary object with counts by severity and list of findings

---

## Phase 4: Ship

### Step 4.1: Final Test Run

```bash
# Run the full test suite one final time
# pytest / npm test / vitest / etc.
```

### Step 4.2: Commit Any Review Fixes

If Phase 3 produced fixes:
```bash
git add -A
git commit -m "refactor: address code review findings for <epic-id>"
```

### Step 4.3: Close Epic

```bash
bd close <epic-id>
```

### Step 4.4: Push & Report

```bash
git push -u origin <branch-name>
```

Present final summary:

```markdown
## Epic Swarm Complete

**Epic:** <epic-id> - <title>
**Branch:** <branch-name>
**Tasks completed:** N/N
**Waves executed:** N
**Review findings fixed:** N critical, N important

### Changes by Task
- <task-id>: <title> - <files changed summary>
- <task-id>: <title> - <files changed summary>

### Next Steps
- Create a PR: `gh pr create`
- Or review the branch: `git log --oneline <default-branch>..HEAD`
```

### Step 4.5: Write Final Checkpoint

Update checkpoint:
- `current_phase: "complete"`
- Add `completed_at` timestamp

The checkpoint directory can be cleaned up later:
```bash
rm -rf .claude/epic-swarm/<epic-id>
```

---

## Error Handling

### Task Implementation Failure
If a worker agent fails to implement a task:
1. Log the failure with details
2. Add to `tasks_failed` in checkpoint
3. Skip the task (don't close it in beads)
4. Continue with remaining tasks in the wave
5. Report failed tasks at the end

### Merge Conflict Deadlock
If merge conflicts can't be auto-resolved:
1. Show the conflicting files and changes from each agent
2. Ask the user to choose a resolution strategy:
   - Keep agent A's changes
   - Keep agent B's changes
   - Manual merge (show both sides)

### Test Failures After Merge
If tests fail after merging a wave:
1. Identify the likely cause by checking which merge introduced the failure
2. Attempt to fix
3. If unfixable, roll back the problematic merge and skip that task
4. Report the skipped task

### Epic Has No Ready Tasks
If no tasks are ready but open tasks exist:
1. Show blocked tasks and what they're waiting on
2. Ask the user if they want to resolve blockers manually

### Context Compaction Mid-Epic
If you lose context and are re-invoked:
1. The checkpoint file tells you exactly where you left off
2. Read it, report state to user, continue from the current wave
3. You do NOT need to re-read the epic or re-plan waves — it's all in the checkpoint

---

## Key Design Decisions

**Why worktrees instead of sequential implementation:**
- Parallel execution is 2-5x faster for independent tasks
- Worktrees provide true isolation — no file conflicts during implementation
- Each agent has a clean working tree to reason about

**Why `general-purpose` agents, not specialized ones:**
- Implementation tasks need full tool access (Read, Write, Edit, Bash, Grep, Glob)
- Specialized agents (Explore, Plan) are read-only and can't write code
- The task notes contain all the context — no research needed

**Why waves instead of a free-for-all swarm:**
- Respects beads dependency ordering
- Prevents merge hell from too many parallel branches
- Each wave produces a known-good state before the next starts

**Why CE review at the end, not per-task:**
- Review agents see the full picture of all changes together
- Catches cross-cutting concerns that per-task review would miss
- More efficient (one review pass vs. N passes)

**Why checkpointing, not TeammateTool:**
- Workers don't need to talk to each other — tasks are self-contained
- Checkpointing is simpler and survives context compaction
- TeammateTool adds inbox messaging overhead that isn't needed here
- If you need inter-agent coordination (agents negotiating file ownership, shared state), use TeammateTool via a separate command
