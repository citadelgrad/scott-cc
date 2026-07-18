# Current Task: scc-bqp

## Phase 2c — data-steward seat (review stage, blocking, with sovereignty escalation)

### Task ID
scc-bqp

### Status
in_progress

### Priority
P1

### Summary
New risk-triggered, read-only review seat (like domain-modeling) that checks diffs touching migrations, ORM/schema files, or serialization formats against DATA-MODEL.md's invariants and Agent boundary, plus a migration-safety checklist. Extends the reviewer-output contract with an optional sovereignty marker that FIX must never auto-resolve, mechanically enforced by a post-FIX assertion step.

### Description

#### New Seat Entry
- Add to `plugins/review-panel/reviewers/persona-catalog.md` under Risk-Triggered Seats
- Casts: new skill `plugins/review-panel/skills/data-steward/SKILL.md` (read-only, like domain-modeling)

#### Cast-When (fail-closed)
Triggered when diff touches:
- Migration files
- ORM/model definitions
- Schema files (*.sql, schema.*, prisma/, alembic/, migrations/, etc.)
- Serialization formats
- Any file DATA-MODEL.md maps an entity to

#### Model Tier
top-tier

#### Skill Procedure
1. Check the diff against DATA-MODEL.md (invariants, agent boundary)
2. Check against migration-safety checklist:
   - Reversibility/down-path
   - Expand→migrate→contract sequencing
   - Backfill strategy and volume
   - Lock behavior
   - Index-creation strategy
   - Nullable-then-tighten
   - Dual-write windows

#### Sovereignty Escalation (Contract Extension)
Findings keep the standard Critical/Important/Minor shape, plus optional marker `sovereignty: human-required` when:
- Diff crosses the Agent boundary section of DATA-MODEL.md
- DATA-MODEL.md is absent while the diff changes schema semantics

#### Orchestrator Handling
**FIX stage**: Never auto-fixes sovereignty-marked findings (R2, mechanically enforced)
- Add post-FIX assertion step checking every sovereignty-marked finding's target file
- Fails the round loudly if file changed anyway (rather than proceeding silently)
- Lives alongside FIX stage in `fix-and-rereview.md`

**CONVERGE**: Cannot report clean round while unresolved sovereignty findings exist
- Interactive mode: explicit human sign-off request
- mode:agent: emits top-level status `escalated` (extends converged|circuit_broken|error status)

**Unattended consumption (OQ4)**: `escalated` must never block/park consuming automation (Phase 5 Foundry gate)
- Unattended runs stay unattended by default
- Gate's job is to make flag impossible to miss (surfaced in PR description + final mode:agent output)
- Data-layer guard hook (2d) out of scope per R1

#### Files to Edit
- `skills/review-panel/references/fix-and-rereview.md`
- `references/converge-and-pipeline.md`
- `references/dual-mode-contract.md`
- `references/merge-and-validate.md` (marker passes through dedupe untouched)

### Acceptance Criteria

1. **Destructive migration test**: Panel run on diff adding destructive migration (drop column with data) yields data-steward finding at Critical with migration-safety principle named
   - PASS/FAIL: finding present, severity Critical

2. **Agent boundary violation test**: Panel run on diff violating DATA-MODEL.md Agent-boundary entry ends 'escalated' (agent mode) / explicit sign-off request (interactive); FIX did not modify the migration
   - PASS/FAIL: status + untouched file

3. **Fault injection test**: FIX's underlying model attempts to touch sovereignty-marked finding's target file anyway; post-FIX assertion step fails round loudly with explicit sovereignty-violation message
   - PASS/FAIL: round fails, message names violated finding

4. **Non-data-layer diff test**: Diff not touching data-layer paths; seat not cast
   - PASS/FAIL: absent from Cast

5. **Missing DATA-MODEL.md boundary test**: Repo with no DATA-MODEL.md at all; seat still casts on schema diffs and emits sovereignty finding recommending grill-the-schema
   - PASS/FAIL: finding present

### Dependencies
- Depends on: ✓ scc-f9k (Phase 2a — DATA-MODEL.md format)
- Blocks: ← scc-tsa (Phase 5 — Triage spine plugin)

### Key Constraints
- This is the sole mechanism for unattended sovereignty enforcement (per R1 — 2d hook no-ops unattended)
- Hard prerequisite for Phase 5 (R3: Phase 5 is blocked on Phase 2)
- No window where triage-produced migrations ship with no data-steward seat and no sovereignty escalation path
- R2 (mechanical post-FIX assertion) is different concern from OQ4 (giving humans room to judge legitimate escalation) — R2 catches FIX doing something it was never allowed to do at all

### Phase
Phase 2c of the Two-System Architecture (Phase 1 → 2 → 3 → 4 → 5 build order)

### Parent Epic
scc-hzj: Two-System Architecture — Security, Data Stewardship, Taste, Variants, and Triage Spine
