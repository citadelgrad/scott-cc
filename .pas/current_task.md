# Current Task: scc-4rj

## Phase 2d — Data-layer guard hook (interactive-only mechanical negation)

### Task ID
scc-4rj

### Status
in_progress (claimed 2026-07-18)

### Priority
P2

### Summary
New PreToolUse hook that warns-and-confirms when an Edit/Write/NotebookEdit targets data-layer paths without a corresponding DATA-MODEL.md change-log entry. Explicitly scoped to interactive/planning-time use only — it is a developer-loop convenience, not an enforcement mechanism, and must no-op in unattended contexts since a confirm prompt needs a human to answer it.

### Description
New PreToolUse hook that warns-and-confirms when an Edit/Write/NotebookEdit targets data-layer paths without a corresponding DATA-MODEL.md change-log entry. Explicitly scoped to interactive/planning-time use only — it is a developer-loop convenience, not an enforcement mechanism, and must no-op in unattended contexts since a confirm prompt needs a human to answer it.

### Design Details

#### Implementation
- **New file:** `hooks/data_layer_guard.py`, registered as a PreToolUse hook in `hooks/hooks.json` (core plugin, alongside `prefer_modern_tools.py`)
- **Behavior:** Intercept Edit/Write/NotebookEdit targeting data-layer paths
  - Default glob set: `**/migrations/**`, `**/models/**` (for known ORMs), `*.sql`, `**/schema.*`, `prisma/schema.prisma`, `**/alembic/**`
  - Overridable via `.data-guard.json` in repo root
- **On match:** warn-and-confirm (hook exit code prompting), with an allow flag once a DATA-MODEL.md change-log entry for the current work exists
- **CI behavior:** Never hard-fail CI — this is a developer-loop guard only

#### Scope (R1 — Resolved)
- Interactive/planning-time only, not an unattended enforcement point
- A warn-and-confirm hook needs a human to answer it, so it makes no sense as an enforcement mechanism for unattended PAS/Foundry runs
- The hook detects an unattended/no-TTY (or mode:agent) context and no-ops — documented behavior, not a silent accident
- Defers entirely to the data-steward review seat (2c) for sovereignty enforcement in unattended contexts

#### Design Rationale
- Makes the review seat's escalated status (2c) and Phase 5's Foundry consumption of it (OQ4) the sole mechanism for unattended sovereignty enforcement — not one of two
- Depends on 2a for the change-log entry format the hook checks for

### Files to Create
- `hooks/data_layer_guard.py` — the PreToolUse hook implementation
- Modify `hooks/hooks.json` — register the new hook (alongside prefer_modern_tools.py)

### Acceptance Criteria

1. **Interactive session without change-log entry:** An Edit to `migrations/0002_x.py` without a DATA-MODEL change-log entry triggers the confirm prompt.
   - PASS/FAIL: confirm prompt observed

2. **Interactive session with change-log entry:** The same edit after adding a DATA-MODEL.md change-log entry passes silently.
   - PASS/FAIL: no prompt triggered; edit proceeds

3. **Unattended/mode:agent context (R1):** The same Edit does not trigger a confirm prompt — the hook no-ops and the round proceeds to the data-steward review seat for enforcement instead.
   - PASS/FAIL: no prompt triggered; seat cast as normal on the resulting diff

### Dependencies
- Depends on: ✓ scc-f9k (Phase 2a — DATA-MODEL.md format, for change-log entry format)
- Related: scc-bqp (Phase 2c — data-steward seat with sovereignty escalation, unattended enforcement)

### Key Constraints
- This is Phase 2d (final Phase 2 task) in the strict Phase 1 → 2 → 3 → 4 → 5 build order
- Phase 2 completion is required before Phase 3, 4, and 5 can begin
- Must be interactive-only; unattended contexts must no-op, not prompt
- Hook exit code can prompt; never hard-fail CI

### Phase
Phase 2d of the Two-System Architecture (Phase 1 → 2 → 3 → 4 → 5 build order)

### Parent Epic
scc-hzj: Two-System Architecture — Security, Data Stewardship, Taste, Variants, and Triage Spine

### Related Work
- Phase 2a (scc-f9k): DATA-MODEL.md format specification — COMPLETE
- Phase 2b (scc-b56): grill-the-schema skill — COMPLETE
- Phase 2c (scc-bqp): data-steward seat with sovereignty escalation — COMPLETE
- Phase 2d (scc-4rj): data-layer guard hook — THIS TASK (FINAL PHASE 2)
