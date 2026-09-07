"""AC-T16-001: real concurrent lanes remain isolated and parent-verified."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import pytest

from . import _common as common


def test_valid_parent_owned_swarm_is_concurrent_isolated_and_verified(
    tmp_path: Path,
) -> None:
    spec = common.fixture("01_isolated_swarm.json")
    swarm = common.setup_swarm(tmp_path, spec["lanes"])

    results = common.run_children(
        swarm,
        timeout=spec["timeout_seconds"],
    )
    assert len(results) == spec["max_processes"]
    assert all(result.returncode == 0 for result in results.values()), results

    # Every child ran in a distinct linked worktree, under a depth-zero packet.
    worktrees = {str(lane["worktree"].resolve()) for lane in swarm["lanes"].values()}
    assert len(worktrees) == len(spec["lanes"])
    assert all(
        lane["packet"]["delegation"] == {"allowed": False, "max_child_depth": 0}
        for lane in swarm["lanes"].values()
    )
    for issue_id, lane in swarm["lanes"].items():
        changed = lane["spec"]["path"]
        assert (lane["worktree"] / changed).is_file()
        for other_id, other in swarm["lanes"].items():
            if other_id != issue_id:
                assert not (other["worktree"] / changed).exists()

    result_shas = {
        issue_id: common.import_lane(swarm, issue_id) for issue_id in results
    }
    common.checkpoint(swarm, result_shas)
    freezes = [
        common.freeze_and_verify(swarm, issue_id, result_shas[issue_id])
        for issue_id in sorted(result_shas)
    ]

    # Cooperative ownership has one unique epoch-bearing record per issue.
    ownership = swarm["modules"].beads_ownership.OwnershipStore.open_existing(
        swarm["run"]["run_directory"].parent
    )
    records = [
        ownership.inspect_readonly(issue_id).record for issue_id in sorted(results)
    ]
    assert all(record and record["run_id"] == common.RUN_ID for record in records)
    assert len({record["issue_id"] for record in records if record}) == len(results)

    ci = swarm["modules"].coordinator_integration
    built = ci.build_candidate(swarm["context"], lane_freeze_sha256s=freezes)
    assert built["status"] == "partial"  # combined review is independently required
    review = common.integration.reviewer_record(
        run_id=common.RUN_ID,
        target_kind="combined_candidate",
        target_sha256=built["candidate_record_sha256"],
        reviewer_id="independent-combined-reviewer",
        implementer_ids=[f"worker-{issue_id}" for issue_id in sorted(results)],
    )
    review_path = common.integration.write_review(
        swarm["modules"], swarm["run"]["run_directory"], review
    )
    assert (
        ci.record_combined_review(swarm["context"], review_path)["status"] == "success"
    )
    applied = ci.apply_candidate(
        swarm["context"], built["candidate_id"], expected_predecessor=swarm["head"]
    )
    assert applied["status"] == "success"
    for lane in spec["lanes"]:
        assert (swarm["repo"] / lane["path"]).read_text(encoding="utf-8") == lane[
            "content"
        ]


def test_child_timeout_is_one_shared_deadline_and_reaps_every_worker(
    tmp_path: Path,
) -> None:
    lanes = [{"issue_id": f"scc-timeout-{index}"} for index in range(3)]
    swarm = common.setup_swarm(tmp_path, lanes)
    behaviors = {
        lane["issue_id"]: f"sleep_exit:{delay}"
        for lane, delay in zip(lanes, (0.8, 1.6, 2.4), strict=True)
    }

    started = time.monotonic()
    with pytest.raises(subprocess.TimeoutExpired):
        common.run_children(swarm, behaviors=behaviors, timeout=1)
    elapsed = time.monotonic() - started

    assert elapsed < 2.0
    for issue_id, lane in swarm["lanes"].items():
        pid_path = lane["packet_path"].with_name(f"job-{issue_id}.pid")
        pid = int(pid_path.read_text(encoding="ascii"))
        with pytest.raises(ProcessLookupError):
            os.kill(pid, 0)


def test_partial_launch_failure_reaps_workers_already_started(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    swarm = common.setup_swarm(
        tmp_path,
        [{"issue_id": "scc-started"}, {"issue_id": "scc-launch-fails"}],
    )
    real_popen = common.subprocess.Popen
    spawned: list[subprocess.Popen[str]] = []

    def fail_second_launch(*args, **kwargs):
        if spawned:
            raise OSError("injected launch failure")
        process = real_popen(*args, **kwargs)
        spawned.append(process)
        return process

    monkeypatch.setattr(common.subprocess, "Popen", fail_second_launch)
    try:
        with pytest.raises(OSError, match="injected launch failure"):
            common.run_children(
                swarm,
                behaviors={"scc-started": "sleep_exit:60"},
                timeout=1,
            )
        assert spawned[0].wait(timeout=1) is not None
    finally:
        if spawned and spawned[0].poll() is None:
            spawned[0].kill()
            spawned[0].wait(timeout=1)
