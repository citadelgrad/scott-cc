---
name: mental-models-economics
description: >-
  Use when a diff adds a new dependency or vendor, includes a TODO/FIXME/HACK
  marker, or the PR description discusses a trade-off or deferred work. Frames
  changes as resource-allocation decisions using mental models (Scarcity,
  Trade-offs, Debt, Build-vs-Buy, etc.). Not for code-level simplicity
  trade-offs (use mental-models-simplifier) or runtime behavior (use
  mental-models-systems).
argument-hint: "[file, PR, diff, or design doc with a resource/dependency/debt decision]"
allowed-tools: Read, Grep, Glob
metadata:
  category: pattern
---

# Mental Models: Economics/Debt

Frames the change as a resource-allocation decision. No other seat in this plugin reasons about
engineering economics specifically: technical debt taken on knowingly vs. silently, build-vs-buy,
vendor lock-in, and whether effort is proportional to the value a change actually delivers.

## Model catalog

Apply the models listed under **Economics/Debt** in
[`../../reviewers/mental-models-catalog.md`](../../reviewers/mental-models-catalog.md) — each row
is a model paired with the code-review question it reframes into. Work through the full list; do
not cherry-pick a subset.

## Procedure

1. Read the target once, in full, before applying any model.
2. Identify every resource-allocation decision visible in the diff: a new dependency added, a
   TODO/FIXME/HACK marker, a vendor or service chosen over a build-it-yourself path, a shortcut
   with no stated payoff plan, effort spent on a low-traffic path while a high-traffic path stays
   thin.
3. For each model in the catalog table, ask its reframed question against those decisions. Skip
   silently past models with nothing to say rather than manufacturing a finding.
4. Where a model surfaces something, state which model produced it and the concrete cost/benefit
   it exposes — the switching cost of the lock-in, the interest rate on the debt, the maintenance
   burden being taken on — not a generic "this adds tech debt."

## When NOT to Apply

- Whether an approach is conceptually the simplest one for the *problem* — that's
  `mental-models-simplifier`.
- Runtime/systems behavior under load — that's `mental-models-systems`.
- Bugs, security holes, hostile input — that's `adversarial-reviewer`'s scope.

## Output Contract

Findings **must** be emitted using the shared reviewer output contract defined in
[`../../contracts/reviewer-output.md`](../../contracts/reviewer-output.md): Strengths / Issues
(Critical, Important, Minor, each with file:line) / Recommendations / Assessment. Every issue
names the model that produced it and states the concrete cost/benefit or lock-in it exposes, not a
restated definition of the model.

## Critical Rules

**DO:**
- Name the specific model behind every finding
- Point to the actual resource decision (dependency, TODO, vendor choice, effort allocation) the
  finding is about
- State the concrete cost being taken on, not a generic "this is tech debt"
- Emit output in the shared `contracts/reviewer-output.md` structure

**DON'T:**
- Restate a pure simplicity/approach finding `mental-models-simplifier` would already catch
- Manufacture a finding just to cover every model in the list
- Flag debt without checking whether it's already tracked with an owner/ticket — that's a
  Strength, not an Issue
