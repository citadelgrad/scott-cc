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

Fetch every child task in **one call** and write the full JSON straight to a file — never `bd show` per task, and never read the full payload into your own context:

```bash
mkdir -p .claude/epic-swarm/<epic-id>
bd list --parent=<epic_id> --status=open --json > .claude/epic-swarm/<epic-id>/tasks.json
```

Then pull only the compact fields you actually need to plan waves:

```bash
jq -r '.[] | "\(.id)|\(.title)|\(.status)|\(.dependencies|join(","))"' .claude/epic-swarm/<epic-id>/tasks.json
```

That id/title/status/deps table is everything Step 1.3 needs. The full `description` and `acceptance_criteria` for every task stay on disk in `tasks.json` — Phase 2 hands worker agents the file path instead of pasting their contents into your context.

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

### Step 2.2: Spawn ONE Wave Coordinator

**Do not** spawn workers directly, and do not merge or run tests yourself. Both dump large amounts of output — `git merge` logs, full test suite runs — straight into your context, which is the thing that fills it up on large epics. Instead, spawn a single coordinator agent for the wave that does that noisy work in its **own** context and hands you back a small JSON summary.

```
Agent(
  description: "Coordinate wave <N> for epic <epic-id>",
  subagent_type: "general-purpose",
  mode: "auto",
  prompt: "<wave coordinator prompt - see below>"
)
```

Do **not** set `isolation: "worktree"` on the coordinator itself — it needs to run in the real checkout on `<feature-branch>` so its merges land there directly. (The workers it spawns get `isolation: "worktree"`.)

If the wave has more tasks than `--max-parallel`, tell the coordinator that limit and let it sub-batch its worker spawns internally — it still returns one summary for the whole wave.

### Wave Coordinator Prompt Template

```
You are the WAVE COORDINATOR for wave <N> of epic <epic-id>. You are running
in the real repo checkout on branch <feature-branch>.

## Tasks this wave
<task-id-1>, <task-id-2>, ...

Full details for every task (description, acceptance_criteria, dependencies)
are already on disk — do NOT ask beads for them yourself:
  <absolute-path-to-repo>/.claude/epic-swarm/<epic-id>/tasks.json

## What to do

1. For each task ID above, spawn an Agent (isolation: "worktree",
   subagent_type: "general-purpose") with a prompt that tells it to:
   - Pull its own entry out of tasks.json, e.g.:
     jq '.[] | select(.id=="<task-id>")' <absolute-path>/.claude/epic-swarm/<epic-id>/tasks.json
   - Implement the code change it describes, write tests if the task
     involves testable logic, run the project's test command, fix
     failures, and commit.
   - Follow existing code patterns; don't refactor unrelated code; don't
     install new dependencies unless the task requires it.
   Launch ALL of this wave's workers in a SINGLE message so they run in
   parallel (max <max-parallel> at once — sub-batch if there are more).

2. After every worker finishes, for each one that returned a worktree
   branch with changes: `git merge <branch> --no-edit`, redirecting output
   to a scratch file rather than printing it. Resolve simple conflicts
   yourself (keep both sides' changes if they touch different parts of a
   file); if a conflict is too ambiguous to resolve confidently, leave it
   unmerged and report it — don't guess. `git branch -d <branch>` after
   each clean merge.

3. Run the project's test command exactly once, after all merges, with
   output redirected to a file (e.g. `<test-cmd> >
   <absolute-path-to-repo>/.claude/epic-swarm/<epic-id>/wave-<N>-tests.log
   2>&1`). Only inspect that file for pass/fail and failing test names.

4. Return ONLY this JSON as your final message — no prose, no pasted
   command output, no test logs:

{
  "wave": <N>,
  "tasks_completed": ["<id>", ...],
  "tasks_failed": [{"id": "<id>", "reason": "<one line>"}],
  "test_status": "pass" | "fail",
  "failure_summary": "<one paragraph, or null>",
  "merged_branches": ["<branch>", ...],
  "unresolved_conflicts": [{"branch": "<branch>", "files": ["..."]}]
}
```

**Important:** The coordinator prompt only needs task IDs and the path to `tasks.json` — never paste task descriptions into it. The coordinator reads them itself, in its own context, not yours.

### Step 2.3: Handle the Coordinator's Result

The coordinator's returned JSON is small — safe to read in full.

- `unresolved_conflicts` non-empty → stop, show the user the conflicting branch/files, follow Error Handling below.
- `test_status: "fail"` → show the user `failure_summary` only. If it needs deeper investigation, spawn a fresh small agent to dig in rather than re-running the suite yourself in the foreground.
- Otherwise, close the completed tasks:

```bash
bd close <task-id-1> <task-id-2> ...
```

Tasks listed in `tasks_failed` stay open — don't close them.

### Step 2.4: Write Wave Checkpoint

**After every wave**, update the checkpoint:
- Move completed task IDs from `tasks_remaining` to `tasks_completed`
- Add any failed task IDs to `tasks_failed`
- Increment `current_wave`
- Add the wave number to `completed_waves`
- Record merged branch names in `merged_branches`
- Update `updated_at`

This is the most important checkpoint write. If context compacts between waves, the orchestrator can read this file and know exactly where to resume.

### Step 2.5: Report Wave Progress

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

### Step 2.6: Repeat for Next Wave

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

Write the diff to a file — do **not** print it to your own context, and do not paste it inline into each agent's prompt (that quadruplicates a potentially huge diff across one message):

```bash
git diff <default-branch>...HEAD > .claude/epic-swarm/<epic-id>/review-diff.patch
git diff --stat <default-branch>...HEAD  # small, safe to glance at for sanity
```

Spawn all review agents in parallel, each pointed at the file by path:

```
Agent(
  description: "Architecture review",
  subagent_type: "compound-engineering:review:architecture-strategist",
  prompt: "Read the diff at <absolute-path-to-repo>/.claude/epic-swarm/<epic-id>/review-diff.patch and review it for architectural concerns.

Focus on:
- Pattern compliance and design integrity
- Cross-cutting concerns
- Coupling and cohesion issues

Return a concise list of findings with severity (CRITICAL/IMPORTANT/NICE-TO-HAVE) — no pasted code, just file:line + description.",
  run_in_background: true
)

Agent(
  description: "Simplicity review",
  subagent_type: "compound-engineering:review:code-simplicity-reviewer",
  prompt: "Read the diff at <absolute-path-to-repo>/.claude/epic-swarm/<epic-id>/review-diff.patch and review it for unnecessary complexity.

Focus on:
- YAGNI violations
- Over-engineering
- Simplification opportunities

Return a concise list of findings with severity — no pasted code, just file:line + description.",
  run_in_background: true
)

// ... same pattern for security-sentinel, performance-oracle, etc. — every
// agent reads the same file, none of them get the diff pasted into their prompt.
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

Redirect output to a file and only report pass/fail — don't let a full suite run dump into your context:

```bash
# pytest / npm test / vitest / etc., e.g.:
<test-cmd> > .claude/epic-swarm/<epic-id>/final-tests.log 2>&1 && echo PASS || echo FAIL
```

On FAIL, inspect the log file for the failing test names only, not the whole run.

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

Ask the user before pushing — "Push `<branch-name>` to origin? (yes/no)" — pushing is a shared, hard-to-reverse action and needs a fresh confirmation even if the user approved the epic run earlier. If they decline, skip straight to the final summary.

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
If the wave coordinator reports a task in `tasks_failed`:
1. Add it to `tasks_failed` in checkpoint (from the coordinator's `reason`)
2. Skip the task (don't close it in beads)
3. Report failed tasks at the end

### Merge Conflict Deadlock
If the coordinator reports non-empty `unresolved_conflicts`, the repo is sitting exactly where it left it — the conflict markers are still in those specific files in the working tree. Only look at the files it listed, not the whole diff:
1. Read the conflict markers in the listed files
2. Ask the user to choose a resolution strategy:
   - Keep one side's changes
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

**Why a wave coordinator, not the orchestrator itself, spawns workers and merges/tests:**
- `bd show`/`bd list` output, `git merge` logs, and test suite runs are the actual source of context bloat on large epics — not the worker agents, which were already delegated
- Every one of those is now written to a file or absorbed into a subagent's own context; the orchestrator only ever sees compact JSON summaries and small id/title/status tables
- The orchestrator's context now scales with *wave count*, not with total task/test/diff volume — that's what lets it survive a 20-task epic without compacting
