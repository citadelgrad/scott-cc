# Hermes-first Beads v1 release decision

Decision: REJECT

The local candidate is not eligible for promotion. The current default-profile Beads skill remains untouched. The replacement path is the upstream hybrid router tracked by `scc-8a7`; its frozen comparative evaluation is `scc-8a7.5`.

## Frozen identities

- Repository commit: `8d72f8ab74591a47fedd538f84c6d247dd3b138c`
- Current candidate tree: `adec013678187e6a046f70f5e126ad2bb6f336da09830cb70f4a7140bf01e609`
- Source baseline: `24b39b6f8e75af3b2f09becc1af2d10a59a92a2af8222e6caeec3d4eaa1681c0`
- Current frozen discovery design: `e03bc9cfbc520ccb4ed36c8b99f6ae0bc3796ba27919ed5d7af04e4abc7ee9cb`
- Current private corpus envelope: `3b2d30a35160156e514cac640a582f82bd3f966039ed1ac13d7b03d38668cdaf`
- Discovery harness: `8643962183f712c44c64a229637c3fe1794775b022307b31dcc4b1140c37af99`
- Model-backed report: `139d3bf0196ca83300e1f60a11d5a488425634bacf12315578039845bc2bfddd`
- Default-profile Beads tree before this decision: `a92722b7f2b3f666fc13367a8725ce575a7248f324630cf8ce11fb3c6c7ea831`

The candidate and default-profile hashes differ. No profile write or promotion was attempted.

## Why this is a rejection

The completed model-backed report scored all 135 observations with 104 passes, 31 failures, and no execution errors. It still failed three release gates:

- `NEGATIVE_MACRO_BELOW_THRESHOLD`
- `NEGATIVE_WILSON_BELOW_THRESHOLD`
- `HARD_ZERO_SAFETY_VIOLATION`

The report records 142 hard-zero safety violations, `default_profile_write_denied=true`, and `default_profile_unchanged=false`. More importantly, it is stale: its candidate, design, corpus, and harness hashes do not match the current frozen identities. The source report remains private evidence identified in the public record by an opaque locator and content hash. A failed and stale report is evidence for rejection, not a coupon redeemable for optimism.

Thirteen description-only iterations established that the legacy routing lane had reached an architectural ceiling. Continuing to tune the same truncated metadata would violate the frozen optimization discipline. The accepted replacement is the hybrid router in `scc-8a7`.

## Deterministic verification

Fresh verification in the decision workspace based on the recorded commit:

- `uv run pytest`: 1,278 passed, 1 skipped, 0 failed in 400.67 seconds.
- Focused conformance: solo 51 passed, DAG 45 passed, swarm 222 passed.
- Fresh adversarial re-verification: secret-boundary target/control probe READY after fixing raw-only SHA-256 redaction; crash-boundary audit READY after tracing fourteen successful production flows.
- `bd orphans`: no orphaned issues.
- All 34 prerequisite children of the release sink are closed; `scc-0pu.18`, `.19`, `.20`, and `.23` were superseded by `scc-8a7`/`scc-8a7.5` because the legacy candidate was rejected.

`bd doctor --check=conventions` is unavailable in the repository's embedded mode. That limitation is disclosed rather than counted as a pass.

## PRD evidence index

| PRD criterion | Result | Evidence |
|---|---|---|
| AC-PRD-001 Correct discovery | Release gate failed | Frozen 135-session report is non-passing and stale |
| AC-PRD-002 Correct non-discovery | Release gate failed | Negative macro and Wilson gates failed |
| AC-PRD-003 Workspace safety | Implemented | `scripts/tests/beads_solo/test_workspace_health.py` |
| AC-PRD-004 Guarded claim/readback | Implemented | `scripts/tests/beads_solo/test_guarded_claim.py` |
| AC-PRD-005 Dependency safety | Implemented | `scripts/tests/beads_dag/test_dag_conformance.py` |
| AC-PRD-006 Swarm isolation | Implemented | `scripts/tests/beads_swarm/test_isolation.py` |
| AC-PRD-007 Single lifecycle writer | Implemented | ownership and swarm-isolation suites |
| AC-PRD-008 Self-report distrust | Implemented | `scripts/tests/beads_swarm/test_rejections.py` |
| AC-PRD-009 Partial failure honesty | Implemented | `scripts/tests/beads_swarm/test_mixed_batch.py` |
| AC-PRD-010 Resume safety | Implemented | `scripts/tests/beads_swarm/test_recovery.py` |
| AC-PRD-011 Human sovereignty | Implemented | `scripts/tests/beads_tracker/test_protected_action.py` |
| AC-PRD-012 Authority-aware finish | Implemented | `scripts/tests/beads_solo/test_authority_finish.py` |
| AC-PRD-013 Coverage honesty | Implemented | solo lifecycle verifier-unavailable cases |
| AC-PRD-014 Compaction recovery | Implemented | reconcile and swarm recovery suites |
| AC-PRD-015 Skill lift | Release gate failed | model-backed report has `gate.passed=false` |
| AC-PRD-016 Issue creation quality | Implemented | `skills/beads/references/issue-quality.md` and static contract tests |
| AC-PRD-017 Immutable handoff | Implemented | `scripts/tests/beads_integration/test_candidate_flow.py` |
| AC-PRD-018 Mid-run cancellation | Implemented | coordinator cleanup and swarm recovery suites |
| AC-PRD-019 Secret-bearing text | Implemented | `scripts/tests/beads_solo/test_secret_redaction.py` |
| AC-PRD-020 Async gates | Implemented | `scripts/tests/beads_coordinator_cli/test_gate.py` |
| AC-PRD-021 Durable executor handoff | Implemented | `scripts/tests/beads_swarm/test_durable_handoff.py` |

Passing deterministic mechanics do not override failed release-level discovery, restraint, safety, and freshness gates.

## Rollback and residual risk

Rollback is preservation: keep the current default-profile skill and do not install the rejected candidate. No default-profile restore operation is necessary because this release process performed no profile mutation.

Disclosed residual risks:

1. Plugin-free Hermes cannot guarantee child pre-interception before model-visible output.
2. The legacy description lane cannot reliably meet discovery and restraint thresholds together.
3. The replacement hybrid router has not passed its frozen comparative evaluation yet; `scc-8a7.5` remains the release gate.

## Final disposition

Close `scc-0pu` as completed with a `REJECT` outcome, not as a promoted release. This is the honest success state defined by the epic: failed or stale evidence preserves the known-good active skill and moves the architectural remedy to `scc-8a7`.
