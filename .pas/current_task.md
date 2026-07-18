# Current Task: scc-b56

## Phase 2b — grill-the-schema skill (planning-stage DATA-MODEL.md interview)

### Task ID
scc-b56

### Status
in_progress

### Priority
P2

### Summary
Create a new planning-stage skill (`grill-the-schema`) that interviews the human to build DATA-MODEL.md. This skill mirrors the existing `grill-with-docs` skill but targets DATA-MODEL.md instead of CONTEXT.md, covering entities, invariants, lifecycle decisions (soft-delete? audit? retention?), volume/access patterns, and boundaries.

### Description
New planning-stage skill, modeled on grill-with-docs, that interviews the human to build DATA-MODEL.md instead of CONTEXT.md — covering entities, invariants, lifecycle (soft-delete? audit? retention?), volume/access patterns, and boundaries.

### Design Details

#### Mechanics
- Mirror grill-with-docs: one question at a time, recommended answers, explore the codebase instead of asking when possible, update artifacts inline
- Target DATA-MODEL.md (from Phase 2a) instead of CONTEXT.md
- Interview topics: entities, invariants, lifecycle (soft-delete? audit? retention?), volume/access patterns, and boundaries
- Stress-test with concrete scenarios
- Cross-reference actual schema/migration files for contradictions
- Create DATA-MODEL.md lazily on first resolved decision

#### ADR Gate
- ADR offers follow the same 3-part gate as grill-with-docs (hard to reverse, surprising, real trade-off)
- Schema decisions frequently clear this gate

#### Invariant 5 Compliance
- This skill proposes/drafts but the resulting file is a human-owned artifact produced through the grilling conversation, not silently generated
- Agents may propose edits but FIX never auto-modifies DATA-MODEL.md

### Files to Create
- `plugins/review-panel/skills/grill-the-schema/SKILL.md` — new skill definition file (modeled on existing grill-with-docs)

### Acceptance Criteria

1. **Grilling session produces complete DATA-MODEL.md**: Grilling session on a fixture repo with an orders schema produces a DATA-MODEL.md containing at least:
   - Entities section
   - One invariant
   - An Agent boundary section
   - PASS/FAIL: file exists with all required sections

### Dependencies
- Depends on: ✓ scc-f9k (Phase 2a — DATA-MODEL.md format)
- Blocks: ← Phase 3 tasks (taste system), Phase 5 (triage spine plugin)

### Key Constraints
- Invariant 5 applies: human-owned artifacts must be produced through grilling conversation, not silently generated
- This is Phase 2b in the strict Phase 1 → 2 → 3 → 4 → 5 build order
- Phase 2 completion is blocking Phase 3 (taste system), Phase 4 (variants), and Phase 5 (triage)
- Skill should follow the same 3-part ADR gate as grill-with-docs (hard to reverse, surprising, real trade-off)

### Phase
Phase 2b of the Two-System Architecture (Phase 1 → 2 → 3 → 4 → 5 build order)

### Parent Epic
scc-hzj: Two-System Architecture — Security, Data Stewardship, Taste, Variants, and Triage Spine

### Related Work
- Phase 2a (scc-f9k): DATA-MODEL.md format specification — COMPLETE
- Phase 2c (scc-bqp): data-steward seat with sovereignty escalation — COMPLETE
- Phase 2d (scc-4rj): data-layer guard hook (next Phase 2 task after this one)
