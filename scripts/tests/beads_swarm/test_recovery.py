"""AC-T16-004: crash injection converges by durable probe, never blind replay."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from . import _common as common

RECOVERY_FIXTURE = common.fixture("04_crash_resume.json")


class CrashOnce:
    def __init__(self, label: str, occurrence: int = 1) -> None:
        self.label = label
        self.occurrence = occurrence
        self.seen = 0

    def __call__(self, event: str) -> None:
        if event == self.label:
            self.seen += 1
            if self.seen == self.occurrence:
                raise RuntimeError(f"injected crash: {event}:{self.seen}")


def _prepared_lane(tmp_path: Path, issue_id: str = "scc-recovery") -> tuple[dict, str]:
    swarm = common.setup_swarm(
        tmp_path,
        [
            {
                "issue_id": issue_id,
                "path": "src/recovery.py",
                "content": "RECOVERED = True\n",
            }
        ],
    )
    assert len(swarm["lanes"]) == RECOVERY_FIXTURE["max_processes"]
    child = common.run_children(swarm, timeout=RECOVERY_FIXTURE["timeout_seconds"])[
        issue_id
    ]
    assert child.returncode == 0, child
    result_sha = common.import_lane(swarm, issue_id)
    common.checkpoint(swarm, {issue_id: result_sha})
    return swarm, result_sha


@pytest.mark.parametrize(
    "crash_point",
    RECOVERY_FIXTURE["freeze_crash_points"],
)
def test_lane_freeze_resume_converges_for_each_filesystem_boundary(
    tmp_path: Path, crash_point: dict[str, Any]
) -> None:
    swarm, result_sha = _prepared_lane(tmp_path)
    ci = swarm["modules"].coordinator_integration
    crashing = CrashOnce(str(crash_point["boundary"]), int(crash_point["occurrence"]))
    swarm["context"].crash_hook = crashing

    with pytest.raises(RuntimeError, match="injected crash"):
        ci.freeze_lane(
            swarm["context"], "scc-recovery", expected_result_sha256=result_sha
        )

    resumed = ci.open_run(swarm["run"]["run_directory"])
    first = ci.freeze_lane(resumed, "scc-recovery", expected_result_sha256=result_sha)
    second = ci.freeze_lane(resumed, "scc-recovery", expected_result_sha256=result_sha)
    assert (
        first["status"]
        == second["status"]
        == RECOVERY_FIXTURE["expected_resume_status"]
    )
    assert first["status"] in RECOVERY_FIXTURE["expected_terminal_states"]
    assert first["freeze_sha256"] == second["freeze_sha256"]
    assert crashing.seen == int(crash_point["occurrence"])

    records = resumed.journal.read().records
    prepared = [
        record
        for record in records
        if record.get("effect_type") == ci.EFFECT_FREEZE
        and record.get("phase") == "PREPARED"
    ]
    resolutions = [
        record
        for record in records
        if record.get("effect_type") == ci.EFFECT_FREEZE
        and record.get("phase") == "RESOLUTION"
    ]
    assert len(prepared) <= 1
    assert len(resolutions) <= 1
    assert not any(
        record.get("status") in {"UNKNOWN", "CONFLICT"} for record in resolutions
    )


def test_crash_after_primary_mutation_is_probed_and_not_replayed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    swarm, result_sha = _prepared_lane(tmp_path)
    ci = swarm["modules"].coordinator_integration
    freeze = common.freeze_and_verify(swarm, "scc-recovery", result_sha)
    built = ci.build_candidate(swarm["context"], lane_freeze_sha256s=[freeze])

    # Simulate process death immediately after the real reset succeeds, before
    # the coordinator can append its APPLIED resolution.
    real_run = ci.subprocess.run
    primary = swarm["repo"].resolve()
    primary_mutations = 0

    def crash_after_reset(argv, *args, **kwargs):
        nonlocal primary_mutations
        completed = real_run(argv, *args, **kwargs)
        if (
            list(argv[:3]) == ["git", "reset", "--hard"]
            and Path(kwargs["cwd"]).resolve() == primary
        ):
            primary_mutations += 1
            if primary_mutations == 1:
                raise RuntimeError("injected crash after primary mutation")
        return completed

    monkeypatch.setattr(ci.subprocess, "run", crash_after_reset)
    with pytest.raises(RuntimeError, match="injected crash"):
        ci.apply_candidate(
            swarm["context"], built["candidate_id"], expected_predecessor=swarm["head"]
        )
    applied_head = common.git(swarm["repo"], "rev-parse", "HEAD")
    assert applied_head != swarm["head"]

    resumed = ci.open_run(swarm["run"]["run_directory"])
    recovered = ci.apply_candidate(
        resumed, built["candidate_id"], expected_predecessor=swarm["head"]
    )
    with pytest.raises(ci.IntegrationError) as repeat:
        ci.apply_candidate(
            resumed, built["candidate_id"], expected_predecessor=swarm["head"]
        )
    assert recovered["status"] == RECOVERY_FIXTURE["expected_resume_status"]
    assert recovered["status"] in RECOVERY_FIXTURE["expected_terminal_states"]
    assert repeat.value.code == "PRIMARY_PREDECESSOR_MISMATCH"
    assert repeat.value.status == RECOVERY_FIXTURE["expected_repeat_status"]
    assert repeat.value.status in RECOVERY_FIXTURE["expected_terminal_states"]
    assert primary_mutations - 1 <= RECOVERY_FIXTURE["expected_max_native_replays"]
    assert common.git(swarm["repo"], "rev-parse", "HEAD") == applied_head
    assert (
        common.git(swarm["repo"], "rev-list", "--count", f"{swarm['head']}..HEAD")
        == "1"
    )

    apply_records = [
        record
        for record in resumed.journal.read().records
        if record.get("effect_type") == ci.EFFECT_APPLY
    ]
    assert len([r for r in apply_records if r["phase"] == "PREPARED"]) == 1
    assert len([r for r in apply_records if r["phase"] == "RESOLUTION"]) == 1
    assert [r["status"] for r in apply_records if r["phase"] == "RESOLUTION"] == [
        "APPLIED"
    ]


@pytest.mark.parametrize("crash_point", RECOVERY_FIXTURE["native_io_crash_points"])
def test_apply_resume_probes_before_reentering_each_native_io_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, crash_point: dict[str, Any]
) -> None:
    swarm, result_sha = _prepared_lane(tmp_path)
    ci = swarm["modules"].coordinator_integration
    freeze = common.freeze_and_verify(swarm, "scc-recovery", result_sha)
    built = ci.build_candidate(swarm["context"], lane_freeze_sha256s=[freeze])
    real_run = ci.subprocess.run
    prefix = list(crash_point["argv_prefix"])
    phase = crash_point["phase"]
    primary = swarm["repo"].resolve()
    crashed = False
    completed_mutations = {"update-ref": 0, "reset": 0}

    def crash_at_native_io(argv, *args, **kwargs):
        nonlocal crashed
        command = list(argv)
        targeted = (
            command[: len(prefix)] == prefix
            and Path(kwargs["cwd"]).resolve() == primary
            and not crashed
        )
        if targeted and phase == "before":
            crashed = True
            raise RuntimeError("injected crash before native I/O")
        completed = real_run(argv, *args, **kwargs)
        if command[:2] == ["git", "update-ref"]:
            completed_mutations["update-ref"] += 1
        if command[:3] == ["git", "reset", "--hard"]:
            completed_mutations["reset"] += 1
        if targeted and phase == "after":
            crashed = True
            raise RuntimeError("injected crash after native I/O")
        return completed

    monkeypatch.setattr(ci.subprocess, "run", crash_at_native_io)
    with pytest.raises(RuntimeError, match="injected crash"):
        ci.apply_candidate(
            swarm["context"], built["candidate_id"], expected_predecessor=swarm["head"]
        )

    resumed = ci.open_run(swarm["run"]["run_directory"])
    recovered = ci.apply_candidate(
        resumed, built["candidate_id"], expected_predecessor=swarm["head"]
    )
    assert recovered["status"] == RECOVERY_FIXTURE["expected_resume_status"]
    assert crashed
    assert completed_mutations == {"update-ref": 1, "reset": 1}
    assert (
        common.git(swarm["repo"], "rev-list", "--count", f"{swarm['head']}..HEAD")
        == "1"
    )
