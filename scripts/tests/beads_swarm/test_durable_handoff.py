"""AC-T16-005: durable execution never transfers Hermes lifecycle ownership."""

from __future__ import annotations

import json
import hashlib
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from . import _common as common

TRACKER_COMMON = common.ROOT / "scripts" / "tests" / "beads_tracker" / "_common.py"
EXECUTOR = Path(__file__).with_name("durable_executor_process.py")
tracker_common = common._load(TRACKER_COMMON, "beads_swarm_tracker_common")
m = tracker_common.modules("direct_operation", "coordinator_handoff")
do = m.direct_operation
ch = m.coordinator_handoff
state = m.coordinator_state
safe_bd = m.safe_bd
ISSUE = "scc-durable"
DURABLE_FIXTURE = common.fixture("05_durable_handoff.json")


def _context(run):
    return do.RunContext(
        run_directory=run["run_directory"],
        manifest=run["manifest"],
        journal=run["journal"],
        checkpoints=run["checkpoints"],
        crash_hook=state.NOOP_HOOK,
    )


def _handoff(run, fixture: dict[str, Any]) -> dict[str, Any]:
    executor = fixture["executor"]
    return {
        "schema_version": "beads.durable-handoff.v1",
        "run_id": run["run_id"],
        "handoff_id": "a" * 64,
        "root_issue_id": run["root_issue_id"],
        "scope_issue_ids": [ISSUE],
        "held_ownership": [{"issue_id": ISSUE, "epoch": run["epochs"][ISSUE]}],
        "tracker_sha256": "0" * 64,
        "dependency_sha256": "1" * 64,
        "ready_front_sha256": "2" * 64,
        "authority_sha256": "3" * 64,
        "base_commit": "0" * 40,
        "isolation_target": str(run["run_directory"]),
        "unresolved_gates": [],
        "stages": ["execute"],
        "resume_topology": ["execute"],
        "executor_type": executor["type"],
        "executor_identity": executor["identity"],
        "beads_authority": executor["beads_authority"],
        "allowed_effects": {
            "repository_write": True,
            "local_commit": False,
            "git_remote": False,
            "dolt_remote": False,
            "external_side_effects": False,
            "beads_mutation": executor["beads_mutation"],
        },
        "required_result_schema": "/durable-executor-result-v1.schema.json",
        "created_at": tracker_common.now(),
        "expires_at": "2999-01-01T00:00:00.000000Z",
    }


def _operation(run):
    return do.DirectOperation(
        caller_key="durable-handoff/accept",
        effect_type="TRACKER_CLAIM",
        target_identity=f"bd://issue/{ISSUE}",
        issue_id=ISSUE,
        ownership_epoch=run["epochs"][ISSUE],
        arguments={"issue_id": ISSUE},
        readback=do.Readback(
            profile="issue_get",
            arguments={"issue_id": ISSUE},
            intended={"status": "in_progress", "assignee": "parent"},
            prestate={"status": "open"},
        ),
    )


def _execute(tmp_path: Path):
    fixture = DURABLE_FIXTURE
    repo = tmp_path / "repo"
    repo.mkdir()
    run = tracker_common.make_run(m, repo, issue_ids=[ISSUE])
    executor_input = tmp_path / "executor-input"
    executor_output = tmp_path / "executor-output"
    executor_input.mkdir(mode=0o700)
    executor_output.mkdir(mode=0o700)
    handoff = _handoff(run, fixture)
    handoff["isolation_target"] = str(executor_output.resolve())
    launched = ch.launch(_context(run), handoff=handoff, actor="parent")
    assert launched.status == do.APPLIED
    frozen = (
        run["run_directory"] / "_operations" / f"{handoff['handoff_id']}.handoff.json"
    )
    executor_handoff = executor_input / "handoff.json"
    shutil.copyfile(frozen, executor_handoff)
    executor_handoff.chmod(0o400)
    frozen_sha256 = hashlib.sha256(frozen.read_bytes()).hexdigest()
    result_path = executor_output / "durable-result.json"
    completed = subprocess.run(
        [sys.executable, str(EXECUTOR), str(executor_handoff), str(result_path)],
        capture_output=True,
        text=True,
        timeout=fixture["timeout_seconds"],
    )
    assert completed.returncode == 0, completed
    assert fixture["max_processes"] == 1
    assert hashlib.sha256(frozen.read_bytes()).hexdigest() == frozen_sha256
    run["durable_paths"] = {
        "frozen": frozen,
        "executor_input": executor_input,
        "executor_output": executor_output,
    }
    return fixture, run, handoff, json.loads(result_path.read_bytes())


def _native_success():
    return tracker_common.FakeNative(
        safe_bd,
        responses={
            "issue_comments": [[]],
            "issue_get": [
                {"id": ISSUE, "status": "open", "assignee": None},
                {"id": ISSUE, "status": "in_progress", "assignee": "parent"},
            ],
            "append_marker_note": {"ok": True},
            "claim_exact": {"id": ISSUE, "status": "in_progress", "assignee": "parent"},
        },
        allowed=["issue_comments", "issue_get", "append_marker_note", "claim_exact"],
    )


def test_durable_executor_return_reenters_parent_verification_without_ownership_transfer(
    tmp_path: Path,
) -> None:
    fixture, run, handoff, result = _execute(tmp_path)
    before = run["ownership"].inspect_readonly(ISSUE).record
    assert before["actor"] == "parent"
    assert handoff["beads_authority"] == "readonly"
    assert handoff["allowed_effects"]["beads_mutation"] is False
    assert result["beads_mutated"] is False
    paths = run["durable_paths"]
    assert paths["executor_output"].parent == paths["executor_input"].parent
    assert paths["executor_output"] not in paths["frozen"].parents
    assert Path(result["artifact"]["path"]).is_relative_to(paths["executor_output"])

    native = _native_success()
    accepted = ch.accept(
        _context(run),
        handoff=handoff,
        result=result,
        operation=_operation(run),
        actor="parent",
        ownership=run["ownership"],
        runner=native,
    )
    assert accepted.guard_passed is True
    assert accepted.status == do.APPLIED
    assert accepted.operation_result and accepted.operation_result.dispatched is True
    assert native.profiles[-1] == "issue_get"  # ordinary parent readback decides
    after = run["ownership"].inspect_readonly(ISSUE).record
    assert after["actor"] == "parent"
    assert after["run_id"] == before["run_id"] == run["run_id"]
    assert after["epoch"] == before["epoch"]
    assert fixture["executor"]["identity"] != after["actor"]


@pytest.mark.parametrize(
    "case",
    DURABLE_FIXTURE["tamper_cases"],
    ids=lambda case: case["id"],
)
def test_untrusted_durable_return_tampering_never_reaches_tracker(
    tmp_path: Path, case: dict[str, str]
) -> None:
    tamper = case["id"]
    case_root = tmp_path / tamper
    case_root.mkdir()
    _fixture, run, handoff, result = _execute(case_root)
    if tamper == "handoff_sha256":
        result["handoff_sha256"] = "f" * 64
    elif tamper == "executor_identity":
        result["executor_identity"] = "forged-executor"
    elif tamper == "artifact_sha256":
        result["artifact"]["sha256"] = "e" * 64
    elif tamper == "artifact_bytes":
        Path(result["artifact"]["path"]).write_bytes(b"tampered after return\n")
    elif tamper == "artifact_path_escape":
        escaped = run["run_directory"] / "executor-controlled.patch"
        escaped.write_bytes(b"outside executor output boundary\n")
        result["artifact"].update(
            {
                "path": str(escaped.resolve()),
                "size_bytes": escaped.stat().st_size,
                "sha256": hashlib.sha256(escaped.read_bytes()).hexdigest(),
            }
        )
    elif tamper == "ownership_epoch":
        run["ownership"].release(
            ISSUE,
            run["run_directory"],
            epoch=run["epochs"][ISSUE],
            operation_id="4" * 64,
            now=datetime.now(timezone.utc),
        )
        run["ownership"].acquire(
            issue_id=ISSUE,
            actor="parent",
            run_directory=run["run_directory"],
            tracker_state_sha256="0" * 64,
            operation_id="5" * 64,
            now=datetime.now(timezone.utc),
        )
    elif tamper == "beads_mutated":
        result["beads_mutated"] = True

    native = tracker_common.FakeNative(safe_bd, responses={}, allowed=[])
    if case["failure_stage"] == "schema":
        with pytest.raises(ch.schema_runtime.ValidationFailure) as refused:
            ch.accept(
                _context(run),
                handoff=handoff,
                result=result,
                operation=_operation(run),
                actor="parent",
                ownership=run["ownership"],
                runner=native,
            )
        assert type(refused.value).__name__ == case["expected_error"]
    else:
        refused = ch.accept(
            _context(run),
            handoff=handoff,
            result=result,
            operation=_operation(run),
            actor="parent",
            ownership=run["ownership"],
            runner=native,
        )
        assert refused.guard_passed is False
        assert refused.error_code == case["expected_error"]
    assert native.calls == []
