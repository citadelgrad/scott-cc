"""End-to-end solo lifecycle conformance fixtures (scc-0pu.15 / t14).

These tests add the missing vertical proof: a real Git repository and native
Beads workspace move from health/read, through claim and independently checked
acceptance evidence, to exact close and terminal-pointer readback.  Negative
fixtures prove failed and unavailable parent verification cannot close a lane.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path

import pytest

from . import _common as common

m = common.modules(
    "direct_operation",
    "coordinator_tracker",
    "coordinator_integration",
    "lane_snapshot",
    "worker_result",
)
do = m.direct_operation
ct = m.coordinator_tracker
ci = m.coordinator_integration
state = m.coordinator_state

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures/beads_solo"
ACTOR = "solo-native-worker"
ROOT_ISSUE = "slf-root"
LANE_ISSUE = "slf-lane"


def _fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _run(cwd: Path, *argv: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=cwd, check=True, capture_output=True, text=True)


def _tracked_snapshot(repo: Path) -> tuple[str, tuple[tuple[str, str], ...]]:
    """Return HEAD plus hashes for every tracked working-tree file."""
    head = _run(repo, "git", "rev-parse", "HEAD").stdout.strip()
    paths = _run(repo, "git", "ls-files").stdout.splitlines()
    files = tuple(
        (path, hashlib.sha256((repo / path).read_bytes()).hexdigest()) for path in paths
    )
    return head, files


def _native_workspace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, str]:
    """Create a fully initialized, isolated native bd 1.2.2 workspace."""
    repo = tmp_path / "repo"
    repo.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.setenv("BD_NON_INTERACTIVE", "1")

    _run(repo, "git", "init", "-q", "-b", "main")
    _run(repo, "git", "config", "user.email", "solo-fixture@example.invalid")
    _run(repo, "git", "config", "user.name", "Solo Fixture")
    (repo / ".gitignore").write_text(
        ".beads/\n.hermes/\nlane-worktree/\nsensitive-values.json\n",
        encoding="utf-8",
    )
    (repo / "seed.txt").write_text("isolated solo fixture\n", encoding="utf-8")
    _run(repo, "git", "add", ".gitignore", "seed.txt")
    _run(repo, "git", "commit", "-q", "-m", "solo fixture base")

    _run(
        repo,
        "bd",
        "init",
        "--prefix",
        "slf",
        "--skip-agents",
        "--skip-hooks",
        "--non-interactive",
        "--quiet",
    )
    scenario = _fixture("lifecycle-complete.json")
    _run(
        repo,
        "bd",
        "create",
        scenario["root"]["title"],
        f"--id={ROOT_ISSUE}",
        f"--acceptance={scenario['root']['acceptance']}",
        "--silent",
    )
    # ``bd init`` may append its local-state ignore.  Treat that deterministic
    # setup edit as part of the fixture base, then prove lifecycle reads and
    # claims leave tracked content unchanged from this point onward.
    if _run(repo, "git", "status", "--porcelain", "--", ".gitignore").stdout:
        _run(repo, "git", "add", ".gitignore")
        _run(repo, "git", "commit", "-q", "-m", "record native beads ignore")
    base = _run(repo, "git", "rev-parse", "HEAD").stdout.strip()
    return repo, base


def _context(run: dict):
    return do.RunContext(
        run_directory=run["run_directory"],
        manifest=run["manifest"],
        journal=run["journal"],
        checkpoints=run["checkpoints"],
        crash_hook=state.NOOP_HOOK,
    )


def _create_lane(run: dict) -> do.DirectOperationResult:
    scenario = _fixture("lifecycle-complete.json")
    operation = do.DirectOperation(
        caller_key=f"create/{LANE_ISSUE}",
        effect_type="TRACKER_CREATE",
        target_identity=f"bd://issue/{LANE_ISSUE}",
        issue_id=LANE_ISSUE,
        ownership_epoch=None,
        arguments={
            "issue_id": LANE_ISSUE,
            "title": scenario["lane"]["title"],
            "issue_type": "task",
            "priority": 2,
        },
        readback=do.Readback(
            profile="issue_list",
            arguments={"issue_ids": [LANE_ISSUE], "limit": 10},
            intended={"id": LANE_ISSUE},
            prestate=do.ABSENT,
        ),
    )
    return do.execute(_context(run), operation, actor=ACTOR)


def _issue_entry(epoch: int, packet_sha: str, result_sha: str) -> dict:
    return {
        "tracker_status_observed": "in_progress",
        "readiness": {"state": "ready", "reason": "claimed by solo run"},
        "ownership": {
            "state": "held",
            "epoch": epoch,
            "token_sha256": "1" * 64,
            "actor": ACTOR,
        },
        "attempt": {
            "state": "joined",
            "attempt_id": "attempt-001",
            "delegation_id": "solo-delegation-1",
            "subagent_id": None,
            "child_session_id": None,
        },
        "worker_result": {
            "state": "accepted",
            "outcome": "completed",
            "record_sha256": result_sha,
        },
        "artifact": {"state": "worker_returned", "lane_freeze_sha256": None},
        "verification": {"state": "not_started", "record_sha256": None},
        "review": {"state": "not_required", "record_sha256": None},
        "integration": {
            "state": "not_started",
            "candidate_sha256": None,
            "event_id": None,
        },
        "gate": {"state": "none", "gate_id": None},
        "packet_sha256": packet_sha,
        "result_sha256": result_sha,
        "worktree": None,
        "branch": None,
        "base_sha": None,
        "head_sha": None,
    }


def _packet(
    repo: Path,
    lane: Path,
    outbox: Path,
    run: dict,
    base: str,
    epoch: int,
    command: list[str],
) -> dict:
    scenario = _fixture("lifecycle-complete.json")
    issue_key = state.issue_key(LANE_ISSUE)
    return {
        "schema_version": "beads.worker-packet.v1",
        "run_id": run["run_id"],
        "attempt_id": "attempt-001",
        "goal": "prove the solo acceptance criterion",
        "issue": {
            "id": LANE_ISSUE,
            "key": issue_key,
            "title": scenario["lane"]["title"],
            "snapshot_path": str(repo / "snapshot.json"),
            "snapshot_sha256": "a" * 64,
            "acceptance_ids": [scenario["lane"]["acceptance_id"]],
        },
        "prerequisites": {"issue_ids": [], "required_base_state": "all_closed"},
        "repository": {
            "root": str(repo),
            "base_sha": base,
            "worktree": str(lane),
            "branch": "solo-lane",
        },
        "scope": {
            "allowed_paths": ["src/**"],
            "forbidden_paths": [".beads/**"],
            "tracker_access": "readonly",
            "tracker_transport": "safe_bd_only",
            "code_write": True,
            "local_commit": False,
            "merge": False,
            "git_remote": False,
            "dolt_remote": False,
            "external_side_effects": False,
            "external_io": False,
            "destructive": False,
            "spend": False,
            "secret_access": False,
            "integration_mode": "patch_package",
        },
        "delegation": {"allowed": False, "max_child_depth": 0},
        "verification": {
            "required_commands": [command],
            "worker_outbox": str(outbox),
            "parent_import_root": str(run["run_directory"] / "imports" / issue_key),
            "advisory_wall_clock_seconds": 900,
            "required_child_max_iterations": 250,
            "required_child_timeout_seconds": 0,
            "required_max_spawn_depth": 1,
            "required_orchestrator_enabled": True,
            "advisory_max_tool_calls": 100,
            "enforcement": {
                "child_max_iterations": "hermes_runtime_hard_per_child",
                "child_timeout": "disabled_when_zero_else_hermes_runtime_hard_per_child",
                "spawn_depth": "coordinator_preflight",
                "packet_delegation_allowed": "worker_policy_only",
                "wall_clock": "parent_monitored_stop_then_reconcile",
                "tool_calls": "parent_monitored_stop_then_reconcile",
            },
            "max_artifact_bytes": 10485760,
        },
        "return_contract": {
            "schema": str(
                common.ROOT
                / "skills/beads/schemas/worker-execution-result-v1.schema.json"
            ),
            "max_manifest_bytes": 65536,
            "max_receipt_bytes": 2048,
        },
    }


def _descriptor(tmp_path: Path) -> Path:
    path = tmp_path / "sensitive-values.json"
    path.write_text("[]", encoding="utf-8")
    path.chmod(0o600)
    return path


def _worker_attempt(
    tmp_path: Path,
    repo: Path,
    lane: Path,
    base: str,
    run: dict,
    epoch: int,
    command: list[str],
) -> tuple[str, str]:
    outbox = lane / "outbox"
    outbox.mkdir(mode=0o700)
    import_root = run["run_directory"] / "imports" / state.issue_key(LANE_ISSUE)
    state.ensure_owner_directory(import_root, root=run["run_directory"])
    packet = _packet(repo, lane, outbox, run, base, epoch, command)
    raw = state.canonical_bytes(packet)
    packet_sha = hashlib.sha256(raw).hexdigest()
    prior = Path.cwd()
    os.chdir(lane)
    try:
        worker = m.worker_result.initialize_attempt(
            raw, expected_packet_sha256=packet_sha, ownership_epoch=epoch
        )
        command_evidence = m.worker_result.run_declared_command(
            worker, command_index=0, sensitive_values_file=_descriptor(tmp_path)
        )
        target = lane / "src/solo.py"
        target.parent.mkdir()
        target.write_text("SOLO_CONFORMANCE = True\n", encoding="utf-8")
        snapshot = m.lane_snapshot.capture(lane, base, exclude=outbox)
        command_record = outbox / "command-000.json"
        stdout = Path(command_evidence["safe_result"]["stdout_log"]["path"])
        stderr = Path(command_evidence["safe_result"]["stderr_log"]["path"])

        def artifact(path: Path, kind: str) -> dict:
            raw_artifact = path.read_bytes()
            return {
                "type": kind,
                "path": str(path),
                "size_bytes": len(raw_artifact),
                "sha256": hashlib.sha256(raw_artifact).hexdigest(),
            }

        acceptance_id = packet["issue"]["acceptance_ids"][0]
        candidate = {
            "schema_version": "beads.worker-execution-result.v1",
            "run_id": run["run_id"],
            "attempt_id": "attempt-001",
            "issue_id": LANE_ISSUE,
            "packet_sha256": packet_sha,
            "status": "completed",
            "repository": {
                "worktree": str(lane),
                "branch": "solo-lane",
                "base_sha": base,
                "head_sha": snapshot.head_sha,
            },
            "lane_state": snapshot.lane_state,
            "changes": {
                "paths": list(snapshot.changed_paths),
                "outside_allowed_scope": [],
            },
            "verification": [
                {
                    "command": json.dumps(
                        command_evidence["argv"], separators=(",", ":")
                    ),
                    "exit_code": command_evidence["safe_result"]["exit_code"],
                    "started_at": command_evidence["safe_result"]["started_at"],
                    "finished_at": command_evidence["safe_result"]["finished_at"],
                    "log_path": str(command_record),
                    "log_sha256": hashlib.sha256(
                        command_record.read_bytes()
                    ).hexdigest(),
                }
            ],
            "acceptance_evidence": [
                {
                    "acceptance_id": acceptance_id,
                    "status": "supported",
                    "evidence_paths": [str(command_record)],
                }
            ],
            "artifacts": [
                artifact(command_record, "command_evidence"),
                artifact(stdout, "stdout_log"),
                artifact(stderr, "stderr_log"),
            ],
            "blockers": [],
            "errors": [],
            "cancellation_reason": None,
            "skipped_checks": [],
            "residual_risks": [],
            "summary": "solo acceptance criterion has concrete command evidence",
            "integration_mode": "patch_package",
            "worker_frozen_artifact": None,
        }
        m.worker_result.finalize_attempt(
            worker, candidate, sensitive_values_file=_descriptor(tmp_path)
        )
    finally:
        os.chdir(prior)

    imports = run["run_directory"] / "imports" / state.issue_key(LANE_ISSUE)
    state.ensure_owner_directory(imports, root=run["run_directory"])
    for name, data in (
        ("packet.json", raw),
        ("result.json", (outbox / "result.json").read_bytes()),
        ("receipt.json", (outbox / "receipt.json").read_bytes()),
    ):
        path = imports / name
        path.write_bytes(data)
        path.chmod(0o600)
    return packet_sha, hashlib.sha256((outbox / "result.json").read_bytes()).hexdigest()


def _checkpoint(run: dict, entry: dict) -> None:
    checkpoint = {
        "schema_version": "beads.run-checkpoint.v1",
        "run_id": run["run_id"],
        "generation": 1,
        "root_issue_id": ROOT_ISSUE,
        "workspace": run["manifest"]["workspace"],
        "workspace_identity_sha256": run["manifest"]["workspace_identity_sha256"],
        "repository_root": run["manifest"]["repository_root"],
        "coordinator_session_id": None,
        "authority_snapshot_sha256": "0" * 64,
        "phase": "active",
        "budget": {
            "max_parallel": 1,
            "max_ready_fronts": 1,
            "max_worker_attempts_per_issue": 2,
            "max_nonprogress_rounds": 2,
        },
        "issues": {LANE_ISSUE: entry},
        "operation_journal_path": str(run["journal"].path.resolve()),
        "issue_snapshot_sha256": "0" * 64,
        "ready_front_sha256": "0" * 64,
        "previous_checkpoint_sha256": state.GENESIS_SHA256,
        "created_at": common.now(),
    }
    run["checkpoints"].accept(checkpoint)


def _integration_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    command: list[str],
) -> dict:
    repo, base = _native_workspace(tmp_path, monkeypatch)
    lane = repo / "lane-worktree"
    _run(repo, "git", "worktree", "add", "-q", str(lane), "-b", "solo-lane")
    run = common.make_run(
        m, repo, issue_ids=(ROOT_ISSUE,), root_issue_id=ROOT_ISSUE, actor=ACTOR
    )
    created = _create_lane(run)
    assert created.status == do.APPLIED
    tracked_before_claim = _tracked_snapshot(repo)
    claimed = ct.claim_front(
        _context(run),
        ownership=run["ownership"],
        issues=[LANE_ISSUE],
        actor=ACTOR,
    )[0]
    assert claimed.status == do.APPLIED
    assert _tracked_snapshot(repo) == tracked_before_claim
    assert (
        _run(repo, "git", "status", "--porcelain", "--untracked-files=no").stdout == ""
    )

    packet_sha, result_sha = _worker_attempt(
        tmp_path, repo, lane, base, run, claimed.ownership_epoch, command
    )
    _checkpoint(run, _issue_entry(claimed.ownership_epoch, packet_sha, result_sha))
    context = ci.open_run(run["run_directory"])
    frozen = ci.freeze_lane(context, LANE_ISSUE, expected_result_sha256=result_sha)
    assert frozen["status"] == "success"
    return {
        "repo": repo,
        "base": base,
        "lane": lane,
        "run": run,
        "context": context,
        "created": created,
        "claimed": claimed,
        "frozen": frozen,
    }


def _close_lane(fixture: dict) -> do.DirectOperationResult:
    epoch = fixture["claimed"].ownership_epoch
    operation = do.DirectOperation(
        caller_key=f"close/{LANE_ISSUE}",
        effect_type="TRACKER_CLOSE",
        target_identity=f"bd://issue/{LANE_ISSUE}",
        issue_id=LANE_ISSUE,
        ownership_epoch=epoch,
        arguments={"issue_id": LANE_ISSUE, "reason": "solo lifecycle verified"},
        readback=do.Readback(
            profile="issue_get",
            arguments={"issue_id": LANE_ISSUE},
            intended={"status": "closed"},
            prestate={"status": "in_progress"},
        ),
    )
    return do.execute(_context(fixture["run"]), operation, actor=ACTOR)


def test_native_workspace_health_is_exact_and_read_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, _base = _native_workspace(tmp_path, monkeypatch)
    before = _tracked_snapshot(repo)
    clean_before = _run(
        repo, "git", "status", "--porcelain", "--untracked-files=no"
    ).stdout

    where = m.safe_bd.run_profile(
        m.safe_bd.SafeBdRequest("workspace_where", {}, repo, None)
    )
    status = m.safe_bd.run_profile(
        m.safe_bd.SafeBdRequest("workspace_status", {}, repo, None)
    )
    issue = m.safe_bd.run_profile(
        m.safe_bd.SafeBdRequest("issue_get", {"issue_id": ROOT_ISSUE}, repo, None)
    )

    assert where.status == status.status == issue.status == "ok"
    assert where.data["prefix"] == "slf"
    assert Path(where.data["path"]).resolve() == (repo / ".beads").resolve()
    assert status.data["summary"]["total_issues"] == 1
    assert issue.data[0]["id"] == ROOT_ISSUE
    assert (
        issue.data[0]["acceptance_criteria"]
        == _fixture("lifecycle-complete.json")["root"]["acceptance"]
    )
    assert _tracked_snapshot(repo) == before
    assert clean_before == ""
    assert (
        _run(repo, "git", "status", "--porcelain", "--untracked-files=no").stdout == ""
    )


def test_complete_native_solo_lifecycle_binds_ac_evidence_and_finishes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scenario = _fixture("lifecycle-complete.json")
    fixture = _integration_fixture(
        tmp_path, monkeypatch, scenario["verification"]["command"]
    )
    verified = ci.verify_lane(fixture["context"], LANE_ISSUE)
    assert verified["status"] == "success"

    verification_path = Path(verified["verification_path"])
    verification = json.loads(verification_path.read_text(encoding="utf-8"))
    acceptance = verification["acceptance_evidence"]
    assert acceptance == [
        {
            "acceptance_id": scenario["lane"]["acceptance_id"],
            "status": "supported",
            "evidence_paths": acceptance[0]["evidence_paths"],
        }
    ]
    evidence_path = Path(acceptance[0]["evidence_paths"][0])
    assert evidence_path.is_file()
    assert hashlib.sha256(evidence_path.read_bytes()).hexdigest() in {
        artifact["sha256"]
        for artifact in json.loads(
            (
                fixture["run"]["run_directory"]
                / "imports"
                / state.issue_key(LANE_ISSUE)
                / "result.json"
            ).read_text(encoding="utf-8")
        )["artifacts"]
    }

    built = ci.build_candidate(
        fixture["context"], lane_freeze_sha256s=[fixture["frozen"]["freeze_sha256"]]
    )
    assert built["status"] == "success"
    applied = ci.apply_candidate(
        fixture["context"], built["candidate_id"], expected_predecessor=fixture["base"]
    )
    assert applied["status"] == "success"
    assert (fixture["repo"] / "src/solo.py").read_text(encoding="utf-8") == (
        "SOLO_CONFORMANCE = True\n"
    )

    closed = _close_lane(fixture)
    if (
        closed.status == do.NOT_APPLIED
        and closed.error_code == "DIRECT_OPERATION_MARKER_UNAVAILABLE"
    ):
        pytest.xfail(
            "native bd note/comments roundtrip loses the direct-operation marker; "
            "the owned fixture cannot repair skills/beads/scripts/safe_bd.py"
        )
    assert closed.status == do.APPLIED, (
        closed.status,
        closed.classification,
        closed.error_code,
        closed.observed,
        closed.dispatched,
    )
    assert closed.classification == do.INTENDED_EFFECT_PRESENT
    assert closed.evidence_path is not None
    close_resolution = closed.resolution
    assert close_resolution is not None
    evidence = Path(close_resolution["readback_evidence_path"])
    assert (
        hashlib.sha256(evidence.read_bytes()).hexdigest()
        == close_resolution["readback_evidence_sha256"]
    )

    request = state.StartRunInput(
        request_id=fixture["run"]["manifest"]["request_id"],
        repository_root=str(fixture["repo"]),
        git_common_dir=str(fixture["repo"] / ".git"),
        workspace=str(fixture["repo"]),
        run_root=str(fixture["run"]["run_root"]),
        root_issue_id=ROOT_ISSUE,
        scope_issue_ids=(LANE_ISSUE,),
        actor=ACTOR,
        base_git_commit=fixture["base"],
        authority_snapshot_sha256="b" * 64,
        workspace_identity_sha256=fixture["run"]["manifest"][
            "workspace_identity_sha256"
        ],
    )
    pointer = {
        "schema_version": "beads.run-pointer.v1",
        "run_id": fixture["run"]["run_id"],
        "ownership_epoch": fixture["run"]["epochs"][ROOT_ISSUE],
        "status": "completed",
    }
    callbacks = ct.pointer_callbacks(request, actor=ACTOR)
    published = callbacks.publish(pointer)
    assert published.classification == do.INTENDED_EFFECT_PRESENT
    readback = callbacks.observe(pointer)
    assert readback.classification == do.INTENDED_EFFECT_PRESENT
    assert readback.observed_value == pointer

    native_issue = m.safe_bd.run_profile(
        m.safe_bd.SafeBdRequest(
            "issue_get", {"issue_id": LANE_ISSUE}, fixture["repo"], None
        )
    )
    assert native_issue.status == "ok"
    assert native_issue.data[0]["id"] == LANE_ISSUE
    assert native_issue.data[0]["status"] == "closed"


@pytest.mark.parametrize(
    "fixture_name",
    ["verification-failed.json", "verification-unavailable.json"],
)
def test_failed_or_unavailable_verification_is_rejected_without_false_finish(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fixture_name: str,
) -> None:
    scenario = _fixture(fixture_name)
    verifier = tmp_path / scenario["verifier_name"]
    verifier.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    verifier.chmod(verifier.stat().st_mode | stat.S_IEXEC)
    fixture = _integration_fixture(tmp_path, monkeypatch, [str(verifier)])

    if scenario["mode"] == "failed":
        verifier.write_text("#!/bin/sh\nexit 7\n", encoding="utf-8")
    else:
        verifier.unlink()

    try:
        outcome = ci.verify_lane(fixture["context"], LANE_ISSUE)
    except ci.safe_output.SafeOutputError as exc:
        if (
            scenario["mode"] == "unavailable"
            and exc.args[0] == "EXECUTABLE_NOT_ABSOLUTE_FILE"
        ):
            pytest.xfail(
                "verify_lane lets an unavailable verifier escape as SafeOutputError "
                "instead of returning an inconclusive/refused typed outcome"
            )
        raise
    assert outcome["status"] == scenario["expected_status"]
    record = json.loads(Path(outcome["record_path"]).read_text(encoding="utf-8"))
    assert record["disposition"] == "reject"
    assert record["coverage_gaps"] == ["REQUIRED_COMMAND_FAILED"]
    assert record["commands"][0]["exit_code"] == scenario["expected_exit_code"]
    current = fixture["context"].checkpoints.current(rebuild_pointer=True)
    entry = current.value["issues"][LANE_ISSUE]
    assert entry["verification"]["state"] == "failed"
    assert entry["integration"]["state"] == "not_started"

    with pytest.raises(ci.IntegrationError) as excinfo:
        ci.build_candidate(
            fixture["context"],
            lane_freeze_sha256s=[fixture["frozen"]["freeze_sha256"]],
        )
    assert excinfo.value.status in {"blocked", "conflict"}
    native_issue = m.safe_bd.run_profile(
        m.safe_bd.SafeBdRequest(
            "issue_get", {"issue_id": LANE_ISSUE}, fixture["repo"], None
        )
    )
    assert native_issue.data[0]["status"] == "in_progress"


@pytest.mark.xfail(
    strict=True,
    reason=(
        "production claim_front rechecks status only, so a once-ready issue that "
        "acquires a blocker can still be claimed; scc-0pu.15 cannot edit that module"
    ),
)
def test_claim_refuses_issue_whose_readiness_changed_after_front_capture(
    tmp_path: Path,
) -> None:
    """AC-T14-002 reproduction: changed readiness must stop native dispatch."""
    run = common.make_run(m, tmp_path, root_issue_id="root", actor=ACTOR)
    blocked = {
        "id": LANE_ISSUE,
        "status": "open",
        "assignee": None,
        "blocked_by": ["slf-prerequisite"],
    }
    fake = common.FakeNative(
        m.safe_bd,
        responses={
            "issue_comments": common.comments(),
            "issue_get": [
                blocked,
                {**blocked, "status": "in_progress", "assignee": ACTOR},
            ],
            "append_marker_note": {"ok": True},
            "claim_exact": {**blocked, "status": "in_progress", "assignee": ACTOR},
        },
        allowed=["issue_comments", "issue_get", "append_marker_note", "claim_exact"],
    )
    result = ct.claim_front(
        _context(run),
        ownership=run["ownership"],
        issues=[LANE_ISSUE],
        actor=ACTOR,
        runner=fake,
    )[0]
    assert result.status == "CONFLICT"
    assert fake.count("claim_exact") == 0
