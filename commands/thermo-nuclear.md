---
name: thermo-nuclear
description: Run a zero-mercy structural-simplification review against a diff, PR, or branch, grounded in Cursor's thermo-nuclear-code-quality-review doctrine; biases toward ambitious rewrites over preserving imperfect-but-working code
argument-hint: "[base..head | branch | PR]"
allowed-tools: Read, Grep, Glob, Bash
---

# Thermo-Nuclear Review

Human entry point for the thermo-nuclear structural review. This command's only job is
to resolve the review target, then hand off to the skill — it does not itself apply the
doctrine.

## Arguments

$ARGUMENTS

Parse this to extract the review target: a `base..head` range, a branch name, a PR
reference, or (if omitted) the current working-tree diff against `HEAD`. Pass this
through unparsed to the skill, which owns target resolution.

## Action

Invoke the **thermo-nuclear** skill (`skills/thermo-nuclear/SKILL.md`). Read the full
`SKILL.md` and follow it — do not run the doctrine from memory of this command file. The
skill:

- Resolves the diff/target and reads full touched files, not just diff hunks.
- Applies the 7-criterion structural doctrine and the Approval Bar.
- Produces a report of doctrine violations, at least one named ambitious restructuring
  recommendation, and an explicit approve/block verdict.

This skill sets `disable-model-invocation: true` — it only ever runs via this command,
never by automatic keyword matching, so it never fires unexpectedly alongside
`/review-panel` or `adversarial-reviewer`.

## Example usage

```
/scott-cc:thermo-nuclear
/scott-cc:thermo-nuclear main..feature/checkout-fix
/scott-cc:thermo-nuclear feature/checkout-fix
```

- No arguments: reviews the current working-tree diff against `HEAD`.
- A range, branch, or PR reference: reviews that diff instead.
