---
name: subtractive-review
description: >-
  Use when reviewing a diff, PR, plan, design, bug fix, process, or config change
  to counter subtractive neglect: the default bias to solve problems by adding
  code, layers, checks, steps, flags, or dependencies while overlooking the
  option to remove something. Forces a subtraction-first search, compares
  subtractive and additive options on net system complexity, and reports which
  one actually meets the goal. Not a general simplicity pass (use ponytail-review
  or a language simplifier for that).
argument-hint: '[diff, PR, file, plan, design doc, or proposal]'
license: MIT
metadata:
  category: discipline
  triggers: [subtractive-neglect, additive-bias, subtraction, remove-instead-of-add, less-is-more, deletion, root-cause, design-review, code-review, plan-review, scope-reduction, net-complexity]
  sources:
    - "Adams, Converse, Hales & Klotz, 'People systematically overlook subtractive changes', Nature 592, 258–261 (2021)"
    - "Leidy Klotz, Subtract: The Untapped Science of Less (2021)"
---

# Subtractive Review

When asked to improve something, people search for things to add. They consider removal late, rarely, or never, even when removal is cheaper and better. The search, not the judgment, is where it fails: the subtractive option is not rejected, it is never generated. This review forces that search and then judges both options on equal terms.

When invoked with `$ARGUMENTS`, review that target. Without arguments, review the current diff against its base branch, or the proposal in the conversation.

## Core rule

**No additive change is accepted until at least one subtractive alternative has been generated, stated concretely, and judged against the same goal.**

Treat this as a gate, not a suggestion. "We need X" is a proposed solution. Restate it as the problem X solves, then search the removal space for that problem first.

The gate requires a real *search*, not a finding. If the search is done and no subtractive option meets the goal, the gate is passed: report zero findings and the verdict `add-justified`. Never invent a subtraction to satisfy the gate.

## Size the review

Fit the depth to the target before you start:

| Target | Depth |
|---|---|
| Proposal, plan, issue, or diff under ~300 changed source lines | Full procedure on everything |
| Larger diff or multi-file commit | Inventory all of it, then walk the lenses and fence checks only on the 3–5 hunks with the largest additions. List the hunks you skipped. |
| Whole codebase or subsystem | Use the code lenses only, ranked by size of the module; report as an audit, not a gate |

Tests and fixtures: count them in the inventory on their own line, but do not walk lenses on them. Exception: flag test helpers or fixtures that duplicate each other (lens L16).

## Why the subtractive option goes missing

Name the mechanism when you report a finding. It helps the author see the bias, not only the fix.

| Mechanism | What it looks like in engineering work |
|---|---|
| Additive default search | The first three ideas all add: a flag, a retry, a wrapper, a new service. |
| No cue to subtract | Nobody said "removing costs nothing," so nobody looked. |
| Cognitive load | Under deadline or in a large diff, reviewers fall back to "add a guard." |
| Visibility and credit | Added work is visible and rewarded. A deleted module looks like no work. |
| Loss aversion and sunk cost | "We spent a sprint on that cache," so it stays. |
| Symptom patching | Each incident adds a check. Nobody removes the cause that makes checks necessary. |
| Ownership boundaries | It is easier to add in your own module than to remove from someone else's. |

## Procedure

### 1. Frame the goal, not the solution

Write one sentence: the outcome the change must produce, and how you will know it is met. Strip the proposed mechanism out of it. "Add a retry wrapper around the client" becomes "calls to the payment service succeed under normal transient failure rates."

If you cannot state the goal without naming the solution, report that as the first finding. The scope is unclear.

### 2. Take an additive inventory

List everything the change or proposal adds. Count each kind:

- code: new functions, branches, special cases, modules, files
- structure: layers, wrappers, indirection, abstractions, interfaces
- dependencies: packages, services, queues, caches, external calls
- state: new fields, tables, flags, settings, environment variables
- behavior: retries, fallbacks, validations, checks, guards
- process: steps, approvals, gates, docs, meetings, tickets
- surface: new CLI options, endpoints, UI controls, config keys

Count each item once, under its main kind; do not double-count a validator as both code and behavior. Rough counts and approximate line deltas are enough.

Also list what the change removes. Record the net delta. A change that only adds is not wrong, but it has not shown that it looked the other way.

### 3. Cue the subtraction search explicitly

Say it to yourself in writing: *removing things is allowed and costs nothing to propose.* Then walk the lenses in [the subtraction lens catalog](references/subtraction-lenses.md) that apply to the target type:

| Target type | Lenses to walk |
|---|---|
| Code diff, PR, or bug fix | L1–L9, L16, L17 |
| Plan, spec, design doc, or feature request | L1, L3–L6, L10–L12, L16, plus L7 for any new option |
| Process, workflow, or runbook | L1, L10, L12–L15 |

For each lens, either write a concrete candidate or mark it `n/a` with a one-line reason. You may group `n/a` lenses that share a reason. Do not stop at the first good candidate. The bias returns the moment the search becomes casual.

Start with the lenses that find the most:

- **L1 Remove the cause** (all targets). What existing thing makes this addition necessary? For a bug fix: can the code path that made the bug possible be deleted?
- **L16 Remove the second implementation** (code and plans). Does the change add a near-copy of something that exists? Delete one.
- **L10 Remove the requirement** (plans and processes). Is the requirement real, current, and owned by someone?

### 4. Check every fence before you pull it down

For each subtractive candidate, find out why the thing exists before you recommend removing it (Chesterton's fence). Use evidence, not guesses:

- `git log -S` / `git blame` for the commit and reason that added it
- call sites and references (`rg`, LSP references, import graphs)
- tests that pin its behavior, and whether they test a real requirement
- runtime evidence where available: usage metrics, logs, feature flag data
- linked issues, ADRs, incident reports

Record what you found. "Nobody knows why it is there" is a finding, not permission. It means the removal needs a safe, reversible path.

### 5. Judge both options on the same terms

For each viable subtractive candidate, compare it against the additive proposal:

| Criterion | Question |
|---|---|
| Goal met | Does it fully meet the goal from step 1? Partial counts as partial. |
| Net system complexity | After the change, is the whole system smaller and simpler? Count across modules, not only this file. |
| Risk | What could break? How likely? How bad? Who is affected? |
| Reversibility | Can it be undone cheaply (flag, revert, staged rollout)? |
| Evidence | How strong is the proof that the removed thing is not needed? |
| Future cost | What does each option cost to maintain, read, and change later? |

Prefer the subtractive option when it meets the goal with equal or lower risk. Prefer a hybrid when a small addition enables a larger removal. Accept the additive option when the search was real and no subtractive option meets the goal. Say so plainly; that is a valid outcome.

### 6. Guard against false subtraction

These are not subtraction. Reject them:

- **Moving complexity.** Deleting a check here so every caller must do it. Net complexity rises.
- **Removing a safeguard without evidence.** Security checks, validation at trust boundaries, data integrity constraints, and error handling need proof they are redundant, not only a feeling.
- **Hiding instead of removing.** Wrapping, renaming, or moving code to another file.
- **Removing tests to make a change pass.**
- **Subtraction for its own sake.** The goal from step 1 still rules. Removal that misses the goal is a regression.

## Evidence states

Tag every finding with one state. Never promote a finding without new evidence.

- `verified`: the removal was tried (branch, test run, build, or probe) and the goal still holds.
- `supported`: concrete evidence (no call sites, dead flag, unused config, superseded path) but no trial run.
- `hypothesis`: plausible removal; the fence has not been checked yet. Never blocking.

Only `verified` and `supported` findings can drive a `subtract` or `hybrid` verdict. If the best findings are all `hypothesis`, the verdict is `insufficient-evidence`, and each finding states the fence check that would settle it.

## Output

Report in this order. Keep it short. Zero findings is a valid result; do not invent subtractions to fill the report.

1. **Goal** — the one-sentence outcome from step 1.
2. **Scope** — target, size tier, and any hunks skipped.
3. **Additive inventory** — counts per kind, tests separately, and the net delta (added vs removed).
4. **Lenses run** — which lenses produced candidates and which were `n/a`.
5. **Findings** — one entry each:
   - `ID` — short stable ID such as `SUB-1`
   - **Remove:** what goes away (path, symbol, step, requirement)
   - **Instead of:** the addition it replaces or makes unnecessary
   - **Mechanism:** which bias from the table hid it
   - **Fence check:** why it exists and what the evidence shows
   - **Goal still met:** yes / partially / no, with reason
   - **Net delta:** rough before/after (lines, files, dependencies, settings, steps)
   - **Risk and reversibility**
   - **Evidence state:** `verified` / `supported` / `hypothesis`
   - **Action:** `do-now` (verified or supported, low risk) / `check-fence` (name the check) / `drop` (fails the goal or the guards in step 6)
6. **Verdict** — exactly one for the change as a whole. Per-finding actions carry the detail.
   - `subtract` — a subtractive option meets the goal and should replace the additive one
   - `hybrid` — a small addition enables a larger removal
   - `add-justified` — the search was real and no subtractive option meets the goal
   - `reframe` — the goal is unclear or the change solves the wrong problem
   - `insufficient-evidence` — a promising removal needs a fence check before a decision

## Relation to other reviews

- **ponytail-review / language simplifiers**: find over-engineering already in the code. This review targets the *choice of fix*: was removal ever considered as the answer to the problem?
- **karpathy-guidelines**: keeps a change small. This review asks whether the right change has a negative size.
- **adversarial-reviewer**: asks how a change breaks. Run it on any subtraction you recommend that touches safeguards.

This skill is a read-only review. It recommends removals; it does not delete code. When the user wants the change made, implement it as a separate step with tests that prove the goal still holds.

## Further reading

- [Subtraction lens catalog](references/subtraction-lenses.md) — the full prompt set for step 3, with engineering examples
- [Research basis](references/research.md) — what the studies found and how this skill applies it
