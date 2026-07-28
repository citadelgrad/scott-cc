---
name: karpathy-guidelines
description: >-
  Use when writing, reviewing, or refactoring code to avoid overcomplication,
  make surgical changes, surface assumptions, and define verifiable success
  criteria. Behavioral guidelines to reduce common LLM coding mistakes.
license: MIT
metadata:
  category: discipline
  triggers: [overcomplication, over-engineering, surgical-changes, simplicity, assumptions, LLM-mistakes, code-review, refactoring]
---

# Karpathy Guidelines

Behavioral guidelines to reduce common LLM coding mistakes, derived from [Andrej Karpathy's observations](https://x.com/karpathy/status/2015883857489522876) on LLM coding pitfalls.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

**Violating the letter of these rules is violating the spirit of these rules.** Don't rationalize "I'm following the spirit" while adding speculative code.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll add this abstraction for future flexibility" | YAGNI. Single-use abstractions add complexity without value. Remove it. |
| "While I'm here, I'll clean up this other code" | Surgical changes only. File a separate issue for unrelated cleanup. |
| "This is too simple to state assumptions for" | Simple tasks have hidden assumptions. State them. 30 seconds of clarity prevents 30 minutes of rework. |
| "I already know what they want" | Multiple interpretations exist more often than you think. Present options, don't pick silently. |
| "I'll just refactor this adjacent function too" | Every changed line must trace to the user's request. If it doesn't, revert it. |

## Red Flags — STOP

- Adding code the user didn't ask for
- "Improving" adjacent code, comments, or formatting
- Writing 200 lines when 50 would do
- Skipping assumptions because the task "seems obvious"
- No verifiable success criteria defined before starting

All of these mean: pause, re-read the request, and simplify.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Treating guidelines as "nice to have" | These are constraints, not suggestions |
| Adding error handling for impossible states | Trust your types and validation |
| Refactoring unrelated code in the same PR | Touch only what the request requires |
| Defining success as "it works" | Define specific, testable criteria before starting |
| Adding configuration/flexibility not requested | Ship the simplest thing that solves the problem |
