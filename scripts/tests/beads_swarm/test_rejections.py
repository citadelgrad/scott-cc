"""AC-T16-002: untrusted or failed evidence never reaches the primary."""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from . import _common as common

REJECTION_FIXTURE = common.fixture("02_rejection_matrix.json")
EXPECTED_ERRORS = {
    case["id"]: case["expected_error"] for case in REJECTION_FIXTURE["cases"]
}


def _one(tmp_path: Path, issue_id: str = "scc-reject") -> dict:
    return common.setup_swarm(
        tmp_path,
        [{"issue_id": issue_id, "path": "src/reject.py", "content": "VALUE = 1\n"}],
    )


def _run(swarm: dict, **kwargs):
    assert len(swarm["lanes"]) <= REJECTION_FIXTURE["max_processes"]
    return common.run_children(
        swarm,
        timeout=REJECTION_FIXTURE["timeout_seconds"],
        output_limit=REJECTION_FIXTURE["output_limit_bytes"],
        **kwargs,
    )


def _assert_not_integrated(swarm: dict, issue_id: str) -> None:
    assert not (swarm["repo"] / "src" / "reject.py").exists()
    if "context" in swarm:
        entry = (
            swarm["context"]
            .checkpoints.current(rebuild_pointer=True)
            .value["issues"][issue_id]
        )
        assert entry["integration"]["state"] != "primary_integrated"


def test_child_tracker_mutation_is_rejected_inside_child_process(
    tmp_path: Path,
) -> None:
    swarm = _one(tmp_path)
    result = _run(swarm, behaviors={"scc-reject": "child_tracker_mutation"})[
        "scc-reject"
    ]

    assert result.returncode == 3
    assert EXPECTED_ERRORS["child_tracker_mutation"] in result.stdout
    assert not (swarm["lanes"]["scc-reject"]["outbox"] / "result.json").exists()
    assert "SafeBdError" in result.stdout
    assert common.git(swarm["repo"], "rev-parse", "HEAD") == swarm["head"]


@pytest.mark.parametrize(
    "tamper",
    [
        "forged_result_identity",
        "stale_ownership_epoch",
        "missing_command_evidence",
    ],
)
def test_forged_stale_or_missing_worker_evidence_never_freezes(
    tmp_path: Path, tamper: str
) -> None:
    swarm = _one(tmp_path)
    offsets = {"scc-reject": 1} if tamper == "stale_ownership_epoch" else {}
    child = _run(swarm, epoch_offsets=offsets)["scc-reject"]
    assert child.returncode == 0, child
    outbox = swarm["lanes"]["scc-reject"]["outbox"]
    if tamper == "forged_result_identity":
        value = json.loads((outbox / "result.json").read_bytes())
        value["issue_id"] = "scc-forged"
        (outbox / "result.json").write_bytes(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode() + b"\n"
        )
    elif tamper == "missing_command_evidence":
        (outbox / "command-000.json").unlink()

    result_sha = common.import_lane(swarm, "scc-reject")
    common.checkpoint(swarm, {"scc-reject": result_sha})
    ci = swarm["modules"].coordinator_integration
    with pytest.raises(Exception) as refused:
        ci.freeze_lane(
            swarm["context"], "scc-reject", expected_result_sha256=result_sha
        )
    code = getattr(refused.value, "code", str(refused.value))
    assert str(code) == EXPECTED_ERRORS[tamper]
    _assert_not_integrated(swarm, "scc-reject")


def test_cancelled_lane_remains_recoverable_and_never_becomes_candidate(
    tmp_path: Path,
) -> None:
    swarm = _one(tmp_path)
    recovery = common.fixture("04_crash_resume.json")
    expected = next(
        case for case in recovery["recovery_scenarios"] if case["id"] == "cancellation"
    )
    child = _run(swarm, behaviors={"scc-reject": "cancelled"})["scc-reject"]
    assert child.returncode == 0, child
    result_sha = common.import_lane(swarm, "scc-reject")
    common.checkpoint(swarm, {"scc-reject": result_sha})
    ci = swarm["modules"].coordinator_integration

    frozen = ci.freeze_lane(
        swarm["context"], "scc-reject", expected_result_sha256=result_sha
    )
    verified = ci.verify_lane(swarm["context"], "scc-reject")

    assert verified["status"] == expected["expected_status"]
    assert verified["error_code"] == expected["expected_error"]
    assert expected["expected_error"] == EXPECTED_ERRORS["cancelled_lane"]
    with pytest.raises(ci.IntegrationError, match="LANE_NOT_VERIFIED"):
        ci.build_candidate(
            swarm["context"], lane_freeze_sha256s=[frozen["freeze_sha256"]]
        )
    _assert_not_integrated(swarm, "scc-reject")


def test_failed_lane_review_is_retained_but_not_candidate_eligible(
    tmp_path: Path,
) -> None:
    swarm = common.setup_swarm(
        tmp_path,
        [
            {
                "issue_id": "scc-reject",
                "path": "src/security_policy.py",
                "content": "ENFORCED = True\n",
            }
        ],
    )
    assert _run(swarm)["scc-reject"].returncode == 0
    result_sha = common.import_lane(swarm, "scc-reject")
    common.checkpoint(swarm, {"scc-reject": result_sha})
    ci = swarm["modules"].coordinator_integration
    frozen = ci.freeze_lane(
        swarm["context"], "scc-reject", expected_result_sha256=result_sha
    )
    verified = ci.verify_lane(swarm["context"], "scc-reject")
    assert verified["status"] == "partial"
    review = common.integration.reviewer_record(
        run_id=common.RUN_ID,
        target_kind="lane_freeze",
        target_sha256=frozen["freeze_sha256"],
        reviewer_id="independent-reviewer",
        implementer_ids=["worker-scc-reject"],
        verdict="fail",
    )
    path = common.integration.write_review(
        swarm["modules"], swarm["run"]["run_directory"], review
    )
    outcome = ci.record_review(swarm["context"], "scc-reject", path)
    assert outcome["status"] == "refused"
    assert outcome["error_code"] == EXPECTED_ERRORS["failed_lane_review"]
    with pytest.raises(ci.IntegrationError):
        ci.build_candidate(
            swarm["context"], lane_freeze_sha256s=[frozen["freeze_sha256"]]
        )
    _assert_not_integrated(swarm, "scc-reject")


def test_failed_candidate_test_and_conflicting_candidate_never_apply(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A real verified lane reaches the candidate test runner, whose real command
    # is replaced only at that OS-command boundary with /usr/bin/false.
    test_root = tmp_path / "test-failure"
    test_root.mkdir()
    swarm = _one(test_root, "scc-reject")
    assert _run(swarm)["scc-reject"].returncode == 0
    result_sha = common.import_lane(swarm, "scc-reject")
    common.checkpoint(swarm, {"scc-reject": result_sha})
    freeze = common.freeze_and_verify(swarm, "scc-reject", result_sha)
    ci = swarm["modules"].coordinator_integration
    real_run = ci.safe_output.run_command

    def fail_candidate_command(spec, *args, **kwargs):
        if spec.profile == "verification":
            spec = dataclasses.replace(spec, argv=("/usr/bin/false",))
        return real_run(spec, *args, **kwargs)

    monkeypatch.setattr(ci.safe_output, "run_command", fail_candidate_command)
    built = ci.build_candidate(swarm["context"], lane_freeze_sha256s=[freeze])
    monkeypatch.undo()
    assert built["status"] == "refused"
    assert built["error_code"] == EXPECTED_ERRORS["failed_candidate_test"]
    with pytest.raises(
        ci.IntegrationError, match=EXPECTED_ERRORS["failed_candidate_test"]
    ):
        ci.apply_candidate(
            swarm["context"], built["candidate_id"], expected_predecessor=swarm["head"]
        )
    _assert_not_integrated(swarm, "scc-reject")

    # Independently verified siblings that write incompatible bytes to one path
    # are preserved as lane artifacts, never auto-resolved into the primary.
    conflict_root = tmp_path / "conflict"
    conflict_root.mkdir()
    lanes = [
        {"issue_id": "scc-a", "path": "src/shared.py", "content": "SIDE = 'a'\n"},
        {"issue_id": "scc-b", "path": "src/shared.py", "content": "SIDE = 'b'\n"},
    ]
    conflict = common.setup_swarm(conflict_root, lanes)
    assert len(conflict["lanes"]) == REJECTION_FIXTURE["max_processes"]
    children = _run(conflict)
    assert all(child.returncode == 0 for child in children.values())
    shas = {issue: common.import_lane(conflict, issue) for issue in children}
    common.checkpoint(conflict, shas)
    freezes = [
        common.freeze_and_verify(conflict, issue, shas[issue]) for issue in sorted(shas)
    ]
    conflict_ci = conflict["modules"].coordinator_integration
    with pytest.raises(conflict_ci.IntegrationError) as refused:
        conflict_ci.build_candidate(conflict["context"], lane_freeze_sha256s=freezes)
    assert refused.value.code == EXPECTED_ERRORS["candidate_conflict"]
    assert not (conflict["repo"] / "src" / "shared.py").exists()


def test_unknown_primary_readback_is_journaled_unknown_not_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    swarm = _one(tmp_path)
    assert _run(swarm)["scc-reject"].returncode == 0
    result_sha = common.import_lane(swarm, "scc-reject")
    common.checkpoint(swarm, {"scc-reject": result_sha})
    freeze = common.freeze_and_verify(swarm, "scc-reject", result_sha)
    ci = swarm["modules"].coordinator_integration
    built = ci.build_candidate(swarm["context"], lane_freeze_sha256s=[freeze])
    real_subprocess_run = ci.subprocess.run
    primary = swarm["repo"].resolve()

    def suppress_primary_reset(argv, *args, **kwargs):
        if (
            list(argv[:3]) == ["git", "reset", "--hard"]
            and Path(kwargs["cwd"]).resolve() == primary
        ):
            return ci.subprocess.CompletedProcess(list(argv), 0, b"", b"")
        return real_subprocess_run(argv, *args, **kwargs)

    monkeypatch.setattr(ci.subprocess, "run", suppress_primary_reset)
    with pytest.raises(ci.IntegrationError) as unknown:
        ci.apply_candidate(
            swarm["context"], built["candidate_id"], expected_predecessor=swarm["head"]
        )
    assert unknown.value.code == EXPECTED_ERRORS["unknown_primary_result"]
    assert unknown.value.status == "unknown"
    statuses = [
        record["status"]
        for record in swarm["context"].journal.read().records
        if record.get("effect_type") == ci.EFFECT_APPLY
        and record.get("phase") == "RESOLUTION"
    ]
    assert statuses == ["UNKNOWN"]
    _assert_not_integrated(swarm, "scc-reject")


def test_rejection_fixture_names_every_executed_case() -> None:
    fixture_cases = set(EXPECTED_ERRORS)
    assert fixture_cases == {
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
