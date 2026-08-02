---
name: delegate-first
description: Keep the main conversation clean by forking implementation work to sub-agents. Use when you want ongoing conversation without context pollution from file reads, shell output, and tool noise.
allowed-tools: Agent, Bash, AskUserQuestion
---

# /delegate-first — Keep the main thread clean

The main thread is for thinking and talking. Implementation goes to sub-agents.

## What to fork

Fork anything that would produce tool noise in the main context:
- Reading more than one file
- Writing or editing code
- Running shell commands
- Multi-step tasks: build, generate, render, validate
- Git operations beyond `git status` or `git log`

## What stays inline

- Direct answers to questions
- Single-line edits shown to the user for review before applying
- Planning and discussion
- Summarizing what a fork did

## Worktree isolation for heavy work

Heavy forks and bounded background tasks run in a linked Git worktree. Do not let an experimental worker edit the primary checkout.

1. Resolve the repository root and record the primary branch, HEAD, and `git status --short`.
2. Derive a lowercase task ID containing only letters, numbers, and dashes. Validate both names with `git check-ref-format --branch task/<task-id>`.
3. Refuse to overwrite an existing branch or worktree. If one already exists, inspect it and offer to resume it.
4. Create the isolated lane from the recorded HEAD:

```bash
mkdir -p <repo>/.worktrees
git -C <repo> worktree add <repo>/.worktrees/<task-id> -b task/<task-id> <base-sha>
```

5. Launch the worker with `<repo>/.worktrees/<task-id>` as its explicit working directory. Include the base SHA, allowed scope, commit policy, and verification commands in its prompt.

Never `cd` a persistent parent shell into a disposable worktree. Use the tool's working-directory option, a subshell, or `git -C`.

## How to fork

Use `subagent_type: "fork"`. The fork inherits full conversation context so it knows what has been happening, but its tool output stays out of the main thread. Agent-spawned forks are experimental; if the running Claude Code does not expose fork mode, use a named or `general-purpose` subagent and put all required context in the prompt instead.

```
Agent({
  subagent_type: "fork",
  description: "Short task label",
  prompt: "Work only in <absolute-worktree-path>, based on <base-sha>. Do X. Write Y to Z. Do not touch the primary checkout or merge. Follow the stated commit policy. Run verification. Report changed files, git status, test results, and blockers."
})
```

After launching: tell the user what is running, then stop. Do not fill the thread while waiting.

When the fork returns, independently inspect the worktree diff and run the required gates there. A worker saying “done” is not verification.

Do not assume the worker returns a fixed JSON or object schema. Request the
summary fields in its prompt and validate them against the worktree.

## Integration and teardown

1. Preserve failed, unverified, dirty, or conflicted worktrees and report their paths.
2. On verified success, show the scoped diff and ask for explicit approval to integrate. Do not commit, merge, delete a branch, or force-remove a worktree without that approval.
3. Before integration, confirm the primary HEAD/status has not changed incompatibly and that the task branch contains only intended files.
4. With approval, commit in the task worktree if needed, then merge from the primary checkout without auto-resolving conflicts. Re-run verification on the integrated tree.
5. Remove the worktree only after the integration is proven merged or patch-equivalent and the worktree is clean:

```bash
git -C <repo> worktree remove <repo>/.worktrees/<task-id>
git -C <repo> branch -d task/<task-id>
```

Never use `--force` as routine cleanup. An unmerged worktree is evidence, not trash.

## The pattern

1. User asks for something → plan it inline in 1-2 sentences
2. Create the task worktree
3. Fork the implementation into that worktree
4. Tell the user the fork is running
5. Verify, request integration approval, merge safely, then tear down

## When NOT to fork

If the user says "show me", "do it here", or "inline", do it inline. The user is always in control of this.
