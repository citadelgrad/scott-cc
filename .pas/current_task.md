# Current Task: scc-g12

## Phase 1b — Plan-security pass (planning-stage threat-model checkpoint)

### Task ID
scc-g12

### Status
IN_PROGRESS

### Summary
Add a lightweight threat-model pass at the end of planning, before build — the planning-stage counterpart of the review seat. This is not a comprehensive audit (that's the future Foundry suite); it's a checkpoint asking: trust boundaries crossed? new data flows? authn/authz surface changed? secrets introduced? third-party deps added?

### Description
New skill: `plugins/security-suite/skills/plan-security-review/SKILL.md`.

- **Input**: a plan/PRD/spec document (path or in-conversation).
- **Procedure**: extract security-relevant deltas → map to OWASP cheatsheet topics (reuse `security-advisor.md`'s topic table; WebFetch when online, degrade to built-in checklist when air-gapped) → emit findings as CLEAR/TRIGGERED/N/A lines (same vocabulary as domain-modeling, for future merge-ability) plus a one-paragraph go/no-go.
- **Explicit boundary** to document in the skill: 'Not for reviewing code diffs — that is the panel's security seat.'
- **Wire-in points** (documentation edits only, no new mechanism):
  - `plugins/review-panel/skills/grill-with-docs/SKILL.md`: add a closing step that offers the plan-security pass when the grilling session ends with a build-ready plan.
  - This spec's Phase 5 (Foundry section) lists it as a schedulable pre-build gate in `docs/foundry-recipes.md`.

### Design Notes
Distinct from the Phase 2c data-steward seat and the Phase 1a security seat — those operate on diffs at review time; this operates on plans at the end of planning. Keep the vocabulary (CLEAR/TRIGGERED/N/A) consistent with domain-modeling for future cross-tool merge-ability.

### Acceptance Criteria
1. **Auth-relevant plan**: Given a plan that adds a login endpoint, the pass TRIGGERs at least authn/session topics with cheatsheet citations. PASS/FAIL: triggered lines cite topic names.
2. **No security-relevant delta**: Given a plan with no security-relevant delta (pure UI copy change), output is all CLEAR/N/A with an explicit 'no security-relevant surface' statement — no forced findings. PASS/FAIL: zero TRIGGERED lines.
3. **Offline degradation**: Offline (no WebFetch): the pass completes using the built-in checklist and notes the degraded mode. PASS/FAIL: completion + explicit degradation note.

### Blocking
- This task blocks scc-tsa (Phase 5 — Triage spine plugin)

### Files to Create/Modify
- `plugins/security-suite/skills/plan-security-review/SKILL.md` (new)
- `plugins/review-panel/skills/grill-with-docs/SKILL.md` (wire-in documentation)
- `docs/foundry-recipes.md` (Phase 5 section reference)

### Applicable Invariants
- Invariant 3: Coverage honesty (findings reported explicitly)
- Invariant 5: Human artifacts (planning session is human-grilled)
