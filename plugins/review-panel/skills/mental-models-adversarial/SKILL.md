---
name: mental-models-adversarial
description: Use when a diff introduces a new algorithm, heuristic, threshold, retry/backoff
  policy, or config value that shapes downstream behavior, or when a design rationale
  makes a "this is safe because X" claim. Pressure-tests reasoning using mental models
  (Inversion, Second-Order Thinking, Margin of Safety, Incentives, etc.). Not for
  hunting bugs/exploits in code (use adversarial-reviewer) or module structure (use
  design-review). Hanlon's Razor, and others)
argument-hint: '[file, PR, diff, or design rationale to pressure-test]'
allowed-tools: Read, Grep, Glob
metadata:
  category: pattern
  triggers:
  - adversarial-thinking
  - threat-modeling
  - security
---

# Mental Models: Adversarial/Risk

## When to Use
- A diff introduces a new algorithm, heuristic, threshold, retry/backoff policy, or config value
- A design rationale makes a "this is safe because X" claim that needs pressure-testing
- Evaluating reasoning behind a change (not bugs in the code itself)
- Applying adversarial mental models: Inversion, Second-Order Thinking, Margin of Safety, Incentives

Pressure-tests the *reasoning* behind a change, not the code as written. `adversarial-reviewer`
already attacks the implementation for bugs, exploits, and hostile input; this skill instead asks
whether the decision to build it *this way* holds up — the assumptions, incentives, and systemic
risk that don't show up from reading the diff alone.

## Model catalog

Apply the models listed under **Adversarial/Risk** in
[`../../reviewers/mental-models-catalog.md`](../../reviewers/mental-models-catalog.md) — each row
is a model paired with the code-review question it reframes into. Work through the full list; do
not cherry-pick a subset.

## Procedure

1. Read the target (diff, file, or design rationale/comment) once, in full, before applying any model.
2. For each model in the catalog table, ask its reframed question against the target. Not every
   model will surface a finding on every target — skip silently past ones with nothing to say
   rather than manufacturing a finding to fill the row.
3. Where a model surfaces something, state which model produced it — this is what distinguishes
   the finding from a generic adversarial-reviewer pass and makes the reasoning behind the finding
   auditable.
4. If prior findings or a design rationale exist for this target, treat "Circle of Competence" and
   "Hanlon's Razor" as license to question the rationale itself, not just the code — e.g. "this
   comment claims retries are safe because the call is idempotent; is that actually true here?"

## When NOT to Apply

- Bug-hunting, exploit-hunting, or hostile-input handling on the code as written — that's
  `adversarial-reviewer`'s scope; don't duplicate it here.
- Static module/abstraction/naming quality — that's `design-review`'s funnel.
- Runtime/systems dynamics (feedback loops, bottlenecks, scale) — that's `mental-models-systems`.

## Output Contract

Findings **must** be emitted using the shared reviewer output contract defined in
[`../../contracts/reviewer-output.md`](../../contracts/reviewer-output.md): Strengths / Issues
(Critical, Important, Minor, each with file:line) / Recommendations / Assessment. Every issue
names the model that produced it, states the question that model asks, and answers it concretely
for this target — not a restated definition of the model.

## Critical Rules

**DO:**
- Name the specific model behind every finding
- Work the full catalog list, skip silently where a model has nothing to say
- Pressure-test stated rationale (comments, PR description, prior findings), not just code shape
- Emit output in the shared `contracts/reviewer-output.md` structure

**DON'T:**
- Restate a bug/exploit/hostile-input finding `adversarial-reviewer` would already catch
- Manufacture a finding just to cover every model in the list
- Report a finding without naming which model produced it

## Limitations
- Use this skill only when the task clearly matches the scope described above.
- Pressure-tests reasoning, not code — use adversarial-reviewer for bug/exploit hunting.
- Do not manufacture findings to cover every model in the catalog.
- Stop and ask for clarification if the design rationale, assumptions, or change context is unclear.
