# Tier Verification — `--lite` / `--medium` / `--auto`

Verification for `scc-c56.7`, the closing task of epic `scc-c56` (review-panel Narrowed Review
Tiers). Checks the fixture set and reasoning against all nine of that issue's acceptance criteria.

## Methodology note — read this before the rest of the document

**Every walkthrough below is hand-worked, not live-dispatched.** `PRESSURE-TEST.md` (Section 3)
ran one live 2-seat `Task` dispatch (Correctness/Adversarial + Domain-Intent) against
`order-fulfillment/` and worked the rest of that pipeline by hand. This document has **zero**
live-dispatch capability available to it at all: it was produced by a forked subagent with no
`Task` tool, under an explicit instruction not to spawn further agents. So unlike
`PRESSURE-TEST.md`, 100% of the verification here is a literal, line-cited application of the
seven reference files' documented rules to constructed fixtures — no seat was actually invoked,
no orchestrator actually ran. Where `PRESSURE-TEST.md`'s own live results are reused as known
inputs (the order-fulfillment fixture's three seeded bugs and their MERGE confidence scores),
that reuse is called out explicitly. Every dispatch count below is a derivation, not a
measurement. See "Limits of this verification" (Section 8) for exactly how much weight that
should carry.

Reference files cited throughout (all locked, none modified by this task):
`reviewers/persona-catalog.md`, `skills/review-panel/references/cast-and-spawn.md`,
`references/merge-and-validate.md`, `references/fix-and-rereview.md`,
`references/converge-and-pipeline.md`, `references/lite-mode.md`, `references/dual-mode-contract.md`.

---

## 1. Low-risk fixture: dispatch counts across tiers (AC2, AC3)

Reuses `fixtures/order-fulfillment/` — see `PRESSURE-TEST.md` Section 1 for the fixture's full
description and Section 3 for the one live dispatch this document borrows numbers from. Three
seeded bugs, confirmed live by `PRESSURE-TEST.md`:

- **F1 — null-deref** (Correctness/Adversarial, Critical, MERGE confidence 100)
- **F2 — resource leak + off-by-one**, merged as one MERGE row (Adversarial, Critical, confidence 100)
- **F3 — domain-term coherence drift** (Domain-Intent, non-Critical/"Important", confidence 75) —
  missed by the plain single-pass baseline in `PRESSURE-TEST.md` Section 2, caught only once
  Domain-Intent was cast

A `CONTEXT.md` exists at the fixture root (confirmed: `fixtures/order-fulfillment/CONTEXT.md`),
so Domain-Intent's cast-when and RE-REVIEW Axis (b) both have something to check against.

### Round-1 seat eligibility, by tier

Per `persona-catalog.md`'s Tier-eligibility footnote and each seat's own Cast-when: Adversarial,
Simplicity, Structural, Fresh-Eyes are the catalog's "always cast" core seats; Domain-Intent casts
on a type/schema/CONTEXT.md-documented match; Change-Trajectory casts because this diff modifies
existing code (not a from-scratch file). Security's trigger (auth/crypto/secrets/dependency paths)
and Data Steward's trigger (migration/schema paths) don't match this fixture, so both are excluded
from all three tiers here — see `persona-catalog.md`'s Security and Data Steward entries.

| Seat | Lite | Medium | Full |
|---|---|---|---|
| Adversarial | cast | cast | cast |
| Simplicity | — (medium/full only) | cast | cast |
| Structural | — (medium/full only) | cast | cast |
| Fresh-Eyes | — (full only) | — (full only) | cast |
| Domain-Intent | — (full only) | — (full only) | cast |
| Change-Trajectory | — (full only) | — (full only) | cast |
| **Round-1 SPAWN count** | **1** | **3** | **6** |

Lite and medium's SPAWN excludes Domain-Intent entirely — neither can catch F3 in round 1.

### Round-1 VALIDATE, by tier

Lite: flat 1 validator per finding. Medium: Critical → exactly 2, non-Critical → 1. Full:
Critical → 2 (confidence ≥75) or 3 (confidence <75), non-Critical → 1. F1 and F2 are both
Critical/confidence-100; F3 (confidence 75, non-Critical) is only visible where Domain-Intent was
cast.

| Tier | Findings caught round 1 | VALIDATE dispatches |
|---|---|---|
| Lite | F1, F2 | 1 + 1 = **2** |
| Medium | F1, F2 | 2 + 2 = **4** |
| Full | F1, F2, F3 | 2 + 2 + 1 = **5** |

### RE-REVIEW round 1

FIX applies fixes to whatever round 1 caught (F1+F2 under lite/medium; F1+F2+F3 under full).

- **Axis (a)** (`fix-and-rereview.md` lines 119-140): always re-cast Adversarial; re-cast any
  other seat whose finding was fixed, scoped to the tier's SPAWN candidates; re-cast Fresh-Eyes
  only in full mode, and only as a judgment call. Lite/medium: only Adversarial found anything, so
  axis (a) = **1** dispatch. Full: Adversarial (always) + Domain-Intent (its F3 fix is in the
  fixed set and Domain-Intent is a valid full-mode candidate) = **2** dispatches; Fresh-Eyes is
  assumed *not* re-cast here (localized single-module fixes, not a broad restructure) — a judgment
  call, flagged in Section 8.
- **Axis (b)** (`fix-and-rereview.md` lines 146-169): **unmodified by tier**, runs identically
  everywhere. Since the fixed files are CONTEXT.md-documented, Domain-Intent is (re-)cast for this
  axis regardless of what SPAWN cast this round. Under lite/medium this is Domain-Intent's *first*
  appearance in the run, and it surfaces F3 as a brand-new finding. Under full, F3 was already
  fixed, so axis (b) is a clean re-check. = **1** dispatch, every tier (with the full-mode caveat
  noted in Section 8 about axis (a) and axis (b) plausibly collapsing into a single Domain-Intent
  call in a real implementation rather than two).

| Tier | RE-REVIEW round-1 dispatches | Round-1 result |
|---|---|---|
| Lite | 1 (axis a) + 1 (axis b) = **2** | **dirty** — axis (b) just surfaced F3, never caught by SPAWN |
| Medium | 1 + 1 = **2** | **dirty** — same reason |
| Full | 2 + 1 = **3** | **clean** — F3 was already fixed in round 1 |

### CONVERGE

Per `converge-and-pipeline.md` step 0 (no sovereignty finding here — see Section 4 for that path)
then step 1/2:

- **Full**: clean round 1 → **`converged`** after 1 round. Total dispatches: 6 + 5 + 3 = **14**.
- **Lite**: dirty round 1, cap is 1 total round (`converge-and-pipeline.md` line 38-40) → **do
  not loop** → **`capped`**, with F3 reported outstanding. Total dispatches: 1 + 2 + 2 = **5**.
- **Medium**: dirty round 1, cap is 2 total rounds, round 1 has budget remaining → loop back to
  SPAWN for round 2 (line 41-43), dispatching medium's same narrowed candidate set again
  (`{Adversarial, Simplicity, Structural}`, per `converge-and-pipeline.md`'s "full cast list" note
  applying per-tier, not per-run) = 3. F3 was already surfaced by round-1's axis (b) and is fed
  directly into round 2's MERGE pass per `fix-and-rereview.md` line 168 ("treated as a new finding
  for the next MERGE pass"), so it doesn't need medium's SPAWN to organically re-find it — VALIDATE
  round 2 = 1 (F3, non-Critical). FIX fixes F3. RE-REVIEW round 2: axis (a) = Adversarial only (1,
  since Domain-Intent isn't a medium-tier axis-a candidate); axis (b) re-checks Domain-Intent once
  more (1) and comes back clean this time. Round 2 clean → **`converged`**, using both permitted
  rounds. Total dispatches: (3+4+2) + (3+1+2) = 9 + 6 = **15**.

### Comparison table (AC2, AC3)

| Metric | Lite | Medium | Full |
|---|---|---|---|
| Terminal status | `capped` | `converged` | `converged` |
| Rounds used | 1 (of 1 cap) | 2 (of 2 cap) | 1 (uncapped) |
| SPAWN dispatches | 1 | 3 + 3 = 6 | 6 |
| VALIDATE dispatches | 2 | 4 + 1 = 5 | 5 |
| RE-REVIEW dispatches | 2 | 2 + 2 = 4 | 3 |
| **Total dispatches** | **5** | **15** | **14** |
| Findings resolved at terminal | F1, F2 (F3 outstanding) | F1, F2, F3 | F1, F2, F3 |

**AC2 assessment: PARTIAL.** AC2's literal text requires matching "a pre-feature baseline
capture" — no such artifact exists in this repo (`PRESSURE-TEST.md` predates the tier feature and
is itself a partial 2-seat dispatch, not a full-mode capture), and this document has no live-run
capability to produce one. What *is* verifiable, and is verified above: every narrowing clause in
all four reference files is textually conditioned on `--lite`/`--medium` (`if under --lite or
--medium`, `tier conditional`, `scoped to just the tier's candidate seats`), and full mode falls
through to an unconditioned default in every stage — SPAWN casts the full catalog-driven list,
VALIDATE uses the uncapped Critical→2-or-3 rule, RE-REVIEW's axis (a) draws from the full seat
set including the Fresh-Eyes judgment call, and CONVERGE has no round cap. This is an
architectural/textual argument for invariant 5, not a measured before/after diff, so it is graded
PARTIAL rather than PASS.

**AC3 assessment: PARTIAL, with an honest caveat the AC's own phrasing doesn't anticipate.**
Round 1 in isolation is strict: SPAWN 1 < 3 < 6, VALIDATE 2 < 4 < 5, RE-REVIEW-round-1 2 = 2 < 3
(lite and medium tie here, not strictly less). At the *terminal* comparison the ordering breaks
down further: lite (5 total) < full (14 total), consistent with AC3 — but medium (15 total) is
**not** less than full (14 total) here. This isn't a bug in the tier design; it's RE-REVIEW Axis
(b) being genuinely unmodified by tier (`fix-and-rereview.md` line 146-148) doing exactly what
it's specified to do: it force-casts Domain-Intent post-fix regardless of whether SPAWN narrowed
it away, so a narrowed tier that missed a coherence issue in round 1 discovers it late and either
can't act on it (lite, `capped`) or needs a whole extra round to clean it up (medium). Full mode,
having Domain-Intent in round 1 already, needed only one round. So per-round dispatch counts are
strictly ordered as AC3 describes, but *total-to-terminal* dispatch count is not monotonic in
tier narrowness in general — it depends on whether a narrowed tier's SPAWN gap happens to line up
with what axis (b) unconditionally re-checks. Graded PARTIAL: the criterion holds as literally
measured within a single round, and holds for lite vs. full, but does not hold for medium vs.
full on this fixture's terminal totals, and that's a structural property of the design, not a
fixture artifact.

---

## 2. Security / data-sensitive fixture (AC4)

**A previous verification pass on this branch found a genuine inconsistency here and resolved it
— but this branch has since been rebased onto upstream's own redesign of the Security seat, which
resolves the same tension the other way and supersedes that earlier fix. This section documents
the current, canonical state: both halves of AC4 are real, demonstrable seats.**

The previous pass's finding: `persona-catalog.md`'s Security entry, prior to this rebase, cast
Security *if and only if* CAST Step 4 (live-scan) found a security-specific skill installed —
content alone was not sufficient, because Security had no vendored skill of its own to name in a
Step 6 cast-list entry (`{seat name, target skill path, ...}`) without Step 4 first discovering
one. Three other passages in this epic's own additions had assumed content-triggered,
Step-4-independent casting anyway; the previous pass judged the "content alone forces Security in"
reading **not mechanically coherent** under that no-vendored-skill premise, and rewrote all four
passages to the strict Step-4-gated reading.

**That premise no longer holds.** Upstream's redesign (merged into this branch via the rebase onto
"Two-System Architecture: plan/build/review + triage plugins") makes Security a **primary catalog
cast** with a concrete, always-known target: `security-suite`'s `agents/security-engineer.md`,
dispatched via `Task` as agent type `security-suite:security-engineer` — see `persona-catalog.md`'s
Security entry. Security now has exactly what the previous pass's objection said it lacked: a
vendored skill it can name without Step 4 ever running. Its Cast-when is therefore a direct Steps
1-3 content/path match (auth, crypto, secrets, input validation, deserialization, dependency
manifests, IaC, CI config) — the same shape as Data Steward's, which is likewise now a real catalog
entry (`skills/data-steward/SKILL.md`, fail-closed on migration/ORM/schema/serialization paths or
`DATA-MODEL.md`-mapped files), not the hypothetical future seat the previous pass's
Tier-eligibility rewrite treated it as. Both seats are Steps-1-3-decidable and fail-closed-forced
into every tier including `--lite`/`--medium` — see `persona-catalog.md`'s Tier-eligibility
footnote and `cast-and-spawn.md`'s "Seat set: full vs. narrowed tiers" section, both of which now
state this directly rather than singling Security out as the one exception.

This is the same honesty discipline the previous pass applied and this document continues to
apply: the fixture work below (`dependency-bump/`, `sensitive-migration/`) was originally written
against the now-superseded Step-4-gated reading and has been updated in place to match the current
reference files, rather than left to silently contradict them.

### `fixtures/dependency-bump/` — trips Security's own trigger list

`package.json` + `package-lock.json`, `left-pad` bumped `^1.3.0` → `^1.4.0`. files_changed=2,
lines_changed=10. This is the genuine AC4 fixture: both files match persona-catalog's Security
"Dependency/supply-chain" Path-identifiable pattern (`package.json` manifest,
`package-lock.json` lockfile) *and* its content-based trigger category.

Under the current reading (Security's cast-when is a Steps-1-3 content/path match, with no
dependency on CAST Step 4/live-scan — see Section 2 above), the content-and-path match alone is
sufficient to force the seat in, in every tier:

| Tier | Security cast? |
|---|---|
| Lite | **Yes** — Steps 1-3 match Security's dependency/supply-chain trigger directly; Step 4 being skipped under Lite is irrelevant to this seat |
| Medium | **Yes** — same reasoning as Lite |
| Full | **Yes** — same match, plus whatever Step 4/live-scan would add on top (moot for this fixture: no security skill needs discovering, since Security's own target is vendored, not live-scan-discovered) |

This demonstrates AC4's "fail-closed seats present under all three modes" half for Security
cleanly: the cast itself, not just a disclosure, is tier-independent, because Security's Cast-when
never depended on Step 4 once it has its own named target skill
(`security-suite:security-engineer`) to dispatch.

### `fixtures/sensitive-migration/` — does *not* trip Security, only Data Steward

`db/migrations/0012_add_customer_tax_id.sql` (new file) + one added row in `DATA-MODEL.md`
documenting the new `tax_id` column. files_changed=2, lines_changed=6.

Migration/data-model paths are **not** in Security's own trigger list (auth/authn/authz/session/
oauth/login/jwt; crypto/cipher/secrets/credentials/.env/*.pem/*.key; dependency lockfiles/
manifests) — so this fixture does not cast Security. It matches Data Steward's own cast-when
instead: `db/migrations/` is one of `persona-catalog.md`'s Data Steward entry's fail-closed path
patterns (migration/schema directories, `DATA-MODEL.md`-mapped files), and the `DATA-MODEL.md` edit
is itself a mapped file under that same entry.

**Data Steward is a real seat in this branch's `persona-catalog.md`** (see its "Data Steward"
entry) — casting `skills/data-steward/SKILL.md`, Top-tier, fail-closed on exactly this fixture's
path shape. Like Security, its cast-when is Steps-1-3-decidable with no Step 4/live-scan
dependency, so it is forced into SPAWN dispatch in every tier:

| Tier | Data Steward cast? |
|---|---|
| Lite | **Yes** — Steps 1-3 match the migration/`DATA-MODEL.md` path pattern directly |
| Medium | **Yes** — same reasoning as Lite |
| Full | **Yes** — same match |

This fixture now demonstrates both AC4's "Data-Steward is cast" half and the `sensitive_path_match`
signal (Section 5, AC9), and gives Section 4's sovereignty walkthrough a concrete, on-disk finding
to hang its reasoning on — no longer a hypothetical stand-in for an unimplemented seat.

**AC4 assessment: PASS.** Both halves are now demonstrated concretely and cleanly:

- The Security half (`dependency-bump/`) casts Security under all three tiers, including
  `--lite`/`--medium` — the cast itself is tier-independent, not just a disclosure obligation,
  because Security's Cast-when is Steps-1-3-decidable against its own vendored target
  (`security-suite:security-engineer`) with no Step 4/live-scan dependency.
- The Data Steward half (`sensitive-migration/`) casts Data Steward under all three tiers on the
  same basis: a real catalog entry, Steps-1-3-decidable, fail-closed-forced into every tier.

Both seats are cast, not merely disclosed, under `--lite`/`--medium` — AC4's literal "both cast
under narrowed tiers" requirement holds without qualification on these fixtures.

---

## 3. Medium-vs-lite distinctness fixture (AC5)

`fixtures/needless-abstraction/`: `before.ts` is a four-line pure function
(`formatDiscountLabel`); `after.ts` wraps it in an unused-generality `DiscountLabelStrategy`
interface + single implementation + factory, then calls through all three layers to produce the
*exact same* output. files_changed=1, lines_changed=24 — small enough to auto-resolve to lite
(see Section 5), so this fixture must be driven with explicit `--lite`/`--medium` flags, not
`--auto`, to test what AC5 actually asks.

- **`--lite`**: SPAWN = Adversarial only (Simplicity/Structural excluded, medium/full only per
  Tier-eligibility). Adversarial's scope is correctness — `after.ts` is behaviorally identical to
  `before.ts` for every input, so Adversarial has nothing to flag. **Lite's output: no finding.**
- **`--medium`**: SPAWN = Adversarial + Simplicity + Structural. Simplicity's cast-when
  (`persona-catalog.md` line 107, "Always cast... for diff-scoped panel runs") applies unconditionally
  once the seat is in the tier's candidate set, and its over-engineering checklist
  (delete/stdlib/native/yagni/shrink) is a direct hit: a single-implementation Strategy pattern
  plus a factory for a four-line pure function is the textbook YAGNI case that checklist exists
  to catch. **Medium's output: the over-engineering finding, present.**

This is exactly AC5's required shape: same fixture diff, medium's SPAWN set includes a seat whose
cast-when is unconditional once eligible and whose scope covers this specific issue, lite's
SPAWN set structurally excludes that seat. **AC5 assessment: PASS** — the distinctness is
mechanical (a seat included vs. excluded from SPAWN by tier), not a coincidence of what any one
seat happens to notice.

---

## 4. Sovereignty walkthrough (AC6)

**Data Steward is a real seat in this branch's `persona-catalog.md`** (confirmed in Section 2) —
the honesty constraint a previous verification pass stated here no longer applies; that constraint
was about a seat that didn't exist, and the seat now exists. What remains true, and is stated
plainly per this document's own Methodology note: this forked verification agent has zero
`Task`-dispatch capability of its own, so this section still cannot *observe* Data Steward actually
running — it can only hand-apply the seat's real, documented cast-when and
`converge-and-pipeline.md`'s step 0 text to a constructed fixture, the same treatment every other
section in this document gives every other seat. What follows is a literal, hand-applied
walkthrough of `converge-and-pipeline.md`'s step 0 text against a sovereignty-relevant finding on
Data Steward's real cast-when match — the same treatment `PRESSURE-TEST.md` Section 4 gave the
circuit-breaker, now applied to a mechanism that (unlike in the previous pass) is fully
implemented, just not live-dispatched by this document.

**Verbatim step 0** (`converge-and-pipeline.md`, Decision rule, step 0):

> 0. **Sovereignty check, ahead of the clean/dirty call, in every tier.** Before applying the
> clean/dirty rule below or either narrowed tier's iteration cap in step 2, check whether any
> surviving finding ... still carries `sovereignty: human-required` (produced by the Data-Steward
> seat — see `reviewers/persona-catalog.md`'s "Data Steward" entry). This is a **new terminal
> state**, not a loop condition... This check runs identically in every tier including full mode —
> narrowing the review scope never narrows it (SPEC Architecture invariant 3...). If one or more
> sovereignty-marked findings remain: Emit status `escalated`... Do **not** loop back to SPAWN for
> these findings, and do **not** collapse this into `circuit_broken` or `capped`... If
> sovereignty-marked findings coexist with other, ordinary unresolved findings in the same round,
> still apply the dirty-round loop... subject to the active tier's cap... Report `escalated` as the
> overall run status once every *non*-sovereignty finding has otherwise reached a clean state, or
> once the active tier's cap is reached on those ordinary findings (report both `escalated` and the
> tier-cap diagnosis together in that case)...

The last clause is new since the previous pass's quote and matters here: `escalated` can now
*coexist* with a tier-cap diagnosis in the same report, when sovereignty and ordinary findings are
both outstanding at once (see `dual-mode-contract.md`'s merged `capped`/`escalated` status fields).
The walkthrough below has only a single finding — the sovereignty one — so that coexistence case
doesn't arise on this fixture; it's noted here for completeness, not because it changes this
fixture's result.

### Applying it to `sensitive-migration/`

Data Steward is cast against `fixtures/sensitive-migration/` per its real cast-when (the
migration file + `DATA-MODEL.md` pairing — Section 2 above). Assume, for this hand-worked
walkthrough (no live dispatch — see the Methodology note), that it reports an unresolved
sovereignty-relevant finding — e.g. "government-issued taxpayer ID added to a customer table with
no documented data-residency or retention policy in `DATA-MODEL.md`."

- **Under `--lite`:** CONVERGE reaches step 0 before step 1 or step 2. Step 0 finds the unresolved
  sovereignty finding → status is **`escalated`**. This happens *before* lite's 1-round cap (step
  2) is even consulted — the cap logic never runs. Lite does **not** report `capped`, even though
  a `capped` verdict might otherwise seem plausible for a lite run with an unresolved finding at
  round 1.
- **Under `--medium`:** identical precedence. Step 0 fires first, regardless of whether medium
  has 0, 1, or 2 rounds of cap budget remaining → status is **`escalated`**, never `capped`.
- **Under full mode:** identical precedence, stated explicitly in the source text ("identically in
  every tier including full mode") — full mode would also report `escalated`, not
  `circuit_broken`, even on a 3-strikes-stagnant run, if a sovereignty finding were unresolved.

**Result: status resolves to `escalated` under both narrowed tiers (and full), never `capped` or
`circuit_broken`, purely from the decision rule's literal step ordering** — step 0 is
unconditional and runs before step 2's tier-cap branch is reached, so no tier's cap logic ever
gets the chance to produce a competing verdict.

**AC6 assessment: PASS.** The *precedence rule itself* is verified as literally correct and
tier-independent by direct textual application — there is no ambiguity in step 0's ordering
relative to step 1/2, and no way to read the decision rule that lets a tier cap preempt it. Data
Steward, the seat that produces the sovereignty-marked finding, is a real, Steps-1-3-decidable,
fail-closed-forced catalog entry that matches `sensitive-migration/`'s real path shape (Section 2)
— the only thing this walkthrough cannot do is *observe* a live dispatch confirming the seat's
actual finding text, a limitation of this document's own zero-`Task` capability (Methodology
note), not of the design. That same limitation applies equally to every hand-worked section in
this document (Section 1's dispatch counts, Section 5's fixtures) without preventing those from
grading PASS, so it does not block PASS here either: the precedence rule, the seat, and the
fixture match are all real and unambiguous; only the live run itself is out of this document's
reach.

---

## 5. Auto-resolution fixtures (AC8, AC9)

Decision table (`lite-mode.md` lines 85-98), evaluated top-to-bottom, first match wins, ties
resolve to the cheaper tier:

1. `sensitive_path_match=true` → full, regardless of size
2. `files_changed<=3` AND `lines_changed<=200` → lite
3. `files_changed<=15` AND `lines_changed<=1000` → medium
4. otherwise → full

All four fixtures below are purely mechanical — `--auto`'s resolver "never reads live-scan
results and never reads file content beyond path matching" (`lite-mode.md`), so file *contents*
here are synthetic placeholder TypeScript (`export const {tag}_{n} = {n};` repeated), not
realistic code. Stated plainly rather than dressed up as real diffs — see Section 8.

| Fixture | files_changed | lines_changed | sensitive_path_match | Rule that fires | Resolves to |
|---|---|---|---|---|---|
| `auto-resolution/at-lite-boundary/` | 3 | 200 | false | Rule 2, exactly at boundary | **lite** |
| `auto-resolution/just-over-lite-boundary/` | 3 | 201 | false | Rule 2 fails (201>200); Rule 3 fires | **medium** |
| `auto-resolution/above-medium-boundary/` | 16 | 80 | false | Rule 2 fails; Rule 3 fails (16>15 files); Rule 4 | **full** |
| `sensitive-migration/` | 2 | 6 | **true** (migration/DATA-MODEL.md forward-compat pattern) | Rule 1, short-circuits before size is even checked | **full** |

- **`at-lite-boundary/`**: 3 files (`module-a/b/c.ts`, 67+67+66 lines) = exactly 200 lines,
  exactly 3 files. Rule 2's `<=` on both dimensions matches at the boundary itself — per
  `lite-mode.md`'s explicit "boundary values resolve to the cheaper tier," this must resolve to
  lite, not medium. Confirmed: 3<=3 and 200<=200 both hold, so rule 2 fires first (rule order
  matters here only in that rule 2 is checked before rule 3, but at this exact point both would
  also satisfy rule 3 — rule 2 firing first is what makes this the cheap-tier case).
- **`just-over-lite-boundary/`**: identical file count (3) and layout, but `module-c.ts` is 67
  lines instead of 66, pushing lines_changed to 201. Rule 2's line-count condition now fails
  (201 > 200) even though the file-count condition still passes — a single line over the boundary
  is enough to fall through to rule 3 (files: 3<=15, lines: 201<=1000, both true) → medium. This
  isolates the *line-count* dimension of the boundary independent of file count.
  Adjacent-fixture, exactly-boundary-vs-one-over pair — this is the direct AC8 falsification test
  for the lite/medium edge.
- **`above-medium-boundary/`**: 16 files (`module-01.ts`...`module-16.ts`), 5 lines each = 80
  lines total — small by line count, but 16 files is one over medium's 15-file cap. Rule 3 fails
  on the file-count dimension alone (16 > 15) despite easily passing the line-count dimension
  (80 <= 1000) → falls through to rule 4, full. This isolates the *file-count* dimension of the
  medium/full boundary independent of line count, the complementary edge case to the line-count
  isolation above.
- **`sensitive-migration/`** (reused from Section 2): only 2 files, 6 lines — well inside lite's
  own boundary by both dimensions, and would resolve to lite under rules 2-4 alone. But rule 1 is
  evaluated first and short-circuits: `sensitive_path_match=true` (migration path pattern) forces
  full regardless of size. This is the AC9 fixture precisely: "a diff small enough to otherwise
  qualify for lite that touches a sensitive path... resolves to full anyway."

**AC8 assessment: PASS.** Three size-band fixtures exist, each isolating a specific boundary
condition (exact lite boundary tie-goes-cheap, one-line-over on the line dimension, one-file-over
on the file dimension), each confirmed against the literal decision table.

**AC9 assessment: PASS.** `sensitive-migration/` is small enough by both dimensions to otherwise
resolve to lite under rules 2-4, but rule 1's short-circuit forces full — distinct from the three
size-band fixtures (it isolates the path-sensitivity dimension, not a size dimension), matching
AC9's explicit requirement that it be "distinct from the three size-band fixtures."

---

## 6. Tooling gates (AC1, AC7)

Results below were captured by actually running each command against this repository state, not
hand-derived.

- **`python3 scripts/verify_plugin.py`** → `OK: plugin manifests parse cleanly; versions match;
  hook file references exist: ...` — **exit 0.** Confirms the `plugin.json`/`marketplace.json`
  version bump (`0.2.1` → `0.3.0`, Section 7 note) stayed in sync. **AC1: PASS.**
- **`uv run pytest -q`** → `no tests ran in 0.06s` — **exit 5** (pytest's standard code for "zero
  tests collected," not a test failure). This is a pre-existing repo condition, not something
  introduced by this epic: the repo has no `test_*.py`/`*_test.py` files anywhere (confirmed via
  `fd -e py`; the only `.py` files in the whole repo are `hooks/prefer_modern_tools.py`,
  `scripts/verify_plugin.py`, and `skills/property-based-testing/examples.py` — none of them
  pytest test modules), and no `[tool.pytest]`/`testpaths` config exists to point elsewhere. This
  epic's changes are exclusively Markdown, JSON, and TypeScript fixture content — no Python file
  in the repo was added, removed, or modified by any phase of `scc-c56`.
- **`uv run ruff check --fix`** → `All checks passed!` — **exit 0**, no-op (nothing to fix),
  exactly as expected since no Python files are touched by this epic.

**AC7 assessment: PASS.** Re-checked against the beads issue's own verbatim text (`bd show
scc-c56.7`): "Given `uv run pytest` and `uv run ruff check --fix` are run against any Python-side
tooling touched by this epic, both gates pass. PASS/FAIL: exit code 0 for both, **or** an explicit
note that no Python files were touched by this epic." The second, disjunctive clause is not a
consolation branch for a partial result — it is a full, independent satisfaction condition, and it
is squarely met: ruff passes at exit 0, and it is factually true (confirmed above via `fd -e py`)
that no Python file was touched by any phase of this epic. pytest's exit 5 is a pre-existing
condition of the repo having zero pytest test modules anywhere, unrelated to and unaffected by
this epic's changes, and the AC's own text explicitly anticipates exactly this "no Python touched"
case rather than requiring pytest to somehow exit 0 on an empty collection. Grading this PARTIAL
under-applies the AC's own escape clause; PASS is the correct, literal reading.

---

## 7. Final acceptance-criteria self-assessment

| # | Acceptance criterion (paraphrased) | Verdict | Justification |
|---|---|---|---|
| AC1 | `verify_plugin.py` exits 0, no manifest/schema errors | **PASS** | `python3 scripts/verify_plugin.py` → `OK: ...versions match...` — exit 0 (Section 6) |
| AC2 | Full mode matches a pre-feature baseline capture across Cast/VALIDATE/RE-REVIEW/CONVERGE | **PARTIAL** | No baseline capture artifact exists anywhere in the repo and this task has no live-dispatch capability to produce one; verified instead via architectural/textual citation that every narrowing clause is explicitly tier-conditioned and full mode falls through to an unconditioned default in all four stages (Section 1) |
| AC3 | lite < medium < full dispatch count on the same fixture | **PARTIAL** | Holds per-round and for lite-vs-full totals; does not hold for medium-vs-full *terminal* totals (15 vs. 14) on `order-fulfillment/`, because RE-REVIEW Axis (b) is unconditionally tier-independent and forces a narrowed tier into extra rounds to catch what its narrower SPAWN missed — a structural property of the design, demonstrated numerically in Section 1, not a fixture defect |
| AC4 | Security and Data-Steward both cast under `--lite`/`--medium` on a sensitive fixture | **PASS** | Security is a real, Steps-1-3-decidable, fail-closed-forced primary catalog cast (`security-suite:security-engineer`), cast under all three tiers on `dependency-bump/`; Data Steward is likewise a real, Steps-1-3-decidable, fail-closed-forced catalog entry, cast under all three tiers on `sensitive-migration/` (Section 2) — a previous verification pass's Step-4-gated reading of Security is superseded by upstream's own redesign of the seat, merged via this branch's rebase |
| AC5 | Medium catches a Simplicity/Structural finding lite misses | **PASS** | `needless-abstraction/`: lite (Adversarial-only) finds nothing on a behaviorally-identical refactor; medium (adds Simplicity) flags the textbook YAGNI over-engineering, mechanically via SPAWN seat-set inclusion, not incidentally |
| AC6 | Sovereignty-marked finding produces `escalated`, not `capped`/`circuit_broken`, under narrowed tiers | **PASS** | The precedence rule (CONVERGE step 0 before step 1/2) is verified as literally, unambiguously tier-independent by direct textual application to a finding on Data Steward's real cast-when match (Section 4); Data Steward is a real seat on this branch, so only the live dispatch itself (not the seat, not the rule) is out of this document's zero-`Task` reach — the same limitation every hand-worked section here already carries without blocking a PASS grade |
| AC7 | `pytest` and `ruff check --fix` both pass, or explicit note that no Python was touched | **PASS** | `ruff` exit 0, clean; `pytest` exit 5 ("no tests ran" — repo has no pytest test files at all, pre-existing and unrelated to this epic); no Python file was touched by any phase of `scc-c56` (Section 6) — AC's own disjunctive escape clause ("or an explicit note that no Python files were touched") is squarely satisfied, confirmed against the beads issue's verbatim text |
| AC8 | Three auto-resolution size-band fixtures exist and resolve correctly | **PASS** | `at-lite-boundary/` (exact tie → lite), `just-over-lite-boundary/` (201 lines → medium), `above-medium-boundary/` (16 files → full) — each isolates a distinct boundary dimension per the literal decision table |
| AC9 | Sensitive-path-override fixture, distinct from the size-band fixtures | **PASS** | `sensitive-migration/`: small by both size dimensions (would resolve to lite), but rule 1's `sensitive_path_match` short-circuit forces full; isolates the path dimension rather than a size dimension |

Of nine criteria: **7 PASS** (AC1, AC4, AC5, AC6, AC7, AC8, AC9), **2 PARTIAL** (AC2, AC3),
**0 FAIL.** No criterion is graded FAIL because every remaining gap traces to a capability this
task genuinely does not have (live dispatch, a pre-feature baseline artifact) — not to a fixture
that fails to demonstrate something it was supposed to, and not to a seat or mechanism that
doesn't exist: both Security and Data Steward are real, Steps-1-3-decidable, fail-closed-forced
seats in this branch's `persona-catalog.md`.

---

## 8. Limits of this verification

- **Zero live dispatch, across the entire document.** Every dispatch count, every SPAWN/VALIDATE/
  RE-REVIEW/CONVERGE outcome above is a hand-application of literal rule text to a constructed
  scenario, not an observed run. This is a stronger caveat than `PRESSURE-TEST.md` needed, since
  that document had one real dispatch to anchor against; this one has none of its own (it reuses
  `PRESSURE-TEST.md`'s pre-existing live results as known inputs, but performed no new dispatch).
- **Two judgment calls in Section 1's full-mode RE-REVIEW count**, both flagged inline: whether
  Fresh-Eyes gets re-cast under axis (a) for the order-fulfillment fixes (assumed no — localized,
  single-module fixes), and whether Domain-Intent's axis (a) and axis (b) re-casts would in
  practice collapse into one dispatch rather than two in a real implementation. Neither changes
  which tier converges vs. caps, only the exact full-mode dispatch total by ±1. Separately,
  order-fulfillment's Change-Trajectory seat (cast in full mode round 1 per its own cast-when) is
  assumed to return clean with no additional finding — plausible for a scoped bug-fix diff, but
  not independently verified.
- **The Security cast-when question (Section 2) has a documented history worth restating here.** A
  previous verification pass on this branch found the same locked-reference inconsistency this
  section originally described, and resolved it toward a strict Step-4-gated reading of Security's
  Cast-when, for a specific mechanical reason: Security had no vendored skill of its own to name in
  a cast-list entry without Step 4/live-scan first discovering one. This branch has since been
  rebased onto upstream's own, independent redesign of the Security seat, which gives Security a
  concrete, always-known vendored target (`security-suite:security-engineer`) and resolves the same
  tension the other way — Steps-1-3 content/path matching, no Step 4 dependency, exactly like Data
  Steward. That redesign is now the branch's canonical, locked state; the previous pass's fix is
  superseded, not layered on top of it. This document's Section 2 and its two fixtures were updated
  to match during this task, rather than left describing a reading the reference files no longer
  hold.
- **Auto-resolution fixture content is synthetic and mechanically inert by design**, not
  realistic code — appropriate given `--auto`'s resolver is documented as reading only path and
  size signals, never content, but worth stating plainly rather than presenting these fixtures as
  representative of a real diff's content.
- **AC2's "pre-feature baseline capture" refers to an artifact that does not exist** — it was never
  captured before this feature landed, and this document has no live-dispatch capability to
  produce one retroactively. (AC6's Data-Steward gap, previously paired with this bullet, no longer
  applies — Data Steward is a real seat as of this task's Section 2 update; see the first bullet in
  this section for the remaining, document-capability-only limitation on AC6.)
- **No fixture in this set was actually run through `/review-panel`.** All of the above should be
  read as "here is what the documented rules say would happen," suitable for a documentation-level
  verification sweep, but not a substitute for eventually exercising these fixtures through a real
  invocation once that becomes possible in this task's execution context.
