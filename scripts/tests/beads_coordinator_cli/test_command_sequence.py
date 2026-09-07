"""AC-T13-001/002: the public coordinator commands compose over real state."""

from __future__ import annotations

import hashlib
import importlib
import json
import subprocess
from types import SimpleNamespace

from beads_contract import test_worker_packet as packet_factory
from beads_integration import _common as integration_common

from . import _common as common

bc = common.bc
safe_bd = common.safe_bd

ROOT_ISSUE = "scc-root"
LANE = "scc-lane-a"


def _write_json(path, payload) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _run(argv, capsys) -> dict:
    assert bc.main([*argv, "--json"]) == 0
    return json.loads(capsys.readouterr().out)


def test_real_claim_freeze_verify_review_candidate_close_finish_command_sequence(
    tmp_path, monkeypatch, capsys
):
    """Exercise public commands without replacing their state-transition owners.

    Native Beads is represented by one stateful transport double; filesystem,
    journal, ownership, worker-result validation, Git integration, tracker
    operation, and finish succession all use their production implementations.
    """
    repo, lane_worktree, _head = packet_factory._git_lane(tmp_path)
    (repo / ".gitignore").write_text(
        ".hermes/\nlane/\nsensitive-values.json\nsnapshot.json\n", encoding="utf-8"
    )
    subprocess.run(["git", "add", ".gitignore"], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "ignore runtime"], cwd=repo, check=True
    )
    subprocess.run(["git", "merge", "--ff-only", "main"], cwd=lane_worktree, check=True)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    hermes = repo / ".hermes"
    hermes.mkdir(mode=0o700)
    run_root = hermes / "beads-runs"
    run_root.mkdir(mode=0o700)
    pointer_metadata: dict[str, str] = {}
    lane_state: dict[str, str | None] = {"status": "open", "assignee": None}

    def issue_get(request):
        issue_id = request.arguments["issue_id"]
        if issue_id == ROOT_ISSUE:
            return {"id": ROOT_ISSUE, "metadata": dict(pointer_metadata)}
        assert issue_id == LANE
        return {
            "id": LANE,
            "status": lane_state["status"],
            "assignee": lane_state["assignee"],
        }

    def set_pointer(request):
        key = bc.coordinator_tracker._POINTER_METADATA_KEY
        pointer_metadata[key] = request.arguments["value"]
        return {"id": ROOT_ISSUE, "metadata": dict(pointer_metadata)}

    def claim_exact(_request):
        lane_state["status"] = "in_progress"
        lane_state["assignee"] = "parent"
        return {"id": LANE, "status": "in_progress", "assignee": "parent"}

    def close_exact(_request):
        lane_state["status"] = "closed"
        return {"id": LANE, "status": "closed", "assignee": "parent"}

    fake = common.FakeNative(
        safe_bd,
        responses={
            "issue_get": issue_get,
            "set_run_pointer": set_pointer,
            "issue_comments": lambda _request: [],
            "append_marker_note": {"ok": True},
            "claim_exact": claim_exact,
            "close_exact": close_exact,
        },
        allowed=[
            "issue_get",
            "set_run_pointer",
            "issue_comments",
            "append_marker_note",
            "claim_exact",
            "close_exact",
        ],
    )
    monkeypatch.setattr(safe_bd, "run_profile", fake)

    start_input = tmp_path / "start.json"
    request_id = "request-0001-real-cli-sequence"
    _write_json(
        start_input,
        {
            "request_id": request_id,
            "repository_root": str(repo),
            "git_common_dir": str(repo / ".git"),
            "workspace": str(repo),
            "run_root": str(run_root),
            "root_issue_id": ROOT_ISSUE,
            "scope_issue_ids": [LANE],
            "actor": "parent",
            "base_git_commit": head,
            "authority_snapshot_sha256": "b" * 64,
            "workspace_identity_sha256": "c" * 64,
        },
    )
    started = _run(
        ["start-run", "--input", str(start_input), "--actor", "parent"], capsys
    )
    run_id = started["run_id"]
    run_dir = run_root / run_id

    tracker_input = tmp_path / "tracker-claim.json"
    _write_json(tracker_input, {"issues": [LANE]})
    claimed = _run(
        [
            "tracker-update",
            "--run-dir",
            str(run_dir),
            "--input",
            str(tracker_input),
            "--actor",
            "parent",
        ],
        capsys,
    )
    assert claimed["status"] == "success"

    ownership = common.beads_ownership.OwnershipStore(run_root)
    lane_record = ownership.inspect_readonly(LANE).record
    assert lane_record is not None
    epoch = lane_record["epoch"]
    packet = packet_factory._packet(tmp_path)
    outbox = lane_worktree / "outbox"
    outbox.mkdir(mode=0o700, exist_ok=True)
    packet["run_id"] = run_id
    packet["issue"]["id"] = LANE
    packet["issue"]["key"] = hashlib.sha256(LANE.encode()).hexdigest()
    packet["repository"]["root"] = str(repo)
    packet["repository"]["base_sha"] = head
    packet["repository"]["worktree"] = str(lane_worktree)
    packet["repository"]["branch"] = "lane"
    packet["verification"]["worker_outbox"] = str(outbox)
    packet["verification"]["required_commands"] = [["/usr/bin/printf", "ok"]]
    packet["scope"]["allowed_paths"] = ["src/**"]
    packet["scope"]["integration_mode"] = "patch_package"

    modules = SimpleNamespace(
        coordinator_state=bc.state,
        worker_result=importlib.import_module("worker_result"),
        lane_snapshot=bc.coordinator_integration.lane_snapshot,
    )
    packet_sha, result_sha = integration_common.import_attempt(
        modules,
        run_dir,
        LANE,
        epoch=epoch,
        worktree=lane_worktree,
        outbox=outbox,
        head=head,
        changed_file="src/atomic.py",
        file_content="value = 1\n",
        packet=packet,
    )
    context = bc.direct_operation.open_run(run_dir)
    current = context.checkpoints.current(rebuild_pointer=True)
    entry = integration_common.issue_entry(
        modules, epoch=epoch, result_sha=result_sha, packet_sha=packet_sha
    )
    entry["ownership"]["token_sha256"] = lane_record["token_sha256"]
    checkpoint = dict(current.value)
    checkpoint.update(
        generation=current.generation + 1,
        issues={LANE: entry},
        previous_checkpoint_sha256=current.generation_sha256,
        created_at=common.now(),
    )
    context.checkpoints.accept(checkpoint)

    _run(
        [
            "freeze",
            "--run-dir",
            str(run_dir),
            "--issue-id",
            LANE,
            "--expected-result-sha256",
            result_sha,
        ],
        capsys,
    )
    freeze_sha = context.checkpoints.current(rebuild_pointer=True).value["issues"][
        LANE
    ]["artifact"]["lane_freeze_sha256"]
    assert isinstance(freeze_sha, str)
    assert (
        bc.main(["verify", "--run-dir", str(run_dir), "--issue-id", LANE, "--json"])
        == 1
    )
    verified = json.loads(capsys.readouterr().out)
    assert verified["status"] == "blocked"

    review = integration_common.reviewer_record(
        run_id=run_id,
        target_kind="lane_freeze",
        target_sha256=freeze_sha,
        reviewer_id="reviewer-independent",
        implementer_ids=["worker-implementer"],
    )
    review_path = integration_common.write_review(modules, run_dir, review)
    _run(
        [
            "review",
            "--run-dir",
            str(run_dir),
            "--issue-id",
            LANE,
            "--review-path",
            str(review_path),
        ],
        capsys,
    )

    candidate_input = tmp_path / "candidate.json"
    _write_json(
        candidate_input,
        {"lane_freeze_sha256s": [freeze_sha], "expected_predecessor": head},
    )
    assert (
        bc.main(
            [
                "build-candidate",
                "--run-dir",
                str(run_dir),
                "--input",
                str(candidate_input),
                "--json",
            ]
        )
        == 1
    )
    build_result = json.loads(capsys.readouterr().out)
    assert build_result["status"] == "blocked"
    candidates = list((run_dir / "candidates").iterdir())
    assert len(candidates) == 1
    candidate_id = candidates[0].name
    candidate_path = candidates[0] / "candidate.json"
    candidate_sha = bc.state.sha256_bytes(candidate_path.read_bytes())
    combined_review = integration_common.reviewer_record(
        run_id=run_id,
        target_kind="combined_candidate",
        target_sha256=candidate_sha,
        reviewer_id="reviewer-combined-independent",
        implementer_ids=["worker-implementer"],
    )
    combined_review_path = integration_common.write_review(
        modules, run_dir, combined_review
    )
    _run(
        [
            "review-combined",
            "--run-dir",
            str(run_dir),
            "--review-path",
            str(combined_review_path),
        ],
        capsys,
    )
    _run(
        [
            "apply-candidate",
            "--run-dir",
            str(run_dir),
            "--candidate-id",
            candidate_id,
            "--expected-predecessor",
            head,
        ],
        capsys,
    )

    close_input = tmp_path / "tracker-close.json"
    _write_json(
        close_input,
        {"action": "close", "issues": [LANE], "reason": "independently verified"},
    )
    _run(
        [
            "tracker-update",
            "--run-dir",
            str(run_dir),
            "--input",
            str(close_input),
            "--actor",
            "parent",
        ],
        capsys,
    )

    root_record = ownership.inspect_readonly(ROOT_ISSUE).record
    assert root_record is not None
    finish_input = tmp_path / "finish.json"
    _write_json(
        finish_input,
        {
            "terminal_status": "completed",
            "git_common_dir": str(repo / ".git"),
            "scope_issue_ids": [LANE],
            "base_git_commit": head,
            "authority_snapshot_sha256": "b" * 64,
            "ownership_epoch": root_record["epoch"],
        },
    )
    finished = _run(
        [
            "finish",
            "--run-dir",
            str(run_dir),
            "--input",
            str(finish_input),
            "--actor",
            "parent",
        ],
        capsys,
    )

    assert finished["status"] == "success"
    assert (repo / "src" / "atomic.py").read_text(encoding="utf-8") == "value = 1\n"
    assert ownership.inspect_readonly(LANE).disposition == "released"
    assert ownership.inspect_readonly(ROOT_ISSUE).disposition == "released"
    pointer = json.loads(pointer_metadata[bc.coordinator_tracker._POINTER_METADATA_KEY])
    assert pointer == {
        "ownership_epoch": root_record["epoch"],
        "run_id": run_id,
        "schema_version": "beads.run-pointer.v1",
        "status": "terminal",
    }
    journal = context.journal.read().records
    assert any(
        event["effect_type"] == bc.coordinator_integration.EFFECT_FREEZE
        and event["status"] == "APPLIED"
        for event in journal
        if event["phase"] == "RESOLUTION"
    )
    assert any(
        event["effect_type"] == bc.coordinator_integration.EFFECT_APPLY
        and event["status"] == "APPLIED"
        for event in journal
        if event["phase"] == "RESOLUTION"
    )
    assert fake.count("claim_exact") == 1
    assert fake.count("close_exact") == 1
    assert fake.count("set_run_pointer") == 2
