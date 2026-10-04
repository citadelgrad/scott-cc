---
name: delegate-first
description: >-
  Use when a task involves multiple file reads, code edits, builds, or verbose
  shell output that would flood the main conversation context. Also use when
  work splits into parallel research or implementation tracks.
license: MIT
metadata:
  category: technique
  triggers: [subagent, delegation, fork, context-pollution, noisy-output, worktree, parallel-work, multi-file-edit, build-logs, verbose-output]
---

# Delegate First

Keep the parent focused on coordination and decisions. Prefer bounded native
workers for noisy implementation, research and verification when available.
The user can always request inline work; simple answers need no delegation.

## Capability preflight

Read [worker-adapters.md](references/worker-adapters.md) before dispatch. Discover
the actual native tool and live schema; never assume Claude-specific tools,
named plugin agents, a fork type or a version-dependent parameter exists.
Record context isolation separately from filesystem isolation.

- **Native workers available:** use the host's real dispatch/wait mechanism.
  For ordinary implementation, inherited context may be useful. A fork inheriting
  conversation is not independent and cannot provide clean-room validation.
- **No delegation capability:** explicitly choose bounded **sequential** execution
  in the current conversation, save verbose logs as artifacts, and return short
  summaries. This is not independent or parallel. Do not invent API calls.
- **Independence required but unavailable:** stop with `unsupported` before work
  and state the missing capability. Do not pass off a role-play as another agent.
- **Already in an assigned worker/worktree:** respect that lane. Do not spawn
  nested workers or create another worktree unless authorized and supported.

## Isolate heavy implementation

Before creating a lane, record repository root, branch, HEAD and
`git status --short`. Preserve existing changes; do not require discarding them.
Choose a base revision explicitly: uncommitted parent edits do not appear in a
new worktree automatically. Transfer only approved inputs if they are necessary.

Validate a lowercase task branch and inspect existing branches/paths before use:

```bash
git -C <repo> check-ref-format --branch task/<task-id>
git -C <repo> worktree list --porcelain
git -C <repo> worktree add <absolute-lane> -b task/<task-id> <base-sha>
```

Never overwrite an existing lane. Resume only after inspecting its status and
confirming ownership. Pin the worker's permitted edits and execution directory to
the absolute lane. Use the tool's working-directory option or `git -C`; do not
strand the persistent parent shell in a disposable directory. A provided isolated
container/lane is sufficient; do not nest worktrees for appearance. If no isolation
can be guaranteed, do not dispatch mutating work through that adapter.

## Worker packet

Provide the concrete goal, approved input paths, base SHA, allowed writes,
verification commands, resource limits and commit policy. Ask for artifact paths
and hashes plus a short result, not raw logs. Explicitly pass required context;
never assume all workers inherit the conversation, or none do.

Example packet (plain text, **not** a tool signature):

```text
Work only in <absolute-lane>, based on <base-sha>. Implement <bounded goal>.
Do not touch the primary checkout, commit, merge or push without permission.
Inputs: <paths>. Owned paths: <paths>. Run: <verification commands>.
Persist full logs to <artifact-directory>. Return status, changed files,
artifact paths/hashes, command exit codes and blockers.
```

Parallelize only genuinely independent tasks with disjoint write ownership.
Limit concurrency to available resources. Read-only reviewers use separate fresh
contexts when independence matters, not the implementer's continuing context.

## Parent behavior

After launching workers, do not duplicate their work or paste their noisy output.
Wait using the real host result mechanism; handle errors/cancellation explicitly.
Summarize what changed, verification and blockers. A worker report is a claim,
not a completion proof: read back the target diff/artifacts and run relevant tests.

## Verify, integrate and clean up

1. Inspect lane status/diff and verify results against the approved goal.
2. Preserve the lane on failure, conflicts, unrelated changes or incomplete tests.
3. Obtain approval for commits, integration, branch deletion and destructive cleanup
   according to the active policy. Never treat worker success as that approval.
4. Check the primary HEAD/status against the recorded baseline before integration;
   merge only with permission, without auto-resolving conflicts, then re-run tests.
5. Remove only clean, merged or patch-equivalent worktrees. Use non-force removal
   and branch deletion; unmerged worktrees are recovery artifacts:

```bash
git -C <repo> worktree remove <absolute-lane>
git -C <repo> branch -d task/<task-id>
```

## Limitations

Delegation does not itself prove independent reasoning, correct work, or safe tool
permissions. Prompt-only write limits are not a filesystem sandbox; disclose the
actual enforcement level. Sequential mode preserves useful execution but not
context separation. Missing permissions or acceptance criteria require clarification.
