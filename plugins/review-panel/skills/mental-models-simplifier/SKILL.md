---
name: mental-models-simplifier
description: >-
  Use when a diff is primarily a performance optimization, introduces a new
  abstraction/layer/pattern, or touches code already known to be complex.
  Questions whether this is even the right problem/approach using mental models
  (Occam's Razor, First Principles, Diminishing Returns, etc.) — conceptual,
  not mechanical. Not for mechanical delete/simplify passes (use
  ponytail-review) or structural quality (use design-review).
argument-hint: "[file, PR, diff, or design doc to question]"
allowed-tools: Read, Grep, Glob
metadata:
  category: pattern
---

# Mental Models: Simplifier

## When to Use
- A diff is primarily a performance optimization
- New abstraction, layer, or pattern is being introduced
- Code already known to be complex is being touched
- Questioning whether the right problem is being solved using Occam's Razor, First Principles, etc.

Questions the *frame*, not the syntax. `ponytail-review` already does the mechanical pass — delete
dead code, replace hand-rolled logic with stdlib, cut unneeded abstractions — over the diff as
literally written. This skill asks a level up: is this even the right problem being solved, is
effort aimed at the actual constraint, and would a genuinely different (not just shorter) approach
serve better.

## Model catalog

Apply the models listed under **Simplifier** in
[`../../reviewers/mental-models-catalog.md`](../../reviewers/mental-models-catalog.md) — each row
is a model paired with the code-review question it reframes into. Work through the full list; do
not cherry-pick a subset.

## Procedure

1. Read the target once, in full, before applying any model.
2. For each model in the catalog table, ask its reframed question against the target. Skip
   silently past models with nothing to say rather than manufacturing a finding.
3. Where a model surfaces something, state which model produced it and what the simpler
   alternative actually looks like — a named replacement, not just "this could be simpler."
4. Distinguish conceptual findings (wrong frame, wrong optimization target) from mechanical ones
   (dead code, reinvented stdlib) — route the latter to `ponytail-review`'s scope instead of
   duplicating it here.

## When NOT to Apply

- Mechanical delete/stdlib/native/yagni/shrink findings on the diff as literally written — that's
  `ponytail-review`'s scope; don't duplicate it here.
- Static module/abstraction/information-hiding quality — that's `design-review`'s funnel.
- Bugs, security holes, hostile input — that's `adversarial-reviewer`'s scope.

## Output Contract

Findings **must** be emitted using the shared reviewer output contract defined in
[`../../contracts/reviewer-output.md`](../../contracts/reviewer-output.md): Strengths / Issues
(Critical, Important, Minor, each with file:line) / Recommendations / Assessment. Every issue
names the model that produced it and states a concrete simpler alternative, not a restated
definition of the model.

## Critical Rules

**DO:**
- Name the specific model behind every finding
- Work the full catalog list, skip silently where a model has nothing to say
- Give a concrete alternative approach, not just "simplify this"
- Emit output in the shared `contracts/reviewer-output.md` structure

**DON'T:**
- Restate a mechanical over-engineering finding `ponytail-review` would already catch
- Manufacture a finding just to cover every model in the list
- Flag a trade-off as wrong without naming the alternative and its own cost

## Limitations
- Use this skill only when the task clearly matches the scope described above.
- Conceptual, not mechanical — use ponytail-review for delete/simplify passes.
- Do not manufacture findings to cover every model in the catalog.
- A trade-off flagged as wrong must name the alternative and its own cost.
- Stop and ask for clarification if the optimization goal, complexity context, or abstraction rationale is unclear.
