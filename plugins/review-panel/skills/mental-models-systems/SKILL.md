---
name: mental-models-systems
description: >-
  Use when a diff touches concurrency, queues/message buses, caching,
  retries/backoff, rate limiting, service-to-service calls, or connection
  pooling. Evaluates dynamic runtime behavior — feedback loops, bottlenecks,
  emergence, scale — using mental models (Feedback Loops, Equilibrium, Critical
  Mass, etc.). Not for static module quality (use design-review) or assumption
  pressure-testing (use mental-models-adversarial).
argument-hint: "[file, PR, diff, or design doc touching runtime/systems behavior]"
allowed-tools: Read, Grep, Glob
metadata:
  category: pattern
---

# Mental Models: Systems/Boundaries

Evaluates *dynamic* behavior — how components interact at runtime, under load, and over time —
as opposed to `design-review`'s funnel, which evaluates *static* module and abstraction quality.
Two components can each look well-designed in isolation while their combination produces behavior
neither one's own logic shows; that's this skill's target.

## Model catalog

Apply the models listed under **Systems/Boundaries** in
[`../../reviewers/mental-models-catalog.md`](../../reviewers/mental-models-catalog.md) — each row
is a model paired with the code-review question it reframes into. Work through the full list; do
not cherry-pick a subset.

## Procedure

1. Read the target once, in full, before applying any model.
2. Trace every point where this change interacts with another component: a queue, a cache, a
   downstream service, a shared connection pool, a retry policy, a rate limiter. This is the map
   the models below get applied against.
3. For each model in the catalog table, ask its reframed question against that interaction map.
   Skip silently past models with nothing to say rather than manufacturing a finding.
4. Where a model surfaces something, state which model produced it and describe the concrete
   failure mode (what state it converges to, what threshold it crosses, what emerges from the
   combination) — not a generic "this could have issues at scale."

## When NOT to Apply

- Static module boundaries, abstraction quality, information hiding — that's `design-review`'s
  funnel; don't duplicate it here.
- Assumptions/incentives/single-points-of-failure in the decision itself — that's
  `mental-models-adversarial`.
- Bugs, security holes, hostile input in the code as written — that's `adversarial-reviewer`'s
  scope.

## Output Contract

Findings **must** be emitted using the shared reviewer output contract defined in
[`../../contracts/reviewer-output.md`](../../contracts/reviewer-output.md): Strengths / Issues
(Critical, Important, Minor, each with file:line) / Recommendations / Assessment. Every issue
names the model that produced it and describes the concrete runtime failure mode, not a restated
definition of the model.

## Critical Rules

**DO:**
- Name the specific model behind every finding
- Trace the actual interaction map before applying models to it
- Describe the concrete failure mode (steady state, threshold, emergent behavior), not a vague
  "issues at scale"
- Emit output in the shared `contracts/reviewer-output.md` structure

**DON'T:**
- Restate a static structural finding `design-review` would already catch
- Manufacture a finding just to cover every model in the list
- Apply this skill to a diff with no cross-component interaction to trace (e.g. a pure
  single-function utility) — say so and stop rather than forcing a finding
