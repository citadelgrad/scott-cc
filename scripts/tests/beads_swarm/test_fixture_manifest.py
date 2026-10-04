"""Coverage and provenance checks for the executable T16 fixture corpus."""

from __future__ import annotations

import json
from pathlib import Path

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "beads_swarm"
EXPECTED_ACS = {f"AC-T16-{index:03d}" for index in range(1, 6)}
EXPECTED_FIXTURE_IDS = {
    "isolated-parent-owned-swarm",
    "untrusted-evidence-matrix",
    "mixed-batch-partial-success",
    "crash-resume-convergence",
    "durable-executor-handoff",
}
REQUIRED_REJECTION_CASES = {
    "child_tracker_mutation",
    "forged_result_identity",
    "stale_ownership_epoch",
    "missing_command_evidence",
    "cancelled_lane",
    "failed_lane_review",
    "failed_candidate_test",
    "candidate_conflict",
    "unknown_primary_result",
}
REQUIRED_CRASH_FLOWS = {
    "lane_freeze",
    "durable_handoff_launch",
    "direct_operation_close",
}
REQUIRED_NATIVE_IO_CRASH_POINTS = {
    (prefix, phase)
    for prefix in (
        ("git", "commit-tree"),
        ("git", "update-ref"),
        ("git", "reset", "--hard"),
    )
    for phase in ("before", "after")
}
REQUIRED_DURABLE_TAMPER_CASES = {
    "handoff_sha256",
    "executor_identity",
    "ownership_epoch",
    "artifact_sha256",
    "artifact_bytes",
    "artifact_path_escape",
    "beads_mutated",
}
COMMON_FIELDS = {
    "schema_version",
    "id",
    "acceptance_criteria",
    "timeout_seconds",
    "output_limit_bytes",
    "max_processes",
}
EXACT_FIELDS = {
    "isolated-parent-owned-swarm": COMMON_FIELDS
    | {"lanes", "deadline_probe", "ownership_contention"},
    "untrusted-evidence-matrix": COMMON_FIELDS | {"cases"},
    "mixed-batch-partial-success": COMMON_FIELDS
    | {"lanes", "expected_integrated", "expected_recoverable", "expected_close_status"},
    "crash-resume-convergence": COMMON_FIELDS
    | {
        "crash_flows",
        "native_io_crash_points",
        "expected_max_native_replays",
        "expected_terminal_states",
        "expected_resume_status",
        "expected_repeat_status",
        "recovery_scenarios",
    },
    "durable-executor-handoff": COMMON_FIELDS | {"executor", "tamper_cases"},
}


def test_fixture_corpus_covers_every_acceptance_criterion() -> None:
    paths = sorted(FIXTURES.glob("*.json"))
    assert paths, "the beads_swarm conformance corpus is missing"
    covered: set[str] = set()
    fixture_ids: set[str] = set()
    for path in paths:
        fixture = json.loads(path.read_text(encoding="utf-8"))
        covered.update(fixture["acceptance_criteria"])
        fixture_ids.add(fixture["id"])
        assert set(fixture) == EXACT_FIELDS[fixture["id"]]
        assert fixture["schema_version"] == "beads.swarm-fixture.v1"
        assert fixture["timeout_seconds"] <= 30
        assert 1 <= fixture["output_limit_bytes"] <= 65536
        assert 1 <= fixture["max_processes"] <= 4
        if "lanes" in fixture:
            assert fixture["max_processes"] == len(fixture["lanes"])
        if fixture["id"] == "isolated-parent-owned-swarm":
            assert fixture["max_processes"] >= 2
        assert len(fixture["acceptance_criteria"]) == 1
    assert covered == EXPECTED_ACS
    assert fixture_ids == EXPECTED_FIXTURE_IDS


def test_case_fixtures_declare_machine_checkable_verdicts() -> None:
    rejection = json.loads(
        (FIXTURES / "02_rejection_matrix.json").read_text(encoding="utf-8")
    )
    assert all(
        set(case) == {"id", "expected_error"} and case["id"] and case["expected_error"]
        for case in rejection["cases"]
    )
    assert {case["id"] for case in rejection["cases"]} == REQUIRED_REJECTION_CASES

    recovery = json.loads(
        (FIXTURES / "04_crash_resume.json").read_text(encoding="utf-8")
    )
    assert recovery["expected_resume_status"] in recovery["expected_terminal_states"]
    assert recovery["expected_repeat_status"] in recovery["expected_terminal_states"]
    assert {flow["id"] for flow in recovery["crash_flows"]} == REQUIRED_CRASH_FLOWS
    assert all(
        set(flow) == {"id", "scope", "boundary_selector", "crash_points"}
        and flow["scope"]
        and flow["boundary_selector"] in {"all", "after_handoff_", "after_operation_"}
        and flow["crash_points"]
        and all(
            set(point) == {"boundary", "occurrence"} for point in flow["crash_points"]
        )
        for flow in recovery["crash_flows"]
    )
    assert {
        (tuple(case["argv_prefix"]), case["phase"])
        for case in recovery["native_io_crash_points"]
    } == REQUIRED_NATIVE_IO_CRASH_POINTS
    assert {case["id"] for case in recovery["recovery_scenarios"]} == {
        "cancellation",
        "consecutive_roots",
        "unknown_late_child",
        "repeat_resume",
        "durable_handoff_result",
    }
    assert all(len(case) >= 2 for case in recovery["recovery_scenarios"])

    isolated = json.loads(
        (FIXTURES / "01_isolated_swarm.json").read_text(encoding="utf-8")
    )
    assert set(isolated["deadline_probe"]) == {
        "deadline_seconds",
        "elapsed_limit_seconds",
        "sleep_seconds",
        "output_flood_bytes",
    }
    assert len(isolated["deadline_probe"]["sleep_seconds"]) == isolated["max_processes"]
    assert set(isolated["ownership_contention"]) == {
        "issue_id",
        "first_actor",
        "second_actor",
        "expected_disposition",
    }
    assert all(
        set(lane) == {"issue_id", "path", "content"} for lane in isolated["lanes"]
    )

    mixed = json.loads((FIXTURES / "03_mixed_batch.json").read_text(encoding="utf-8"))
    lane_ids = {lane["issue_id"] for lane in mixed["lanes"]}
    assert all(set(lane) == {"issue_id", "outcome", "path"} for lane in mixed["lanes"])
    assert set(mixed["expected_close_status"]) == lane_ids
    assert set(mixed["expected_integrated"]) | set(mixed["expected_recoverable"]) == (
        lane_ids
    )

    durable = json.loads(
        (FIXTURES / "05_durable_handoff.json").read_text(encoding="utf-8")
    )
    assert durable["executor"]["artifact_scope"] == "isolated_executor_output"
    assert set(durable["executor"]) == {
        "type",
        "identity",
        "beads_authority",
        "beads_mutation",
        "artifact_scope",
    }
    assert all(
        set(case) == {"id", "expected_error", "failure_stage"}
        and case["failure_stage"] in {"schema", "guard"}
        for case in durable["tamper_cases"]
    )
    assert {case["id"] for case in durable["tamper_cases"]} == (
        REQUIRED_DURABLE_TAMPER_CASES
    )


def test_fixture_provenance_is_documented() -> None:
    provenance = (FIXTURES / "PROVENANCE.md").read_text(encoding="utf-8")
    assert "7dd010076ffd136443d757dbd072b8257f77192b" in provenance
    assert "uv run pytest scripts/tests/beads_swarm" in provenance
