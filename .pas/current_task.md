# Current Task: scc-3x5

## Phase 3b — grill-my-taste skill (choice-based preference elicitation)

### Task ID
scc-3x5

### Status
in_progress (claimed 2026-07-18)

### Priority
P2

### Summary
New grill-family skill that elicits taste via forced choices between realistic alternatives rather than introspective questions, distilling each choice into a candidate rule written to TASTE.md. Includes an evidence-mining mode that mines repo/PR history for places the human rewrote agent or contributor output.

### Description
New grill-family skill that elicits taste via forced choices between realistic alternatives rather than introspective questions, distilling each choice into a candidate rule written to TASTE.md. Includes an evidence-mining mode that mines repo/PR history for places the human rewrote agent or contributor output.

### Design Details

#### Deliverable
New file: `plugins/review-panel/skills/grill-my-taste/SKILL.md`

#### Grill-Family Mechanics

**Elicitation is choice-based, not introspective:**
- Present pairs of realistic alternatives (two API shapes, two error-message styles, two module layouts — generated from the user's actual codebase where available)
- User picks
- Agent asks why
- Distills a candidate rule
- Confirms wording
- Writes to TASTE.md inline

**Evidence mining mode:**
- When pointed at a repo/PR history, find places the human rewrote agent or contributor output
- Turn each rewrite into a forced-choice question (before vs after)

### Files to Create
- `plugins/review-panel/skills/grill-my-taste/SKILL.md` — grill-family mechanics specification

### Acceptance Criteria

A grill-my-taste session of >=5 forced choices produces a TASTE.md where every preference has rule + rationale + strength + provenance.

**PASS/FAIL**: All fields (rule, rationale, strength, provenance) present for all preference entries.

### Dependencies
- Depends on: ✓ scc-cnx (Phase 3a — TASTE.md format)
- Blocks: scc-da0 (Phase 3c — taste feedback loop)
- Blocks: scc-5hy (Phase 4 — variant-explorer plugin)

### Key Constraints
- This is Phase 3b (second Phase 3 task) in the strict Phase 1 → 2 → 3 → 4 → 5 build order
- Phase 3a (TASTE-FORMAT.md) is now complete; Phase 3b is the next sequential task
- Depends on TASTE-FORMAT.md for target sections
- The --distill mode used in 3c is a mode of this same skill, not a separate skill
- Human-owned artifact (Invariant 5) — the TASTE.md file is human-owned, agents produce it via interview

### Phase
Phase 3b of the Two-System Architecture (Phase 1 → 2 → 3 → 4 → 5 build order)

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
- Phase 3b (scc-3x5): grill-my-taste skill — THIS TASK
