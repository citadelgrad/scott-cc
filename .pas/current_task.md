# Current Task: scc-4tt

## Phase 3d — Taste seat (review stage)

### Task ID
scc-4tt

### Status
in_progress (started 2026-07-18)

### Priority
P2

### Summary
New risk-triggered, read-only, mid-tier review seat that applies TASTE.md as a review lens, citing specific clauses and mapping severity from each preference's declared strength.

### Description
New risk-triggered, read-only, mid-tier review seat that applies TASTE.md as a review lens, citing specific clauses and mapping severity from each preference's declared strength. The seat never casts if TASTE.md doesn't exist, and never produces Critical or sovereignty-marked findings.

### Design Details

#### Overview
New entry in persona-catalog.md under Risk-Triggered Seats:
- **Casts**: new read-only skill `plugins/review-panel/skills/taste-review/SKILL.md`
- **Cast-when**: TASTE.md exists in the target repo. (No TASTE.md → seat never casts; no generic fallback.)
- **Model tier**: mid-tier (applying a written preference file is procedural)
- **Findings**: cite the specific TASTE.md clause; severity mapped from the preference's strength:
  - absolute → Important+
  - strong → Important
  - weak → Minor
  - Taste findings are never Critical and never sovereignty-marked

### Acceptance Criteria

1. **Happy path**: Panel run on a diff violating a strong preference yields a taste finding citing the clause verbatim. PASS/FAIL: clause quoted in finding.
2. **No TASTE.md**: Repo without TASTE.md → taste seat absent from Cast; no taste findings. PASS/FAIL: absent.
3. **Error state**: Malformed TASTE.md (missing strength) — seat reports the file as unusable in Coverage Honesty rather than guessing. PASS/FAIL: explicit note.

### Dependencies
- Depends on: ✓ scc-cnx (Phase 3a — TASTE.md format)
- Blocks: ○ scc-5hy (Phase 4 — variant-explorer plugin)

### Key Constraints
- This is Phase 3d (fourth Phase 3 task) in the strict Phase 1 → 2 → 3 → 4 → 5 build order
- Depends on Phase 3a (TASTE-FORMAT.md) for the clause/strength fields it reads and cites
- Invariant 3 (coverage honesty) governs the malformed-file error state — report unusable, don't guess
- The seat never casts if TASTE.md doesn't exist (no generic fallback)
- Taste findings are never Critical and never sovereignty-marked

### Phase
Phase 3d of the Two-System Architecture (Phase 1 → 2 → 3 → 4 → 5 build order)

### Parent Epic
scc-hzj: Two-System Architecture — Security, Data Stewardship, Taste, Variants, and Triage Spine

### Related Work
- Phase 1a (scc-4xa): Security seat — COMPLETE
- Phase 1b (scc-g12): Plan-security pass — COMPLETE
- Phase 2a (scc-f9k): DATA-MODEL.md format — COMPLETE
- Phase 2b (scc-b56): grill-the-schema skill — COMPLETE
- Phase 2c (scc-bqp): data-steward seat — COMPLETE
- Phase 2d (scc-4rj): data-layer guard hook — COMPLETE
- Phase 3a (scc-cnx): TASTE.md format — COMPLETE
- Phase 3b (scc-3x5): grill-my-taste skill — COMPLETE
- Phase 3c (scc-da0): Taste feedback loop — COMPLETE
- Phase 3d (scc-4tt): Taste seat — THIS TASK
