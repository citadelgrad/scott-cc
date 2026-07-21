# review-panel Lite Mode — PRD

**Status:** Draft — self-approved (planning-only session, no code changes; see stage-5-approval.md)
**Date:** 2026-07-18
**Owner:** Scott
**Pairs with:** [review-panel-lite-spec.md](./review-panel-lite-spec.md)
**Beads Epic:** [scc-c56](https://github.com/gastownhall/beads) — `bd show scc-c56`

> This doc is the durable product-requirements artifact. It captures the *why* and *what*.
> The paired spec captures the *how*. Written so work can resume after a context
> compact/clear — read top-to-bottom to reconstruct the full intent.

---

## 1. Vision

`review-panel` is a rigorous, multi-seat code-review orchestrator: CAST → SPAWN → MERGE →
VALIDATE → FIX → RE-REVIEW → CONVERGE. A typical full run fans out to roughly **18-30 subagent
`Task` dispatches** for one diff. That rigor is exactly right for a PR about to merge to `main`.
It is the wrong tool for a WIP branch being iterated on ten times an hour, a pre-commit hook that
needs to answer in seconds, or a CI gate on a diff that only touches docs or comments.

Lite mode is **not a second review engine**. It is a narrower parameterization of the same
7-stage loop, selected by a `--lite` or `--medium` flag, that keeps the panel's non-negotiable
safety guarantees (fail-closed Security/Data-Steward casting, the sovereignty guard,
coverage-honesty disclosure) while cutting the dispatch count for the common low-risk case. Three
tiers exist: **full** (default, no flag), **medium** (`--medium`), and **lite** (`--lite`) — one
narrowing spectrum, not three separate engines.

A fourth flag, **`--auto`**, is not a tier itself — it is a *resolver* that picks one of the three
tiers for you, from cheap, pre-CAST diff signals (files changed, lines changed, whether a
fail-closed-sensitive path is touched), computed before CAST ever runs and never from live-scan
output. `--auto` exists for the invoker who doesn't want to think about which tier fits a given
diff; it never introduces a fourth, in-between, or continuously-scaled depth — the resolved tier is
always exactly `full`, `medium`, or `lite`, and is disclosed identically to an explicit tier choice
plus a statement that it was auto-resolved and why. `--lite`, `--medium`, and `--auto` are
pairwise mutually exclusive (pick at most one tier-selecting flag); any of the three is composable
with `--mode=agent`.

| Stage | Full (default) | Medium (`--medium`) | Lite (`--lite`) |
|---|---|---|---|
| CAST | full catalog + live-scan | full catalog, **no live-scan** | full catalog, **no live-scan** |
| SPAWN | 6 core + risk-triggered + uncapped live-scan seats, max 5 concurrent | Adversarial + Simplicity + Structural + fail-closed-forced seats only | Adversarial + fail-closed-forced seats only |
| MERGE | dedupe, confidence anchors | same mechanism, fewer seats to agree | same mechanism, fewest seats to agree |
| VALIDATE | 1 validator/finding, 2-3 for every Critical | 1 validator/finding, **capped at 2** for Critical | 1 validator/finding, **capped at 1** — no Critical escalation |
| FIX | 1 dispatch, whole list | 1 dispatch, same | 1 dispatch, same |
| RE-REVIEW | scoped subset, 2-4 dispatches | re-cast whichever of {Adversarial, Simplicity, Structural} + fixed fail-closed seats | Adversarial-only regression re-cast (+ fixed fail-closed seats) |
| CONVERGE | loop to SPAWN, 3-strikes, cap round 8 | max **2** loop iterations total; dirty round 2 terminates | max **1** loop iteration total; dirty round 1 terminates |
| Terminal status | `converged\|circuit_broken\|error\|escalated` | same four, plus new `capped` for the tier's iteration-cap exit | same four, plus new `capped` for the tier's iteration-cap exit |
| Disclosure | `"tier": "full"`, `narrowed_guarantees: []` | `"tier": "medium"`, `narrowed_guarantees` populated | `"tier": "lite"`, `narrowed_guarantees` populated |

Both paths still terminate through the same `dual-mode-contract.md` (human-interactive report or
`mode:agent` JSON). `--lite`/`--medium` are composable with `--mode=agent` — a narrowed run can
still be a foundry gate, just a cheaper one.

`--auto` does not add a column to this table — it resolves, before CAST, to exactly one of the
three existing columns, then that column's row-by-row behavior applies unchanged. The only new
surface `--auto` adds is disclosure: which column it resolved to, and why (see Phase 6 in the
spec).

## 2. Placement in the stack

| Layer | Role | How lite mode is used there |
|---|---|---|
| **review-panel (plugin)** | Sole diff-review substrate for this repo | Hosts both full mode (default) and lite mode (`--lite`) as one orchestrator, one skill directory |
| **Pre-commit hooks** | Local, synchronous, must be fast | Natural home for `--lite --mode=agent`: a low-latency sanity pass before a commit lands |
| **Foundry** | Scheduled/unattended gates | `foundry.yaml` gates on low-risk diff classes (docs-only, WIP branches, dependency patch bumps below a triage-defined risk bar) can call `--lite --mode=agent` instead of the full panel, at the gate author's discretion |
| **CI (interactive PR)** | Pre-merge, highest stakes | Stays on full mode by default; lite mode is opt-in per gate, never a silent substitute |

## 3. Goals (what we are building)

Listed in priority order. Each maps to a phase in the spec.

1. **A `--lite` and a `--medium` flag on `/review-panel` that narrow dispatch count for low-risk,
   fast-iteration review, at two different points on one spectrum.** Composable with the existing
   `--mode=agent` flag, following the same `$ARGUMENTS` parsing precedent; mutually exclusive with
   each other. Both are parameterizations of the existing 7-stage loop's SKILL.md and references —
   not a fork, not a second orchestrator, and not two independent features.
2. **Eliminate the single biggest uncontrolled cost multiplier: uncapped live-scan enrichment.**
   CAST's Step 4 (discovering `<plugin>:review:*`-namespaced agent types beyond the persona
   catalog) is skipped entirely under both `--lite` and `--medium`. This is the primary lever;
   everything else in this feature is secondary tightening.
3. **Narrow SPAWN, by tier, to a fixed seat set plus whatever fail-closed logic still forces in.**
   Reuse `cast-and-spawn.md`'s existing Steps 1-3 and `persona-catalog.md`'s existing Security/
   Data-Steward cast-when criteria verbatim in both tiers. Lite mode casts Adversarial only (plus
   fail-closed-forced seats); medium mode restores Simplicity and Structural alongside Adversarial
   (plus fail-closed-forced seats). Neither tier may invent new casting logic — both narrow the
   *optional/risk-triggered/live-scan* seat set only, never the fail-closed-forced set.
4. **Cap VALIDATE and CONVERGE to bound worst-case dispatch count, by tier.** VALIDATE: lite caps
   at 1 validator per finding (no Critical escalation); medium caps Critical-finding escalation at
   2 validators (down from full mode's 2-3). CONVERGE: lite allows at most 1 loop iteration total;
   medium allows at most 2. A dirty round past a tier's cap terminates with a recommendation to run
   the full panel, rather than looping back to SPAWN again.
5. **Make every narrowed run unmistakably disclosed as narrowed, in both output modes, naming its
   tier.** Extends the panel's existing coverage-honesty invariant (SKILL.md) rather than
   introducing a new disclosure mechanism: the human report and the `mode:agent` JSON both carry an
   explicit, impossible-to-miss tier marker (`full`/`medium`/`lite`) plus a statement of exactly
   which guarantees were narrowed for that tier.
6. **Add an `--auto` flag that resolves to one of full/medium/lite from cheap, pre-CAST diff
   signals, never silently.** Files-changed count, lines-changed count, and whether a
   fail-closed-sensitive path (reusing the exact path-matching criteria Security/Data-Steward
   casting already uses — never a newly invented heuristic) is touched determine the resolved
   tier. A diff matching a fail-closed-sensitive path always resolves to full, regardless of its
   size — auto is never less safe than the invoker manually picking a tier. The resolution and its
   driving signals are disclosed with the same unmissability as goal 5's tier marker, so an
   `--auto` run is never mistakable for a manually-chosen one by omission.

## 4. Non-goals (explicit)

- **A tier finer-grained than three (full/medium/lite).** No `--medium-lite` or other additional
  gradation. If real usage shows a need for a fourth point on the spectrum, that is a future epic,
  not scope creep on this one.
- **Implicit, always-on diff-risk tier selection.** Heuristic tier selection only happens when the
  invoker explicitly opts in with `--auto` — an unflagged invocation is always full mode, never
  silently downgraded because the panel judged a diff "looks simple." `--auto` itself is designed
  to never under-review: any diff matching a fail-closed-sensitive path resolves to full regardless
  of size, so opting into auto-selection is never less safe than an invoker manually picking a
  tier. See PRD goal 6 and spec Phase 6.
- **Continuous or dynamic review depth.** `--auto` always resolves to exactly one of the three
  existing discrete tiers (full/medium/lite) — never a fourth tier, and never a continuously-scaled
  depth computed from a formula. If discrete tiers prove too coarse for `--auto` specifically, that
  is a future epic, not scope creep on this one.
- **Weakening or bypassing the Data-Steward sovereignty guard.** The post-FIX mechanical
  hash-based integrity check and the `escalated` terminal status apply identically in every tier.
  This is a hard constraint, not a design option (see spec's Architecture Invariants).
- **A new lite- or medium-specific reviewer seat or persona.** `adversarial-reviewer`,
  `simplicity-reviewer` (or equivalent Simplicity seat), and the Structural seat already exist in
  the full-mode catalog; narrowed tiers reuse them rather than authoring new reviewer content.
- **Changing full mode's behavior in any way.** Full mode (the default, no flag) must be
  byte-for-byte unchanged in dispatch count, seat selection, and output shape. Both narrowed tiers
  are strictly additive.

## 5. Future direction (recorded, not scheduled)

- **Lite-mode-aware foundry gate templates.** A documented `foundry.yaml` recipe pairing
  `--lite --mode=agent` or `--medium --mode=agent` with specific low-risk diff-class triggers
  (docs-only, WIP branch pushes, dependency patch bumps) could ship alongside
  `dual-mode-contract.md`'s existing example gate. Left as an implementation-time nicety, not a
  planned task in this epic.
- **Configurable `--auto` thresholds (e.g. via `foundry.yaml`).** v1 ships fixed, hard-coded
  files-changed/lines-changed constants (see spec Phase 6). Per-repo tuning of those thresholds is
  future work, worth revisiting once real usage data shows the fixed defaults are miscalibrated for
  a given repo's typical diff size.

## 6. Users

- **Primary:** Scott, iterating on WIP branches locally and wanting a fast, cheap sanity pass
  before committing or pushing, without waiting for or paying for a full 18-30-dispatch panel run
  on every iteration.
- **Secondary:** any pre-commit hook or foundry gate author in this repo who wants a review-panel
  invocation cheap enough to run synchronously or on every commit, on diff classes where the full
  panel's rigor is not worth its cost.

## 7. Success criteria (product level)

- A lite run on a typical small WIP diff completes with materially fewer than 18-30 `Task`
  dispatches; a medium run completes with fewer dispatches than full but visibly more than lite —
  both driven by skipping live-scan enrichment and narrowing SPAWN/VALIDATE/CONVERGE per their
  tier's fixed parameters, not by silently dropping fail-closed seats.
- A lite or medium run on a diff that touches auth, secrets, a trust boundary, or a
  migration/schema file still casts the Security and/or Data-Steward seats exactly as full mode
  would — neither narrowed tier ever silently drops fail-closed coverage.
- A narrowed run's human report and `mode:agent` JSON output both make it unmistakable which tier
  the run was (`full`/`medium`/`lite`) and state explicitly which guarantees (multi-seat agreement
  bump, Critical-finding multi-validator challenge, multi-iteration convergence) were narrowed for
  that tier.
- The Data-Steward sovereignty guard (mechanical post-FIX file-integrity check, `escalated`
  status) behaves identically across all three tiers — no code path exists where `--lite` or
  `--medium` weakens it.
- Full mode's behavior (dispatch count, seat selection, output shape) is unchanged by this
  feature's existence — verified by the panel's existing full-mode fixtures continuing to pass
  unmodified.
- A `--medium` run on a diff where lite's Adversarial-only SPAWN would have missed a
  Simplicity/Structural-class issue catches it (fixture-verified) — proving medium is a materially
  different, not cosmetically different, tier from lite.
- An `--auto` run resolves to `lite` on a small fixture diff, `medium` on a moderate one, and
  `full` on a large one — fixture-verified across all three size bands using the fixed thresholds
  from spec Phase 6.
- An `--auto` run on a diff that touches a fail-closed-sensitive path resolves to `full` regardless
  of diff size (fixture-verified with a diff small enough to otherwise qualify for `lite`) — proving
  auto is never less safe than a manually-chosen tier.
- An `--auto` run's disclosure (human report and JSON) states both the resolved tier and that it
  was auto-resolved, plus the signals that drove the resolution — an `--auto` run's output is never
  indistinguishable from a manually-chosen tier's output by omission.

## 8. Decisions log

| # | Decision | Choice |
|---|---|---|
| D1 | Fork the orchestrator or parameterize it? | **Parameterize.** `--lite` is a flag read by the existing SKILL.md/references, following the `mode:agent` precedent — not a second orchestrator or a copy of the 7-stage loop. |
| D2 | What is the primary cost lever to cut? | **Live-scan enrichment (CAST Step 4).** It is the single uncapped multiplier; skipping it under `--lite` is the biggest, safest cut available. |
| D3 | Does lite mode ever narrow fail-closed casting (Security/Data-Steward)? | **No.** Lite mode narrows only the optional/risk-triggered/live-scan seat set. Fail-closed logic is reused verbatim from `cast-and-spawn.md`/`persona-catalog.md`, never re-derived or weakened. |
| D4 | How many CONVERGE iterations does lite mode allow? | **At most 1.** A dirty round after the first pass terminates with a "run the full panel" recommendation instead of looping back to SPAWN a second time. |
| D5 | Does a narrowed tier get a new `mode:agent` JSON `status` value for its iteration-cap exit? | **Yes — a new `capped` status value, distinct from `circuit_broken`.** Resolved 2026-07-19 by explicit human decision (overriding this session's original provisional "reuse `circuit_broken`" call). Rationale: hitting a tier's iteration cap is expected, by-design behavior chosen by the invoker, not an anomaly — `circuit_broken` should keep meaning "something went wrong" (full mode's genuine 3-strikes/round-8 stagnation) and never be conflated with "this tier did exactly what it was told to do and stopped on schedule." A foundry gate can now branch on `capped` structurally instead of parsing `diagnosis` text. See §9 OQ4 (resolved). |
| D6 | Is `--lite`/`--medium` mutually exclusive with `--mode=agent`? | **No — composable.** `--lite --mode=agent`, `--medium --mode=agent`, and either order, are all valid; the tier flag controls SPAWN/VALIDATE/CONVERGE scope, `--mode` controls output format. Orthogonal flag families. |
| D7 | Does the narrowed-tier logic get its own `references/lite-mode.md`? | **Yes, provisionally — formalized in the spec.** One reference file (not two), read just-in-time only when `--lite` or `--medium` is present, documenting both tiers' parameters side by side. Explicitly not a fork of orchestration logic — it documents narrowed-tier *parameters* (which stages narrow, and how, per tier), referencing the existing full-mode reference files for everything it does not override. |
| D8 | Where does the "this run was narrowed" disclosure live? | **Both output modes, following the coverage-honesty precedent.** Human report gets a banner section naming the tier; `mode:agent` JSON gets a top-level `"tier"` string field (`"full"\|"medium"\|"lite"`, replacing the earlier two-state `"lite": true/false` boolean design, which cannot represent three states) plus a `narrowed_guarantees` list. No new disclosure mechanism invented — this extends SKILL.md's existing Coverage Honesty rule. |
| D9 | Does this feature touch full mode's behavior at all? | **No.** Full mode is default (no tier flag) and must remain byte-for-byte unchanged. |
| D10 | New epic or nest under `scc-hzj`? | **New, separate epic.** `scc-hzj` (Two-System Architecture) is closed at 13/13; this feature builds on review-panel but is scoped and planned independently. |
| D11 | What is medium mode's SPAWN seat set? | **Adversarial + Simplicity + Structural + fail-closed-forced seats.** Restores the two next-most-valuable core seats beyond lite's Adversarial-only, per §5's original future-direction sketch — now promoted into scope. All other optional/risk-triggered core seats (Domain-Intent, Fresh-Eyes, Change-Trajectory, Design-Alternatives, Test-Design Quality, Taste) remain full-mode only. |
| D12 | What is medium mode's VALIDATE cap? | **2 validators for Critical findings (down from full's 2-3), 1 for everything else (same as full/lite).** A meaningful but bounded Critical-finding challenge — cheaper than full, richer than lite's flat 1. |
| D13 | What is medium mode's CONVERGE cap? | **2 total loop iterations (vs. lite's 1, full's up to 8/3-strikes).** Gives medium one retry before escalating to a full-panel recommendation, consistent with it sitting strictly between lite and full on every dimension. |
| D14 | What happens if both `--lite` and `--medium` are passed together? | **Hard error — reject the invocation.** Consistent with the plugin's fail-closed philosophy: ambiguous tier selection is refused rather than silently resolved by picking one flag over the other. |
| D15 | Does medium mode's RE-REVIEW re-cast set differ from lite's? | **Yes — re-casts whichever of {Adversarial, Simplicity, Structural} had a finding fixed, plus any fixed fail-closed seat**, mirroring lite's existing "re-cast whichever seats were actually cast and had findings fixed" rule, just applied to medium's larger SPAWN set. Fresh-Eyes stays excluded from RE-REVIEW under both narrowed tiers, since it's excluded from SPAWN under both. |
| D16 | Is `--auto` a fourth tier, or a resolver? | **A resolver.** `--auto` is not a tier value — it picks one of the three existing tiers (full/medium/lite) and that tier's unmodified machinery runs. The JSON `tier` field never contains `"auto"`; a separate `tier_source` field records how the tier was picked. |
| D17 | What signals does `--auto` use to resolve a tier? | **Files-changed count and lines-changed count (additions+deletions) from a cheap, pre-CAST `git diff --stat`-equivalent, plus a fail-closed-sensitive-path match reusing `persona-catalog.md`'s existing Security/Data-Steward cast-when path criteria verbatim.** Never live-scan output, never file content beyond path-pattern matching, never a new heuristic invented for this feature alone. |
| D18 | What are the resolution thresholds? | **Resolved 2026-07-19, confirmed against this repo's actual commit history (fixed constants, not repo-configurable in v1): ≤3 files AND ≤200 changed lines → lite; ≤15 files AND ≤1000 changed lines → medium; otherwise → full. A fail-closed-sensitive path match overrides all size thresholds and forces full.** A files/lines-changed pass over the last 49 non-merge commits in this repo under the originally-proposed ≤40/≤300 thresholds produced a 17/19/13 lite/medium/full split (balanced, not skewed); the human reviewed that data and opted to widen both line ceilings, producing a ~51/41/8 split that favors lite/medium by default and reserves full for genuinely large diffs. See §9 OQ5. |
| D19 | Is `--auto` mutually exclusive with `--lite`/`--medium`? | **Yes — pairwise hard error, same as D14's `--lite`+`--medium` rule.** At most one tier-selecting flag may be present; passing two is rejected before CAST runs. |
| D20 | How is an `--auto` resolution disclosed? | **Two new fields alongside the existing `tier`/`narrowed_guarantees` pair: `"tier_source": "explicit"\|"auto"` (always present) and `"auto_signals"` (an object with `files_changed`, `lines_changed`, `sensitive_path_match`, present only when `tier_source` is `"auto"`).** Human report gets one additional line naming the resolved tier and the signals, appended to the existing `## Narrowed Run` block (or a full-mode-only version of that disclosure when auto resolves to full, since full mode currently has no banner at all — see spec Phase 6). |
| D21 | Where in Setup does `--auto` resolve, relative to target resolution? | **After target resolution, before CAST.** Resolving a tier from diff stats requires the review target (bare working tree, PR, or range) to already be known, so `--auto`'s resolution step is sequenced after Setup's existing target-resolution logic and before CAST begins — the one point where flag handling has a genuine data dependency on target resolution, unlike `--lite`/`--medium`/`--mode=agent`, which are independent of it. |

## 9. Open questions for agreement

- **OQ1 — Exact `--lite`/`--medium`/`--auto` CLI syntax edge cases. Resolved 2026-07-19: reject
  with a clear error.** A tier flag passed alone (no other flags) still defaults to
  human-interactive, consistent with full mode's own default — that part was never in question.
  What was open: `--lite=false` (or `--medium=false`/`--auto=false`) is **not** a valid way to
  force full mode. The flags remain presence-only (no `=false` form for any of the three,
  consistent with how `--mode=agent` has no `--mode=agent=false` counterpart today), and a
  malformed `=false` attempt is rejected with a clear error before CAST runs — the same fail-closed
  code path as D14/D19's multiple-tier-flags rejection, rather than being silently treated as
  flag-absent. Rationale: silently falling back to full mode on a malformed flag would mask a
  typo'd CI invocation (e.g. a script that meant `--lite=true`) as a normal full-mode pass instead
  of surfacing the mistake.
- **OQ2 — Exact wording of the narrowed-run disclosure banner.** The spec defines the required
  *content* (tier name, which guarantees narrowed) but the exact human-report prose is left to
  implementation-time drafting, matching how other disclosure banners (Coverage Honesty) are
  specified by requirement rather than verbatim text elsewhere in the plugin. **Still open — no
  action needed now**, deferred to implementation time by design.
- **OQ3 — Whether a `--medium` tier is worth building now.** **Resolved 2026-07-19: yes.** The
  human confirmed adding it; this epic's scope now includes it. See the tier table in §1 and D11-D15
  for the concrete design. (This reverses this section's original "no, deferred" answer.)
- **OQ4 — Reuse existing JSON `status` values vs. add a new one for a narrowed tier's iteration-cap
  exit.** **Resolved 2026-07-19: add a new `capped` status value**, distinct from `circuit_broken`.
  See D5 for the full rationale. (This reverses this session's original "reuse `circuit_broken`"
  provisional answer — the human explicitly asked for the judgment call to be made rather than
  left open, and on the merits a by-design tier cap is semantically different from a genuine
  circuit-breaker stagnation, independent of the ergonomics argument for foundry gates.)
- **OQ5 — Are `--auto`'s proposed resolution thresholds right for this repo's typical diff sizes?
  Resolved 2026-07-19: yes, at widened thresholds (D18).** The original ≤40/≤300 line proposal was
  checked against the last 49 non-merge commits in this repo (files/lines-changed via
  `git show --numstat`), producing a 17/19/13 lite/medium/full split — balanced, confirming the
  mechanism itself wasn't skewed. The human reviewed that data and chose to widen both line
  ceilings to ≤200 (lite) and ≤1000 (medium), which shifts the same commit history to a ~51/41/8
  split — biasing the default toward the fast tiers and reserving full for diffs that are large by
  either files or lines, not moderate-size diffs that happen to cross a low line count. File-count
  ceilings (≤3 lite / ≤15 medium) were left unchanged; only the line ceilings moved.
- **OQ6 — Should `--auto` resolving to `full` render any disclosure at all, given full mode
  currently has no banner/disclosure block in either output mode?** An `--auto` run that resolves
  to `full` still needs *some* signal that auto-resolution happened (per PRD goal 6's "never
  mistakable by omission" requirement) even though the resolved tier itself carries no narrowing to
  disclose. **Open — flagged for human confirmation**; spec Phase 6 proposes a minimal one-line
  addition for this specific case, distinct from the full `## Narrowed Run` block narrowed tiers
  get.
