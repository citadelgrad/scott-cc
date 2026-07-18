# Current Task: scc-4xa

## Phase 1a — Security seat in the review panel (cast security-suite's security-engineer)

### Task ID
scc-4xa

### Status
IN_PROGRESS

### Summary
Rewrite the Security seat entry in `plugins/review-panel/reviewers/persona-catalog.md` to cast the existing `security-engineer` agent from `security-suite` directly, closing the documented gap that the catalog currently says is unfilled.

### Description
`plugins/review-panel/reviewers/persona-catalog.md` currently states 'No security-specific skill is vendored in this plugin' and makes the Security seat conditional on live-scan enrichment — but `plugins/security-suite/agents/security-engineer.md` already exists in this repo, diff-shaped for vulnerability assessment, threat modeling, and OWASP/CWE coverage. The catalog documents a gap that is already filled. Rewrite the Security seat entry to cast that agent directly, closing the gap without vendoring a duplicate skill into review-panel.

### Design Notes
- **Casts:** security-suite's security-engineer agent. Precedent exists — Fresh-Eyes casts agents/clean-room-alternative.md
- **Cast-when (risk-triggered, fail-closed):** diff touches auth, crypto, secrets, input validation at a trust boundary, deserialization, dependency manifests/lockfiles, IaC, or CI config
- **Model tier:** top-tier (unchanged from current conditional entry)
- **Missing-plugin fallback:** if security-suite is not installed, keep current behavior verbatim plus explicit coverage-gap note
- **No vendoring:** cross-plugin reference preferred; both plugins ship together in scott-cc
- **Output conformance:** must conform to Critical/Important/Minor + verdict shape in contracts/reviewer-output.md

### Acceptance Criteria
1. **With security-suite installed + dependency lockfile diff:** Panel run's Cast section lists the Security seat with a cast rationale. PASS/FAIL: seat present in Cast output
2. **Without security-suite + same diff:** Final report's Coverage Honesty section states no dedicated security seat was cast and why. PASS/FAIL: explicit gap statement present
3. **Docs-only diff:** Security seat is not cast. PASS/FAIL: seat absent from Cast output
4. **Security findings validation:** At least one seeded vulnerable-diff fixture produces validated security finding in MERGE. PASS/FAIL: finding appears with fingerprints and confidence anchors

### Blocking
- This is a hard prerequisite for Phase 5 (scc-tsa: Triage spine plugin)

### Files to Modify
- `plugins/review-panel/reviewers/persona-catalog.md`
- Possibly: `plugins/security-suite/agents/security-engineer.md` (conformance note if needed)

### Applicable Invariants
- Invariant 1: Substrate rule (diffs handed to review-panel)
- Invariant 3: Coverage honesty (every gap reported explicitly)
- Invariant 4: Graceful cross-plugin degradation (missing-plugin fallback)
