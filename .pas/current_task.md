# Current Task: scc-da0

## Phase 3c — Taste feedback loop (capture + --distill)

### Task ID
scc-da0

### Status
in_progress (claimed 2026-07-18)

### Priority
P2

### Summary
Close the loop between human overrides/rejections during review and TASTE.md's Candidate rules section, plus a distillation mode that periodically promotes, merges, or rejects candidates with the human.

### Description
Close the loop between human overrides/rejections during review and TASTE.md's Candidate rules section, plus a distillation mode that periodically promotes, merges, or rejects candidates with the human.

### Design Details

#### Capture
Convention + bd remember — whenever the human overrides a panel finding or rejects agent output with a reason, record it as a taste candidate. This is documented in the skill; no new tooling is required in v1.

#### Distillation
A mode of grill-my-taste (--distill) that walks Candidate rules, promotes/merges/rejects each, and prunes stale preferences. Foundry-schedulable (e.g., monthly) as a prompt to run the session — the session itself stays interactive (human-owned artifact, invariant 5).

### Acceptance Criteria

--distill on a TASTE.md with >=3 candidate rules ends with zero remaining candidates (each promoted, merged, or rejected with the human). PASS/FAIL: Candidate section empty after session.

### Dependencies
- Depends on: ✓ scc-3x5 (Phase 3b — grill-my-taste skill)
- Depends on: ✓ scc-cnx (Phase 3a — TASTE.md format)
- Blocks: scc-5hy (Phase 4 — variant-explorer plugin)

### Key Constraints
- This is Phase 3c (third Phase 3 task) in the strict Phase 1 → 2 → 3 → 4 → 5 build order
- Phase 3a and 3b are now complete; Phase 3c is the next sequential task
- Foundry only schedules the *prompt* to run the session — the distillation conversation itself must remain interactive per invariant 5
- Human-owned artifact (Invariant 5) — TASTE.md is human-owned, maintained via interactive sessions

### Phase
Phase 3c of the Two-System Architecture (Phase 1 → 2 → 3 → 4 → 5 build order)

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
- Phase 3c (scc-da0): Taste feedback loop — THIS TASK
