---
name: google-standard
description: Run a review against Google's published Standard of Code Review against a diff, PR, or branch — favors approving once a change definitely improves code health, even if imperfect, using the Nit:/blocking distinction
argument-hint: "[base..head | branch | PR]"
allowed-tools: Read, Grep, Glob, Bash
---

# Google Standard Review

Human entry point for the google-standard review. This command's only job is to resolve
the review target, then hand off to the skill — it does not itself apply the standard.

## Arguments

$ARGUMENTS

Parse this to extract the review target: a `base..head` range, a branch name, a PR
reference, or (if omitted) the current working-tree diff against `HEAD`. Pass this
through unparsed to the skill, which owns target resolution.

## Action

Invoke the **google-standard** skill (`skills/google-standard/SKILL.md`). Read the full
`SKILL.md` and follow it — do not run the standard from memory of this command file. The
skill:

- Resolves the diff/target.
- Evaluates the change against the Core Principle (approve once code health definitely
  improves, even if imperfect) and the Review Principles (technical facts, style-guide
  authority, codebase consistency).
- Categorizes every finding as blocking or `Nit:`.
- Produces a report with an explicit approve/request-changes verdict.

This skill can also be invoked automatically by the model, or by another orchestrating
skill or agent (e.g. `/review-panel`), when a review calls for this pragmatic
code-health bar — in addition to running via this explicit command.

## Example usage

```
/scott-cc:google-standard
/scott-cc:google-standard main..feature/checkout-fix
/scott-cc:google-standard feature/checkout-fix
```

- No arguments: reviews the current working-tree diff against `HEAD`.
- A range, branch, or PR reference: reviews that diff instead.
