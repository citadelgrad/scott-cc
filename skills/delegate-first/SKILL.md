---
name: delegate-first
description: >-
  Use when tasks would otherwise flood context with file reads, shell output,
  build logs, or multi-step execution details. Keeps the main conversation clean
  by forking implementation work to sub-agents.
license: MIT
metadata:
  category: technique
  triggers: [subagents, delegation, context-management, claude-code]
---

# Delegate First

The main thread is for coordination, decisions, and user-visible summaries. Implementation work should run in forked sub-agents by default when it would produce noisy tool output.

## When to Use

Use this skill when:
- A task requires reading multiple files.
- A task requires code edits, generated artifacts, builds, tests, or validation.
- A task has independent research/review/implementation lanes.
- The user wants to keep an ongoing conversation clean while work happens elsewhere.
- You are about to run commands likely to produce verbose output.

Do not use this skill for direct answers, small clarifications, or work the user explicitly asked to do inline.

## Core Rule

Fork first for implementation. Keep the parent thread focused on:
- Confirming the approach.
- Launching the fork.
- Reporting high-level progress.
- Summarizing the final result.

The fork owns noisy discovery and execution: file reads, shell commands, edits, logs, and validation output. Heavy implementation forks also own an isolated linked Git worktree; they never experiment in the primary checkout.

## Fork Trigger Checklist

Fork if any of these are true:
- More than one file needs to be read.
- Any code will be written or edited.
- Any build, test, render, migration, or validation command will run.
- The work splits into parallel research/review/implementation tracks.
- The parent context would be polluted by long logs or repeated tool calls.

Keep inline if all of these are true:
- The answer can be given directly from current context.
- No tool output is needed.
- The user asked to see the work inline.
- The edit is a one-line patch being discussed before application.

## How to Fork

### Create an isolated lane

Before a heavy fork or bounded background task:

1. Record repository root, current branch, HEAD SHA, and primary `git status --short`.
2. Derive a lowercase, dasherized task ID and validate `task/<task-id>` with `git check-ref-format --branch`.
3. If the branch or `.worktrees/<task-id>` already exists, inspect and offer to resume it; never overwrite it.
4. Create the linked worktree from the recorded SHA:

```bash
mkdir -p <repo>/.worktrees
git -C <repo> worktree add <repo>/.worktrees/<task-id> -b task/<task-id> <base-sha>
```

Do not `cd` a persistent parent shell into a disposable worktree. Use the tool's working-directory option, a subshell, or `git -C` so teardown cannot strand the shell.

Use Claude Code's `Agent` tool with `subagent_type: "fork"` so the child inherits the full conversation context while keeping its tool output out of the parent transcript. The prompt must pin the worker to the absolute worktree path.

Prompt shape:

```
Agent({
  subagent_type: "fork",
  description: "Short task label",
  prompt: "Work only in <absolute-worktree-path>, based on <base-sha>. Do X. Do not touch the primary checkout or merge. Follow the stated commit policy. Run the relevant verification. Report: changed files, git status, verification, blockers."
})
```

### PAS CLI / Reckoner compatibility

- For local PAS CLI or ordinary sub-agent execution, pass the worktree path as the job working directory.
- Reckoner tasks already run in isolated containers. Do not nest a local worktree merely for appearance; record the container/task ID and treat its result branch/PR as the isolated lane.
- If an orchestrator cannot guarantee an isolated working directory, do not dispatch heavy work through it.

## Parent-Thread Behavior

After launching a fork:
1. Tell the user what is running in one sentence.
2. Stop. Do not narrate or duplicate the fork's work.
3. When the fork returns, summarize in 2-3 sentences:
   - What changed.
   - Where it changed.
   - What verification passed or what is blocked.

Never paste long tool output from a fork into the parent thread unless the user explicitly asks for it.

## Verify, integrate, and clean up

1. Independently inspect worktree status/diff and run the required tests there. Worker self-report is not proof.
2. Preserve the worktree on failure, conflict, unrelated changes, or incomplete verification; report its absolute path.
3. On verified success, show the scoped result and ask for explicit approval before any commit, merge, branch deletion, or destructive cleanup.
4. Before integration, confirm the primary HEAD/status remains compatible with the recorded baseline.
5. With approval, commit in the worktree if necessary, merge without auto-resolving conflicts, and re-run verification on the integrated primary tree.
6. Remove only a clean worktree whose changes are merged or patch-equivalent, then delete the task branch with non-force deletion:

```bash
git -C <repo> worktree remove <repo>/.worktrees/<task-id>
git -C <repo> branch -d task/<task-id>
```

Never use `--force` as normal cleanup. Unmerged worktrees are recovery artifacts.

## Prompting Forks Well

A good fork prompt includes:
- The concrete goal.
- Relevant files, commands, or constraints already known.
- Whether edits are allowed.
- Verification expected before reporting done.
- Output format for the return summary.

Example:

```
Use the current repository context. Add the missing delegate-first plugin assets: a Claude Code skill and slash command. Update manifests/docs/counts if needed. Verify with the repo's plugin verification script and git diff. Return changed files and command results only.
```

## When NOT to Fork

Do not fork when:
- The user says "show me", "do it here", "inline", or equivalent.
- The task is a simple answer with no repo inspection needed.
- The user is actively reviewing a specific snippet and wants live discussion.
- The next step is a user decision, not implementation.

The user is always in control. If they ask for inline work, do it inline.
