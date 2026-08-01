---
name: concurrency-atomicity
description: Run a concurrency-correctness and atomicity review against a diff, PR, or branch — race conditions, TOCTOU, deadlock/lock-ordering, and transactional atomicity, grounded in real CWE reference entries
argument-hint: "[base..head | branch | PR]"
allowed-tools: Read, Grep, Glob, Bash
---

# Concurrency & Atomicity Review

Human entry point for the concurrency-atomicity review. This command's only job is to
resolve the review target, then hand off to the skill — it does not itself apply any
checkpoint.

## Arguments

$ARGUMENTS

Parse this to extract the review target: a `base..head` range, a branch name, a PR
reference, or (if omitted) the current working-tree diff against `HEAD`. Pass this
through unparsed to the skill, which owns target resolution.

## Action

Invoke the **concurrency-atomicity** skill (`skills/concurrency-atomicity/SKILL.md`).
Read the full `SKILL.md` and follow it — do not run the checkpoints from memory of this
command file. The skill:

- Resolves the diff/target.
- Applies its four bug-class checkpoints — race conditions/shared mutable state, TOCTOU
  non-atomicity, deadlock/lock-ordering violations, and transactional atomicity — each
  grounded in a cited CWE reference entry.
- Categorizes each finding by severity and by which CWE checkpoint it violates.
- Produces a report grouped by checkpoint, with an explicit approve/block verdict.

This skill can also be invoked automatically by the model, or by another orchestrating
skill or agent (e.g. `/review-panel`), when a diff's concurrency or atomicity surface
area warrants this lens — in addition to running via this explicit command.

## Example usage

```
/scott-cc:concurrency-atomicity
/scott-cc:concurrency-atomicity main..feature/checkout-fix
/scott-cc:concurrency-atomicity feature/checkout-fix
```

- No arguments: reviews the current working-tree diff against `HEAD`.
- A range, branch, or PR reference: reviews that diff instead.
