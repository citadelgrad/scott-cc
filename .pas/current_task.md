# Current Task: scc-tsa

## Phase 5 — Triage spine plugin (System 2 v1, Foundry-resident)

### Task ID
scc-tsa

### Status
in_progress (started 2026-07-18)

### Priority
P2

### Summary
New standalone plugin `plugins/triage/` implementing the triage loop: intake → reproduce → diagnose → fix → gate. Two v1 detectors (library upgrades, prod errors) with registry stubbed for three more. Every detector emits a normalized triage item that the spine turns into a bead, reproduces E2E, fixes via PAS, and gates through review-panel --mode=agent.

### Description
New standalone plugin `plugins/triage/`, kept separate from review-panel (invariant 2: dependency direction is triage → review-panel only, never the reverse). Implements the one loop — intake → reproduce → diagnose → fix → gate — with two v1 detectors (library upgrades, prod errors) and a detector registry stubbed for three more (system upgrades, IaC drift, security-advisory sweeps). Every detector emits a normalized triage item that the spine turns into a bead, reproduces E2E, fixes via PAS, and gates through review-panel --mode=agent.

### Design Details

Plugin layout:
```
plugins/triage/
├── .claude-plugin/plugin.json
├── skills/
│   ├── triage-spine/SKILL.md        # the one loop: intake → reproduce → diagnose → fix → gate
│   └── detectors/
│       ├── lib-upgrades/SKILL.md    # v1 detector
│       └── prod-errors/SKILL.md     # v1 detector (log/Sentry-shaped input)
└── docs/foundry-recipes.md          # schedule wiring for Foundry
```

**Spine contract:** Every detector emits a normalized triage item: `{source, severity, evidence, affected-paths, suggested-loop}` → spine files a bead (with AC per the acceptance-criteria rule), reproduces the issue E2E first (per CLAUDE.md's bug-fix rule), produces a fix diff via PAS, and gates it through review-panel --mode=agent.

**Status handling (resolved — OQ4):**
- **circuit_broken / error** — the loop itself failed; park the bead for the human.
- **escalated** — a sovereignty flag, not a loop failure. The gate must NOT block or park the run on this status; unattended runs stay unattended by default. The bead and its PR instead carry an unmissable 'sovereignty: human sign-off required' annotation, sourced from the panel finding detail, surfaced in both the PR description and the final mode:agent output.
- **converged** — reported ready-to-merge (auto-merge remains out of scope for v1).

**v1 detectors:** library upgrades (outdated/CVE-flagged deps from manifest scan) and prod errors (pointed at a log source; Sentry integration is a config detail, not a dependency). System upgrades, IaC drift, and security-advisory sweeps are registered in the detector registry as stubs — the registry design (one spine, five detectors) is the deliverable; filling all five is not.

**Foundry wiring:** `docs/foundry-recipes.md` documents scheduling each detector as a periodic Foundry check and the panel gate as the mandatory post-fix step. Also lists Phase 1b's plan-security pass and Phase 3c's distillation prompt as schedulable entries, consolidating 'what Foundry runs' in one place.

### Key Constraints

- Blocked on Phase 1 (security seat must exist before triage feeds it dependency diffs) and Phase 2 (data-steward seat + sovereignty escalation path must exist before triage-produced migrations/IaC diffs can ship). All dependencies now satisfied.
- Invariant 2 (dependency direction) is critical: review-panel must never import from, detect, or special-case triage — the reference direction is triage → review-panel only.

### Acceptance Criteria

1. **AC1 — Lib-upgrade detector fixture:** Lib-upgrade detector on a fixture repo with an outdated dep emits a valid triage item and the spine files a bead with AC. PASS/FAIL: bead exists, AC present, item validates against contract.

2. **AC2 — End-to-end status handling:** Detector → fix diff → mode:agent panel run returns JSON whose status is one of `converged | escalated | circuit_broken | error`; bead updated per the resolved status handling. PASS/FAIL: all four statuses produce their documented bead/PR outcome (fixtures may force each).

3. **AC3 — Escalated status handling:** Given a panel run returning escalated, the bead is not parked and the pipeline does not halt; the produced PR carries an explicit 'sovereignty: human sign-off required' annotation. PASS/FAIL: bead unparked, annotation present in PR body.

4. **AC4 — Prod-error detector with E2E reproduction:** Prod-error detector given a log line with a stack trace produces a triage item whose evidence includes the trace and whose spine run attempts E2E reproduction before any fix. PASS/FAIL: reproduction step precedes fix in the transcript/bead trail.

5. **AC5 — Contract validation:** Error state: detector output failing contract validation is rejected with a named field error; spine never processes a malformed item. PASS/FAIL: rejection path.

6. **AC6 — Boundary: zero findings:** Zero findings from a detector run → no beads filed, one-line 'clean' log, no panel invocation. PASS/FAIL: no side effects.

### Dependencies (all satisfied)
- ✓ scc-4xa: Phase 1a — Security seat in the review panel
- ✓ scc-g12: Phase 1b — Plan-security pass
- ✓ scc-bqp: Phase 2c — data-steward seat

### Parent Epic
scc-hzj: Two-System Architecture — Security, Data Stewardship, Taste, Variants, and Triage Spine

### Notes
This is the final (Phase 5) and only remaining task in the Two-System Architecture epic. All dependencies (Phases 1–2) are satisfied. Previous phases (3–4) are also complete. The triage spine completes the architecture by consolidating automated defect detection/triage and feeding fixes through review-panel for human verification before merge.
