# PRD: Epic B — Persona Catalog Maintenance Workflow

**Status:** Approved
**Author:** Claude (epic-planner agent)
**Created:** 2026-08-31
**Beads Epic:** `scc-6lj`

---

## Overview

`plugins/review-panel/reviewers/persona-catalog.md` is the curated, human-owned
manifest that the `review-panel` orchestrator uses to cast reviewer "seats"
against a diff. It was built as part of Epic A
(`docs/plans/2026-07-10-review-panel-plugin-plan.md`, closed 2026-07-10, all
14 children done). Epic A's plan explicitly deferred a second problem (plan
§8.4): keeping that catalog correct as the plugin's skill set changes over
time. A catalog that is accurate on day one drifts silently — skills get
added, renamed, or removed; other files the catalog depends on (like
design-review's lens funnel) change; nobody re-reads a 566-line manifest on a
schedule.

This feature builds a repeatable maintenance workflow for that catalog: a way
to find coverage holes, and a way to evaluate whether a new or external skill
belongs in the catalog. It is a maintenance tool, not a one-time audit.

**Proof this problem is live today:** research for this PRD cross-checked
every directory in `plugins/review-panel/skills/` (33 total) against the
catalog's seat table (14 seats) and its "Excluded from Individual Casting"
section (15 entries with reasons). Three skill directories —
`adr-skill`, `grill-my-taste`, `grill-the-schema` — are accounted for in
neither list; they are only mentioned in passing prose elsewhere in the file.
This is exactly the class of drift this feature exists to catch.

## Goals

1. Give a mechanical, repeatable way to find coverage gaps in
   `persona-catalog.md` (skills that should be catalogued as a seat or
   formally excluded, but are neither).
2. Give a mechanical, repeatable way to evaluate one candidate skill
   (internal or external) for catalog inclusion, producing a concrete
   recommendation.
3. Keep the workflow advisory: it proposes changes to the human-owned
   catalog file; it never edits the file automatically.
4. Ground the audit in a deterministic script (not pure LLM judgment) for
   the mechanically-checkable facts (does a catalogued seat's target skill
   still exist; does the Excluded section's design-review lens list still
   match design-review's actual content), following the same pattern
   already used in this file for the Data Steward seat's glob snapshot
   (`hooks/data_layer_guard.py` + sync test).
5. Make the workflow re-runnable on a schedule via `foundry.yaml` (the
   repo's mandated control layer for scheduled/CI-style automation), not
   as a one-off manual task.

### Non-Goals

- This is **not** a repeat of the `scc-jnb`/`scc-j2d` context-management/
  orchestration-architecture audit (`docs/reports/skill-context-architecture-audit.md`).
  That work checked 70 skills for context-safety risk. This feature checks
  one file's reviewer-coverage quality. No overlap in scope.
- This feature does not automatically edit `persona-catalog.md`. All output
  is a proposal for a human to apply.
- This feature does not evaluate more than one candidate skill per run of
  the new-skill-evaluation procedure. Batch evaluation of many candidates
  at once is out of scope.
- This feature does not add checkpoint/resume machinery. Both procedures
  are single-shot and small enough (one file, ~33 skill directories) that
  resumability would be unnecessary complexity.
- This feature does not decide the three Epic-A-adjacent backlog questions
  it may someday help evaluate (the superpowers-workflow-plugin decision,
  the ponytail-base-mode decision, the `ce-dogfood` seat addition). Those
  are filed as separate, sibling backlog issues, not part of this feature.

## User Stories

- **US-1:** As the repo maintainer, I want to run a catalog hole-finding
  check so that I can find skills that are undocumented in
  `persona-catalog.md` before they cause a missed review lens.
- **US-2:** As the repo maintainer, I want to run a catalog hole-finding
  check so that I can find catalogued seats whose target skill was renamed
  or removed, before `review-panel` fails to cast them at review time.
- **US-3:** As the repo maintainer, I want to evaluate one new or external
  skill against the catalog so that I get a concrete recommendation (new
  seat / add trigger / exclude with reason / reject) instead of having to
  manually re-derive the catalog's own conventions each time.
- **US-4:** As the repo maintainer, I want this check to run on a schedule
  without me remembering to trigger it, so that catalog drift is caught
  automatically over time.
- **US-5:** As the repo maintainer, I want the workflow's output to be a
  proposal, not an automatic edit, so that I retain control over the
  curated catalog file's content.

## Functional Requirements

- **FR-1:** A deterministic script, `scripts/catalog_seat_audit.py`, parses
  `persona-catalog.md`'s Seat Summary Table and Excluded-from-Individual-
  Casting section, and cross-checks the result against the real directory
  listing of `plugins/review-panel/skills/`. It reports, for every skill
  directory: catalogued as a seat, formally excluded with a reason, or
  **undocumented** (in neither list).
- **FR-2:** The same script verifies that every catalogued seat's stated
  skill path actually exists on disk, and flags any seat whose target is
  missing or renamed.
- **FR-3:** The same script cross-checks the Excluded section's list of
  design-review-subsumed lenses against the lens set actually referenced in
  `plugins/review-panel/skills/design-review/SKILL.md`, and flags any
  mismatch in either direction (a lens no longer in design-review's funnel,
  or a lens in the funnel not listed as subsumed).
- **FR-4:** The script emits a structured report (markdown with an embedded
  JSON summary block) to a file path passed as an argument, and exits
  non-zero if any finding is present (undocumented skill, missing seat
  target, or lens-list mismatch), so it can be used as a CI/foundry gate.
- **FR-5:** A new skill, `catalog-steward`, under
  `plugins/review-panel/skills/catalog-steward/`, implements the
  hole-finding procedure: it invokes `scripts/catalog_seat_audit.py`,
  reads its report as an artifact, and turns any findings into a proposed
  catalog diff (concrete suggested edits, not just a restatement of the
  script's raw findings) for a human to review and apply.
- **FR-6:** `catalog-steward` also implements a new-skill-evaluation
  procedure: given the path or name of exactly one candidate skill, it
  reads that skill's frontmatter/purpose, compares it against the
  catalog's existing seats and Excluded-section reasoning, and produces one
  of: a proposed new seat entry, a proposed new `cast-when` trigger on an
  existing seat, a proposed Excluded-section entry with reasoning, or a
  reject recommendation with reasoning.
- **FR-7:** Both `catalog-steward` procedures are read-only with respect to
  `plugins/review-panel/reviewers/persona-catalog.md` — they write their
  output to a separate report artifact, never editing the catalog file
  directly.
- **FR-8:** `scripts/tests/test_catalog_seat_audit.py` covers: a skill
  directory correctly identified as catalogued, correctly identified as
  excluded, correctly flagged as undocumented; a seat whose target path is
  missing is flagged; a design-review lens mismatch (added and removed) is
  flagged in both directions; a fully-consistent catalog produces zero
  findings and exit code 0.
- **FR-9:** A `foundry.yaml` profile (e.g. `catalog-audit`) runs
  `scripts/catalog_seat_audit.py` on a schedule (proposed: monthly cron)
  and is wired to `integrations.beads.on_needs_human: true` so that a
  non-zero exit (drift found) automatically files a beads issue rather
  than failing silently.
- **FR-10:** `catalog-steward` is registered as a component in
  `scripts/verify_orchestration_contracts.py`'s `COMPONENTS` tuple if (and
  only if) its implementation dispatches sub-agent reads; if it stays a
  single-shot, non-dispatching skill, this registration is not required
  and that decision should be stated explicitly in its SKILL.md.

## Success Criteria

- Running `scripts/catalog_seat_audit.py` against the current, unmodified
  `persona-catalog.md` correctly flags exactly the 3 known gaps found in
  research (`adr-skill`, `grill-my-taste`, `grill-the-schema`) and no
  false positives among the other 30 skill directories.
- `scripts/tests/test_catalog_seat_audit.py` passes under `uv run pytest`.
- `catalog-steward`'s hole-finding procedure, run against the current
  catalog, produces a proposed diff that a human can review and apply in
  under 10 minutes to close the 3 known gaps.
- `catalog-steward`'s new-skill-evaluation procedure, run against a
  deliberately-chosen test candidate skill, produces one of the four
  defined recommendation types with stated reasoning.
- The `foundry.yaml` catalog-audit profile runs successfully via
  `foundry run catalog-audit --dry-run` (or equivalent) without a live
  schedule needing to fire during review.
- No changes are made to `persona-catalog.md` by any part of this feature
  without a human applying a proposed diff.

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Feature scope creeps into a full context-safety audit (duplicating scc-jnb/scc-j2d) | Explicit non-goal stated above; scope is fixed to one file + one directory's frontmatter, not a repo-wide skill-content audit. |
| Excluded-section drift check produces false positives when design-review's funnel legitimately changes | Findings are advisory (flagged for human review), not auto-corrected; script never edits files. |
| Advisory-only output is generated but never acted on, letting drift persist anyway | `foundry.yaml` schedule + `beads.on_needs_human` wiring converts a silent report into a tracked, filed issue. |
| Over-building `catalog-steward` into a full orchestrator with checkpointing it doesn't need | Explicit non-goal stated above; FR-10 makes orchestrator registration conditional, not automatic. |
| New-skill-evaluation procedure's judgment calls (e.g., "should this be a new seat or a new trigger") are ambiguous | Procedure always produces one of four bounded recommendation types with stated reasoning, for a human to confirm — it does not silently auto-decide. |
