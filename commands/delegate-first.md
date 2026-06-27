---
name: delegate-first
description: Keep the main conversation clean by forking implementation work to sub-agents. Use when you want ongoing conversation without context pollution from file reads, shell output, and tool noise.
allowed-tools: Agent
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

## How to fork

Use `subagent_type: "fork"`. The fork inherits full conversation context so it knows what has been happening, but its tool output stays out of the main thread.

```
Agent({
  subagent_type: "fork",
  description: "Short task label",
  prompt: "Do X. Write Y to Z. Report back with what changed in one paragraph."
})
```

After launching: tell the user what is running, then stop. Do not fill the thread while waiting.

When the fork returns: summarize in 2-3 sentences. Say what changed, where it is, and what is next. Do not paste tool output.

## The pattern

1. User asks for something → plan it inline in 1-2 sentences
2. Fork the implementation
3. Tell the user the fork is running
4. When it returns → summarize and move on

## When NOT to fork

If the user says "show me", "do it here", or "inline", do it inline. The user is always in control of this.
