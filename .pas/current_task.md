# Current Task: scc-f9k

## Phase 2a — DATA-MODEL.md format (shared contract)

### Task ID
scc-f9k

### Status
IN_PROGRESS

### Summary
Define the shared format for DATA-MODEL.md, sibling of CONTEXT-FORMAT.md, establishing it as the implementation-detail record for data — in explicit contrast to CONTEXT.md, which is a glossary that forbids implementation detail. This format is the foundation the grill-the-schema skill (2b), the data-steward seat (2c), and the data-layer guard hook (2d) all read from or write to.

### Description
New file: `plugins/review-panel/formats/DATA-MODEL-FORMAT.md`

**Required Sections:**
- Entities & relationships (with storage mapping)
- Invariants (what must never be violated)
- Ownership & routing (which system writes what)
- Agent boundary (decisions agents may not revisit without escalation)
- Change log (dated, human-initialed)

**Key Requirements:**
- **Explicit contrast with CONTEXT.md**: must be documented in the format file. CONTEXT.md is a glossary and forbids implementation detail; DATA-MODEL.md is exactly the implementation-detail record for data. Cross-link both files' formats to each other with this distinction.
- **Cross-system contract declaration**: Explicitly declare DATA-MODEL.md as a cross-system contract: System 2 fixes (migrations in a library upgrade, IaC data-store changes) are bound by it identically to System 1 changes.

### Design Notes
This format establishes the contract that three downstream tasks depend on:
- grill-the-schema skill (2b) uses it to elicit schema details from the human
- data-steward seat (2c) uses it to block/escalate sovereignty violations
- data-layer guard hook (2d) uses it to enforce integrity across upgrades

Invariant 5 (human artifacts are human-owned) applies: DATA-MODEL.md is written through grilling sessions with the human; agents may propose edits but FIX never auto-modifies it (enforced mechanically in task 2c via the post-FIX assertion step).

### Acceptance Criteria
Grilling session on a fixture repo with an orders schema produces a DATA-MODEL.md containing at least entities, one invariant, and an Agent boundary section. PASS/FAIL: file exists with all required sections (verified indirectly via task 2b's grilling flow, but the format itself must define and require these sections).

### Blocking
- scc-bqp (Phase 2c — data-steward seat)
- scc-b56 (Phase 2b — grill-the-schema skill)
- scc-4rj (Phase 2d — Data-layer guard hook)

### Files to Create/Modify
- `plugins/review-panel/formats/DATA-MODEL-FORMAT.md` (new)
- Cross-link to CONTEXT-FORMAT.md with explicit contrast

### Applicable Invariants
- Invariant 5: Human artifacts are human-owned (grilled, never auto-modified)
