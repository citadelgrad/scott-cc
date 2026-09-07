"""Public finish delegates terminal succession to the owning tracker module."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from . import _common as common

bc = common.bc
safe_bd = common.safe_bd

ROOT_ISSUE = "scc-root"
LANE_A = "scc-lane-a"
TERMINAL_STATUSES = (
    "completed",
    "partially_completed",
    "blocked",
    "human_required",
    "budget_exhausted",
    "circuit_broken",
    "inconclusive",
    "cancelled",
    "error",
)


def _write_json(path, payload) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _finish_input(repo, **overrides):
    payload = {
        "terminal_status": "completed",
        "git_common_dir": str(repo / ".git"),
        "scope_issue_ids": [LANE_A],
        "base_git_commit": "a" * 40,
        "authority_snapshot_sha256": "b" * 64,
        "ownership_epoch": 1,
    }
    payload.update(overrides)
    return payload


def _argv(run_directory, input_path):
    return [
        "finish",
        "--run-dir",
        str(run_directory),
        "--input",
        str(input_path),
        "--actor",
        "parent",
        "--json",
    ]


@pytest.mark.parametrize("terminal_status", TERMINAL_STATUSES)
def test_finish_forwards_every_protocol_terminal_status_to_the_owning_module(
    tmp_path, monkeypatch, capsys, terminal_status
):
    repo = tmp_path / "repo"
    repo.mkdir()
    run = common.make_run(repo, root_issue_id=ROOT_ISSUE)
    captured = {}

    def finish_run(request, **kwargs):
        captured.update(kwargs)
        captured["request"] = request
        return bc.coordinator_tracker.FinishRunResult(
            bc.direct_operation.APPLIED,
            bc.direct_operation.INTENDED_EFFECT_PRESENT,
            None,
        )

    monkeypatch.setattr(bc.coordinator_tracker, "finish_run", finish_run)
    input_path = tmp_path / f"finish-{terminal_status}.json"
    _write_json(input_path, _finish_input(repo, terminal_status=terminal_status))

    assert bc.main(_argv(run["run_directory"], input_path)) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "success"
    assert captured["terminal_status"] == terminal_status
    assert captured["scope_issue_ids"] == [LANE_A]
    assert captured["actor"] == "parent"


def test_finish_rejects_pointer_status_as_a_run_terminal_status(tmp_path, capsys):
    repo = tmp_path / "repo"
    repo.mkdir()
    run = common.make_run(repo, root_issue_id=ROOT_ISSUE)
    input_path = tmp_path / "finish.json"
    _write_json(input_path, _finish_input(repo, terminal_status="terminal"))

    assert bc.main(_argv(run["run_directory"], input_path)) == 2
    out = json.loads(capsys.readouterr().out)
    assert out["error_code"] == "INPUT_INVALID"


def _terminal_lane_entry(record, *, tracker_status="closed"):
    return {
        "tracker_status_observed": tracker_status,
        "readiness": {"state": "ready", "reason": ""},
        "ownership": {
            "state": "held",
            "epoch": record["epoch"],
            "token_sha256": record["token_sha256"],
            "actor": "parent",
        },
        "attempt": {
            "state": "joined",
            "attempt_id": "attempt-001",
            "delegation_id": "delegation-1",
            "subagent_id": None,
            "child_session_id": None,
        },
        "worker_result": {
            "state": "accepted",
            "outcome": "completed",
            "record_sha256": "a" * 64,
        },
        "artifact": {"state": "verified", "lane_freeze_sha256": "b" * 64},
        "verification": {"state": "passed", "record_sha256": "c" * 64},
        "review": {"state": "passed", "record_sha256": "d" * 64},
        "integration": {
            "state": "primary_integrated",
            "candidate_sha256": "e" * 64,
            "event_id": "f" * 64,
        },
        "gate": {"state": "none", "gate_id": None},
        "packet_sha256": "1" * 64,
        "result_sha256": "a" * 64,
        "worktree": None,
        "branch": None,
        "base_sha": None,
        "head_sha": None,
    }


def test_finish_full_path_releases_lane_and_root_then_publishes_terminal_pointer(
    tmp_path, monkeypatch, capsys
):
    repo = tmp_path / "repo"
    repo.mkdir()
    hermes = repo / ".hermes"
    hermes.mkdir(mode=0o700)
    run_root = hermes / "beads-runs"
    run_root.mkdir(mode=0o700)
    fake, box = common.tracker_double(ROOT_ISSUE)
    monkeypatch.setattr(safe_bd, "run_profile", fake)

    start_input = tmp_path / "start.json"
    _write_json(
        start_input,
        {
            "request_id": "request-0002-finish-complete",
            "repository_root": str(repo),
            "git_common_dir": str(repo / ".git"),
            "workspace": str(repo),
            "run_root": str(run_root),
            "root_issue_id": ROOT_ISSUE,
            "scope_issue_ids": [LANE_A],
            "actor": "parent",
            "base_git_commit": "a" * 40,
            "authority_snapshot_sha256": "b" * 64,
            "workspace_identity_sha256": "c" * 64,
        },
    )
    assert (
        bc.main(
            ["start-run", "--input", str(start_input), "--actor", "parent", "--json"]
        )
        == 0
    )
    started = json.loads(capsys.readouterr().out)
    run_dir = run_root / started["run_id"]
    ownership = common.beads_ownership.OwnershipStore(run_root)
    root_record = ownership.inspect_readonly(ROOT_ISSUE).record
    assert root_record is not None
    lane = ownership.acquire(
        issue_id=LANE_A,
        actor="parent",
        run_directory=run_dir,
        tracker_state_sha256="0" * 64,
        operation_id="4" * 64,
        now=datetime.now(timezone.utc),
    )
    assert lane.record is not None

    context = bc.direct_operation.open_run(run_dir)
    current = context.checkpoints.current(rebuild_pointer=True)
    checkpoint = dict(current.value)
    checkpoint.update(
        generation=current.generation + 1,
        phase="completed",
        issues={LANE_A: _terminal_lane_entry(lane.record)},
        previous_checkpoint_sha256=current.generation_sha256,
        created_at=common.now(),
    )
    context.checkpoints.accept(checkpoint)

    finish_input = tmp_path / "finish.json"
    _write_json(
        finish_input,
        _finish_input(repo, ownership_epoch=root_record["epoch"]),
    )
    assert bc.main(_argv(run_dir, finish_input)) == 0
    out = json.loads(capsys.readouterr().out)

    assert out["status"] == "success"
    assert ownership.inspect_readonly(LANE_A).disposition == "released"
    assert ownership.inspect_readonly(ROOT_ISSUE).disposition == "released"
    pointer = json.loads(box["metadata"][bc.coordinator_tracker._POINTER_METADATA_KEY])
    assert pointer["status"] == "terminal"
    assert pointer["run_id"] == started["run_id"]
    assert fake.count("set_run_pointer") == 2


def test_finish_rejects_scope_that_does_not_match_the_allocated_request(
    tmp_path, monkeypatch, capsys
):
    repo = tmp_path / "repo"
    repo.mkdir()
    hermes = repo / ".hermes"
    hermes.mkdir(mode=0o700)
    run_root = hermes / "beads-runs"
    run_root.mkdir(mode=0o700)
    fake, _box = common.tracker_double(ROOT_ISSUE)
    monkeypatch.setattr(safe_bd, "run_profile", fake)
    start_input = tmp_path / "start-scope.json"
    _write_json(
        start_input,
        {
            "request_id": "request-0003-finish-scope-binding",
            "repository_root": str(repo),
            "git_common_dir": str(repo / ".git"),
            "workspace": str(repo),
            "run_root": str(run_root),
            "root_issue_id": ROOT_ISSUE,
            "scope_issue_ids": [LANE_A],
            "actor": "parent",
            "base_git_commit": "a" * 40,
            "authority_snapshot_sha256": "b" * 64,
            "workspace_identity_sha256": "c" * 64,
        },
    )
    assert (
        bc.main(
            ["start-run", "--input", str(start_input), "--actor", "parent", "--json"]
        )
        == 0
    )
    started = json.loads(capsys.readouterr().out)
    finish_input = tmp_path / "finish-wrong-scope.json"
    _write_json(finish_input, _finish_input(repo, scope_issue_ids=[]))

    assert bc.main(_argv(run_root / started["run_id"], finish_input)) == 4
    out = json.loads(capsys.readouterr().out)
    assert out["error_code"] == "FINISH_REQUEST_MISMATCH"
    assert fake.count("set_run_pointer") == 1


@pytest.mark.parametrize(
    "boundary",
    (
        "after_finish_checkpoint",
        "after_finish_pointer_prepared",
        "after_finish_lane_releases",
        "after_finish_root_release_recorded",
        "after_operation_effect",
        "after_operation_resolved",
        "after_finish_pointer",
        "after_finish_root_lock_release",
        "after_finish_request_terminal",
    ),
)
def test_finish_crash_boundaries_converge_without_early_or_duplicate_pointer(
    tmp_path, monkeypatch, boundary
):
    repo = tmp_path / "repo"
    repo.mkdir()
    hermes = repo / ".hermes"
    hermes.mkdir(mode=0o700)
    run_root = hermes / "beads-runs"
    run_root.mkdir(mode=0o700)
    fake, box = common.tracker_double(ROOT_ISSUE)
    request = common.state.StartRunInput(
        request_id=f"request-0004-finish-{boundary}",
        repository_root=str(repo),
        git_common_dir=str(repo / ".git"),
        workspace=str(repo),
        run_root=str(run_root),
        root_issue_id=ROOT_ISSUE,
        scope_issue_ids=(LANE_A,),
        actor="parent",
        base_git_commit="a" * 40,
        authority_snapshot_sha256="b" * 64,
        workspace_identity_sha256="c" * 64,
    )
    started = bc.coordinator_tracker.start_run(
        request, actor="parent", now=common.now(), runner=fake
    )
    run_dir = run_root / started.run_id
    ownership = common.beads_ownership.OwnershipStore(run_root)
    root_record = ownership.inspect_readonly(ROOT_ISSUE).record
    assert root_record is not None
    lane = ownership.acquire(
        issue_id=LANE_A,
        actor="parent",
        run_directory=run_dir,
        tracker_state_sha256="0" * 64,
        operation_id="5" * 64,
        now=datetime.now(timezone.utc),
    )
    assert lane.record is not None
    context = bc.direct_operation.open_run(run_dir)
    current = context.checkpoints.current(rebuild_pointer=True)
    checkpoint = dict(current.value)
    checkpoint.update(
        generation=current.generation + 1,
        phase="active",
        issues={LANE_A: _terminal_lane_entry(lane.record)},
        previous_checkpoint_sha256=current.generation_sha256,
        created_at=common.now(),
    )
    context.checkpoints.accept(checkpoint)
    crash = common.CrashHook(boundary)

    def locked_runner(request, *, sensitive=None):
        if request.profile == "set_run_pointer":
            pointer = json.loads(request.arguments["value"])
            if pointer["status"] == "terminal":
                root_dir = run_root / "_ownership" / common.state.issue_key(ROOT_ISSUE)
                current_record = json.loads((root_dir / "current.json").read_bytes())
                assert current_record["status"] == "released"
                probe = subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        (
                            "import fcntl, os, sys; "
                            f"fd=os.open({str(root_dir / 'lock')!r}, os.O_RDWR); "
                            "\ntry: fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)"
                            "\nexcept BlockingIOError: sys.exit(0)"
                            "\nsys.exit(1)"
                        ),
                    ],
                    check=False,
                )
                assert probe.returncode == 0, "root issue lock was not held"
        return fake(request, sensitive=sensitive)

    with pytest.raises(crash.Crash):
        bc.coordinator_tracker.finish_run(
            request,
            run_directory=run_dir,
            scope_issue_ids=[LANE_A],
            ownership_epoch=root_record["epoch"],
            terminal_status="completed",
            actor="parent",
            runner=locked_runner,
            crash_hook=crash,
        )

    pointer = json.loads(box["metadata"][bc.coordinator_tracker._POINTER_METADATA_KEY])
    root_disposition = ownership.inspect_readonly(ROOT_ISSUE).disposition
    if boundary in {
        "after_finish_checkpoint",
        "after_finish_pointer_prepared",
        "after_finish_lane_releases",
    }:
        assert pointer["status"] == "active"
        assert root_disposition == "held"
    else:
        assert root_disposition == "released"
        if boundary == "after_finish_root_release_recorded":
            assert pointer["status"] == "active"
        else:
            assert pointer["status"] == "terminal"
    checkpoint = context.checkpoints.current(rebuild_pointer=True).value
    assert checkpoint["phase"] == "completed"
    successor = None
    if boundary == "after_operation_effect":
        requests_root = run_root / "_requests"
        old_mapping_path = (
            requests_root / f"{common.state.request_key(request.request_id)}.json"
        )
        old_mapping = common.state._read_request_record(old_mapping_path, requests_root)
        common.state._write_request_record(
            old_mapping_path,
            requests_root,
            {**old_mapping, "status": "recovery_required"},
            common.state.NOOP_HOOK,
        )
        successor = replace(
            request,
            request_id="request-0004-successor-after-visible-terminal",
        )
        successor_result = bc.coordinator_tracker.start_run(
            successor, actor="parent", now=common.now(), runner=fake
        )
        assert successor_result.disposition == "conflict"
        assert fake.count("set_run_pointer") == 2

    result = bc.coordinator_tracker.finish_run(
        request,
        run_directory=run_dir,
        scope_issue_ids=[LANE_A],
        ownership_epoch=root_record["epoch"],
        terminal_status="completed",
        actor="parent",
        runner=locked_runner,
    )
    assert result.status == bc.direct_operation.APPLIED
    assert ownership.inspect_readonly(ROOT_ISSUE).disposition == "released"
    assert ownership.inspect_readonly(LANE_A).disposition == "released"
    mapping = common.state._read_request_record(
        run_root / "_requests" / f"{common.state.request_key(request.request_id)}.json",
        run_root / "_requests",
    )
    assert mapping["status"] == "terminal"
    assert fake.count("set_run_pointer") == 2
    if successor is not None:
        successor_result = bc.coordinator_tracker.start_run(
            successor, actor="parent", now=common.now(), runner=fake
        )
        assert successor_result.disposition == "active"
        successor_pointer = box["metadata"][
            bc.coordinator_tracker._POINTER_METADATA_KEY
        ]
        assert json.loads(successor_pointer)["run_id"] == successor_result.run_id
        successor_owner = ownership.inspect_readonly(ROOT_ISSUE)
        assert successor_owner.disposition == "held"
        assert successor_owner.record is not None
        assert successor_owner.record["run_id"] == successor_result.run_id
        assert fake.count("set_run_pointer") == 3


def test_finish_accepts_exact_bound_recovery_required_mapping(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    hermes = repo / ".hermes"
    hermes.mkdir(mode=0o700)
    run_root = hermes / "beads-runs"
    run_root.mkdir(mode=0o700)
    fake, _box = common.tracker_double(ROOT_ISSUE)
    request = common.state.StartRunInput(
        request_id="request-0005-finish-recovery-required",
        repository_root=str(repo),
        git_common_dir=str(repo / ".git"),
        workspace=str(repo),
        run_root=str(run_root),
        root_issue_id=ROOT_ISSUE,
        scope_issue_ids=(LANE_A,),
        actor="parent",
        base_git_commit="a" * 40,
        authority_snapshot_sha256="b" * 64,
        workspace_identity_sha256="c" * 64,
    )
    started = bc.coordinator_tracker.start_run(
        request, actor="parent", now=common.now(), runner=fake
    )
    run_dir = run_root / started.run_id
    ownership = common.beads_ownership.OwnershipStore(run_root)
    root_record = ownership.inspect_readonly(ROOT_ISSUE).record
    assert root_record is not None
    lane = ownership.acquire(
        issue_id=LANE_A,
        actor="parent",
        run_directory=run_dir,
        tracker_state_sha256="0" * 64,
        operation_id="6" * 64,
        now=datetime.now(timezone.utc),
    )
    assert lane.record is not None
    context = bc.direct_operation.open_run(run_dir)
    current = context.checkpoints.current(rebuild_pointer=True)
    context.checkpoints.accept(
        {
            **current.value,
            "generation": current.generation + 1,
            "phase": "completed",
            "issues": {LANE_A: _terminal_lane_entry(lane.record)},
            "previous_checkpoint_sha256": current.generation_sha256,
            "created_at": common.now(),
        }
    )
    requests_root = run_root / "_requests"
    mapping_path = (
        requests_root / f"{common.state.request_key(request.request_id)}.json"
    )
    mapping = common.state._read_request_record(mapping_path, requests_root)
    common.state._write_request_record(
        mapping_path,
        requests_root,
        {**mapping, "status": "recovery_required"},
        common.state.NOOP_HOOK,
    )

    mismatched = replace(request, base_git_commit="d" * 40)
    with pytest.raises(common.state.StateError, match="FINISH_REQUEST_MISMATCH"):
        bc.coordinator_tracker.finish_run(
            mismatched,
            run_directory=run_dir,
            scope_issue_ids=[LANE_A],
            ownership_epoch=root_record["epoch"],
            terminal_status="completed",
            actor="parent",
            runner=fake,
        )

    result = bc.coordinator_tracker.finish_run(
        request,
        run_directory=run_dir,
        scope_issue_ids=[LANE_A],
        ownership_epoch=root_record["epoch"],
        terminal_status="completed",
        actor="parent",
        runner=fake,
    )

    assert result.status == bc.direct_operation.APPLIED
    assert (
        common.state._read_request_record(mapping_path, requests_root)["status"]
        == "terminal"
    )


def test_finish_missing_required_field_exits_2(tmp_path, capsys):
    repo = tmp_path / "repo"
    repo.mkdir()
    run = common.make_run(repo, root_issue_id=ROOT_ISSUE)
    payload = _finish_input(repo)
    del payload["ownership_epoch"]
    input_path = tmp_path / "finish.json"
    _write_json(input_path, payload)

    assert bc.main(_argv(run["run_directory"], input_path)) == 2
    out = json.loads(capsys.readouterr().out)
    assert out["error_code"] == "INPUT_MISSING_FIELDS"
