# Investigation: scc-bqp — Phase 2c data-steward seat

## Files to modify

All paths are relative to repo root. Note: `.pas/current_task.md`'s "Files to
Edit" list gives paths relative to `plugins/review-panel/`, not the repo
root — the corrected real paths are used below.

1. **NEW** `plugins/review-panel/skills/data-steward/SKILL.md`
2. **EDIT** `plugins/review-panel/reviewers/persona-catalog.md`
3. **EDIT** `plugins/review-panel/skills/review-panel/references/fix-and-rereview.md`
4. **EDIT** `plugins/review-panel/skills/review-panel/references/converge-and-pipeline.md`
5. **EDIT** `plugins/review-panel/skills/review-panel/references/dual-mode-contract.md`
6. **EDIT** `plugins/review-panel/skills/review-panel/references/merge-and-validate.md`
7. **LIKELY NEW** fixtures under `plugins/review-panel/tests/fixtures/` (e.g.
   extending `orders-schema/` with a destructive-migration diff and an
   Agent-boundary-violating diff) + a pressure-test-style doc, to exercise the
   5 acceptance criteria. Not in the task's explicit "Files to Edit" list but
   required to actually validate the AC — decide exact scope during Plan.

Not touched (explicitly out of scope or no change needed — see Risks):
`contracts/reviewer-output.md`, `contracts/verification-before-completion.md`,
`skills/review-panel/references/cast-and-spawn.md`, `skills/review-panel/SKILL.md`
(maybe one summary line), scc-4rj's data-layer guard hook (out of scope per
the task's own R1).

## Current behavior

- **persona-catalog.md**: manifest of reviewer seats. Core seats always cast;
  Risk-Triggered Seats (`Change-Trajectory`, `Design-Alternatives Check`,
  `Test-Design Quality`) cast on diff signal via fail-closed judgment. Each
  entry documents Casts/Cast-when/Model tier/Notes. Ends in a Seat Summary
  Table. Model-tier convention: top-tier reserved for
  Correctness/Adversarial, Security, Fresh-Eyes ("independence and
  adversarial rigor... are the point"); everything else mid-tier "unless a
  specific seat's entry explains a deviation." No Data Steward entry exists
  yet.
- **skills/domain-modeling/SKILL.md**: closest structural precedent for the
  new skill — frontmatter with `allowed-tools: Read, Grep` (read-only), "When
  to Apply," "How to Review" procedure, "Output Contract" section that
  extends the shared Critical/Important/Minor shape with its own
  CLEAR/TRIGGERED/N/A screening vocabulary, documented locally rather than by
  editing `contracts/reviewer-output.md`.
- **fix-and-rereview.md**: FIX stage dispatches exactly ONE fixer with the
  whole validated findings list, an explicit Bash-usage boundary (no commits,
  no installs, no network, no secret reads, no destructive git ops), and an
  "Output" section requiring evidence-before-claims. Nothing here excludes
  any category of finding from being fixed, and there is no post-FIX
  assertion/verification step of any kind — RE-REVIEW starts immediately
  after FIX's output. No concept of a finding the fixer is forbidden from
  touching exists today.
- **converge-and-pipeline.md**: CONVERGE decision rule today is binary at the
  top: clean round → done (`status: converged`); dirty round → loop back to
  SPAWN. Separately, a 3-strikes no-progress circuit-breaker can end the run
  early (`status: circuit_broken`), and a hard cap exists at round 8. There
  is no third terminal condition and no concept of "clean per axis but still
  can't converge."
- **dual-mode-contract.md**: two modes selected once at invocation.
  Human-interactive mode's final report template has a `## Convergence`
  section listing `Status: converged | circuit_broken`. `mode:agent` emits
  one JSON blob with top-level `"status": "converged | circuit_broken |
  error"`. The findings array in that JSON has no per-finding sovereignty
  field. The documented `foundry.yaml` wiring example greps for
  `circuit_broken`/`error` to decide gate failure — any other status
  (including a future `escalated`) already passes through as non-failing by
  default, but this is incidental, not documented.
- **merge-and-validate.md**: MERGE fingerprints by `(file_path, line_bucket
  ±3, normalized_title)`, applies confidence anchors (0/25/50/75/100), bumps
  confidence on 2+ seat agreement, requires quote-the-line evidence. Step 5
  ("Emit the merged list") lists the fields each finding carries forward but
  has no mention of a sovereignty marker (doesn't exist yet). VALIDATE
  assigns 1 validator per finding (2-3 for Critical) from a seat that isn't
  the original finder, and produces a majority-survives-challenge verdict —
  doesn't alter severity or metadata fields.
- **formats/DATA-MODEL-FORMAT.md** (already implemented, Phase 2a): defines
  Entities & relationships / Invariants / Ownership & routing / Agent
  boundary / Change log. Its own "Cross-system contract" section already
  names this exact seat: *"The data-steward seat and the data-layer guard
  hook enforce this file the same way regardless of which system produced
  the diff"* — confirming this file was authored anticipating scc-bqp.
  "Lazy creation" section: DATA-MODEL.md is created only once the first
  entity/invariant/boundary decision is resolved, so its absence in a repo
  that nonetheless has schema/migration files is an expected, not
  exceptional, state.
- **tests/fixtures/orders-schema/**: existing DATA-MODEL.md fixture (Order /
  Line Item / Shipment) with two convention-only Agent-boundary entries
  (line_items immutable once placed; orders read-only to order service after
  delivery) — a ready-made target for AC2 (Agent-boundary violation). Its
  `README.md` references a `schema.sql` in this fixture directory (not
  independently read but referenced) — a candidate base to derive a
  destructive-migration diff for AC1.
- **grill-with-docs/SKILL.md**: precedent for how a skill/finding references
  a sibling capability that may not be installed: "Offer the plan-security
  pass when build-ready" section treats `security-suite`'s
  `plan-security-review` as "a documentation pointer, not a new mechanism,"
  and requires saying explicitly if the sibling isn't installed rather than
  silently skipping. `bd show scc-b56` confirms grill-the-schema (the
  AC5-referenced skill) is still OPEN/unimplemented and is not a `bd`
  dependency of scc-bqp — same soft-reference pattern applies.
- **contracts/verification-before-completion.md**: generic "evidence before
  claims" discipline already referenced by fix-and-rereview.md's FIX Output
  section. Confirmed by reading it in full — it's about the fixer's own
  claims of success, not a mechanical file-level assertion. It does not need
  editing; the new post-FIX assertion step is a distinct, orchestrator-
  performed structural check, independent of what the fixer self-reports.

## Required changes

Mapped to the task's "New Seat Entry / Cast-When / Model Tier / Skill
Procedure / Sovereignty Escalation / Orchestrator Handling" sections and the
5 acceptance criteria.

### 1. `skills/data-steward/SKILL.md` (new)

Modeled directly on `domain-modeling/SKILL.md`'s shape:
- Frontmatter: `name`, `description` (mentioning migrations/ORM/schema/
  serialization triggers so CAST's judgment pass can match it), `argument-hint`,
  `allowed-tools: Read, Grep` (read-only, per task's explicit "like
  domain-modeling").
- "When to Apply": restate the fail-closed cast-when list from the task
  (migration files, ORM/model definitions, schema files incl. `*.sql`,
  `schema.*`, `prisma/`, `alembic/`, `migrations/`; serialization formats;
  any file DATA-MODEL.md maps an entity to).
- "How to Review": two-step procedure — (1) check diff against
  DATA-MODEL.md's Invariants and Agent boundary sections if the file exists;
  (2) check against the 7-item migration-safety checklist (reversibility/
  down-path, expand→migrate→contract sequencing, backfill strategy/volume,
  lock behavior, index-creation strategy, nullable-then-tighten, dual-write
  windows) — each must be named explicitly enough that a Critical finding
  can cite the specific principle violated (AC1 requires "migration-safety
  principle named").
- "Output Contract": standard Critical/Important/Minor + file:line + why/how
  shape (matches `contracts/reviewer-output.md`'s Issue shape, documented
  locally rather than by editing that shared file — same pattern
  domain-modeling uses), PLUS the sovereignty extension: an optional
  `sovereignty: human-required` marker set when (a) the diff crosses a
  DATA-MODEL.md Agent-boundary entry, or (b) DATA-MODEL.md is absent while
  the diff changes schema semantics.
- Missing-DATA-MODEL.md handling: still casts (the file-pattern triggers
  don't depend on DATA-MODEL.md existing), and must emit a sovereignty
  finding recommending the user run `grill-the-schema`
  (`skills/grill-the-schema/SKILL.md`, scc-b56) — phrased as a documentation
  pointer per the `grill-with-docs` precedent, since that skill doesn't
  exist yet (scc-b56 is open, not a `bd` dependency of this task).

### 2. `reviewers/persona-catalog.md`

- New entry under "## Risk-Triggered Seats" (after Test-Design Quality,
  before "## Excluded from Individual Casting"): Casts / Cast-when (the
  fail-closed list above) / Model tier: **top-tier**, with an explicit
  deviation justification since risk-triggered seats default to mid-tier —
  migration/schema mistakes are high-blast-radius and hard-to-reverse
  (data loss/corruption), same class of asymmetric-cost judgment the catalog
  already uses to justify top-tier for Security / Fresh-Eyes / Correctness.
- Notes: read-only; sovereignty marker behavior; missing-DATA-MODEL.md
  fallback recommending grill-the-schema (name it explicitly as
  not-yet-implemented, coverage-honesty style, mirroring the Security seat's
  missing-plugin fallback template).
- Add a new row to the closing Seat Summary Table.

### 3. `skills/review-panel/references/fix-and-rereview.md`

- Extend the "Fixer dispatch contract" list in the FIX section: sovereignty-
  marked findings are never handed to the fixer as fixable work — the fixer
  must be told explicitly which target file(s) it must not modify at all
  (derived from each sovereignty-marked finding's `file_path`).
- New subsection after FIX's "Output" and before "## RE-REVIEW" — e.g.
  "### Sovereignty guard (post-FIX assertion)": orchestrator (not the
  fixer) captures a pre-FIX content hash (e.g. `git hash-object <file>`) of
  every sovereignty-marked finding's target file before dispatching the
  fixer, then re-hashes after FIX returns. Any mismatch fails the round
  loudly with an explicit sovereignty-violation message naming the finding
  and file — this is independent of the fixer's own self-reported
  fixed/skipped claims (AC3 requires this to catch the fixer's underlying
  model touching the file "anyway," i.e. despite instructions — a
  self-report-only check would not satisfy this).
- Note explicitly (per the task's own Key Constraints) that this R2
  mechanical check is a different concern from CONVERGE's `escalated`
  status (OQ4): R2 catches FIX violating a hard rule it was never allowed to
  break; `escalated` is the legitimate, expected outcome when sovereignty
  findings simply remain unresolved by design.

### 4. `skills/review-panel/references/converge-and-pipeline.md`

- Insert a sovereignty check ahead of (or alongside) the existing
  clean/dirty decision rule: even when RE-REVIEW's regression and coherence
  axes are otherwise clean, CONVERGE cannot emit `status: converged` while
  any sovereignty-marked finding remains unresolved (which, by construction,
  all of them do — FIX is barred from touching them). This is a **new
  terminal state**, not a loop condition — looping back to SPAWN again would
  not resolve a sovereignty finding, since it's designed to never be
  auto-fixed.
- New terminal status `escalated`, sitting alongside `converged` /
  `circuit_broken` (and distinct from the FIX-stage `error` used for R2
  violations — see Risks).
- Clarify interaction with the existing 3-strikes circuit-breaker: unresolved
  sovereignty findings must NOT count toward "no progress" strikes (they are
  expected to stay unresolved), otherwise every sovereignty case would
  eventually mis-report as `circuit_broken` instead of `escalated`.

### 5. `skills/review-panel/references/dual-mode-contract.md`

- Human-interactive mode: extend the `## Convergence` report section to
  cover `escalated` — an explicit human sign-off request block naming each
  unresolved sovereignty finding, its file, and why it wasn't auto-fixed.
- `mode:agent` JSON contract: extend `"status"` enum to
  `"converged | circuit_broken | error | escalated"`; add a per-finding
  `sovereignty` field (`"human-required"` or absent/null) to the `findings`
  array schema.
- "Wiring to foundry" section: update prose and the example gate script to
  state explicitly that `escalated` must NOT cause gate failure (OQ4) —
  unattended/Foundry automation stays unattended by default; the gate's only
  job is to make the flag impossible to miss (surfaced in the PR description
  and the final `mode:agent` JSON output), never to block or park the run.

### 6. `skills/review-panel/references/merge-and-validate.md`

- Step 5 ("Emit the merged list"): note that the `sovereignty` marker
  travels with a finding through fingerprinting/dedup untouched — it is not
  part of the fingerprint key `(file_path, line_bucket, normalized_title)`,
  but if two+ seats agree on a finding that any one of them marked
  sovereignty-required, the merged finding keeps the marker. VALIDATE
  doesn't strip or reinterpret it (validators judge survives-challenge
  correctness, not metadata).

## Risks / open questions / dependencies

1. **Path discrepancy**: `.pas/current_task.md`'s "Files to Edit" list uses
   paths relative to `plugins/review-panel/` (e.g.
   `skills/review-panel/references/fix-and-rereview.md`,
   `references/converge-and-pipeline.md`). Confirmed via `find` that actual
   repo paths need the `plugins/review-panel/` prefix. Use the corrected
   paths above during Plan/Implement.
2. **Soft dependency on unimplemented scc-b56 (grill-the-schema)**: AC5
   requires the missing-DATA-MODEL.md finding to "recommend grill-the-schema."
   `bd show scc-b56` confirms it's open, not yet built, and not in scc-bqp's
   `bd` DEPENDS ON list. Per the `grill-with-docs` precedent, this must be
   phrased as a documentation pointer with an explicit "not installed yet"
   caveat, not a hard invocation — do not block this task on scc-b56.
3. **`escalated` vs. R2's `error`/loud-failure — needs a Plan-stage
   decision**: the task's Key Constraints explicitly separate two concerns:
   (a) OQ4 — legitimate, expected sovereignty findings that must produce a
   non-blocking `escalated` status; (b) R2 — the fixer actually violating the
   sovereignty boundary, which must "fail the round loudly." These should
   not collapse into the same status. Recommendation to validate at Plan
   time: reuse the existing `error` status for the R2 violation (a violation
   of the orchestrator's own hard contract, closer to today's narrow
   definition of "a run that failed to execute correctly" than to a normal
   code-quality outcome), and reserve the new `escalated` status solely for
   OQ4's legitimate-and-expected case. This keeps the JSON status enum at 4
   values instead of 5 and avoids overloading `escalated`'s "never blocks
   automation" guarantee with what is actually a bug/violation that SHOULD
   surface loudly (possibly even as a failing gate, unlike `escalated`).
4. **Scope discipline**: the task's own R1 explicitly places the data-layer
   guard hook (Phase 2d, scc-4rj) out of scope — do not touch anything
   related to a pre-commit/pre-write hook; scc-bqp is unattended enforcement
   entirely via the review-panel pipeline (per R1: "this is the sole
   mechanism for unattended sovereignty enforcement").
5. **`contracts/reviewer-output.md` intentionally left unedited**: the task's
   explicit Files-to-Edit list omits it, and the domain-modeling precedent
   shows extensions to the shared finding shape are documented locally in
   the seat's own SKILL.md rather than by editing the shared contract file.
   Confirmed this reading by inspecting `contracts/reviewer-output.md` and
   `domain-modeling/SKILL.md` side by side — recommend following the same
   pattern for the sovereignty marker.
6. **Fixture/test coverage is not explicitly listed as a file to edit but is
   necessary to actually demonstrate the 5 acceptance criteria** — the
   `tests/PRESSURE-TEST.md` convention (live nested-Task dispatch + hand-worked
   MERGE tables + written walkthroughs for things too expensive to run live,
   e.g. the circuit-breaker) is the established precedent for how this
   plugin proves behavior, since it has no executable test suite. Plan should
   decide whether to extend `tests/fixtures/orders-schema/` (already has a
   matching Agent-boundary fixture for AC2) with a destructive-migration diff
   fixture for AC1, or build a new fixture directory.
7. **Model-tier deviation must be justified in prose**, not just declared,
   per persona-catalog.md's own stated convention ("mid-tier for the rest
   unless a specific seat's entry explains a deviation") — already accounted
   for in Required Changes #2 above.
