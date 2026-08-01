---
name: polyglot-idiom
description: Run a per-language idiom review against a diff, PR, or branch for Java, C++, C#, Ruby, or PHP code — checkpoints grounded in the Gemini code-quality research; excludes Python, TypeScript, Go, Rust, and Swift, which have dedicated simplifier skills
argument-hint: "[base..head | branch | PR]"
allowed-tools: Read, Grep, Glob, Bash
---

# Polyglot Idiom Review

Human entry point for the polyglot-idiom review. This command's only job is to resolve
the review target, then hand off to the skill — it does not itself apply any checkpoint.

## Arguments

$ARGUMENTS

Parse this to extract the review target: a `base..head` range, a branch name, a PR
reference, or (if omitted) the current working-tree diff against `HEAD`. Pass this
through unparsed to the skill, which owns target resolution.

## Action

Invoke the **polyglot-idiom** skill (`skills/polyglot-idiom/SKILL.md`). Read the full
`SKILL.md` and follow it — do not run the checkpoints from memory of this command file.
The skill:

- Resolves the diff/target.
- Covers Java, C++, C#, Ruby, and PHP only — it excludes Python, TypeScript/JavaScript,
  Go, Rust, and Swift, which have (or will have) dedicated `*-simplifier` skills. If the
  diff touches only out-of-scope languages, the skill says so and stops instead of
  guessing.
- Applies each touched file's language-specific checkpoint list.
- Produces a report grouped by language and checkpoint, with any excluded files noted.

This skill can also be invoked automatically by the model, or by another orchestrating
skill or agent (e.g. `/review-panel`), when a diff touches one of its five in-scope
languages — in addition to running via this explicit command.

## Example usage

```
/scott-cc:polyglot-idiom
/scott-cc:polyglot-idiom main..feature/checkout-fix
/scott-cc:polyglot-idiom feature/checkout-fix
```

- No arguments: reviews the current working-tree diff against `HEAD`.
- A range, branch, or PR reference: reviews that diff instead.
- If the diff is entirely Python, TypeScript/JavaScript, Go, Rust, or Swift, the skill
  reports that it is out of scope and points to the matching simplifier skill instead.
