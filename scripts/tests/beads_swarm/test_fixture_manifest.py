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
REQUIRED_FREEZE_CRASH_POINTS = {
    ("after_lock_acquire", 1),
    ("after_journal_write", 1),
    ("after_journal_fsync", 1),
    *(
        (boundary, occurrence)
        for occurrence in range(1, 5)
        for boundary in (
            "after_temp_write",
            "after_temp_fsync",
            "after_atomic_rename",
            "after_directory_fsync",
        )
    ),
    ("after_journal_write", 3),
    ("after_journal_fsync", 3),
    ("after_checkpoint_acceptance", 1),
    ("after_pointer_publication", 1),
    ("after_lock_release", 1),
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


def test_fixture_corpus_covers_every_acceptance_criterion() -> None:
    paths = sorted(FIXTURES.glob("*.json"))
    assert paths, "the beads_swarm conformance corpus is missing"
    covered: set[str] = set()
    fixture_ids: set[str] = set()
    for path in paths:
        fixture = json.loads(path.read_text(encoding="utf-8"))
        covered.update(fixture["acceptance_criteria"])
        fixture_ids.add(fixture["id"])
        assert fixture["schema_version"] == "beads.swarm-fixture.v1"
        assert fixture["timeout_seconds"] <= 30
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
    assert {
        (case["boundary"], case["occurrence"])
        for case in recovery["freeze_crash_points"]
    } == REQUIRED_FREEZE_CRASH_POINTS
    assert {
        (tuple(case["argv_prefix"]), case["phase"])
        for case in recovery["native_io_crash_points"]
    } == REQUIRED_NATIVE_IO_CRASH_POINTS

    durable = json.loads(
        (FIXTURES / "05_durable_handoff.json").read_text(encoding="utf-8")
    )
    assert durable["executor"]["artifact_scope"] == "isolated_executor_output"
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
