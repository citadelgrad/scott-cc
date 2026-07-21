# CONVERGE, and Pipeline-Not-Barrier

Stage 7, plus the cross-cutting pipeline-not-barrier mechanism that stages CAST through MERGE
implement (not a separate stage of its own — it's a property of how the earlier stages run).

---

## CONVERGE

**Goal:** decide, after each RE-REVIEW, whether the panel loop is done, needs another round, or
must circuit-break and escalate to a human.

### Decision rule

0. **Sovereignty check, ahead of the clean/dirty call, in every tier.** Before applying the
   clean/dirty rule below or either narrowed tier's iteration cap in step 2, check whether any
   surviving finding (from VALIDATE's output, carried through FIX untouched by construction — see
   [fix-and-rereview.md](fix-and-rereview.md)'s "Sovereignty guard") still carries
   `sovereignty: human-required` (produced by the Data-Steward seat — see
   `reviewers/persona-catalog.md`'s "Data Steward" entry). This is a **new terminal state**, not a
   loop condition: looping back to SPAWN again would not resolve a sovereignty finding, since FIX
   is barred from ever touching it — re-running the loop just re-derives the same unresolved
   finding. This check runs identically in every tier including full mode — narrowing the review
   scope never narrows it (SPEC Architecture invariant 3; see also
   [lite-mode.md](lite-mode.md)'s "The sovereignty guard is untouched"). If one or more
   sovereignty-marked findings remain:
   - Emit status `escalated` (human mode: an explicit human sign-off request block, naming each
     unresolved sovereignty finding, its file, and why it wasn't auto-fixed; `mode:agent`: top-level
     JSON `"status": "escalated"` — see [dual-mode-contract.md](dual-mode-contract.md)).
   - Do **not** loop back to SPAWN for these findings, and do **not** collapse this into
     `circuit_broken` or `capped` — a circuit-break means the loop tried and failed to make
     progress; `capped` means a narrowed tier's round budget ran out on ordinary findings;
     `escalated` means the loop correctly recognized a finding it must never resolve on its own and
     stopped by design. These are three different outcomes and must stay distinguishable
     downstream.
   - If sovereignty-marked findings coexist with other, ordinary unresolved findings in the same
     round, still apply the dirty-round loop (step 2 below) to the ordinary findings across further
     rounds, subject to the active tier's cap — `escalated` is not exclusive of continuing to
     converge on everything else. Report `escalated` as the overall run status once every
     *non*-sovereignty finding has otherwise reached a clean state, or once the active tier's cap is
     reached on those ordinary findings (report both `escalated` and the tier-cap diagnosis
     together in that case); until then, the round is simply dirty (step 2) with the sovereignty
     finding(s) noted as carried-forward-by-design in the report rather than counted as regressions.
1. **Clean round → done.** If RE-REVIEW's Axis (a) regression check and Axis (b) coherence check
   both come back clean (zero new findings, zero unresolved findings from the round that just
   fixed) **and no sovereignty-marked finding remains** (step 0), the loop stops. Emit the final
   report (human mode) or the final JSON blob (`mode:agent`) per
   [dual-mode-contract.md](dual-mode-contract.md), with status `converged`. This is unchanged in
   every tier — a clean round is `converged` whether reached in round 1 under `--lite`, round 1 or
   2 under `--medium`, or any round under full mode.
2. **Dirty round → check the active tier's cap, then loop or terminate.** If RE-REVIEW surfaces any
   new or unresolved finding, first check the round just completed against the active tier's
   iteration cap:
   - **Lite:** capped at **1** total round. If the round that just went dirty was round 1 (it
     always is, under lite), do **not** loop back to SPAWN — terminate immediately with status
     `capped` (see "Narrowed-tier iteration cap" below).
   - **Medium:** capped at **2** total rounds. If the round that just went dirty was round 2,
     terminate with status `capped`. If it was round 1, the tier still has its second permitted
     round available — loop back to SPAWN as step 3 describes, exactly once.
   - **Full** (no tier flag, or `--auto` resolved to full): no tier cap — unchanged from today,
     loop back to SPAWN as step 3 describes, subject only to the existing 3-strikes circuit-breaker
     and the round-8 hard cap below. Full mode's dirty-round-loops-to-SPAWN behavior, the 3-strikes
     breaker, and the round-8 hard cap are all unmodified by this phase and are simply never
     reached under either narrowed tier, since a narrowed-tier loop never proceeds past its own
     cap (1 or 2 rounds) to begin with.

   When step 2 does loop (dirty round, cap not yet reached): take the new packaged diff RE-REVIEW
   already produced and hand it to the next iteration, per step 3 below.
3. **Loop back to SPAWN, not always CAST.** The re-entry point for a looped iteration is
   **SPAWN**, using the same cast list CAST already produced, UNLESS RE-REVIEW's findings suggest
   the diff has changed in a way that plausibly changes which seats should be cast (e.g. FIX
   introduced a new type/schema surface that wasn't there in round 1, which would newly trigger
   Domain-Intent if it wasn't already cast). In that case, re-run CAST first. **Justification for
   defaulting to SPAWN over CAST:** casting judgment is a property of the diff's overall shape
   (does it touch types, security boundaries, new architecture), which rarely changes
   qualitatively between one fix-pass and the next — re-running the full CAST judgment call every
   iteration is redundant work for no expected behavior change in the common case. Re-running MERGE
   is implied either way, since a new SPAWN round always needs a new MERGE pass over its output;
   there's no version of "loop back to MERGE directly" that skips SPAWN, since MERGE has nothing
   to merge without a fresh SPAWN round to consume the new diff. **Full cast list, not RE-REVIEW's
   scoped subset:** this looped SPAWN dispatches the *entire* cast list (all core seats, plus
   whatever risk-triggered/live-scan seats CAST added), not the smaller subset RE-REVIEW's Axis (a)
   re-casts (Correctness/Adversarial plus whichever seats had a finding in the fixed set, scoped to
   the touched files). RE-REVIEW's scoping is a deliberately narrow, fast regression/coherence check
   against FIX's specific edits — it is not a substitute full panel pass, and its efficiency does
   not carry over to the next full SPAWN round: a fix can introduce an issue outside the seats that
   flagged the original problem (e.g. a Domain-Intent fix's implementation detail trips a Security
   concern no one was looking for), and only a full-cast SPAWN round, feeding a fresh MERGE/VALIDATE
   pass, is positioned to catch that.

### What counts as "progress" (for the circuit-breaker)

Define progress precisely, round-over-round, using RE-REVIEW's finding counts (never a vague
"seems better"):

- **Total finding count** (post-MERGE, pre-VALIDATE, across both RE-REVIEW axes) strictly
  decreasing from the previous round, OR
- **Severity mix improving**: even if the raw count is flat or slightly up, progress still counts
  if the number of Critical findings strictly decreased and no new Critical finding appeared, OR
- **A previously-circuit-relevant finding is now resolved**: a specific finding present in round
  N's RE-REVIEW output is absent (and not replaced by a fingerprint-equivalent new finding) in
  round N+1.

**No progress** means: the total finding count is flat or increased, AND the Critical count did
not strictly decrease, AND no previously-flagged finding was actually resolved (a finding that
just moved file:line by more than the ±3 fingerprint tolerance without being genuinely fixed does
not count as resolved — that's evasion, not progress, and should itself be flagged as suspicious
in the report).

**Sovereignty-marked findings are excluded from this count entirely, in both directions.** A
finding carrying `sovereignty: human-required` is never resolved by FIX by construction (see
"Sovereignty guard" in [fix-and-rereview.md](fix-and-rereview.md)) — it is expected, correct
behavior for it to persist round over round. Do not count its persistence as "no progress" (it
would otherwise misfire the 3-strikes breaker on every sovereignty case, mis-reporting a
by-design outcome as `circuit_broken`), and do not count its presence toward the total/Critical
finding tallies this section uses to judge progress on the *rest* of the round's findings. Once
every non-sovereignty finding is resolved, the round's status is `escalated` (Decision rule step
0), not `circuit_broken` — the circuit-breaker exists to catch genuine stagnation, and a
sovereignty finding sitting untouched by design is not stagnation.

### 3-strikes circuit-breaker

Track consecutive rounds with no progress (per the definition above). On the **3rd consecutive**
round with no progress:

1. **Stop looping immediately.** Do not attempt a 4th round.
2. **Escalate to a human.** Human-interactive mode: print an escalation block containing the last
   3 rounds' finding counts (total, by severity), a diagnosis of what specifically isn't
   converging (e.g. "the same Important finding at `foo.ts:42` has survived 3 fix attempts — the
   fixer's approach is not resolving the root cause, or the finding itself may be a false
   positive that VALIDATE incorrectly passed"), and a recommendation (fix manually, or challenge
   the finding's validity directly). `mode:agent`: set the top-level JSON status to
   `circuit_broken` with the same diagnostic detail in a structured field — see
   [dual-mode-contract.md](dual-mode-contract.md).
3. **Do not silently give up.** A circuit-break is a distinct, explicit terminal state — never
   collapse it into either `converged` (it did not converge) or a bare error (it's not a crash,
   it's a designed stop condition), and never collapse it into `escalated` either — a circuit-break
   is unplanned stagnation on findings FIX was supposed to be able to resolve, while `escalated` is
   the expected, by-design outcome for findings FIX was never allowed to touch (Decision rule step
   0 above). Downstream automation (a `foundry` gate) must be able to distinguish "converged
   clean," "circuit broken, needs a human," "escalated for sovereignty sign-off," and "run failed
   to execute" as four different outcomes.

A "strike" resets to 0 the moment a round shows progress by the definition above — this is a
consecutive-rounds counter, not a lifetime counter across the whole run.

### Narrowed-tier iteration cap → `capped`

When decision-rule step 2 above terminates a `--lite` or `--medium` run because its tier's round
cap was reached on a still-dirty round, that is a **new terminal status, `capped`** — deliberately
**not** a reuse of `circuit_broken` (PRD D5, resolving SPEC OQ4; an earlier provisional design that
reused `circuit_broken` for this case is superseded by this decision):

1. **Stop looping immediately** — do not attempt a round beyond the tier's cap (1 for lite, 2 for
   medium), regardless of whether the rounds so far showed progress. A narrowed tier's cap is a
   hard stop on round count, not a progress judgment — unlike the 3-strikes breaker above, `capped`
   can trigger on a *first* dirty round (lite) even if that round's RE-REVIEW was clearly moving in
   the right direction.
2. **Emit a tier-specific diagnosis.** Human-interactive mode: print an escalation block headed
   `## Capped — Narrowed Tier Limit Reached` — structurally parallel to, but visually and textually
   distinct from, the circuit-breaker's `## Circuit Broken` block above, so a reader never confuses
   "this tier did what it was told" with "something is actually wrong." Word the diagnosis for the
   specific tier and cap reached, e.g.:
   - Lite: *"lite mode capped at 1 iteration; findings remain after the first FIX/RE-REVIEW pass —
     re-run without `--lite` (or with `--medium` / no flag) for deeper convergence."*
   - Medium: *"medium mode capped at 2 iterations; findings remain after the second FIX/RE-REVIEW
     pass — re-run without `--medium` (or with no flag) for deeper convergence."*
   `mode:agent`: set the top-level JSON `status` to `capped` (not `circuit_broken`), with the same
   diagnosis text in `convergence.capped.diagnosis`, alongside the run's `tier` and
   `narrowed_guarantees` fields (see [dual-mode-contract.md](dual-mode-contract.md)) so the tier
   context is unmistakable next to the diagnosis without a consumer having to cross-reference which
   flag was passed.
3. **Why a new status value, not `circuit_broken` reuse:** hitting a tier's iteration cap is
   expected, by-design behavior the invoker opted into by selecting `--lite`/`--medium` — it is not
   an anomaly. `circuit_broken` must keep meaning exactly what it means today: full mode's genuine
   3-strikes-or-round-8 stagnation, an actual "something isn't converging" signal. Conflating the
   two under one status value would force every consumer (human or `mode:agent`/`foundry` gate) to
   parse diagnosis text to tell "this tier did what it was told" from "something is actually
   wrong." With `capped` structurally distinct, a `foundry` gate can branch on it directly — e.g.
   `decision_on_failure: warn` and "re-run at a deeper tier," per
   [dual-mode-contract.md](dual-mode-contract.md)'s foundry-wiring guidance — rather than the
   `circuit_broken` gate's "investigate a stuck review" response.
4. **Tier exclusivity, both directions.** Full mode never returns `capped` — it has no tier cap to
   hit, only the circuit-breaker and round-8 hard cap below. Narrowed tiers (`--lite`, `--medium`)
   never return `circuit_broken` — their round count never reaches high enough (1 or 2 rounds) for
   the 3-strikes-consecutive-no-progress condition or the round-8 hard cap to have a chance to
   trigger first; the tier's own cap always terminates the loop before either of those full-mode-
   only conditions could fire.

### Loop iteration cap independent of circuit-breaker

The circuit-breaker triggers on *no progress*; it does not, by itself, cap a slowly-but-genuinely
converging run. In practice this loop should still rarely exceed ~5-6 total rounds even when
making progress every round (real diffs converge fast once Critical/Important findings are fixed).
If a run is still looping past 6 rounds while technically showing progress each time (e.g.
shrinking by one Minor finding per round), treat that as worth flagging in the report as unusually
slow convergence, even though it hasn't tripped the circuit-breaker — this is a coverage-honesty
note, not a hard stop by itself.

**Hard cap at round 8.** Independent of and in addition to the 3-strikes circuit-breaker above,
the loop must not run a 9th round under any circumstances, even if every round so far showed
genuine progress by the strict definition. On reaching the end of round 8 without a clean
RE-REVIEW, force-escalate exactly like a circuit-break: stop looping immediately, and emit the
same escalation shape the 3-strikes breaker uses (human mode: escalation block; `mode:agent`: top-
level status `circuit_broken`), with the diagnosis text noting explicitly that this was the
**iteration cap**, not stagnation (e.g. "8 rounds completed, each showing progress, but the loop
did not converge within the hard round cap — this is not stagnation; consider whether the fixer is
resolving findings correctly but slowly, or whether MERGE/VALIDATE are systematically
under-batching findings per round"). This is a second, independent stop condition, not a
replacement for the 3-strikes breaker — whichever triggers first ends the loop.

---

## Pipeline-Not-Barrier

This is the concurrency shape CAST through MERGE actually run in — described here as its own
section because it's load-bearing across multiple stages, not a property of any single one.

### The principle, in this orchestrator's own words

A seat that finishes reviewing and has nothing to report should be marked done and let the rest of
the pipeline move on immediately — it must not sit and wait for the slowest seat in its batch to
also finish before MERGE is allowed to start processing anyone's output. Symmetrically, a seat that
comes back with findings should have those findings flow into MERGE as soon as they're available,
not held back until every other seat in the batch also reports in. The only point in the entire
7-stage loop where everything must wait for everything else is immediately before final synthesis
— CONVERGE's decision (and the report it produces) genuinely needs every seat's output and every
RE-REVIEW axis's result to make a correct call, since progress-measurement and the clean/dirty
verdict are both whole-round judgments, not per-seat ones.

### Concretely, in this orchestrator

- **Within a SPAWN batch** (see [cast-and-spawn.md](cast-and-spawn.md)'s bounded-parallel
  concurrency bound): as each seat in the batch returns, immediately start MERGE's fingerprinting
  and confidence-scoring work on that seat's findings against whatever has already been merged so
  far, rather than buffering all batch results and starting MERGE only once the whole batch is
  back. A seat reporting zero findings contributes nothing to fingerprinting and should not block
  MERGE's processing of seats that did report findings. **Granularity caveat:** a batch of
  concurrent `Task` dispatches typically returns to the orchestrating conversation together as a
  group, not with true per-seat completion events the orchestrator can observe individually — most
  runtimes have no mechanism to notice "seat 2 of 5 just finished" while seats 1, 3, 4, 5 are still
  running. In practice this principle applies at the granularity of "as each batch of up to 5
  concurrent seats returns," not literally streaming per-individual-seat; the batch-vs-batch
  incrementality described below (start MERGE on batch 1 while batch 2 runs) is where the real
  pipelining benefit comes from in most runtimes. If a specific runtime does expose true per-seat
  completion within a batch, take advantage of it — but don't assume it's available by default.
- **Across SPAWN batches**: if a panel needs 2 batches (more than 5 cast seats), MERGE can begin
  consolidating batch 1's results while batch 2 is still running — MERGE's fingerprint/confidence
  work is incremental (each new finding either joins an existing fingerprint group or starts a
  new one), so there's no structural reason to wait for batch 2 before starting on batch 1's
  output.
- **VALIDATE**: each merged finding's validator(s) can be dispatched as soon as that finding clears
  MERGE, independent of whether other findings have finished merging yet. A finding with a clear,
  early fingerprint match doesn't need to wait for a slower, more ambiguous finding elsewhere in
  the diff to finish its own merge/dedup resolution.
- **The one hard barrier**: CONVERGE's decision. It cannot run until (a) every cast seat's SPAWN
  result is accounted for (returned, or recorded as a coverage gap if it errored/timed out), (b)
  every surviving finding has completed VALIDATE, (c) FIX has completed and reported its
  fix/skip list, and (d) RE-REVIEW has completed both axes. Any one of these still pending means
  CONVERGE cannot yet decide clean-vs-loop-vs-circuit-break, since the decision genuinely depends
  on the complete picture.

### Why this matters here specifically

The plan's core insight is perspective diversity from independent seats — but independence of
*judgment* is not the same as independence of *scheduling*. Serializing every seat behind a full
batch barrier before MERGE can start doesn't add any independence value (each seat already formed
its judgment in isolation during SPAWN); it only adds wall-clock latency. Pipeline-not-barrier is
how this orchestrator keeps the diversity benefit of casting many seats without paying for it with
a slow, fully-serialized stage-by-stage loop.
