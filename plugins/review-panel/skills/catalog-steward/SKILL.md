---
name: catalog-steward
description: Maintains plugins/review-panel/reviewers/persona-catalog.md over time — finds coverage holes and evaluates candidate skills for catalog inclusion. Advisory only; never auto-edits the catalog. Not a per-diff review lens; do not cast this as a review-panel seat.
---

# Catalog Steward

Periodic maintenance skill for `plugins/review-panel/reviewers/persona-catalog.md`, invoked by the
`catalog-audit` foundry schedule or manually — not a per-diff reviewer, and never cast as a
review-panel seat. `persona-catalog.md` is human-owned, the same posture `data-steward` takes
toward `DATA-MODEL.md` and `taste-review` takes toward `TASTE.md`: this skill drafts proposed
edits and a human applies them.

This SKILL.md documents **Procedure A (hole-finding)** only. **Procedure B (new-skill
evaluation)** is a separate, not-yet-built follow-up (tracked as scc-6lj.3) — it is not documented
here rather than silently omitted without explanation.

## Procedure A: Hole-finding

1. Run `uv run python scripts/catalog_seat_audit.py --out <tmp>/report.md`.
2. Check whether the report was actually written before proceeding — see "Script failure" below.
   If it was, read `<tmp>/report.md` as the sole input. Do not separately re-read the raw catalog
   or skill directory contents to re-derive facts the script already computed mechanically.
3. For each finding in the report, translate it into a concrete proposed edit:
   - **`undocumented`** → propose either a new Seat Summary Table row (if the skill looks like a
     diff-scoped review lens) or a new Excluded-section bullet with reasoning (if it looks like a
     construction/build tool, matching the existing `grill-with-docs`/`improve-codebase-architecture`
     pattern).
   - **`missing_target`** → propose either updating the seat's path (search
     `plugins/review-panel/skills/` for a plausible rename target) or removing the seat entry if
     the skill is genuinely gone.
   - **`lens_drift_added` / `lens_drift_removed`** → propose an update to the Excluded section's
     lens list to match `design-review`'s actual funnel.
4. Write the proposed edits to a new output artifact, e.g. `catalog-steward-proposal-<date>.md`
   (a unified diff or a clearly labeled before/after snippet per finding).
5. **Never write to `persona-catalog.md` directly.** This procedure is advisory only — a human
   reviews the proposal artifact and applies whichever edits they accept.

### Zero findings

If the report shows no findings (script exits 0, prints `OK: catalog is clean`, and every report
section renders `(none)`), still produce a proposal artifact — one that states plainly no changes
are needed. Do not skip writing an artifact and do not leave it empty or missing.

### Script failure

`scripts/catalog_seat_audit.py` exits 1 both when findings are present *and* on a hard failure
(e.g. a missing `--catalog`/`--design-review` file or a missing `--skills-dir` directory) — exit
code alone cannot distinguish the two. Detect a hard failure by checking whether `--out` was
actually written (a hard failure calls `fail()` and exits before the report is written) or whether
stdout starts with `FAIL:`. If the report file is absent, **stop and surface the script's `FAIL:`
message** rather than treating it as "0 findings" or writing an empty/fabricated proposal.

## Sub-agent dispatch

Procedure A does **not** dispatch sub-agents: the corpus is one bounded report file, read once, in
the same context. This is a deliberate design choice — small, bounded, single-shot, no
checkpoint/resume machinery — not an oversight, per the PRD's explicit non-goal of over-building
this skill into a full orchestrator. Per SPEC FR-10, `scripts/verify_orchestration_contracts.py`'s
`COMPONENTS` registration is conditional on sub-agent dispatch, so no registration is required for
Procedure A.

## Output Contract

The proposal artifact has one entry per finding: the finding's kind and subject, a concrete
before/after snippet or unified diff for the proposed edit, and a short rationale. If there are no
findings, the artifact says so explicitly instead of being empty.

## Limitations
- Use this skill only for periodic catalog maintenance, not as a per-diff review lens.
- Procedure B (new-skill evaluation) is not yet implemented — do not attempt it with this
  SKILL.md.
- Never writes to `persona-catalog.md` directly; a human must review and apply the proposal.
- Stop and ask for clarification if a finding's proposed edit type (new seat row vs. Excluded-section
  bullet, path update vs. removal) is ambiguous rather than guessing.
