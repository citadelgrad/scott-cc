# Current Task: scc-d0u

## Verification & tooling gates (all phases)

### Task ID
scc-d0u

### Status
in_progress (started 2026-07-18)

### Priority
P2

### Summary
Cross-cutting quality-gate requirements that apply incrementally to every phase's plugin/manifest edits, not a one-time final task. Each phase's PR must pass plugin verification, include a seeded-defect fixture, and pass repo-standard lint/test gates before merging, with README/marketplace catalog counts kept in sync.

### Description
Cross-cutting quality-gate requirements that apply incrementally to every phase's plugin/manifest edits, not a one-time final task. Each phase's PR must pass plugin verification, include a seeded-defect fixture, and pass repo-standard lint/test gates before merging, with README/marketplace catalog counts kept in sync.

### Design Details

Apply scripts/verify_plugin.py, the PRESSURE-TEST.md fixture pattern, uv run pytest, and uv run ruff check --fix as merge gates on every phase PR (1a/1b, 2a-2d, 3a-3d, 4, 5) — not deferred to the end of the epic. Update README.md and the marketplace catalog's command/skill/agent counts as each phase adds new skills (plan-security-review, grill-the-schema, data-steward, taste-review, grill-my-taste, explore-variants, triage-spine, lib-upgrades, prod-errors) and new plugins (variant-explorer, triage).

This task documents a standing gate rather than a single unit of sequential work — treat it as re-run per phase PR, matching the pattern already established for review-panel's own PRESSURE-TEST.md fixtures. Failing to keep marketplace catalog counts in sync has caused version-sync bugs in this repo before (see commit 748dff1, 'fix(marketplace): sync review-panel catalog version to 0.2.0').

### Acceptance Criteria

1. **scripts/verify_plugin.py runs clean**: After each phase's plugin/manifest edits. PASS/FAIL per phase.
2. **Fixtures per phase**: Each phase adds at least one fixture under the owning plugin's tests/ following the review-panel/tests/PRESSURE-TEST.md pattern (seeded defect → expected finding). PASS/FAIL: fixture present per phase.
3. **Lint and test gates**: uv run pytest and uv run ruff check --fix gate every phase per repo rules (CLAUDE.md). PASS/FAIL: both commands clean.
4. **Catalog sync**: README.md / marketplace catalog counts are updated per phase since they enumerate commands/skills/agents explicitly. PASS/FAIL: counts match actual plugin contents after each phase merges.

### Dependencies
- Parent: scc-hzj (Two-System Architecture epic)
- Applies to all phases: 1a, 1b, 2a-2d, 3a-3d, 4, 5

### Key Constraints
- This is a standing gate (re-run per phase PR), not a one-time final task
- Applies to every phase PR merge
- Cross-phase quality assurance for the entire Two-System Architecture pipeline
- Must keep marketplace catalog counts in sync to prevent version-sync bugs

### Phase
Cross-cutting requirement for all phases (1-5) of the Two-System Architecture

### Parent Epic
scc-hzj: Two-System Architecture — Security, Data Stewardship, Taste, Variants, and Triage Spine

### Related Phases
- Phase 1a (scc-4xa): Security seat — COMPLETE
- Phase 1b (scc-g12): Plan-security pass — COMPLETE
- Phase 2a (scc-f9k): DATA-MODEL.md format — COMPLETE
- Phase 2b (scc-b56): grill-the-schema skill — COMPLETE
- Phase 2c (scc-bqp): data-steward seat — COMPLETE
- Phase 2d (scc-4rj): data-layer guard hook — COMPLETE
- Phase 3a (scc-cnx): TASTE.md format — COMPLETE
- Phase 3b (scc-3x5): grill-my-taste skill — COMPLETE
- Phase 3c (scc-da0): Taste feedback loop — COMPLETE
- Phase 3d (scc-4tt): Taste seat — COMPLETE
- Phase 4 (scc-5hy): variant-explorer plugin — READY
- Phase 5 (scc-tsa): Triage spine plugin — READY
