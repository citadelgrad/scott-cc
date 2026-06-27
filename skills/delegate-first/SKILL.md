---
name: delegate-first
description: Keep the main conversation clean by forking implementation work to sub-agents. Use when tasks would otherwise flood context with file reads, shell output, build logs, or multi-step execution details.
license: MIT
tags: [subagents, delegation, context-management, claude-code]
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

The fork owns noisy discovery and execution: file reads, shell commands, edits, logs, and validation output.

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

Use Claude Code's `Agent` tool with `subagent_type: "fork"` so the child inherits the full conversation context while keeping its tool output out of the parent transcript.

Prompt shape:

```
Agent({
  subagent_type: "fork",
  description: "Short task label",
  prompt: "Do X. Use the current repo/context. Make the needed changes. Run the relevant verification. Report back with: changed files, verification result, blockers. Keep the summary concise."
})
```

## Parent-Thread Behavior

After launching a fork:
1. Tell the user what is running in one sentence.
2. Stop. Do not narrate or duplicate the fork's work.
3. When the fork returns, summarize in 2-3 sentences:
   - What changed.
   - Where it changed.
   - What verification passed or what is blocked.

Never paste long tool output from a fork into the parent thread unless the user explicitly asks for it.

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
