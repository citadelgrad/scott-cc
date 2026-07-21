# review-panel Lite Mode — SPEC

**Status:** Draft — self-approved (planning-only session, no code changes; see stage-5-approval.md)
**Date:** 2026-07-18 (amended 2026-07-19: `--medium` tier added per explicit human decision,
resolving OQ3 and OQ4; further amended 2026-07-19: `--auto` tier-resolution flag added per
explicit human decision — see Phase 6 and "Decisions on open questions" at the end of this
document)
**Owner:** Scott
**PRD:** [review-panel-lite-prd.md](./review-panel-lite-prd.md)
**Beads Epic:** scc-c56

> Technical specification for the PRD's five goals. Each phase is independently shippable and
> ordered by build dependency, not strict priority (this is a single-plugin feature — phases are
> smaller and more tightly coupled than the two-system precedent's cross-plugin phases).
> Acceptance criteria are written to be testable (unambiguous PASS/FAIL) so they can seed bead ACs
> at decompose time per the `acceptance-criteria` skill rules: happy path, error states, boundary
> conditions; no Definition-of-Done items.

---

## Architecture invariants (apply to every phase)

1. **Parameterization, not forking.** `--lite`, `--medium`, and `--auto` are read by the existing
   `SKILL.md` and `references/*.md` files as run-time parameters, exactly as `--mode=agent` already
   is. No phase may introduce a second orchestrator, a duplicated copy of a stage's procedure, or a
   parallel `skills/review-panel-lite/` (or `-medium/`, `-auto/`) directory. All narrowed-tier logic
   lives either inline in the existing reference files (as a tier conditional) or in one new
   `references/lite-mode.md` (covering all tier logic including `--auto`'s resolution step — not
   separate files per flag), read just-in-time only when `--lite`, `--medium`, or `--auto` is
   present. `--auto` is a *resolver*, not a fourth tier: it picks one of the three existing tiers
   and then that tier's unmodified machinery runs — Phase 6 adds no new SPAWN/VALIDATE/RE-REVIEW/
   CONVERGE logic of its own.
2. **Fail-closed casting is reused verbatim, never re-derived.** Every phase that touches SPAWN's
   seat selection must cite and reuse `cast-and-spawn.md`'s existing Steps 1-3 and
   `persona-catalog.md`'s existing Security/Data-Steward cast-when criteria byte-for-byte, in every
   tier. No phase may write new casting logic, new trigger conditions, or a new fail-closed rule
   for any narrowed tier. Each tier narrows the *optional/risk-triggered/live-scan* seat set only,
   by a different fixed amount (see "Narrowing tiers" table below). `--auto`'s fail-closed-sensitive
   path check (Phase 6) is bound by this invariant too: it reuses `persona-catalog.md`'s existing
   Security/Data-Steward cast-when path criteria verbatim as its sensitivity signal — it does not
   invent a second, parallel notion of "sensitive path."
3. **The sovereignty guard is untouched.** The post-FIX mechanical `git hash-object` integrity
   check (`fix-and-rereview.md`) and the `escalated` terminal status
   (`converge-and-pipeline.md`, `dual-mode-contract.md`) apply identically regardless of tier. No
   phase may add a tier conditional anywhere inside the sovereignty guard's code path.
4. **Coverage honesty extends, not replaces.** Every phase that narrows a stage under `--lite` or
   `--medium` must add that narrowing to the existing Coverage Honesty disclosure mechanism
   (SKILL.md's Coverage Honesty section, the human report's "Coverage Honesty" block, the JSON
   contract's `coverage` object) — never a silent skip, and never a second, competing disclosure
   mechanism.
5. **Full mode is byte-for-byte unchanged.** Every phase's diff must leave full-mode behavior
   (dispatch count, seat selection, output shape) identical to today when no tier flag is present
   and `--auto` is absent. When `--auto` resolves to full (Phase 6), SPAWN/VALIDATE/RE-REVIEW/
   CONVERGE behavior is likewise identical to unflagged full mode — only the disclosure differs (a
   one-line "auto resolved to full" note, per Phase 6). Any existing full-mode fixture must
   continue to pass unmodified.
6. **Composability with `--mode=agent`; mutual exclusivity between tier-selecting flags.**
   `--lite`/`--medium`/`--auto` and `--mode=agent` are independent, orthogonal flag families parsed
   from `$ARGUMENTS` exactly as `--mode=agent` is parsed today (SKILL.md Setup step 1) — no phase
   may make a tier-selecting flag and `--mode=agent` mutually exclusive or require a specific
   order. `--lite`, `--medium`, and `--auto` ARE pairwise mutually exclusive with *each other*: at
   most one may be present; passing two or more is a hard error (PRD D14, D19), never a silent
   pick-one resolution.

## Narrowing tiers (canonical parameter table — every phase cites this, never restates it)

| Dimension | Full (default) | Medium (`--medium`) | Lite (`--lite`) |
|---|---|---|---|
| CAST Step 4 (live-scan) | runs | **skipped** | **skipped** |
| SPAWN seat set | 6 core + risk-triggered + live-scan, fail-closed-forced always included | Adversarial + Simplicity + Structural + fail-closed-forced | Adversarial + fail-closed-forced |
| VALIDATE cap | 1/finding, 2-3 for Critical | 1/finding, **2** for Critical | 1/finding flat, **no** Critical escalation |
| RE-REVIEW re-cast | scoped subset per existing rule, 2-4 | whichever of {Adversarial, Simplicity, Structural} was fixed + fixed fail-closed seats | Adversarial (if fixed) + fixed fail-closed seats |
| CONVERGE iteration cap | 3-strikes / round 8 | **2** total iterations | **1** total iteration |
| Iteration-cap terminal status | n/a (uses `circuit_broken` for genuine 3-strikes/round-8 stagnation) | `capped`, tier-specific diagnosis | `capped`, tier-specific diagnosis |
| Disclosure | `"tier": "full"`, `narrowed_guarantees: []` | `"tier": "medium"`, `narrowed_guarantees` populated | `"tier": "lite"`, `narrowed_guarantees` populated |

`capped` (new status, PRD D5) is used by both narrowed tiers for the "hit iteration cap with
residual findings" terminal case. It is never returned by full mode. `circuit_broken` remains
exclusively full mode's genuine-stagnation signal and is never returned by a narrowed-tier run.

This table has three columns because there are three tiers. `--auto` (Phase 6) is not a fourth
column — it is a pre-CAST resolver that selects one of these three columns from diff signals, and
that column's row-by-row behavior then applies exactly as written above.

---

## Phase 1 — `--lite`/`--medium`/`--auto` flag parsing and disclosure plumbing

### Problem

Nothing in the plugin currently recognizes a `--lite`, `--medium`, or `--auto` flag. `SKILL.md`'s
Setup section (step 1) already parses `$ARGUMENTS` for `--mode=agent` while ignoring it when
resolving the review target; the same parsing point needs to also recognize all three
tier-selecting flags (pairwise mutually exclusive with each other), and the resulting tier value
needs to be threaded through to every later stage that changes behavior under it (Phases 2-5), plus
into both output shapes' disclosure sections (this phase). This phase handles *detecting* `--auto`
and the resulting `tier`/`tier_source` plumbing; Phase 6 covers `--auto`'s actual resolution
mechanism (which tier it picks, and from what signals).

### Changes

- `plugins/review-panel/skills/review-panel/SKILL.md`:
  - Setup step 1: extend the `$ARGUMENTS` parsing note to also detect `--lite`, `--medium`, and
    `--auto` (flag-presence-only, no `=false` form for any of the three — PRD OQ1, resolved)
    alongside the existing `--mode=agent` detection, ignoring all four when resolving the review
    target the same way `--mode=agent` is already ignored. If two or more of
    `--lite`/`--medium`/`--auto` are present, reject the invocation with a clear error (PRD D14,
    D19) before proceeding to CAST — do not silently prefer one. A malformed `=false` attempt on
    any of the three (e.g. `--lite=false`) is rejected with a clear error the same way, never
    silently treated as flag-absent (PRD OQ1, resolved 2026-07-19: reject, not fall back to full
    mode). `--auto`'s resolution itself (turning "auto was requested" into a concrete tier) happens
    after target resolution, per Phase 6 — this step only needs to detect that `--auto` was
    requested and record it as the (not-yet-resolved) tier source.
  - `argument-hint` frontmatter field: extend to document `--lite`, `--medium`, and `--auto`
    alongside `--mode=agent`.
  - Add a row to the stage-to-reference table: `| Narrowed-tier parameters | references/lite-mode.md
    — only if invoked with --lite, --medium, or --auto |`, following the existing just-in-time
    discipline (same pattern as the `dual-mode-contract.md` row's "only if invoked with
    `mode:agent`" qualifier).
  - Coverage Honesty section: add one sentence establishing that a `--lite`/`--medium`/`--auto`
    run's narrowed guarantees (enumerated per-tier in `references/lite-mode.md`) are a
    coverage-honesty disclosure, not a silent behavior change, and must appear in both output modes
    per Phase 1's disclosure changes below.
- New `plugins/review-panel/skills/review-panel/references/lite-mode.md`:
  - States the flag contract (presence-only, mutually exclusive between `--lite`/`--medium`,
    composable with `--mode=agent`, held constant for the whole run exactly like `--mode=agent`,
    per Architecture invariant 6).
  - States, in one place, the fixed list of guarantees narrowed **per tier** — this becomes the
    canonical source both output-mode disclosures below quote from (see "Narrowing tiers" table
    above for the authoritative values; this file states them as prose guarantee strings, one set
    per tier):
    1. SPAWN restricted to a fixed seat set (tier-dependent) — Phase 2.
    2. VALIDATE capped at a fixed validator count (tier-dependent) — Phase 3.
    3. RE-REVIEW's regression re-cast limited to the tier's SPAWN seat set — Phase 4.
    4. CONVERGE capped at a fixed iteration count (tier-dependent) — Phase 5.
  - Explicitly restates Architecture invariant 3 (sovereignty guard untouched) as a per-file
    reminder, since this is the file most likely to be read by someone deciding whether a narrowed
    tier is safe for a given diff class.
  - Cites (does not restate) `cast-and-spawn.md`, `merge-and-validate.md`, `fix-and-rereview.md`,
    `converge-and-pipeline.md` for the mechanisms it narrows, following `design-lineage.md`'s
    citation-not-copy pattern.
- `plugins/review-panel/skills/review-panel/references/dual-mode-contract.md`:
  - Human report structure: add a `## Narrowed Run` block (renamed from the earlier "Lite Mode"
    working title now that there are two tiers), positioned directly under the report's title
    (before `## Cast`), rendered only when `--lite` or `--medium` was passed. Content: a one-line
    unmissable statement naming the tier ("This was a **medium** run — narrowed for speed, not full
    coverage." / "This was a **lite** run — ...") plus that tier's narrowed-guarantee bullets
    sourced from `lite-mode.md`.
  - `mode:agent` JSON contract: add two top-level fields, both required (never omitted, matching
    the existing `coverage` object's "never omit, empty is itself a signal" rule):
    - `"tier": "full"` — string enum `"full" | "medium" | "lite"`, always present. Replaces the
      earlier two-state `"lite": boolean` design (PRD D8), which cannot represent three states.
    - `"narrowed_guarantees": []` — array of strings, empty when `tier` is `"full"`, populated with
      that tier's fixed guarantee strings from `lite-mode.md` otherwise. Fixed vocabulary (not free
      text) so a downstream `jq` consumer can pattern-match reliably.
    - `"tier_source": "explicit"` — string enum `"explicit" | "auto"`, always present (PRD D16).
      `"explicit"` for every run in this phase (no-flag, `--lite`, or `--medium`); `"auto"` is only
      ever produced once Phase 6 lands and `--auto` resolves. This phase defines the field and wires
      the `"explicit"` value for the three flag states it handles; Phase 6 adds the `"auto"` value
      and the `auto_signals` object that accompanies it — this phase does not populate either.
  - `status` enum gains one new value: `capped` (PRD D5), used exclusively by narrowed-tier runs
    that hit their CONVERGE iteration cap with residual findings (Phase 5). Full mode never returns
    `capped`; narrowed tiers never return `circuit_broken`. The other four values
    (`converged | circuit_broken | error | escalated`) are otherwise unchanged in meaning.
  - Foundry wiring example: add a comment line noting that a gate calling `--lite --mode=agent` or
    `--medium --mode=agent` should branch on `status` including the new `capped` value (treat it as
    "incomplete, needs full-panel follow-up," distinct from both `converged` and `circuit_broken`),
    may additionally log `tier`/`narrowed_guarantees` for visibility, and must not treat a non-full
    `tier` value as a different pass/fail signal on its own.

### Acceptance criteria

- Given `/review-panel --lite` (or `--medium`) with no other arguments, Setup step 1 resolves the
  review target using the same bare-invocation fast path as `/review-panel` alone (current working
  tree vs. `HEAD`), and the run proceeds in human-interactive mode with that tier's narrowing
  applied. **PASS/FAIL:** target resolution unaffected by the tier flag's presence; correct tier's
  narrowing active.
- Given `/review-panel --lite --mode=agent` (and the reverse order `--mode=agent --lite`, and the
  same pair for `--medium`), both orders produce an identical run (order-independent flag parsing).
  **PASS/FAIL:** JSON output identical modulo any inherently nondeterministic content (e.g. finding
  ordering) across both invocations against the same diff.
- Given any two of `--lite`/`--medium`/`--auto` together (e.g. `--lite --medium`, `--lite --auto`,
  `--medium --auto`, or all three at once), the invocation is rejected with a clear error before
  CAST runs. **PASS/FAIL:** no dispatches occur in any of the four conflicting combinations; error
  names the specific flags that conflict.
- Given `/review-panel` with no tier flag, the final report/JSON contains no Narrowed Run
  block/non-full tier — full mode is unaffected. **PASS/FAIL:** `tier` field is `"full"`,
  `tier_source` field is `"explicit"`, `narrowed_guarantees` is `[]`, no `## Narrowed Run` block
  rendered.
- Given a malformed flag attempt `--lite=false` (or `--medium=false`/`--auto=false`), the run is
  rejected with a clear error before CAST runs — the same code path as the multiple-tier-flags
  rejection above — and never silently falls back to full mode (OQ1, resolved — see "Decisions on
  open questions"). **PASS/FAIL:** no dispatches occur; error names the malformed flag and states
  that tier flags are presence-only (no `=false` form).
- Given `/review-panel --auto` alone, Setup step 1 records `--auto` as the requested tier source
  without yet resolving to a concrete tier, and target resolution proceeds unaffected by `--auto`'s
  presence (identical to how `--lite`/`--medium` don't affect target resolution). **PASS/FAIL:**
  target resolution logic identical to the no-flag case; the run does not fail or short-circuit
  before Phase 6's resolution step runs.

---

## Phase 2 — Narrow SPAWN under `--lite`/`--medium`

### Problem

SPAWN currently casts the 6 core seats plus applicable risk-triggered seats plus uncapped
live-scan enrichment (`cast-and-spawn.md`). Under a narrowed tier, SPAWN must cast only that
tier's fixed seat set plus whatever `cast-and-spawn.md` Steps 1-3 and `persona-catalog.md`'s
Security/Data-Steward cast-when criteria still force in — and must skip Step 4 (live-scan
enrichment) entirely in both tiers, since that is the primary, uncapped cost driver identified in
research.

### Changes

- `plugins/review-panel/skills/review-panel/references/cast-and-spawn.md`:
  - At the point CAST's Step 4 (live-scan enrichment) begins, add a tier conditional: skip Step 4
    entirely when `--lite` OR `--medium` is set, moving straight to emitting the cast list from
    Steps 1-3. This is the only new conditional this file needs for CAST — Steps 1-3 (catalog read,
    judgment-match against diff content, fail-closed rule) already run unconditionally and
    unmodified in every tier.
  - At the SPAWN section, add a three-way tier conditional on the cast list Steps 1-3 produced:
    - **Lite:** include only (a) the Adversarial seat (always core, unconditional) and (b) any seat
      Steps 1-3's fail-closed cast-when criteria forced in.
    - **Medium:** include (a) Adversarial, Simplicity, and Structural (always core under medium,
      unconditional) and (b) any seat Steps 1-3's fail-closed cast-when criteria forced in.
    - **Full (no flag):** unchanged — all 6 core seats plus applicable risk-triggered seats plus
      live-scan output.
    Both narrowed tiers exclude every other optional/risk-triggered core seat (Domain-Intent,
    Fresh-Eyes, Change-Trajectory, Design-Alternatives, Test-Design Quality, Taste — plus, for lite
    only, Simplicity and Structural) that Steps 1-3 would have cast under full mode's "always cast
    the 6 core seats" rule but that did not independently match a fail-closed trigger.
  - No change to `persona-catalog.md` itself — Phase 2 reuses its cast-when criteria unmodified
    (Architecture invariant 2); this phase only changes which of CAST's *output* seats SPAWN
    dispatches, per tier.
  - Update the Seat Summary Table's header or a footnote to note each seat's tier eligibility
    (Adversarial: always, all tiers; Simplicity/Structural: medium and full; Security/Data-Steward:
    fail-closed, all tiers; all others: full-mode only).

### Acceptance criteria

- Given a docs-only diff under `--lite`, only the Adversarial seat is cast (no Security,
  Data-Steward, or other seat matches a fail-closed trigger). **PASS/FAIL:** Cast section lists
  exactly one seat.
- Given the same docs-only diff under `--medium`, Adversarial, Simplicity, and Structural are all
  cast, and no other optional seat is. **PASS/FAIL:** Cast section lists exactly three seats.
- Given a diff modifying a dependency lockfile under `--lite` or `--medium`, Security is cast
  alongside each tier's base seat set (Security's existing fail-closed cast-when criteria match,
  unmodified from full mode). **PASS/FAIL:** Cast section lists the tier's base seats + Security,
  matching what full mode's Steps 1-3 alone (without live-scan) would also produce for the same
  diff.
- Given a diff touching a migration file under `--lite` or `--medium` with `DATA-MODEL.md` present,
  Data-Steward is cast alongside each tier's base seat set, identically to how it would cast under
  full mode's fail-closed logic. **PASS/FAIL:** Data-Steward present in Cast output under `--lite`,
  `--medium`, and full mode for the same fixture diff.
- Given any diff, a live-scan-discoverable seat (e.g. a compound-engineering `agents/review/*`
  persona) that would be cast under full mode is absent from the Cast list under both `--lite` and
  `--medium`, and the Coverage Honesty section states live-scan was skipped because of the active
  tier. **PASS/FAIL:** seat absent in both tiers; explicit disclosure present in both.
- Given the same diff run under `--lite`, `--medium`, and with no flag, the full-mode run's Cast
  list is unchanged from its pre-this-feature behavior (regression check against Architecture
  invariant 5). **PASS/FAIL:** full-mode Cast list identical before/after this phase's changes
  land.
- Given a diff where Simplicity or Structural would flag a real issue that Adversarial's scope
  does not cover, `--medium` catches it and `--lite` does not (fixture-verified). **PASS/FAIL:**
  finding present in medium's output, absent from lite's, for the same fixture diff — proves
  medium's wider seat set is materially, not cosmetically, different from lite.

---

## Phase 3 — Cap VALIDATE under `--lite`/`--medium`

### Problem

VALIDATE currently dispatches 1 validator per surviving finding by default, but 2-3 for every
Critical-severity finding (`merge-and-validate.md`). Under a narrowed tier, this escalation must
be capped: lite disables it entirely (every finding gets exactly 1 validator); medium caps it at
2 (down from 2-3).

### Changes

- `plugins/review-panel/skills/review-panel/references/merge-and-validate.md`:
  - At VALIDATE's validator-count determination step, add a three-way tier conditional:
    - **Lite:** dispatch exactly 1 validator per surviving finding, skipping the Critical-severity
      escalation rule entirely (no conditional on confidence <75 vs >=75 either, since that
      branching only exists to pick between 2 and 3 — irrelevant once capped at 1).
    - **Medium:** dispatch exactly 2 validators for every Critical-severity finding (dropping the
      confidence-based 2-vs-3 branch — always 2, never 3), 1 validator for everything else,
      unchanged from full mode's non-Critical default.
    - **Full (no flag):** unchanged — 1 default, 2-3 for Critical per the existing confidence
      branch.
  - The validator's own procedure (clean-room independence, never-the-original-finder rule,
    majority-survives-challenge verdict) is unchanged in every tier; only the *count* narrows, and
    only for Critical findings under medium, or for all findings under lite.
  - Note inline that both narrowings are `lite-mode.md` guarantees (tier-specific) and must appear
    in that file's canonical list (Phase 1) and in Coverage Honesty disclosure for any run where a
    finding was Critical and would have received full mode's validator count.

### Acceptance criteria

- Given a round with one Critical finding under `--lite`, exactly 1 validator is dispatched for
  it. **PASS/FAIL:** validator dispatch count is 1, not 2-3.
- Given the same round under `--medium`, exactly 2 validators are dispatched for it (never 3,
  regardless of confidence). **PASS/FAIL:** validator dispatch count is 2.
- Given the same fixture run under full mode, the run still dispatches 2-3 validators for the
  Critical finding per the existing confidence branch (regression check). **PASS/FAIL:** full-mode
  validator count unchanged by this phase's changes.
- Given a round with only Important/Minor findings under `--lite` or `--medium`, validator count is
  1 per finding in both tiers, identical to full mode's own default (no behavior change for
  non-Critical findings in any tier). **PASS/FAIL:** counts match across `--lite`, `--medium`, and
  full mode for non-Critical-only rounds.
- Given a Critical finding under `--lite` whose single validator returns "refuted," the finding is
  dropped from the validated list on a 1-0 tally (no majority-of-3 recount is attempted, since
  only 1 validator ran). **PASS/FAIL:** finding absent from post-VALIDATE list, tally recorded as
  `"0-1"` or equivalent single-validator shape.
- Given a Critical finding under `--medium` where both validators disagree (1-1), the tally is
  recorded as a non-majority split rather than forcing a third tie-breaking validator (medium never
  dispatches a 3rd). **PASS/FAIL:** tally recorded as `"1-1"`; no 3rd validator dispatch occurs;
  documented tie-handling rule applied (e.g. finding retained pending human review, matching
  whatever full mode's own non-majority handling already does when its 2-count case ties, if such a
  case exists there — otherwise a new, explicitly documented tie rule for medium).

---

## Phase 4 — Narrow RE-REVIEW's regression re-cast under `--lite`/`--medium`

### Problem

RE-REVIEW currently re-casts a scoped subset: always Adversarial, plus any seat whose prior
finding was in the fixed set, plus conditionally Fresh-Eyes for broad-surface fixes
(`fix-and-rereview.md`). Under a narrowed tier, this subset narrows to whichever seats that tier's
SPAWN could have cast in the first place — consistent with Phase 2's SPAWN narrowing, and with
Fresh-Eyes excluded from both narrowed tiers' SPAWN, so it should not appear in either tier's
RE-REVIEW either.

### Changes

- `plugins/review-panel/skills/review-panel/references/fix-and-rereview.md`:
  - At RE-REVIEW's re-cast step, add a three-way tier conditional:
    - **Lite:** re-cast Adversarial (if its finding was fixed) plus any fail-closed seat
      (Security/Data-Steward) whose finding was fixed, using the *existing* unmodified "any seat
      whose finding was fixed" clause applied to lite's actual SPAWN output — this is not a new
      rule, just the existing rule correctly scoped. Skip the conditional Fresh-Eyes re-cast
      entirely (Fresh-Eyes is never cast under lite SPAWN per Phase 2).
    - **Medium:** re-cast whichever of {Adversarial, Simplicity, Structural} had a finding fixed,
      plus any fail-closed seat whose finding was fixed — same existing clause, applied to medium's
      wider SPAWN output. Skip the conditional Fresh-Eyes re-cast (Fresh-Eyes is never cast under
      medium SPAWN either).
    - **Full (no flag):** unchanged — scoped subset per the existing rule, including the
      conditional Fresh-Eyes re-cast for broad-surface fixes.
  - Axis (a) regression and Axis (b) domain-intent coherence checks (vs. CONTEXT.md) are otherwise
    unmodified — both axes still run in every tier, just with a narrower re-cast seat set for
    Axis (a)'s reviewer coverage under `--lite`/`--medium`.

### Acceptance criteria

- Given a round under `--lite` where only an Adversarial finding was fixed, RE-REVIEW re-casts
  Adversarial only. **PASS/FAIL:** re-cast list contains exactly one seat.
- Given a round under `--medium` where an Adversarial finding and a Structural finding were both
  fixed, RE-REVIEW re-casts both Adversarial and Structural, but not Simplicity (its finding, if
  any, wasn't fixed). **PASS/FAIL:** re-cast list contains exactly Adversarial + Structural.
- Given a round under `--lite` (or `--medium`) where a fail-closed Security finding was fixed
  alongside an Adversarial finding, RE-REVIEW re-casts both Adversarial and Security in either tier
  (the existing fixed-seat-re-cast rule applied to each tier's actual cast set, not a
  tier-specific exclusion of Security). **PASS/FAIL:** both seats present in re-cast list, in both
  tiers.
- Given a round under `--lite` or `--medium` with a broad-surface fix that would trigger
  conditional Fresh-Eyes re-casting under full mode, Fresh-Eyes is NOT re-cast under either
  narrowed tier. **PASS/FAIL:** Fresh-Eyes absent from both narrowed tiers' re-cast lists
  regardless of fix surface area.
- Given the same fixture run under full mode (no tier flag), the broad-surface fix still triggers
  Fresh-Eyes re-casting (regression check). **PASS/FAIL:** full-mode Fresh-Eyes conditional
  unchanged.
- Domain-intent coherence (Axis b) still runs and produces a coherence verdict under `--lite` and
  `--medium` exactly as under full mode, since Axis (b) is not seat-count-scoped. **PASS/FAIL:**
  coherence section present and non-empty (clean, no-CONTEXT.md, or findings) in all three tiers.

---

## Phase 5 — Cap CONVERGE under `--lite`/`--medium`

### Problem

CONVERGE currently loops back to SPAWN (with the full cast list, not RE-REVIEW's scoped subset)
on a dirty round, up to a 3-strikes circuit-breaker or a hard cap of round 8
(`converge-and-pipeline.md`). Under a narrowed tier, this must cap at a fixed, smaller number of
total loop iterations: 1 for lite, 2 for medium. Past that cap, a dirty round does not loop back to
SPAWN again — instead the run terminates with a new recommendation to escalate to the full panel.

### Changes

- `plugins/review-panel/skills/review-panel/references/converge-and-pipeline.md`:
  - Decision rule: step 0 (sovereignty check) is unmodified and runs first regardless of tier
    (Architecture invariant 3) — an unresolved sovereignty finding still produces `escalated` in
    every tier exactly as under full mode, before any tier-specific loop-count logic is considered.
  - After step 0, add a three-way tier conditional at the clean/dirty branch: clean round →
    `converged` (unchanged, every tier). Dirty round → check round count against the tier's cap
    (1 for lite, 2 for medium, n/a for full); if the cap is reached, do NOT loop back to SPAWN —
    instead terminate with the `capped` status described below. Full mode's existing
    dirty-round-loops-to-SPAWN behavior, 3-strikes breaker, and round-8 hard cap are all unmodified
    and simply never reached under either narrowed tier, since the loop never proceeds past its
    tier's cap.
  - New terminal status value `capped` (PRD D5, resolving OQ4 — **a new value, not a reuse of
    `circuit_broken`**) for the narrowed-tier iteration-cap case: set
    `convergence.capped.diagnosis` to an explicit, tier-specific message (e.g. "lite mode capped at
    1 iteration; findings remain after the first FIX/RE-REVIEW pass — re-run without --lite (or
    with --medium/no flag) for deeper convergence" / the medium-equivalent message at 2 iterations),
    and set `tier`/`narrowed_guarantees` (Phase 1) to make the tier context unmistakable alongside
    the diagnosis. Human-mode report gets a `capped`-specific escalation block, structurally
    parallel to the existing `circuit_broken` block but visually and textually distinct (different
    heading, e.g. "## Capped — Narrowed Tier Limit Reached" vs. "## Circuit Broken").
  - Rationale for a new status value rather than reusing `circuit_broken` (documented inline,
    cross-referencing PRD D5): hitting a tier's iteration cap is expected, by-design behavior
    chosen by the invoker when they selected `--lite`/`--medium` — it is not an anomaly, and
    `circuit_broken` should keep meaning exactly what it means today, full mode's genuine
    3-strikes/round-8 stagnation. Conflating the two under one status value would force every
    consumer to parse `diagnosis` text to tell "this tier did what it was told" from "something
    is actually wrong." A foundry gate can now branch on `capped` structurally: e.g. treat it as
    "re-run with a deeper tier" rather than "investigate a stuck review."

### Acceptance criteria

- Given a diff whose round-1 RE-REVIEW is clean under `--lite`, status is `converged` after
  exactly 1 round. **PASS/FAIL:** `rounds: 1`, `status: "converged"`.
- Given a diff whose round-1 RE-REVIEW is dirty under `--lite`, the run terminates after round 1
  with `status: "capped"` and a diagnosis string explicitly mentioning lite mode's 1-iteration cap.
  **PASS/FAIL:** no second SPAWN dispatch occurs; diagnosis text names the lite cap; status is
  `capped`, not `circuit_broken`.
- Given a diff whose round-1 RE-REVIEW is dirty under `--medium` but round-2 RE-REVIEW is clean,
  status is `converged` after 2 rounds (medium gets its full permitted iteration before capping).
  **PASS/FAIL:** `rounds: 2`, `status: "converged"`, a second SPAWN dispatch occurred.
- Given a diff whose round-2 RE-REVIEW is still dirty under `--medium`, the run terminates after
  round 2 with `status: "capped"` and a diagnosis string explicitly mentioning medium mode's
  2-iteration cap. **PASS/FAIL:** no third SPAWN dispatch occurs; diagnosis text names the medium
  cap; status is `capped`, not `circuit_broken`.
- Given an unresolved sovereignty finding under `--lite` or `--medium` (Data-Steward
  fail-closed-forced per Phase 2), status is `escalated`, not `capped` — step 0 takes precedence
  over tier-loop-cap logic exactly as it does over full mode's loop logic. **PASS/FAIL:** status is
  `escalated` in both tiers; sovereignty finding IDs populated.
- Given the identical dirty-round-1 fixture run under full mode (no tier flag), CONVERGE loops back
  to SPAWN with the full cast list (regression check against Architecture invariant 5).
  **PASS/FAIL:** a second SPAWN dispatch occurs under full mode for the same fixture; status is
  never `capped` under full mode.
- Boundary: a diff that would take exactly 8 rounds to converge under full mode terminates at
  round 1 under `--lite` and round 2 under `--medium`, both with their respective `capped`
  diagnoses, never attempting the remaining rounds. **PASS/FAIL:** total SPAWN dispatch count
  corresponds to 1 round for lite, 2 for medium — not 8 in either case.

---

## Phase 6 — `--auto` tier resolution

### Problem

`--auto` is detected by Phase 1 but not yet resolved to a concrete tier — Setup records
`tier_source: "auto"` and stops there. Something must turn "auto was requested" into one of
`full`/`medium`/`lite` before CAST runs, using only cheap, pre-CAST signals (never live-scan,
never file content beyond path matching), and that resolution must be disclosed with the same
unmissability as an explicitly-chosen tier (PRD Goal 6, D16-D21).

### Changes

- `plugins/review-panel/skills/review-panel/SKILL.md`:
  - Setup: add a new step, sequenced immediately after target resolution and before CAST — the one
    point in Setup where a tier-selecting flag has a genuine data dependency on the resolved review
    target (PRD D21; unlike `--lite`/`--medium`/`--mode=agent`, which are independent of target
    resolution and can be parsed at step 1). This step only runs when `tier_source` is `"auto"`;
    for `"explicit"` runs it is a no-op.
  - The step computes three signals from the already-resolved diff, via the same cheap
    `git diff --stat`-equivalent mechanism the plugin already has available (no new git plumbing
    invented):
    1. `files_changed` — count of files touched by the diff.
    2. `lines_changed` — total added + deleted lines across the diff.
    3. `sensitive_path_match` — boolean, true if any changed file matches the Security/Data-Steward
       cast-when path criteria already defined in `references/persona-catalog.md`. This step reuses
       those criteria verbatim (Architecture invariant 2) — it does not define a second, competing
       notion of "sensitive path."
  - New `plugins/review-panel/skills/review-panel/references/lite-mode.md` section, "Auto
    resolution": states the resolver function as a simple, auditable decision table (PRD D18):
    - `sensitive_path_match` is `true` → resolve to `full`, regardless of `files_changed`/
      `lines_changed`. This check runs first and short-circuits the size-based bands below — auto
      is never less safe than a human manually picking a tier for the same diff.
    - Else, `files_changed <= 3` AND `lines_changed <= 200` → resolve to `lite`.
    - Else, `files_changed <= 15` AND `lines_changed <= 1000` → resolve to `medium`.
    - Else → resolve to `full`.
    - These thresholds are fixed constants for v1 (PRD OQ5, resolved 2026-07-19 — the original
      ≤40/≤300 line proposal was checked against this repo's last 49 non-merge commits, producing a
      balanced 17/19/13 lite/medium/full split; the human then chose to widen both line ceilings to
      ≤200/≤1000, shifting the same history to a ~51/41/8 split that favors the fast tiers by
      default and reserves full for diffs large by either files or lines). File-count ceilings (≤3
      lite / ≤15 medium) are unchanged from the original proposal. Per-repo tuning (e.g. via
      `foundry.yaml`) is out of scope, per the PRD's Future direction section.
  - Once resolved, the run proceeds exactly as if the resolved tier's flag (`--lite`/`--medium`/no
    flag) had been passed explicitly — Phases 2-5's conditionals read the resolved tier value, not
    `tier_source`, so they require no changes for `--auto` to work (Architecture invariant 1: Phase
    6 adds no new SPAWN/VALIDATE/RE-REVIEW/CONVERGE logic of its own).
- `plugins/review-panel/skills/review-panel/references/dual-mode-contract.md`:
  - `mode:agent` JSON contract: add one new top-level field, present only when `tier_source` is
    `"auto"` (omitted entirely for `"explicit"` runs — this is the one field in the contract that is
    conditionally present rather than always-emitted-possibly-empty, since it has no meaningful
    empty value for an explicit run) (PRD D20):
    - `"auto_signals"`: object with `"files_changed"` (integer), `"lines_changed"` (integer), and
      `"sensitive_path_match"` (boolean) — the exact signal values the resolver used, so a consumer
      can audit why `--auto` picked the tier it picked without re-computing the diff stat itself.
  - Human report: when `--auto` resolves to `medium` or `lite`, the existing `## Narrowed Run` block
    (Phase 1) gets one additional line stating the run was auto-resolved and naming the driving
    signals, e.g. "Tier auto-resolved to **lite** (2 files, 18 changed lines, no sensitive path
    matched)." — appended after the existing tier-naming statement, before the guarantee bullets.
  - When `--auto` resolves to `full`, there is no existing banner to extend — full mode currently
    renders no `## Narrowed Run` block at all (Architecture invariant 5). Per PRD OQ6, this phase
    adds a minimal, full-mode-only disclosure for this one case: a single line, positioned in the
    same place the `## Narrowed Run` block would go, stating auto-resolution occurred and why, e.g.
    "Tier auto-resolved to **full** (14 files, 260 changed lines)." or "Tier auto-resolved to
    **full** (sensitive path matched: `db/migrations/`)." — no guarantee bullets follow, since full
    mode has none to disclose. This is the smallest change that satisfies the "never mistakable by
    omission" requirement (PRD Goal 6) without giving full mode a permanent banner it doesn't
    otherwise have.

### Acceptance criteria

- Given a diff touching 2 files with 18 total changed lines and no sensitive-path match, `--auto`
  resolves to `lite`. **PASS/FAIL:** `tier: "lite"`, `tier_source: "auto"`,
  `auto_signals: {files_changed: 2, lines_changed: 18, sensitive_path_match: false}`; SPAWN/
  VALIDATE/RE-REVIEW/CONVERGE behave exactly as an explicit `--lite` run against the same diff
  (Phases 2-5 unmodified).
- Given a diff touching 10 files with 150 total changed lines and no sensitive-path match, `--auto`
  resolves to `medium`. **PASS/FAIL:** `tier: "medium"`, `tier_source: "auto"`, signals populated
  correctly; behavior identical to an explicit `--medium` run against the same diff.
- Given a diff touching 20 files with 500 total changed lines and no sensitive-path match, `--auto`
  resolves to `full`. **PASS/FAIL:** `tier: "full"`, `tier_source: "auto"`; no `narrowed_guarantees`;
  behavior identical to an unflagged full run against the same diff.
- Given a diff small enough to otherwise qualify for `lite` (e.g. 1 file, 10 changed lines) that
  touches a path matching the Security/Data-Steward sensitive-path criteria (e.g. a migration file
  under a `DATA-MODEL.md`-governed directory), `--auto` resolves to `full`, not `lite`. **PASS/FAIL:**
  `tier: "full"`, `auto_signals.sensitive_path_match: true`, despite `files_changed`/`lines_changed`
  being within the `lite` band — proves the override takes precedence over size thresholds.
- Given the same sensitive-path fixture run three ways — explicit `--lite`, explicit `--auto`, and
  full mode with no flag — the explicit `--lite` run still fail-closed-casts Security/Data-Steward
  per Phase 2 (narrowed tiers were never unsafe), and `--auto` avoids the narrowed tier entirely by
  resolving to `full`. **PASS/FAIL:** fail-closed seat present in all three runs' Cast output;
  `--auto`'s resolved tier is `full`, not `lite`.
- Given `/review-panel --auto --lite` (or any pairing of `--auto` with `--lite`/`--medium`), the
  invocation is rejected with a clear error before CAST runs, identically to Phase 1's existing
  `--lite --medium` rejection. **PASS/FAIL:** no dispatches occur; error names `--auto` and the
  conflicting flag.
- Given an `--auto` run that resolves to `medium` or `lite`, the human report's `## Narrowed Run`
  block contains an additional line naming the auto-resolution and its driving signals, distinct
  from the tier-naming line an explicit `--medium`/`--lite` run produces. **PASS/FAIL:** auto-run
  report text differs from the explicit-run report text for an otherwise-identical resolved tier
  (proves auto and explicit are not visually indistinguishable, per PRD OQ6/Goal 6).
- Given an `--auto` run that resolves to `full`, the human report contains the new minimal one-line
  disclosure (not the full `## Narrowed Run` block, which has no guarantees to show for full mode),
  while an unflagged full run's report contains no such line. **PASS/FAIL:** auto-resolved-to-full
  report text differs from a no-flag full report by exactly this one line; no other content changes.
- Given the identical diff fixture run under explicit `--lite`, explicit `--medium`, no flag, and
  `--auto` (with signals engineered to land in each of the three bands across separate fixture
  runs), the resolved tier's SPAWN/VALIDATE/RE-REVIEW/CONVERGE dispatch counts and output shape are
  byte-for-byte identical between the `--auto` run and the matching explicit run (regression check
  against Architecture invariant 1: Phase 6 adds no new stage logic). **PASS/FAIL:** dispatch counts
  and finding sets match between each `--auto`/explicit pair.

---

## Verification & tooling (all phases)

- `scripts/verify_plugin.py` runs clean after each phase's `SKILL.md`/`references/*.md` edits.
- Each phase adds at least one fixture under `plugins/review-panel/tests/` following the existing
  `tests/PRESSURE-TEST.md` pattern (seeded defect → expected finding), parameterized to run under
  `--lite`, `--medium`, and full mode against the same seeded diff so the "full mode unchanged"
  invariant (Architecture invariant 5) and each narrowed tier's distinctness from the others are
  mechanically checked, not just asserted in prose.
- Phase 6 additionally requires fixtures spanning all three auto-resolution size bands (lite/
  medium/full boundaries per D18's thresholds) plus the sensitive-path-override fixture (a diff
  small enough to otherwise qualify for `lite` that touches a sensitive path, asserting resolution
  to `full` anyway) — these are the fixtures Phase 6's acceptance criteria cite directly.
- `uv run pytest` and `uv run ruff check --fix` gate every phase (repo rules), to the extent any
  Python-side tooling (e.g. `scripts/workspace`, `scripts/review-package`) is touched — expected to
  be none for this feature, since all changes are markdown reference files, but the gate applies if
  that assumption turns out wrong during implementation.
- README.md / marketplace catalog: update review-panel's command/flag documentation to mention
  `--lite`, `--medium`, and `--auto` alongside the existing `--mode=agent` mention, if such a
  mention exists there today (verify at implementation time; not assumed here).

## Decompose plan (after agreement)

1. One epic (new, not nested under `scc-hzj` per PRD D10), with roughly one task per phase, Phase
   1 possibly splitting into 2 sub-tasks (flag-parsing/threading vs. the new `lite-mode.md` file +
   both output-mode disclosure changes) given its larger surface area, matching `scc-hzj`'s
   demonstrated granularity of splitting a phase into sub-tasks only when it has genuinely
   separable file-level changes. Adding `--medium` does not add new phase-level tasks — each
   existing phase's task grows a third tier-branch within the same file(s) it already touches, per
   the "Narrowing tiers" table above. Adding `--auto` (Phase 6) does add one new phase-level task,
   since it is new resolution logic in its own right, not a branch within an existing phase.
2. AC for each bead seeded from this spec's acceptance criteria via the `acceptance-criteria`
   skill (`--acceptance=...` per this repo's CLAUDE.md rule).
3. Build order: Phase 1 first (flag plumbing and the canonical `lite-mode.md` guarantee list every
   other phase's Coverage Honesty note and disclosure content depends on) → Phases 2, 3 next,
   order-independent between themselves (each narrows a different, non-overlapping stage: SPAWN,
   VALIDATE respectively) but each depends on Phase 1 existing (they all reference `lite-mode.md`'s
   canonical guarantee list and the flags Phase 1 defines) → Phase 4 depends on Phase 2 (RE-REVIEW's
   tier-scoped re-cast needs SPAWN's tier-scoped cast set already decided) → Phase 5 last among the
   narrowing phases, wired as a hard dependency on Phases 2/3/4 in beads even though its own
   mechanism (capping the loop) is independently implementable, since beads has no soft-dependency
   primitive.
4. Phase 6 (`--auto` resolution) depends only on Phase 1 in the real dependency graph — it needs
   the flag detection, `tier_source` field, and `lite-mode.md` file Phase 1 establishes, but its
   resolver logic is independent of Phases 2-5's stage-narrowing mechanics (Architecture invariant
   1: once resolved, Phase 6 hands off to whichever tier's already-built machinery, adding none of
   its own). It should-sequence after Phases 2-5 exist (so its fixtures can compare `--auto`'s
   resolved-tier output against each explicit tier's established behavior), but does not hard-block
   on them — same softer-dependency judgment call as Phase 5's relationship to Phases 2-4, resolved
   the same way (enforced as a hard `depends-on` in beads regardless, since beads has no
   soft-dependency primitive).
5. A verification/fixture task (mirroring `scc-hzj`'s `scc-d0u` "Verification & tooling gates (all
   phases)" pattern) that adds the three-way `--lite`/`--medium`/full-mode fixture tests plus
   Phase 6's auto-resolution and sensitive-path-override fixtures, depending on all six phase tasks.

## Decisions on open questions (resolved during this planning session, flagged for human review)

- **OQ1 (PRD) — `--lite`/`--medium`/`--auto` CLI syntax edge cases. Resolved 2026-07-19: reject
  with a clear error.** Flag-presence-only stands (no `=false` form for any of the three flags).
  The previously-open question — reject-with-error vs. treat-as-absent for a malformed `--lite=false`
  (or `--medium=false`/`--auto=false`) attempt — is settled: reject, using the same fail-closed
  code path Phase 1 already has for the multiple-tier-flags case. Rationale: silently falling back
  to full mode would mask a typo'd invocation (e.g. a CI script that meant `--lite=true`) as an
  ordinary full-mode pass rather than surfacing the mistake. See Phase 1's Changes and AC sections
  for the exact wiring.
- **OQ3 (PRD) — Whether a `--medium` tier is worth building now. Resolved 2026-07-19: yes**, by
  explicit human decision. This document has been amended throughout to add `--medium` as a full
  peer of `--lite` (see the "Narrowing tiers" table, and Phases 2-5's three-way conditionals).
- **OQ4 (PRD) — Reuse existing `status` values vs. add a new one. Resolved 2026-07-19: add a new
  `capped` status value**, used by both `--lite` and `--medium` for their respective
  iteration-cap terminal case, distinguished from `circuit_broken` (which remains exclusively full
  mode's genuine-stagnation signal). This reverses the session's original "reuse `circuit_broken`"
  provisional call. Rationale: a tier hitting its iteration cap is expected, by-design behavior the
  invoker selected, not an anomaly — collapsing it into `circuit_broken` would force every
  downstream consumer to parse `diagnosis` text to distinguish "did what it was told" from
  "something's actually wrong." See Phase 5 and PRD D5 for the full design.
- **OQ5 (PRD) — Are the proposed `--auto` size thresholds right for this repo? Resolved 2026-07-19:
  yes, at widened line ceilings.** The original ≤3 files/≤40 lines → lite; ≤15 files/≤300 lines →
  medium proposal was checked against this repo's last 49 non-merge commits via `git show
  --numstat`, producing a balanced 17/19/13 lite/medium/full split — confirming the mechanism
  itself wasn't degenerate before any tuning. The human reviewed that data and widened both line
  ceilings: ≤3 files/**≤200 lines** → lite; ≤15 files/**≤1000 lines** → medium (file-count ceilings
  unchanged). Re-run against the same 49 commits, this produces a ~51/41/8 split, biasing `--auto`
  toward the fast tiers by default and reserving `full` for diffs that are large by either files or
  lines rather than moderate diffs that happen to cross a low line count. See PRD D18 and Phase 6's
  decision table for the final constants.
- **OQ6 (PRD) — Should an `--auto` run that resolves to `full` still render disclosure, given full
  mode currently has no banner at all? Resolved 2026-07-19: yes, a minimal one-line disclosure**,
  distinct from the full `## Narrowed Run` block narrowed tiers get (which has guarantee bullets
  full mode has none of). Rationale: PRD Goal 6 requires an `--auto` run to never be mistakable for
  a manually-invoked one by omission — silently resolving to full with zero output difference from
  an unflagged run would violate that even though full mode itself is otherwise unchanged
  (Architecture invariant 5). See Phase 6's `dual-mode-contract.md` changes for the exact line.
