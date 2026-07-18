# Current Task: scc-cnx

## Phase 3a — TASTE.md format

### Task ID
scc-cnx

### Status
in_progress (claimed 2026-07-18)

### Priority
P2

### Summary
Define the shared format for TASTE.md, capturing personal, contested preference — explicitly distinct from universal quality (which belongs in the Ousterhout lens set / Karpathy guidelines, not here). This format underlies grill-my-taste (3b), the taste feedback loop / --distill mode (3c), and the taste review seat (3d).

### Description
Define the shared format for TASTE.md, capturing personal, contested preference — explicitly distinct from universal quality (which belongs in the Ousterhout lens set / Karpathy guidelines, not here). This format underlies grill-my-taste (3b), the taste feedback loop / --distill mode (3c), and the taste review seat (3d).

### Design Details

#### Deliverable
New file: `plugins/review-panel/formats/TASTE-FORMAT.md`

#### Required Sections
- **Preferences**: Each entry must have rule, rationale, strength (weak/strong/absolute), and provenance (which choice or override produced it)
- **Weightings**: Personal calibrations of universal principles (e.g., 'locality beats DRY')
- **Anti-preferences**: Patterns to flag even when defensible
- **Candidate rules**: Captured overrides awaiting distillation (see Phase 3c)
- **Scope note**: Clearly state that universal quality does NOT belong here (that is the Ousterhout lens set / Karpathy guidelines); only personal, contested preference belongs in TASTE.md

#### Design Rationale
- Invariant 5 (human artifacts are human-owned) applies directly — TASTE.md is a human-owned artifact
- Blocks Phase 3b, 3c, 3d, and Phase 4 (variant scoring reads TASTE.md)
- Depends on Phase 2a/2b for the DATA-MODEL.md format context

### Files to Create
- `plugins/review-panel/formats/TASTE-FORMAT.md` — the TASTE.md format specification

### Acceptance Criteria

A grill-my-taste session of >=5 forced choices produces a TASTE.md where every preference has rule + rationale + strength + provenance.

**PASS/FAIL**: All fields (rule, rationale, strength, provenance) present for all preference entries. This will be verified via task 3b's flow, but the format itself must define and require these fields.

### Dependencies
- Depends on: ✓ scc-f9k (Phase 2a — DATA-MODEL.md format)
- Depends on: ✓ scc-b56 (Phase 2b — grill-the-schema skill)
- Depends on: ✓ scc-4rj (Phase 2d — data-layer guard hook, Phase 2 completion)
- Blocks: scc-3x5 (Phase 3b — grill-my-taste skill)
- Blocks: scc-da0 (Phase 3c — taste feedback loop)
- Blocks: scc-4tt (Phase 3d — taste seat)
- Blocks: scc-5hy (Phase 4 — variant-explorer plugin)

### Key Constraints
- This is Phase 3a (first Phase 3 task) in the strict Phase 1 → 2 → 3 → 4 → 5 build order
- Phase 2 is now fully complete; Phase 3a is the next sequential task
- Must distinguish personal, contested preference from universal quality
- Human-owned artifact (Invariant 5) — agents may propose edits but must not auto-modify

### Phase
Phase 3a of the Two-System Architecture (Phase 1 → 2 → 3 → 4 → 5 build order)

### Parent Epic
scc-hzj: Two-System Architecture — Security, Data Stewardship, Taste, Variants, and Triage Spine

### Related Work
- Phase 1a (scc-4xa): Security seat — COMPLETE
- Phase 1b (scc-g12): Plan-security pass — COMPLETE
- Phase 2a (scc-f9k): DATA-MODEL.md format — COMPLETE
- Phase 2b (scc-b56): grill-the-schema skill — COMPLETE
- Phase 2c (scc-bqp): data-steward seat — COMPLETE
- Phase 2d (scc-4rj): data-layer guard hook — COMPLETE
- Phase 3a (scc-cnx): TASTE.md format — THIS TASK
