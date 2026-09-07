"""AC-T16-004: crash injection converges by durable probe, never blind replay."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from . import _common as common

RECOVERY_FIXTURE = common.fixture("04_crash_resume.json")
TRACKER_COMMON = common.ROOT / "scripts" / "tests" / "beads_tracker" / "_common.py"
tracker_common = common._load(TRACKER_COMMON, "beads_swarm_recovery_tracker_common")
tracker_modules = tracker_common.modules("direct_operation", "coordinator_handoff")
do = tracker_modules.direct_operation
ch = tracker_modules.coordinator_handoff
state = tracker_modules.coordinator_state
safe_bd = tracker_modules.safe_bd
DIRECT_ISSUE = "scc-direct-close"


class CrashOnce:
    def __init__(self, label: str, occurrence: int = 1) -> None:
        self.label = label
        self.occurrence = occurrence
        self.seen = 0
        self.crashed_at: int | None = None

    def __call__(self, event: str) -> None:
        if event == self.label:
            self.seen += 1
            if self.seen == self.occurrence:
                self.crashed_at = self.seen
                raise RuntimeError(f"injected crash: {event}:{self.seen}")


class TraceRecorder:
    """Record the production hook trace as label/occurrence coordinates."""

    def __init__(self) -> None:
        self.counts: Counter[str] = Counter()
        self.points: list[dict[str, Any]] = []

    def __call__(self, event: str) -> None:
        self.counts[event] += 1
        self.points.append({"boundary": event, "occurrence": self.counts[event]})


class StatefulCloseNative:
    """A minimal stateful tracker: retries observe whether close really landed."""

    def __init__(self) -> None:
        self.issue = {
            "id": DIRECT_ISSUE,
            "status": "in_progress",
            "assignee": "parent",
        }
        self.comments: list[dict[str, str]] = []
        self.calls: list[Any] = []
        self.close_count = 0

    @property
    def profiles(self) -> list[str]:
        return [call.profile for call in self.calls]

    def __call__(self, request: Any, *, sensitive: Any = None) -> Any:
        del sensitive
        self.calls.append(request)
        if request.profile == "issue_comments":
            value: Any = list(self.comments)
        elif request.profile == "issue_get":
            value = dict(self.issue)
        elif request.profile == "append_marker_note":
            self.comments.append({"text": request.arguments["content"]})
            value = {"ok": True}
        elif request.profile == "close_exact":
            self.close_count += 1
            self.issue["status"] = "closed"
            value = dict(self.issue)
        else:
            raise AssertionError(f"unexpected tracker profile: {request.profile}")
        return safe_bd.SafeBdResult(
            "beads.safe-bd-result.v1",
            request.profile,
            "ok",
            safe_bd.PINNED_BD_VERSION,
            "a" * 64,
            value,
            (),
            None,
        )


def _flow(flow_id: str) -> dict[str, Any]:
    return next(
        flow for flow in RECOVERY_FIXTURE["crash_flows"] if flow["id"] == flow_id
    )


def _in_flow_scope(flow: dict[str, Any], point: dict[str, Any]) -> bool:
    selector = str(flow["boundary_selector"])
    return selector == "all" or str(point["boundary"]).startswith(selector)


def _direct_context(run: dict[str, Any], hook: Callable[[str], None]) -> Any:
    return do.RunContext(
        run_directory=run["run_directory"],
        manifest=run["manifest"],
        journal=run["journal"],
        checkpoints=run["checkpoints"],
        crash_hook=hook,
    )


def _direct_run(tmp_path: Path) -> dict[str, Any]:
    repo = tmp_path / "repo"
    repo.mkdir()
    return tracker_common.make_run(tracker_modules, repo, issue_ids=[DIRECT_ISSUE])


def _close_operation(run: dict[str, Any]) -> Any:
    return do.DirectOperation(
        caller_key="swarm-conformance/close",
        effect_type="TRACKER_CLOSE",
        target_identity=f"bd://issue/{DIRECT_ISSUE}",
        issue_id=DIRECT_ISSUE,
        ownership_epoch=run["epochs"][DIRECT_ISSUE],
        arguments={"issue_id": DIRECT_ISSUE, "reason": "verified"},
        readback=do.Readback(
            profile="issue_get",
            arguments={"issue_id": DIRECT_ISSUE},
            intended={"status": "closed"},
            prestate={"status": "in_progress"},
        ),
    )


def _handoff(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "beads.durable-handoff.v1",
        "run_id": run["run_id"],
        "handoff_id": "b" * 64,
        "root_issue_id": run["root_issue_id"],
        "scope_issue_ids": [DIRECT_ISSUE],
        "held_ownership": [
            {"issue_id": DIRECT_ISSUE, "epoch": run["epochs"][DIRECT_ISSUE]}
        ],
        "tracker_sha256": "0" * 64,
        "dependency_sha256": "1" * 64,
        "ready_front_sha256": "2" * 64,
        "authority_sha256": "3" * 64,
        "base_commit": "0" * 40,
        "isolation_target": str(run["repo"]),
        "unresolved_gates": [],
        "stages": ["execute"],
        "resume_topology": ["execute"],
        "executor_type": "pas",
        "executor_identity": "durable-conformance-executor",
        "beads_authority": "readonly",
        "allowed_effects": {
            "repository_write": True,
            "local_commit": False,
            "git_remote": False,
            "dolt_remote": False,
            "external_side_effects": False,
            "beads_mutation": False,
        },
        "required_result_schema": "/durable-executor-result-v1.schema.json",
        "created_at": tracker_common.now(),
        "expires_at": "2999-01-01T00:00:00.000000Z",
    }


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
    child = common.run_children(
        swarm,
        timeout=RECOVERY_FIXTURE["timeout_seconds"],
        output_limit=RECOVERY_FIXTURE["output_limit_bytes"],
    )[issue_id]
    assert child.returncode == 0, child
    result_sha = common.import_lane(swarm, issue_id)
    common.checkpoint(swarm, {issue_id: result_sha})
    return swarm, result_sha


def _record_successful_flow(tmp_path: Path, flow_id: str) -> list[dict[str, Any]]:
    trace = TraceRecorder()
    if flow_id == "lane_freeze":
        swarm, result_sha = _prepared_lane(tmp_path)
        swarm["context"].crash_hook = trace
        result = swarm["modules"].coordinator_integration.freeze_lane(
            swarm["context"], "scc-recovery", expected_result_sha256=result_sha
        )
        assert result["status"] == "success"
    elif flow_id == "durable_handoff_launch":
        run = _direct_run(tmp_path)
        result = ch.launch(
            _direct_context(run, trace), handoff=_handoff(run), actor="parent"
        )
        assert result.status == do.APPLIED
    elif flow_id == "direct_operation_close":
        run = _direct_run(tmp_path)
        native = StatefulCloseNative()
        result = do.execute(
            _direct_context(run, trace),
            _close_operation(run),
            actor="parent",
            runner=native,
        )
        assert result.status == do.APPLIED
        assert native.close_count == 1
    else:
        raise AssertionError(f"unknown crash-conformance flow: {flow_id}")
    return trace.points


@pytest.mark.parametrize(
    "flow",
    RECOVERY_FIXTURE["crash_flows"],
    ids=lambda flow: flow["id"],
)
def test_crash_manifest_is_exactly_the_recorded_successful_production_trace(
    tmp_path: Path, flow: dict[str, Any]
) -> None:
    """The fixture cannot validate itself: production execution is the oracle.

    Only the three successful parent flows named in the fixture are in T16's
    crash scope. Hooks reachable solely from bootstrap, ownership maintenance,
    finish-run, or rejection paths are unrelated and intentionally excluded.
    Within each named flow, however, every emitted hook occurrence is required.
    """
    observed = [
        point
        for point in _record_successful_flow(tmp_path, str(flow["id"]))
        if _in_flow_scope(flow, point)
    ]
    assert flow["crash_points"] == observed


@pytest.mark.parametrize(
    "crash_point",
    _flow("lane_freeze")["crash_points"],
    ids=lambda point: f"{point['boundary']}:{point['occurrence']}",
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

    # A resumed process does not retain the test-only crash injector.
    swarm["context"].crash_hook = None
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
    assert crashing.crashed_at == int(crash_point["occurrence"])
    assert crashing.crashed_at is not None
    assert crashing.seen >= crashing.crashed_at

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


@pytest.mark.parametrize(
    "crash_point",
    _flow("durable_handoff_launch")["crash_points"],
    ids=lambda point: f"{point['boundary']}:{point['occurrence']}",
)
def test_durable_handoff_launch_resumes_at_every_recorded_boundary(
    tmp_path: Path, crash_point: dict[str, Any]
) -> None:
    run = _direct_run(tmp_path)
    handoff = _handoff(run)
    crashing = CrashOnce(str(crash_point["boundary"]), int(crash_point["occurrence"]))
    with pytest.raises(RuntimeError, match="injected crash"):
        ch.launch(_direct_context(run, crashing), handoff=handoff, actor="parent")

    resumed = do.open_run(run["run_directory"])
    first = ch.launch(resumed, handoff=handoff, actor="parent")
    second = ch.launch(resumed, handoff=handoff, actor="parent")
    assert first.status == second.status == do.APPLIED
    assert second.already_launched is True
    assert crashing.crashed_at == int(crash_point["occurrence"])
    records = resumed.journal.read().records
    launches = [r for r in records if r.get("effect_type") == ch.LAUNCH_EFFECT_TYPE]
    assert len([r for r in launches if r["phase"] == "PREPARED"]) == 1
    assert len([r for r in launches if r["phase"] == "RESOLUTION"]) == 1


@pytest.mark.parametrize(
    "crash_point",
    _flow("direct_operation_close")["crash_points"],
    ids=lambda point: f"{point['boundary']}:{point['occurrence']}",
)
def test_direct_close_resumes_at_every_recorded_boundary_without_blind_replay(
    tmp_path: Path, crash_point: dict[str, Any]
) -> None:
    run = _direct_run(tmp_path)
    operation = _close_operation(run)
    native = StatefulCloseNative()
    crashing = CrashOnce(str(crash_point["boundary"]), int(crash_point["occurrence"]))
    with pytest.raises(RuntimeError, match="injected crash"):
        do.execute(
            _direct_context(run, crashing), operation, actor="parent", runner=native
        )

    resumed = do.open_run(run["run_directory"])
    first = do.execute(resumed, operation, actor="parent", runner=native)
    close_count = native.close_count
    second = do.execute(resumed, operation, actor="parent", runner=native)
    assert first.status in {do.APPLIED, do.UNKNOWN}
    assert second.status == first.status
    assert native.close_count == close_count <= 1
    assert crashing.crashed_at == int(crash_point["occurrence"])
    if first.status == do.UNKNOWN:
        assert native.close_count == 0
        assert first.error_code == "DIRECT_OPERATION_AMBIGUOUS_CAUSALITY"
    else:
        assert native.close_count == 1


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


def _scenario(name: str) -> dict[str, Any]:
    return next(
        case for case in RECOVERY_FIXTURE["recovery_scenarios"] if case["id"] == name
    )


def test_consecutive_roots_and_repeat_resume_are_independently_idempotent(
    tmp_path: Path,
) -> None:
    consecutive = _scenario("consecutive_roots")
    repeat = _scenario("repeat_resume")
    outcomes = []
    for index in range(consecutive["expected_runs"]):
        root = tmp_path / f"root-{index}"
        root.mkdir()
        issue = f"scc-consecutive-{index}"
        swarm, result_sha = _prepared_lane(root, issue)
        ci = swarm["modules"].coordinator_integration
        first = ci.freeze_lane(
            swarm["context"], issue, expected_result_sha256=result_sha
        )
        resumed = ci.open_run(swarm["run"]["run_directory"])
        second = ci.freeze_lane(resumed, issue, expected_result_sha256=result_sha)
        assert first["status"] == repeat["expected_first"]
        assert second["status"] == repeat["expected_repeat"]
        assert first["freeze_sha256"] == second["freeze_sha256"]
        outcomes.append(second["status"])
    assert outcomes == [consecutive["expected_status"]] * consecutive["expected_runs"]


def test_unknown_late_child_with_superseded_epoch_is_rejected(tmp_path: Path) -> None:
    expected = _scenario("unknown_late_child")
    swarm, result_sha = _prepared_lane(tmp_path)
    ownership = swarm["modules"].beads_ownership.OwnershipStore.open_existing(
        swarm["run"]["run_directory"].parent
    )
    epoch = swarm["run"]["epochs"]["scc-recovery"]
    ownership.release(
        "scc-recovery",
        swarm["run"]["run_directory"],
        epoch=epoch,
        operation_id="7" * 64,
        now=None,
    )
    ownership.acquire(
        issue_id="scc-recovery",
        actor="parent",
        run_directory=swarm["run"]["run_directory"],
        tracker_state_sha256="0" * 64,
        operation_id="8" * 64,
        now=None,
    )
    ci = swarm["modules"].coordinator_integration
    with pytest.raises(ci.IntegrationError) as refused:
        ci.freeze_lane(
            swarm["context"], "scc-recovery", expected_result_sha256=result_sha
        )
    assert refused.value.code == expected["expected_error"]
