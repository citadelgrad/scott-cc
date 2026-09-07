"""AC-T16-003: mixed batches commit only independently successful lanes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from . import _common as common


def test_mixed_batch_partially_succeeds_and_preserves_failed_siblings(
    tmp_path: Path,
) -> None:
    spec = common.fixture("03_mixed_batch.json")
    swarm = common.setup_swarm(tmp_path, spec["lanes"])
    children = common.run_children(swarm, timeout=spec["timeout_seconds"])
    assert len(children) == spec["max_processes"]
    assert all(child.returncode == 0 for child in children.values()), children

    lanes_by_outcome = {lane["outcome"]: lane for lane in spec["lanes"]}
    good_id = lanes_by_outcome["completed"]["issue_id"]
    failed_id = lanes_by_outcome["failed"]["issue_id"]
    missing_id = lanes_by_outcome["missing_evidence"]["issue_id"]
    assert set(spec["expected_integrated"]) | set(spec["expected_recoverable"]) == set(
        children
    )
    assert not (swarm["lanes"][missing_id]["outbox"] / "command-000.json").exists()
    result_shas = {issue: common.import_lane(swarm, issue) for issue in children}
    common.checkpoint(swarm, result_shas)
    ci = swarm["modules"].coordinator_integration

    freeze = common.freeze_and_verify(swarm, good_id, result_shas[good_id])
    failed_freeze = ci.freeze_lane(
        swarm["context"],
        failed_id,
        expected_result_sha256=result_shas[failed_id],
    )
    assert failed_freeze["status"] == "success"  # immutable evidence may be retained
    failed_verification = ci.verify_lane(swarm["context"], failed_id)
    assert failed_verification["status"] != "success"
    with pytest.raises(Exception):
        ci.freeze_lane(
            swarm["context"],
            missing_id,
            expected_result_sha256=result_shas[missing_id],
        )

    built = ci.build_candidate(swarm["context"], lane_freeze_sha256s=[freeze])
    assert built["status"] == "success"
    applied = ci.apply_candidate(
        swarm["context"], built["candidate_id"], expected_predecessor=swarm["head"]
    )
    assert applied["status"] == "success"
    for lane in spec["lanes"]:
        integrated = lane["issue_id"] in spec["expected_integrated"]
        assert (swarm["repo"] / lane["path"]).exists() is integrated

    current = swarm["context"].checkpoints.current(rebuild_pointer=True).value
    for issue_id in spec["expected_integrated"]:
        assert (
            current["issues"][issue_id]["integration"]["state"] == "primary_integrated"
        )
    for issue_id in spec["expected_recoverable"]:
        assert (
            current["issues"][issue_id]["integration"]["state"] != "primary_integrated"
        )
        assert swarm["lanes"][issue_id]["outbox"].is_dir()

    # Closure is a parent-only native effect and is attempted only for the
    # independently verified/integrated lane. The runner denies every
    # unscripted profile, so a sibling close would fail this test immediately.
    for issue_id in spec["expected_integrated"]:
        _close_only_successful_lane(swarm, issue_id)


def _close_only_successful_lane(swarm: dict[str, Any], issue_id: str) -> None:
    import direct_operation as do
    import safe_bd

    class ParentTracker:
        def __init__(self) -> None:
            self.calls: list[str] = []
            self.replies = {
                "issue_comments": [[{"text": "no prior marker"}]],
                "issue_get": [
                    {"id": issue_id, "status": "in_progress", "assignee": "parent"},
                    {"id": issue_id, "status": "closed", "assignee": "parent"},
                ],
                "append_marker_note": [{"ok": True}],
                "close_exact": [{"id": issue_id, "status": "closed"}],
            }

        def __call__(self, request, *, sensitive=None):
            del sensitive
            self.calls.append(request.profile)
            assert request.profile in self.replies, (
                f"unauthorized native profile: {request.profile}"
            )
            queue = self.replies[request.profile]
            data = queue.pop(0)
            return safe_bd.SafeBdResult(
                "beads.safe-bd-result.v1",
                request.profile,
                "ok",
                safe_bd.PINNED_BD_VERSION,
                "a" * 64,
                data,
                (),
                None,
            )

    context = do.RunContext(
        run_directory=swarm["run"]["run_directory"],
        manifest=swarm["run"]["manifest"],
        journal=swarm["run"]["journal"],
        checkpoints=swarm["context"].checkpoints,
        crash_hook=swarm["modules"].coordinator_state.NOOP_HOOK,
    )
    operation = do.DirectOperation(
        caller_key=f"mixed-close/{issue_id}",
        effect_type="TRACKER_CLOSE",
        target_identity=f"bd://issue/{issue_id}",
        issue_id=issue_id,
        ownership_epoch=swarm["run"]["epochs"][issue_id],
        arguments={"issue_id": issue_id, "reason": "independently verified"},
        readback=do.Readback(
            profile="issue_get",
            arguments={"issue_id": issue_id},
            intended={"status": "closed"},
            prestate={"status": "in_progress"},
        ),
    )
    tracker = ParentTracker()
    outcome = do.execute(context, operation, actor="parent", runner=tracker)
    assert outcome.status == do.APPLIED
    assert tracker.calls.count("close_exact") == 1
    assert tracker.calls[-1] == "issue_get"
