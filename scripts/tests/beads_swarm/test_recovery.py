"""AC-T16-004: crash injection converges by durable probe, never blind replay."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from . import _common as common
from . import test_durable_handoff as durable_support

RECOVERY_FIXTURE = common.fixture("04_crash_resume.json")
TRACKER_COMMON = common.ROOT / "scripts" / "tests" / "beads_tracker" / "_common.py"
tracker_common = common._load(TRACKER_COMMON, "beads_swarm_recovery_tracker_common")
tracker_modules = tracker_common.modules(
    "direct_operation", "coordinator_handoff", "protected_action", "coordinator_tracker"
)
do = tracker_modules.direct_operation
ch = tracker_modules.coordinator_handoff
ct = tracker_modules.coordinator_tracker
pa = tracker_modules.protected_action
state = tracker_modules.coordinator_state
safe_bd = tracker_modules.safe_bd
DIRECT_ISSUE = "scc-direct-close"
CRASH_TESTED_FLOWS = {
    "start_run_initial_publication",
    "lane_freeze",
    "lane_verify",
    "lane_review_record",
    "candidate_build",
    "candidate_apply",
    "durable_handoff_launch",
    "durable_handoff_accept",
    "direct_operation_close",
    "claim_front",
    "close_lanes",
    "protected_action_resolve",
    "approval_consume",
    "finish_run",
}


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

    def __init__(self, *, status: str = "in_progress") -> None:
        self.issue = {
            "id": DIRECT_ISSUE,
            "status": status,
            "assignee": "parent",
        }
        self.comments: list[dict[str, str]] = []
        self.calls: list[Any] = []
        self.claim_count = 0
        self.close_count = 0

    @property
    def profiles(self) -> list[str]:
        return [call.profile for call in self.calls]

    def __call__(self, request: Any, *, sensitive: Any = None) -> Any:
        del sensitive
        self.calls.append(request)
        if request.profile == "ready_list":
            value = [
                {
                    **self.issue,
                    "blocked_by": [],
                    "defer_until": None,
                }
            ]
        elif request.profile == "issue_comments":
            value: Any = list(self.comments)
        elif request.profile == "issue_get":
            value = dict(self.issue)
        elif request.profile == "append_marker_note":
            self.comments.append({"text": request.arguments["content"]})
            value = {"ok": True}
        elif request.profile == "claim_exact":
            self.claim_count += 1
            self.issue["status"] = "in_progress"
            value = dict(self.issue)
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


class StatefulRootPointerNative:
    """Round-trip root run pointers for real consecutive coordinator runs."""

    def __init__(self, root_issue_id: str) -> None:
        self.root_issue_id = root_issue_id
        self.metadata: dict[str, str] = {}
        self.calls: list[Any] = []

    def __call__(self, request: Any, *, sensitive: Any = None) -> Any:
        del sensitive
        self.calls.append(request)
        if request.profile == "issue_get":
            value = {"id": self.root_issue_id, "metadata": dict(self.metadata)}
        elif request.profile == "set_run_pointer":
            self.metadata[ct._POINTER_METADATA_KEY] = request.arguments["value"]
            value = {"id": self.root_issue_id, "metadata": dict(self.metadata)}
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
    boundary = str(point["boundary"])
    durable_boundaries = {
        "after_journal_write",
        "after_journal_fsync",
        "after_checkpoint_acceptance",
        "after_pointer_publication",
    }
    if selector == "initial_publication":
        return boundary in durable_boundaries | {
            "after_request_publication",
            "after_run_directory_create",
            "after_manifest_rename",
            "after_operation_effect",
        }
    if selector == "journal_checkpoint_pointer":
        return boundary in durable_boundaries
    if selector == "approval":
        return boundary in {"after_journal_write", "after_journal_fsync"}
    if selector in {"after_handoff_", "after_operation_", "after_finish_"}:
        return boundary in durable_boundaries or boundary.startswith(selector)
    return selector == "all"


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


def _prepared_lane(
    tmp_path: Path,
    issue_id: str = "scc-recovery",
    *,
    path: str = "src/recovery.py",
) -> tuple[dict, str]:
    swarm = common.setup_swarm(
        tmp_path,
        [
            {
                "issue_id": issue_id,
                "path": path,
                "allowed": path,
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


def _prepared_integrated_lane(tmp_path: Path) -> dict[str, Any]:
    swarm, result_sha = _prepared_lane(tmp_path, issue_id=DIRECT_ISSUE)
    ci = swarm["modules"].coordinator_integration
    freeze_sha = common.freeze_and_verify(swarm, DIRECT_ISSUE, result_sha)
    built = ci.build_candidate(swarm["context"], lane_freeze_sha256s=[freeze_sha])
    assert built["status"] == "success"
    applied = ci.apply_candidate(
        swarm["context"],
        built["candidate_id"],
        expected_predecessor=swarm["head"],
    )
    assert applied["status"] == "success"
    return swarm


def _start_request(
    tmp_path: Path, request_id: str = "request-crash-inventory"
) -> tuple[Any, Any]:
    repo = tmp_path.resolve() / "repo"
    repo.mkdir()
    run_root = repo / ".hermes" / "beads-runs"
    run_root.mkdir(parents=True, mode=0o700)
    root_issue = "scc-crash-root"
    request = state.StartRunInput(
        request_id=request_id,
        repository_root=str(repo),
        git_common_dir=str(repo / ".git"),
        workspace=str(repo),
        run_root=str(run_root),
        root_issue_id=root_issue,
        scope_issue_ids=(),
        actor="parent",
        base_git_commit="a" * 40,
        authority_snapshot_sha256="b" * 64,
        workspace_identity_sha256="c" * 64,
    )
    return request, StatefulRootPointerNative(root_issue)


def _approval_grant(run: dict[str, Any]) -> tuple[dict[str, Any], str]:
    operation_id = state.sha256_bytes(b"swarm-conformance-design-decision")
    grant = {
        "schema_version": "beads.approval-record.v1",
        "approval_id": state.sha256_bytes(b"swarm-conformance-approval"),
        "run_id": run["run_id"],
        "issue_id": DIRECT_ISSUE,
        "ownership_epoch": run["epochs"][DIRECT_ISSUE],
        "provenance_class": "parent_attested",
        "approver_identity": "parent",
        "evidence_source": "parent-transcript",
        "evidence_sha256": state.sha256_bytes(b"parent-attested-evidence"),
        "authorized_operation_id": operation_id,
        "decision_type": "design_decision",
        "target_sha256": state.sha256_bytes(b"approved-target"),
        "precondition_sha256": state.sha256_bytes(b"approval-prestate"),
        "scope": ["design_decision"],
        "one_shot": True,
        "granted_at": tracker_common.now(),
        "expiry_policy": "no_expiry",
        "expires_at": None,
        "revocation_channel": "parent-transcript",
    }
    return grant, operation_id


def _consume_approval(
    run: dict[str, Any], hook: Callable[[str], None]
) -> dict[str, Any]:
    grant, operation_id = _approval_grant(run)
    return pa.consume_approval_grant(
        _direct_context(run, hook),
        grant,
        protected_class="design_decision",
        authorized_operation_id=operation_id,
        target_sha256=grant["target_sha256"],
        precondition_sha256=grant["precondition_sha256"],
        ownership_epoch=run["epochs"][DIRECT_ISSUE],
        responder_identity="parent",
        issue_id=DIRECT_ISSUE,
    )


def _protected_resolution_setup(
    tmp_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], Callable[..., Any]]:
    run = _direct_run(tmp_path)
    target_text = "swarm harness observed protected target"
    target_sha = state.sha256_bytes(target_text.encode())
    prepared = pa.prepare_protected_action(
        _direct_context(run, state.NOOP_HOOK),
        effect_type="TRACKER_DOLT_PUSH",
        target_identity="dolt://origin/main",
        target_sha256=target_sha,
        precondition_sha256=state.sha256_bytes(b"prior-remote-head"),
        summary="sync tracker state",
        probe_type="dolt_history",
        probe_argv=["/usr/bin/dolt", "ls-remote", "origin", "main"],
        issue_id=DIRECT_ISSUE,
        ownership_epoch=run["epochs"][DIRECT_ISSUE],
    )
    pending = prepared["pending_action"]
    receipt = {
        "schema_version": "beads.harness-receipt.v1",
        "receipt_variant": "protected_harness_effect",
        "action_id": pending["action_id"],
        "operation_id": pending["operation_id"],
        "target_sha256": pending["target_sha256"],
        "action_sha256": pending["action_id"],
        "outcome": "applied",
        "observed_identity": "harness observed target",
        "observed_sha256": target_sha,
        "evidence": {
            "path": "/tmp/swarm-protected-action.log",
            "sha256": state.sha256_bytes(b"swarm-protected-action-evidence"),
            "summary": "harness ran protected action",
        },
        "harness": "current-harness",
        "provider": "manual",
        "version": "1.0.0",
        "timestamp": tracker_common.now(),
    }
    fake_result = type(
        "FakeSafeCommandResult",
        (),
        {"exit_code": 0, "error_code": None, "status": "SUCCESS"},
    )()

    def runner(*_args: Any, **_kwargs: Any) -> tuple[Any, str]:
        return fake_result, target_text

    return run, prepared, receipt, runner


def _record_successful_flow(tmp_path: Path, flow_id: str) -> list[dict[str, Any]]:
    trace = TraceRecorder()
    if flow_id == "start_run_initial_publication":
        request, native = _start_request(tmp_path)
        result = ct.start_run(
            request,
            actor="parent",
            now=tracker_common.now(),
            runner=native,
            crash_hook=trace,
        )
        assert result.disposition == "active"
    elif flow_id == "lane_freeze":
        swarm, result_sha = _prepared_lane(tmp_path)
        swarm["context"].crash_hook = trace
        result = swarm["modules"].coordinator_integration.freeze_lane(
            swarm["context"], "scc-recovery", expected_result_sha256=result_sha
        )
        assert result["status"] == "success"
    elif flow_id == "lane_verify":
        swarm, result_sha = _prepared_lane(tmp_path)
        ci = swarm["modules"].coordinator_integration
        frozen = ci.freeze_lane(
            swarm["context"], "scc-recovery", expected_result_sha256=result_sha
        )
        assert frozen["status"] == "success"
        swarm["context"].crash_hook = trace
        result = ci.verify_lane(swarm["context"], "scc-recovery")
        assert result["status"] in {"success", "partial"}
    elif flow_id == "lane_review_record":
        swarm, result_sha = _prepared_lane(tmp_path, path="src/security.py")
        ci = swarm["modules"].coordinator_integration
        frozen = ci.freeze_lane(
            swarm["context"], "scc-recovery", expected_result_sha256=result_sha
        )
        verified = ci.verify_lane(swarm["context"], "scc-recovery")
        assert verified["status"] == "partial"
        review = common.integration.reviewer_record(
            run_id=common.RUN_ID,
            target_kind="lane_freeze",
            target_sha256=frozen["freeze_sha256"],
            reviewer_id="reviewer-scc-recovery",
            implementer_ids=["worker-scc-recovery"],
        )
        review_path = common.integration.write_review(
            swarm["modules"], swarm["run"]["run_directory"], review
        )
        swarm["context"].crash_hook = trace
        result = ci.record_review(swarm["context"], "scc-recovery", review_path)
        assert result["status"] == "success"
    elif flow_id in {"candidate_build", "candidate_apply"}:
        swarm, result_sha = _prepared_lane(tmp_path)
        ci = swarm["modules"].coordinator_integration
        freeze = common.freeze_and_verify(swarm, "scc-recovery", result_sha)
        if flow_id == "candidate_build":
            swarm["context"].crash_hook = trace
        built = ci.build_candidate(swarm["context"], lane_freeze_sha256s=[freeze])
        if flow_id == "candidate_apply":
            swarm["context"].crash_hook = trace
            applied = ci.apply_candidate(
                swarm["context"],
                built["candidate_id"],
                expected_predecessor=swarm["head"],
            )
            assert applied["status"] == "success"

    elif flow_id == "durable_handoff_launch":
        run = _direct_run(tmp_path)
        result = ch.launch(
            _direct_context(run, trace), handoff=_handoff(run), actor="parent"
        )
        assert result.status == do.APPLIED
    elif flow_id == "durable_handoff_accept":
        native = durable_support._native_success()
        _fixture, run, handoff, executor_result = durable_support._execute(
            tmp_path, native
        )
        context = durable_support._context(run)
        context.crash_hook = trace
        accepted = durable_support.ch.accept(
            context,
            handoff=handoff,
            result=executor_result,
            operation=durable_support._operation(run),
            actor="parent",
            ownership=run["ownership"],
            runner=native,
        )
        assert accepted.status == durable_support.do.APPLIED
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
    elif flow_id == "claim_front":
        repo = tmp_path / "repo"
        repo.mkdir()
        run = tracker_common.make_run(tracker_modules, repo)
        native = StatefulCloseNative(status="open")
        result = ct.claim_front(
            _direct_context(run, trace),
            ownership=run["ownership"],
            issues=[DIRECT_ISSUE],
            actor="parent",
            runner=native,
        )[0]
        assert result.status == do.APPLIED
        assert native.claim_count == 1
    elif flow_id == "close_lanes":
        swarm = _prepared_integrated_lane(tmp_path)
        native = StatefulCloseNative()
        context = _direct_context(
            {**swarm["run"], "checkpoints": swarm["context"].checkpoints}, trace
        )
        result = ct.close_lanes(
            context,
            ownership=swarm["modules"].beads_ownership.OwnershipStore.open_existing(
                swarm["run"]["run_directory"].parent
            ),
            issues=[DIRECT_ISSUE],
            actor="parent",
            reason="verified and integrated",
            runner=native,
        )[0]
        assert result.status == do.APPLIED
        assert native.close_count == 1
    elif flow_id == "approval_consume":
        run = _direct_run(tmp_path)
        result = _consume_approval(run, trace)
        assert result["resolution"]["status"] == do.APPLIED
    elif flow_id == "protected_action_resolve":
        run, prepared, receipt, runner = _protected_resolution_setup(tmp_path)
        result = pa.resolve_protected_action(
            _direct_context(run, trace),
            prepared=prepared["prepared"],
            pending_action=prepared["pending_action"],
            receipt=receipt,
            runner=runner,
        )
        assert result["status"] == pa.APPLIED
    elif flow_id == "finish_run":
        request, native = _start_request(tmp_path, "request-finish-inventory")
        started = ct.start_run(
            request, actor="parent", now=tracker_common.now(), runner=native
        )
        ownership = tracker_modules.beads_ownership.OwnershipStore(
            Path(request.run_root)
        )
        root_record = ownership.inspect_readonly(request.root_issue_id).record
        assert root_record is not None
        finished = ct.finish_run(
            request,
            run_directory=started.run_directory,
            scope_issue_ids=[],
            ownership_epoch=root_record["epoch"],
            terminal_status="cancelled",
            actor="parent",
            runner=native,
            crash_hook=trace,
        )
        assert finished.status == do.APPLIED
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

    Every required successful parent flow contributes its journal, native,
    checkpoint, pointer, approval, or flow-specific semantic boundaries.
    """
    observed = [
        point
        for point in _record_successful_flow(tmp_path, str(flow["id"]))
        if _in_flow_scope(flow, point)
    ]
    assert flow["crash_points"] == observed


@pytest.mark.parametrize(
    "family,flow_id",
    [
        (family, flow_id)
        for family, flows in RECOVERY_FIXTURE["boundary_families"].items()
        for flow_id in flows["required_flows"]
        if family in {"journal", "checkpoint", "pointer"}
    ],
)
def test_manifest_cannot_omit_recorded_durable_boundary_family_points(
    tmp_path: Path, family: str, flow_id: str
) -> None:
    prefixes = {
        "journal": {"after_journal_write", "after_journal_fsync"},
        "checkpoint": {"after_checkpoint_acceptance", "after_finish_checkpoint"},
        "pointer": {"after_pointer_publication", "after_finish_pointer"},
    }
    recorded = _record_successful_flow(tmp_path, flow_id)
    required = [point for point in recorded if point["boundary"] in prefixes[family]]
    assert required, f"{flow_id} emitted no {family} boundary"
    assert all(point in _flow(flow_id)["crash_points"] for point in required)


def test_every_manifest_flow_has_an_actual_crash_resume_exercise() -> None:
    assert {
        flow["id"] for flow in RECOVERY_FIXTURE["crash_flows"]
    } == CRASH_TESTED_FLOWS


@pytest.mark.parametrize(
    "crash_point",
    _flow("start_run_initial_publication")["crash_points"],
    ids=lambda point: f"{point['boundary']}:{point['occurrence']}",
)
def test_start_run_resumes_at_every_initial_publication_boundary(
    tmp_path: Path, crash_point: dict[str, Any]
) -> None:
    request, native = _start_request(tmp_path)
    crashing = CrashOnce(str(crash_point["boundary"]), int(crash_point["occurrence"]))
    with pytest.raises(RuntimeError, match="injected crash"):
        ct.start_run(
            request,
            actor="parent",
            now=tracker_common.now(),
            runner=native,
            crash_hook=crashing,
        )
    try:
        first = ct.start_run(
            request, actor="parent", now=tracker_common.now(), runner=native
        )
    except ct.state.StateError as first_error:
        assert first_error.code == "OPERATION_ID_REUSE_CONFLICT"
        assert first_error.status in {"conflict", "unknown"}
        with pytest.raises(ct.state.StateError) as repeated:
            ct.start_run(
                request, actor="parent", now=tracker_common.now(), runner=native
            )
        assert repeated.value.code == first_error.code
        assert repeated.value.status == first_error.status
    else:
        second = ct.start_run(
            request, actor="parent", now=tracker_common.now(), runner=native
        )
        assert first.disposition == second.disposition == "active"
        assert first.run_id == second.run_id
    assert crashing.crashed_at == int(crash_point["occurrence"])
    assert sum(call.profile == "set_run_pointer" for call in native.calls) <= 1


@pytest.mark.parametrize(
    "flow_id,crash_point",
    [
        (flow_id, point)
        for flow_id in ("candidate_build", "candidate_apply")
        for point in _flow(flow_id)["crash_points"]
    ],
    ids=lambda value: value
    if isinstance(value, str)
    else f"{value['boundary']}:{value['occurrence']}",
)
def test_candidate_recovery_converges_without_blind_replay(
    tmp_path: Path, flow_id: str, crash_point: dict[str, Any]
) -> None:
    swarm, result_sha = _prepared_lane(tmp_path)
    ci = swarm["modules"].coordinator_integration
    freeze = common.freeze_and_verify(swarm, "scc-recovery", result_sha)
    built = None
    if flow_id == "candidate_apply":
        built = ci.build_candidate(swarm["context"], lane_freeze_sha256s=[freeze])
    crashing = CrashOnce(str(crash_point["boundary"]), int(crash_point["occurrence"]))
    swarm["context"].crash_hook = crashing
    with pytest.raises(RuntimeError, match="injected crash"):
        if flow_id == "candidate_build":
            ci.build_candidate(swarm["context"], lane_freeze_sha256s=[freeze])
        else:
            assert built is not None
            ci.apply_candidate(
                swarm["context"],
                built["candidate_id"],
                expected_predecessor=swarm["head"],
            )
    resumed = ci.open_run(swarm["run"]["run_directory"])
    if flow_id == "candidate_build":
        first = ci.build_candidate(resumed, lane_freeze_sha256s=[freeze])
        second = ci.build_candidate(resumed, lane_freeze_sha256s=[freeze])
        assert first["candidate_id"] == second["candidate_id"]
    else:
        assert built is not None
        try:
            first = ci.apply_candidate(
                resumed, built["candidate_id"], expected_predecessor=swarm["head"]
            )
        except ci.IntegrationError as first_error:
            assert first_error.status in RECOVERY_FIXTURE["expected_terminal_states"]
        else:
            assert first["status"] in RECOVERY_FIXTURE["expected_terminal_states"]
            with pytest.raises(ci.IntegrationError) as repeat:
                ci.apply_candidate(
                    resumed, built["candidate_id"], expected_predecessor=swarm["head"]
                )
            assert repeat.value.status in RECOVERY_FIXTURE["expected_terminal_states"]
        assert (
            int(
                common.git(
                    swarm["repo"], "rev-list", "--count", f"{swarm['head']}..HEAD"
                )
            )
            <= 1
        )
    assert crashing.crashed_at == int(crash_point["occurrence"])


@pytest.mark.parametrize(
    "flow_id,crash_point",
    [
        (flow_id, point)
        for flow_id in ("claim_front", "close_lanes")
        for point in _flow(flow_id)["crash_points"]
    ],
    ids=lambda value: value
    if isinstance(value, str)
    else f"{value['boundary']}:{value['occurrence']}",
)
def test_parent_tracker_flow_resume_never_duplicates_native_effect(
    tmp_path: Path, flow_id: str, crash_point: dict[str, Any]
) -> None:
    native = StatefulCloseNative(
        status="open" if flow_id == "claim_front" else "in_progress"
    )
    if flow_id == "claim_front":
        repo = tmp_path / "repo"
        repo.mkdir()
        run = tracker_common.make_run(tracker_modules, repo)
        ownership = run["ownership"]
    else:
        swarm = _prepared_integrated_lane(tmp_path)
        run = {**swarm["run"], "checkpoints": swarm["context"].checkpoints}
        ownership = swarm["modules"].beads_ownership.OwnershipStore.open_existing(
            swarm["run"]["run_directory"].parent
        )

    def invoke(context: Any) -> Any:
        if flow_id == "claim_front":
            return ct.claim_front(
                context,
                ownership=ownership,
                issues=[DIRECT_ISSUE],
                actor="parent",
                runner=native,
            )[0]
        return ct.close_lanes(
            context,
            ownership=ownership,
            issues=[DIRECT_ISSUE],
            actor="parent",
            reason="verified and integrated",
            runner=native,
        )[0]

    crashing = CrashOnce(str(crash_point["boundary"]), int(crash_point["occurrence"]))
    with pytest.raises(RuntimeError, match="injected crash"):
        invoke(_direct_context(run, crashing))
    result = invoke(do.open_run(run["run_directory"]))
    assert result.status in {do.APPLIED, do.CONFLICT, do.UNKNOWN}
    native_count = (
        native.claim_count if flow_id == "claim_front" else native.close_count
    )
    assert native_count <= 1
    if native_count == 0:
        assert result.status != do.APPLIED


@pytest.mark.parametrize(
    "crash_point",
    _flow("protected_action_resolve")["crash_points"],
    ids=lambda point: f"{point['boundary']}:{point['occurrence']}",
)
def test_protected_action_resolution_recovers_by_durable_probe_without_replay(
    tmp_path: Path, crash_point: dict[str, Any]
) -> None:
    run, prepared, receipt, runner = _protected_resolution_setup(tmp_path)
    context = _direct_context(run, state.NOOP_HOOK)
    crashing = CrashOnce(str(crash_point["boundary"]), int(crash_point["occurrence"]))
    context.crash_hook = crashing
    with pytest.raises(RuntimeError, match="injected crash"):
        pa.resolve_protected_action(
            context,
            prepared=prepared["prepared"],
            pending_action=prepared["pending_action"],
            receipt=receipt,
            runner=runner,
        )
    resolutions = tracker_common.journal_records(
        run, effect_type="TRACKER_DOLT_PUSH", phase="RESOLUTION"
    )
    assert len(resolutions) == 1
    assert resolutions[0]["status"] == pa.APPLIED


@pytest.mark.parametrize(
    "crash_point",
    _flow("approval_consume")["crash_points"],
    ids=lambda point: f"{point['boundary']}:{point['occurrence']}",
)
def test_approval_consume_resume_is_one_shot(
    tmp_path: Path, crash_point: dict[str, Any]
) -> None:
    run = _direct_run(tmp_path)
    crashing = CrashOnce(str(crash_point["boundary"]), int(crash_point["occurrence"]))
    with pytest.raises(RuntimeError, match="injected crash"):
        _consume_approval(run, crashing)
    resumed = do.open_run(run["run_directory"])
    resumed_run = {
        **run,
        "journal": resumed.journal,
        "checkpoints": resumed.checkpoints,
    }
    try:
        first = _consume_approval(resumed_run, state.NOOP_HOOK)
    except pa.ProtectedActionError as first_error:
        assert first_error.code == "OPERATION_ID_REUSE_CONFLICT"
        assert first_error.status in {"conflict", "unknown"}
        with pytest.raises(pa.ProtectedActionError) as repeated:
            _consume_approval(resumed_run, state.NOOP_HOOK)
        assert repeated.value.code == first_error.code
        assert repeated.value.status == first_error.status
    else:
        second = _consume_approval(resumed_run, state.NOOP_HOOK)
        assert (
            first["resolution"]["status"]
            == second["resolution"]["status"]
            == do.APPLIED
        )
    records = resumed.journal.read().records
    consumes = [
        r for r in records if r.get("effect_type") == pa.APPROVAL_CONSUME_EFFECT_TYPE
    ]
    assert len([r for r in consumes if r["phase"] == "PREPARED"]) == 1
    assert len([r for r in consumes if r["phase"] == "RESOLUTION"]) <= 1


@pytest.mark.parametrize(
    "crash_point",
    _flow("durable_handoff_accept")["crash_points"],
    ids=lambda point: f"{point['boundary']}:{point['occurrence']}",
)
def test_durable_handoff_accept_resume_never_duplicates_acceptance(
    tmp_path: Path, crash_point: dict[str, Any]
) -> None:
    native = durable_support._native_success()
    _fixture, run, handoff, executor_result = durable_support._execute(tmp_path, native)
    context = durable_support._context(run)
    crashing = CrashOnce(str(crash_point["boundary"]), int(crash_point["occurrence"]))
    context.crash_hook = crashing
    with pytest.raises(RuntimeError, match="injected crash"):
        durable_support.ch.accept(
            context,
            handoff=handoff,
            result=executor_result,
            operation=durable_support._operation(run),
            actor="parent",
            ownership=run["ownership"],
            runner=native,
        )
    resumed = durable_support._context(run)
    result = durable_support.ch.accept(
        resumed,
        handoff=handoff,
        result=executor_result,
        operation=durable_support._operation(run),
        actor="parent",
        ownership=run["ownership"],
        runner=native,
    )
    assert result.status in {durable_support.do.APPLIED, durable_support.do.CONFLICT}
    if result.status == durable_support.do.CONFLICT:
        assert result.error_code == "HANDOFF_RESULT_DUPLICATE"
    records = resumed.journal.read().records
    accepts = [
        r
        for r in records
        if r.get("effect_type") == durable_support.ch.ACCEPT_EFFECT_TYPE
    ]
    assert len([r for r in accepts if r["phase"] == "PREPARED"]) == 1
    assert len([r for r in accepts if r["phase"] == "RESOLUTION"]) <= 1


def test_two_consecutive_interruptions_converge_without_replaying_close(
    tmp_path: Path,
) -> None:
    run = _direct_run(tmp_path)
    native = StatefulCloseNative()
    operation = _close_operation(run)
    first_crash = CrashOnce("after_operation_prepared")
    with pytest.raises(RuntimeError, match="injected crash"):
        do.execute(
            _direct_context(run, first_crash), operation, actor="parent", runner=native
        )
    assert native.close_count == 0

    second_crash = CrashOnce("after_operation_effect")
    resumed_once = do.open_run(run["run_directory"], crash_hook=second_crash)
    with pytest.raises(RuntimeError, match="injected crash"):
        do.execute(resumed_once, operation, actor="parent", runner=native)
    assert native.close_count == 1

    resumed_twice = do.open_run(run["run_directory"])
    third = do.execute(resumed_twice, operation, actor="parent", runner=native)
    fourth = do.execute(resumed_twice, operation, actor="parent", runner=native)
    assert third.status == fourth.status == do.APPLIED
    assert native.close_count == 1


@pytest.mark.parametrize(
    "crash_point",
    _flow("finish_run")["crash_points"],
    ids=lambda point: f"{point['boundary']}:{point['occurrence']}",
)
def test_finish_run_resumes_at_every_release_and_terminal_pointer_boundary(
    tmp_path: Path, crash_point: dict[str, Any]
) -> None:
    request, native = _start_request(tmp_path, "request-finish-crash")
    started = ct.start_run(
        request, actor="parent", now=tracker_common.now(), runner=native
    )
    ownership = tracker_modules.beads_ownership.OwnershipStore(Path(request.run_root))
    root_record = ownership.inspect_readonly(request.root_issue_id).record
    assert root_record is not None
    crashing = CrashOnce(str(crash_point["boundary"]), int(crash_point["occurrence"]))
    kwargs = {
        "run_directory": started.run_directory,
        "scope_issue_ids": [],
        "ownership_epoch": root_record["epoch"],
        "terminal_status": "cancelled",
        "actor": "parent",
        "runner": native,
    }
    with pytest.raises(RuntimeError, match="injected crash"):
        ct.finish_run(request, crash_hook=crashing, **kwargs)
    first = ct.finish_run(request, **kwargs)
    second = ct.finish_run(request, **kwargs)
    assert first.status == second.status == do.APPLIED
    assert ownership.inspect_readonly(request.root_issue_id).disposition == "released"


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
    _flow("lane_verify")["crash_points"],
    ids=lambda point: f"{point['boundary']}:{point['occurrence']}",
)
def test_lane_verify_recovers_by_durable_probe_without_replay(
    tmp_path: Path, crash_point: dict[str, Any]
) -> None:
    swarm, result_sha = _prepared_lane(tmp_path)
    ci = swarm["modules"].coordinator_integration
    frozen = ci.freeze_lane(
        swarm["context"], "scc-recovery", expected_result_sha256=result_sha
    )
    assert frozen["status"] == "success"
    crashing = CrashOnce(str(crash_point["boundary"]), int(crash_point["occurrence"]))
    swarm["context"].crash_hook = crashing

    with pytest.raises(RuntimeError, match="injected crash"):
        ci.verify_lane(swarm["context"], "scc-recovery")

    resumed = ci.open_run(swarm["run"]["run_directory"])
    current = resumed.checkpoints.current(rebuild_pointer=True)
    entry = ci._issue_entry(current, "scc-recovery")
    assert entry["artifact"]["state"] == "verified"
    assert entry["verification"]["state"] == "passed"
    record_path = (
        resumed.run_directory
        / "lanes"
        / state.issue_key("scc-recovery")
        / "parent-verification.json"
    )
    record = state.validate_owner_file(record_path, root=resumed.run_directory)
    assert (
        state.sha256_bytes(record.read_bytes())
        == entry["verification"]["record_sha256"]
    )
    assert crashing.crashed_at == int(crash_point["occurrence"])


@pytest.mark.parametrize(
    "crash_point",
    _flow("lane_review_record")["crash_points"],
    ids=lambda point: f"{point['boundary']}:{point['occurrence']}",
)
def test_lane_review_recovers_by_durable_probe_without_replay(
    tmp_path: Path, crash_point: dict[str, Any]
) -> None:
    swarm, result_sha = _prepared_lane(tmp_path, path="src/security.py")
    ci = swarm["modules"].coordinator_integration
    frozen = ci.freeze_lane(
        swarm["context"], "scc-recovery", expected_result_sha256=result_sha
    )
    assert ci.verify_lane(swarm["context"], "scc-recovery")["status"] == "partial"
    review = common.integration.reviewer_record(
        run_id=common.RUN_ID,
        target_kind="lane_freeze",
        target_sha256=frozen["freeze_sha256"],
        reviewer_id="reviewer-scc-recovery",
        implementer_ids=["worker-scc-recovery"],
    )
    review_path = common.integration.write_review(
        swarm["modules"], swarm["run"]["run_directory"], review
    )
    crashing = CrashOnce(str(crash_point["boundary"]), int(crash_point["occurrence"]))
    swarm["context"].crash_hook = crashing

    with pytest.raises(RuntimeError, match="injected crash"):
        ci.record_review(swarm["context"], "scc-recovery", review_path)

    resumed = ci.open_run(swarm["run"]["run_directory"])
    entry = ci._issue_entry(
        resumed.checkpoints.current(rebuild_pointer=True), "scc-recovery"
    )
    assert entry["artifact"]["state"] == "verified"
    assert entry["review"]["state"] == "passed"
    assert (
        state.sha256_bytes(review_path.read_bytes()) == entry["review"]["record_sha256"]
    )
    assert crashing.crashed_at == int(crash_point["occurrence"])


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
    repo = tmp_path.resolve() / "repo"
    repo.mkdir()
    run_root = repo / ".hermes" / "beads-runs"
    run_root.mkdir(parents=True, mode=0o700)
    root_issue = "scc-consecutive-root"
    native = StatefulRootPointerNative(root_issue)
    run_ids = []
    for index in range(consecutive["expected_runs"]):
        request = state.StartRunInput(
            request_id=f"request-consecutive-root-{index}",
            repository_root=str(repo),
            git_common_dir=str(repo / ".git"),
            workspace=str(repo),
            run_root=str(run_root),
            root_issue_id=root_issue,
            scope_issue_ids=(),
            actor="parent",
            base_git_commit="a" * 40,
            authority_snapshot_sha256="b" * 64,
            workspace_identity_sha256="c" * 64,
        )
        started = ct.start_run(
            request, actor="parent", now=tracker_common.now(), runner=native
        )
        assert started.disposition == "active"
        run_ids.append(started.run_id)
        ownership = tracker_modules.beads_ownership.OwnershipStore(run_root)
        root_record = ownership.inspect_readonly(root_issue).record
        assert root_record is not None
        finished = ct.finish_run(
            request,
            run_directory=started.run_directory,
            scope_issue_ids=[],
            ownership_epoch=root_record["epoch"],
            terminal_status="cancelled",
            actor="parent",
            runner=native,
        )
        assert finished.status == do.APPLIED
        manifest = state.load_run_manifest(started.run_directory)
        assert manifest["repository_root"] == str(repo)
    assert len(set(run_ids)) == consecutive["expected_runs"]


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
