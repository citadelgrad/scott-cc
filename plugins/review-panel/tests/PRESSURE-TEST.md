# Review Panel Pressure Test

**Task:** scc-ns8.14 — "Build pressure-test harness (TDD-for-skills: baseline fails, panel catches)"

This document is a pressure test of the `review-panel` skill (`skills/review-panel/SKILL.md`
and its `references/`), following superpowers' TDD-for-skills discipline: prove the skill's
prescribed process changes the *outcome* (red baseline → green panel), not just that its files
exist. `review-panel` is a set of markdown prompt files that drive Claude subagents through a
7-stage loop — it is **not executable code**, so this is a documented demonstration of effect,
not an automated test suite. See "Limits of this pressure test" at the end for exactly what that
does and doesn't prove.

All raw subagent transcripts referenced below were produced by live `Task`-tool dispatches run
during this task (agent IDs, durations, and full text are in this worktree's session transcript;
this document quotes/summarizes their substance for readability).

---

## 1. The fixture

`plugins/review-panel/tests/fixtures/order-fulfillment/`:

| File | Role |
|---|---|
| `before.ts` | Clean baseline: a small order-fulfillment module with a null-check guard, a `try/finally`-wrapped connection lifecycle, and a correct `MAX_ATTEMPTS`-bounded retry loop. |
| `after.ts` | The PR diff under review — introduces 3 seeded bugs (below), with **no** comments in the file itself pointing at them (an early draft of this fixture accidentally embedded "answer key" comments describing each bug directly in `after.ts`; that was caught and removed before running any review — see "A methodological correction" below). |
| `diff.patch` | `diff -u before.ts after.ts` — the actual unified diff every reviewer/seat in this test was given, generated fresh from the checked-in `before.ts`/`after.ts` pair. |
| `warehouse-client.ts` | Minimal type-only support file so `before.ts`/`after.ts` type-check in isolation; not itself part of the reviewed diff. |
| `CONTEXT.md` | A minimal domain glossary fixture (per `formats/CONTEXT-FORMAT.md`'s detection convention) documenting that this module's domain term is `fulfillment`, not the narrower `shipping`, specifically *because* the workflow validates payment tokens and retries warehouse calls — not just carrier hand-off. Used only to exercise the coherence axis; not wired into any build tooling. |

### Seeded bugs (the "answer key" — lives only in this document, never in the fixture files)

1. **CRITICAL — null-check omission.** `before.ts` guards `order.paymentToken` (typed
   `{ value: string } | null`) with an explicit `if (!order.paymentToken) throw ...` before
   dereferencing `.value`. `after.ts` deletes the guard and replaces it with a comment
   (`// assume payment token is always present`) that the type signature directly contradicts.
   Any order with `paymentToken: null` — a type-legal, ordinary input — now throws an unhandled
   `TypeError` instead of a clear domain error.
2. **IMPORTANT — resource leak + off-by-one.** `before.ts` wraps the retry loop in
   `try { ... } finally { conn.close(); }`, guaranteeing cleanup on every exit path, and loops
   `for (let i = 0; i < MAX_ATTEMPTS; i++)`. `after.ts` removes the `finally` (leaking the
   warehouse connection on every failed-all-attempts or thrown-exception path) **and** changes
   the loop bound to `i <= MAX_ATTEMPTS`, executing 4 attempts against a documented 3-attempt
   budget.
3. **COHERENCE — domain-term drift.** `after.ts` renames `FulfillmentOrder`/`processFulfillment`
   to `ShippingOrder`/`processShipping` (interface, function, param, and doc comment), directly
   contradicting `CONTEXT.md`'s decision log: `shipping` is reserved for the narrow carrier-only
   sub-step, and `fulfillment` was explicitly chosen because this function validates payment
   tokens and retries warehouse calls — behavior the diff leaves completely unchanged. The name
   changed; the behavior that makes the old name correct did not.

### A methodological correction (transparency note)

The first draft of `after.ts` and the diff handed to the baseline reviewer embedded numbered
"1. CRITICAL / 2. IMPORTANT / 3. COHERENCE" comments describing each seeded bug directly in the
diff text. That is an answer key, not a fixture, and it invalidated the first baseline run (it
trivially found everything because it was told what to find, verbatim). This was caught before
drawing any conclusions: `after.ts` was rewritten with no bug-pointing comments, `diff.patch` was
regenerated from the clean files, and the baseline was re-run from scratch against the clean diff.
Everything reported below is from that corrected run. The contaminated first run is not used as
evidence anywhere in this document.

---

## 2. Baseline (RED) — generic single-pass review, no review-panel machinery

**Dispatch:** one `general-purpose` subagent via `Task`, given only `diff.patch`'s content and a
generic "review this diff for bugs, single pass, no special tools/process" prompt. No
`persona-catalog.md`, no CAST/SPAWN/MERGE/VALIDATE, no `CONTEXT.md`. This stands in for "a
plain ad hoc code-review request with no review-panel involvement," per the task's design
guidance.

**Result:** the baseline reviewer caught bugs #1 and #2 (null-deref and leak/off-by-one), citing
file:line-equivalent locations, concrete triggering inputs, and a "Block / Request changes"
verdict. This is a materially strong single-pass review — worth noting honestly rather than
strawmanning it, per this repo's engineering-excellence standard.

**What it missed:** bug #3, the domain-coherence violation. The baseline's own summary explicitly
flags the `Fulfillment→Shipping` rename only as "an unrelated rename bundled into a bug-fix-shaped
diff" — a generic code-hygiene complaint about scope creep — **not** as a violation of any
documented domain decision, because it was never given `CONTEXT.md` to check against. It has no
way to know that `shipping` vs `fulfillment` is a previously-made, written-down domain decision
this diff silently reverses; it can only observe "this looks like an unrelated rename," which is a
weaker, differently-actioned finding (a reviewer might wave that through as a stylistic choice,
whereas "this contradicts a documented architectural decision" is a hard no).

This is the fixture's real, non-strawmanned red result: **coverage of the coherence axis is
structurally unavailable to a review that was never given the domain documentation to check
against** — which is exactly the gap `review-panel`'s RE-REVIEW Axis (b) / Domain-Intent seat
exists to close (see `references/fix-and-rereview.md` "Axis (b) — Coherence vs. domain intent" and
`reviewers/persona-catalog.md`'s Domain-Intent entry).

---

## 3. Panel (GREEN) — live nested Task dispatch of 2 cast seats

**Live dispatch confirmed working.** From within this worktree agent, `Task` successfully spawned
two independent subagents concurrently, each instructed to follow one seat's actual procedure
(read from the merged `skills/review-panel/skills/adversarial-reviewer/SKILL.md` and
`skills/review-panel/skills/domain-modeling/SKILL.md` in this worktree) against the same
`diff.patch`. **This is live nested dispatch, not a walkthrough** — both seats ran as real,
separate `Task` invocations with their own context windows, no shared state with each other or
with the baseline run.

### CAST (abbreviated — 2 of the 6 core seats, chosen for relevance)

Per `references/cast-and-spawn.md` Step 2 (judgment against diff content): this diff modifies
existing logic (a pre-existing function), touches a nullable field at a dereference site, changes
a resource-lifecycle pattern, and renames a type/function that a `CONTEXT.md` documents domain
decisions for. That content profile cast:

- **Correctness/Adversarial** (`skills/adversarial-reviewer/SKILL.md`) — core seat, always cast.
- **Domain-Intent** (`skills/domain-modeling/SKILL.md`) — cast-when: "diff touches a type,
  interface, or entity definition... and whenever a project `CONTEXT.md` exists and the diff
  touches code the CONTEXT.md documents domain decisions for." Both conditions hold.

(A full run would also cast Simplicity, Structural, Fresh-Eyes, and evaluate Security/
Change-Trajectory/Design-Alternatives per the catalog — this pressure test dispatches 2 seats,
not the full panel, since 2 is sufficient to demonstrate the coherence-axis gap the baseline
couldn't cover; casting the remaining seats would not change the red→green result being tested
here. This narrowing is itself flagged in the Coverage Honesty section below.)

### SPAWN (live)

Both seats dispatched in one batch via `Task`, read-only, given the **same** `diff.patch` content
(Correctness/Adversarial got no `CONTEXT.md`, matching its actual scope which doesn't cover
domain-terminology coherence; Domain-Intent got `CONTEXT.md`'s glossary + decision log, matching
its actual cast contract).

### Results

**Correctness/Adversarial seat** independently reproduced bugs #1 and #2 with the same severity
calibration as the baseline (Critical: null-deref on type-legal `null` input; Critical: leak on
failure path; Critical: off-by-one) plus additional adversarial detail the baseline didn't
surface: an explicit distinguishing note that `reserveItems` *throwing* (vs. returning
`{success:false}`) also bypasses the success-only `conn.close()`, and a call for regression tests
on exactly the untested failure branch where both bugs live. It did not flag bug #3 — correctly,
since domain-terminology coherence is out of this seat's scope by design (see
`skills/adversarial-reviewer/SKILL.md`'s Scope list, which does not include naming/glossary
coherence).

**Domain-Intent seat**, given `CONTEXT.md`, caught **all three** bugs, including — critically —
bug #3, with the exact citation the baseline structurally could not produce:

> `TRIGGERED — after.ts:19-21 — glossary/naming coherence — Important — processFulfillment renamed
> to processShipping... The function still validates a payment token and retries against the
> warehouse — exactly the behavior the glossary says disqualifies something from being called
> shipping ("a function that does more than carrier hand-off ... is a fulfillment operation, not
> a shipping operation"). This is a direct, named violation of the decision log's rationale, not
> just a stylistic drift.`

It also independently reached bugs #1 and #2 through the illegal-states-unrepresentable lens
(`paymentToken` typed nullable but handled as if guaranteed; `MAX_ATTEMPTS` "attempt budget"
glossary term silently violated by the off-by-one), giving MERGE's 2+-independent-seat-agreement
bump (`references/merge-and-validate.md` Step 3) a real corroboration path for those two findings
across both dispatched seats, on top of the baseline's independent third catch.

### MERGE, applied to these 2 seats' output (worked by hand against `references/merge-and-validate.md`)

| Finding | Seats reporting | Fingerprint match | Confidence anchor |
|---|---|---|---|
| Null-deref on `paymentToken.value` | Adversarial + Domain-Intent (2 independent seats) | Same file, same line region, same normalized title (`missing null check on paymenttoken`) | 2+ agreement → base 75 (quote-the-line passes, concrete mechanical claim) bumped to **100** |
| Leak + off-by-one on retry loop | Adversarial + Domain-Intent (2 independent seats) | Same file, adjacent lines within ±3, title-equivalent (`connection leak / off-by-one on retry`) | 2+ agreement → **100** |
| `fulfillment`→`shipping` coherence drift | Domain-Intent only (Adversarial's scope excludes this axis by design, so 1-seat is expected, not a gap) | N/A — single seat | Quote-the-line passes (cites CONTEXT.md's exact decision-log sentence), concrete but requires the contextual judgment of "does this violate a documented decision" → **75** |

### VALIDATE (worked by hand, not live-dispatched for this pressure test)

Per `references/merge-and-validate.md`, the null-deref and leak/off-by-one findings are
Critical-severity and would escalate to 2-3 independent clean-room validators; the coherence
finding gets 1. Given that this pressure test's own baseline run functioned as an independent,
blind, clean-room-equivalent check (it never saw the panel seats' reasoning, the fingerprint
methodology, or CONTEXT.md) and it independently reached the same conclusion on bugs #1 and #2
using only the raw diff, that is itself a real-world instance of the "does the claimed issue
survive an independent, code-only challenge" test VALIDATE formalizes — both Critical findings
would SURVIVE. The coherence finding was not independently checked by a second party in this
pressure test (no second Domain-Intent-equivalent pass was run) — flagged honestly as unvalidated
in the Coverage Honesty section below, since VALIDATE proper was not live-dispatched here.

### Conclusion: green

The panel — specifically, casting a Domain-Intent seat armed with `CONTEXT.md` — catches all 3
seeded bugs. The baseline, structurally, cannot catch bug #3, because catching it requires
information (`CONTEXT.md`'s documented decision) the baseline was never given and has no
casting/skill-invocation step that would surface. This is the "skill's presence changes the
outcome" result this pressure test set out to demonstrate: not "the panel is smarter than a
generic reviewer" (on bugs #1/#2, this particular baseline was comparably strong), but "the
panel's casting discipline routes the diff to a reviewer with the specific domain context needed
to catch a class of bug no amount of general code-reading skill can catch without that context."

---

## 4. Circuit-breaker scenario (written walkthrough, not live-executed)

This section constructs a scenario per `references/converge-and-pipeline.md`'s exact 3-strikes
definition and walks through it round-by-round. Not live-executed — the 7-stage loop's CONVERGE
decision requires multiple full SPAWN→MERGE→VALIDATE→FIX→RE-REVIEW rounds, which is out of scope
to actually run for a pressure test; the definitions and thresholds quoted below are the real
ones from the reference file, applied by hand to a constructed scenario.

**Seeded unfixable finding:** imagine `after.ts`'s off-by-one fix is contested — VALIDATE passed
an Important finding: *"the retry loop's semantics are ambiguous: should a `reserveItems` call
that **throws** (network error) consume one unit of the attempt budget, the same as a call that
resolves `{success:false}`? The current code (both before and after this diff) does not
distinguish these cases, and the domain owner has not specified which behavior is correct."* This
is fundamentally a **product decision**, not a code defect a fixer can resolve — there is no
"correct" diff without a human ruling on the semantics.

**Round-by-round, per `converge-and-pipeline.md`'s "What counts as progress" and "3-strikes"
sections:**

- **Round 1 FIX:** the fixer applies the null-check restore, `try/finally` restore, and loop-bound
  fix (all mechanical). For the ambiguous-attempt-budget finding, it reports (per
  `references/fix-and-rereview.md`'s FIX dispatch contract, item 3): *"could not fix: ambiguous
  requirement — need product decision on whether a thrown reserveItems error consumes an attempt
  slot before this can be resolved."* **Round 1 RE-REVIEW:** total finding count drops from 4 to
  1 (the 3 mechanical bugs are gone; the ambiguous finding remains, unresolved, unchanged
  file:line). **CONVERGE:** total finding count strictly decreased (4→1) → **progress**. Strike
  counter: 0 (this round showed progress, so no strike is recorded).
- **Round 2 SPAWN/MERGE/VALIDATE/FIX:** the same ambiguous finding survives re-validation
  unchanged (no seat can resolve what only a human can decide). FIX again reports "could not fix:
  ambiguous requirement" — identical reason, same root cause. **Round 2 RE-REVIEW:** finding count
  is flat (1→1), same fingerprint, no severity-mix change, no resolution. **CONVERGE:** per the
  "No progress" definition — total count flat, Critical count didn't decrease (there is no
  Critical here, it's Important, so trivially "did not strictly decrease" since it started and
  stayed at 0 Critical), and the previously-flagged finding was not resolved. **No progress.**
  Strike counter: **1**.
- **Round 3:** identical outcome — FIX reports the same "could not fix: ambiguous requirement,"
  RE-REVIEW re-surfaces the same finding at the same fingerprint (not moved beyond the ±3 line
  tolerance, not replaced by an equivalent new finding — genuinely the same unresolved item).
  **CONVERGE: no progress.** Strike counter: **2**.
- **Round 4:** same outcome again. **CONVERGE: no progress, 3rd consecutive round.** Per
  `converge-and-pipeline.md`'s 3-strikes rule: **the circuit-breaker fires here — on the 3rd
  consecutive no-progress round, which is this round (strike counter reaches 3).** The loop stops
  immediately; no 4th round is attempted "just in case."

**Escalation content fired (per the reference file's specified diagnosis shape):**

> Human-interactive mode: an escalation block containing the last 3 rounds' finding counts
> (1, 1, 1 — flat), a diagnosis naming the specific finding — *"the same Important finding about
> ambiguous attempt-budget semantics on a thrown `reserveItems` error has survived 3 fix attempts
> at `after.ts`'s retry loop — the fixer's reason each round was identical ('could not fix:
> ambiguous requirement'), indicating this requires a human product decision, not another fix
> attempt"* — and a recommendation to resolve the ambiguity manually rather than re-loop.
> `mode:agent`: `status: "circuit_broken"`, `convergence.circuit_breaker.tripped: true`,
> `consecutive_no_progress_rounds: 3`, and `diagnosis` set to the same human-readable string.

**Confirmed: fires after round 3 (i.e., on the round where the 3rd consecutive no-progress
result is observed), not before** — round 1 showed real progress (3 of 4 findings resolved) and
correctly did not count as a strike; only rounds 2, 3, and the confirming 4th evaluation
accumulate the 3 consecutive misses the rule requires. This matches
`converge-and-pipeline.md`'s explicit statement that "a 'strike' resets to 0 the moment a round
shows progress... this is a consecutive-rounds counter, not a lifetime counter."

---

## 5. Coverage-honesty scenario (written walkthrough)

**Scenario:** the panel is invoked against `diff.patch` in an environment where the
`domain-modeling` skill (the Domain-Intent seat's target) is not installed — e.g. a partial/broken
plugin install, or a session where only a subset of `skills/` was synced. Per
`reviewers/persona-catalog.md`'s "Missing skill handling" section, this is a **core seat**
(`domain-modeling` ships with this plugin), so the rule is: *"report the gap in the
coverage-honesty statement rather than silently dropping the seat."*

**What CAST does:** Step 5 of `references/cast-and-spawn.md` detects that `domain-modeling`'s
target skill is unavailable in this session (a broken install, not merely a live-scan miss) and
records the gap rather than silently omitting the seat from the cast list.

**What the final report says, per `dual-mode-contract.md`'s two output shapes:**

- **Human-interactive mode** — the `## Coverage Honesty` section of the final report (per the
  template in `dual-mode-contract.md`'s "Final report structure") includes an explicit line, not
  a silent omission:

  > **Coverage Honesty:** Domain-Intent seat (`skills/domain-modeling/SKILL.md`) was cast-eligible
  > for this diff (touches a type/interface with a `CONTEXT.md`-documented domain decision at
  > `tests/fixtures/order-fulfillment/CONTEXT.md`) but the target skill was not installed in this
  > session. Domain-terminology coherence (the `fulfillment`/`shipping` distinction this
  > `CONTEXT.md` documents) was **not checked** by this run. This is a genuine coverage gap, not
  > equivalent to a clean result on that axis — a human should manually check the diff against
  > `CONTEXT.md` before merging, or re-run once `domain-modeling` is available.

  This directly demonstrates SKILL.md's own coverage-honesty rule in action: *"A panel run that
  silently skipped coverage and reported 'clean' is worse than one that states what it skipped
  and why."* Without this statement, RE-REVIEW's Axis (b) would simply never run, and — per this
  pressure test's own Section 3 finding — the coherence bug is exactly the class of defect a
  baseline (or a coherence-blind panel run) structurally cannot catch; silently omitting the
  coverage-honesty note would let a genuinely blind spot masquerade as "the panel checked and
  found nothing," which is a materially worse failure mode than an honest "we couldn't check
  this."

- **`mode:agent` JSON contract** — the `coverage` object (per `dual-mode-contract.md`'s JSON
  shape) is never omitted, and in this scenario is populated, not empty:

  ```json
  "coverage": {
    "skipped_seats": [
      {
        "seat": "Domain-Intent",
        "skill": "skills/domain-modeling/SKILL.md",
        "reason": "core seat target skill not installed in this session (broken/partial install)",
        "cast_eligible": true,
        "would_have_checked": "CONTEXT.md coherence (fulfillment/shipping domain-term drift) at tests/fixtures/order-fulfillment/CONTEXT.md"
      }
    ],
    "fallbacks_used": [],
    "notes": [
      "RE-REVIEW Axis (b) (coherence vs. domain intent) did not run this round due to the Domain-Intent seat gap above."
    ]
  }
  ```

  Per the field notes in `dual-mode-contract.md`, this is exactly the distinguishing case the
  spec calls out: the `coverage` object is present and explicit (`skipped_seats` populated with a
  concrete reason) rather than either being omitted or silently reporting an empty
  `skipped_seats` array that a `foundry` gate consuming this JSON could not distinguish from "full
  coverage, nothing to report."

---

## 6. Conclusion

This pressure test demonstrates, with live nested-`Task` dispatch for the CAST/SPAWN portion and
careful hand-application of the documented MERGE/VALIDATE/CONVERGE rules for the rest, that
`review-panel`'s prescribed casting discipline changes the outcome on a realistic 3-bug fixture: a
strong single-pass baseline reviewer independently catches 2 of 3 seeded bugs (null-deref,
leak/off-by-one) but structurally cannot catch the third (domain-term coherence drift) because it
was never given the domain documentation to check against — while the review-panel's Domain-Intent
seat, cast specifically because the diff meets the catalog's documented cast-when criteria and
armed with the `CONTEXT.md` the catalog's casting logic exists to route reviewers toward, catches
all three. The circuit-breaker and coverage-honesty walkthroughs confirm, by careful round-by-round
and section-by-section application of `converge-and-pipeline.md`'s and `dual-mode-contract.md`'s
literal rules to constructed scenarios, that the 3-strikes escalation fires exactly on the 3rd
consecutive no-progress round (not before, not after) with the specified diagnosis content, and
that a bounded-coverage run states what it skipped and why rather than silently reporting false
cleanliness.

**Limits of this pressure test:**

- `review-panel` is a set of markdown prompts orchestrating Claude subagents, not executable code
  — there is no automated regression suite this document produces, and none of this is re-runnable
  by a CI job without a live Claude session driving the same 7-stage judgment calls again. This is
  a documented demonstration of effect (red baseline → green panel), not a deterministic test.
- Sections 1-3 (fixture, baseline, and the 2-seat CAST/SPAWN) are **live**: real `Task` dispatches,
  real subagent output, quoted verbatim/summarized above. Sections 3's MERGE/VALIDATE tables and
  all of Sections 4-5 (circuit-breaker, coverage-honesty) are **worked-by-hand walkthroughs**
  against the reference files' literal rules, not live multi-round panel executions — a full live
  run of MERGE, VALIDATE with real independent validators, FIX, RE-REVIEW, and a real 3-round
  CONVERGE loop was judged out of scope for a pressure-test harness (it would require running the
  actual multi-round orchestration this task is validating the *design* of, which is a much larger
  undertaking than seeding and checking one fixture diff).
  This document labels each section's status (live vs. walkthrough) explicitly rather than
  blurring the distinction, per this task's own instructions.
- The fixture is deliberately small (one file, 3 bugs) so it's cheap to reason about exhaustively;
  it does not exercise the panel's bounded-parallel SPAWN concurrency cap, multi-batch MERGE
  pipelining, or a genuinely large/ambiguous diff where casting judgment itself is harder to get
  right. Those remain untested by this harness and would need a separate, larger fixture if future
  work wants to pressure-test them specifically.
- Only 2 of the catalog's 6 core seats were cast for this pressure test (see Section 3's CAST note)
  — sufficient to demonstrate the red→green result this task requires, but not a demonstration of
  the full panel's Simplicity/Structural/Fresh-Eyes seats or the risk-triggered
  Change-Trajectory/Design-Alternatives seats against this fixture.
