---
name: subtractive-review
description: Run a subtractive-neglect review against a diff, PR, branch, plan, or proposal — force a subtraction-first search before any additive fix is accepted, and judge options on net system complexity
argument-hint: "[base..head | branch | PR | file | plan]"
allowed-tools: Read, Grep, Glob, Bash
---

# Subtractive Review

Human entry point for the subtractive-review. This command's only job is to resolve the
review target, then hand off to the skill — it does not itself apply any lens.

## Arguments

$ARGUMENTS

Parse this to extract the review target: a `base..head` range, a branch name, a PR
reference, a file or plan document, or (if omitted) the current working-tree diff against
`HEAD`. Pass this through unparsed to the skill, which owns target resolution.

## Action

Invoke the **subtractive-review** skill (`skills/subtractive-review/SKILL.md`). Read the
full `SKILL.md` and follow it — do not run the lenses from memory of this command file.
The skill:

- Frames the goal without the proposed mechanism.
- Takes an additive inventory and records the net delta.
- Walks every lens in its subtraction catalog (remove the cause, requirement, special
  case, layer, state, dependency, step, and more).
- Checks Chesterton's fence for each removal candidate with git history and call sites.
- Produces findings with evidence states and exactly one verdict: `subtract`, `hybrid`,
  `add-justified`, `reframe`, or `insufficient-evidence`.

This skill can also be invoked automatically by the model, or by another orchestrating
skill or agent (e.g. `/review-panel`), when a change adds code, layers, checks, or process
to solve a problem — in addition to running via this explicit command.

## Example usage

```
/scott-cc:subtractive-review
/scott-cc:subtractive-review main..feature/retry-wrapper
/scott-cc:subtractive-review docs/plans/2026-10-04-export-formats.md
```

- No arguments: reviews the current working-tree diff against `HEAD`.
- A range, branch, PR reference, or document: reviews that target instead.
