"""AC-T13-002 (action/receipt variant matrix, tracker-update slice): the
``tracker-update`` subcommand's aggregation of ``coordinator_tracker.claim_front``'s
per-lane ``LaneClaimResult`` list into one envelope-level status.

``_handle_tracker_update`` (see ``beads_coordinator.py`` lines 555-599) never
re-derives claim semantics itself -- it only maps each result's raw status
through the shared ``_map_direct_status`` table and aggregates the mapped set
with an explicit priority: conflict > inconclusive > partial > success, with
an empty issue list (or an all-``APPLIED`` list) landing on ``partial``/
``success`` respectively. This file drives that aggregation end to end
through a real ``bc.main()`` dispatch, monkeypatching only
``coordinator_tracker.claim_front`` itself -- proving the CLI's own
aggregation logic, not re-proving ``claim_front``'s own ownership/dispatch
behavior (already covered by ``scripts/tests/beads_tracker/test_coordinator_tracker.py``).
"""

from __future__ import annotations

import json

from . import _common as common

bc = common.bc

ROOT_ISSUE = "scc-root"
LANE_A = "scc-lane-a"
LANE_B = "scc-lane-b"


def _lane(issue_id: str, status: str, *, error_code: str | None = None):
    return bc.coordinator_tracker.LaneClaimResult(
        issue_id=issue_id,
        status=status,
        classification=None,
        ownership_epoch=None,
        error_code=error_code,
    )


def _write_json(path, payload) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _argv(run, input_path, *, actor="parent"):
    return [
        "tracker-update",
        "--run-dir",
        str(run["run_directory"]),
        "--input",
        str(input_path),
        "--actor",
        actor,
        "--json",
    ]


def test_all_applied_reports_success(tmp_path, monkeypatch, capsys):
    run = common.make_run(
        tmp_path, issue_ids=[LANE_A, LANE_B], root_issue_id=ROOT_ISSUE
    )
    monkeypatch.setattr(
        bc.coordinator_tracker,
        "claim_front",
        lambda *a, **k: [
            _lane(LANE_A, bc.direct_operation.APPLIED),
            _lane(LANE_B, bc.direct_operation.APPLIED),
        ],
    )
    input_path = tmp_path / "tracker-update.json"
    _write_json(input_path, {"issues": [LANE_A, LANE_B]})

    exit_code = bc.main(_argv(run, input_path))
    out = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert out["operation"] == "execute_set"
    assert out["status"] == "success"
    assert out["error_code"] is None
    assert out["coverage_gaps"] == []
    assert out["issue_ids"] == [LANE_A, LANE_B]


def test_empty_issue_list_reports_partial_with_no_pending_actions_and_exits_nonzero(
    tmp_path, capsys
):
    """An empty ``issues`` list means ``claim_front`` is never even called
    with anything to do -- ``mapped`` is the empty set, which the handler's
    ``if not mapped or mapped == {"success"}:`` branch reports as
    ``"partial"`` (not ``"success"``) since ``mapped`` is falsy. Because
    ``_handle_tracker_update`` never populates ``pending_actions``,
    ``operation_result.result_exit_code``'s ``status == "partial" and
    pending_actions`` carve-out does not apply here, so this still exits
    non-zero despite reporting "partial" rather than a hard failure status.
    """
    run = common.make_run(tmp_path, issue_ids=[], root_issue_id=ROOT_ISSUE)
    input_path = tmp_path / "tracker-update.json"
    _write_json(input_path, {"issues": []})

    exit_code = bc.main(_argv(run, input_path))
    out = json.loads(capsys.readouterr().out)

    assert out["status"] == "partial"
    assert out["error_code"] == "PARTIAL"
    assert out["coverage_gaps"] == []
    assert exit_code == 1


def test_refused_lane_mixed_with_applied_reports_partial_with_its_own_error_code(
    tmp_path, monkeypatch, capsys
):
    """A ``REFUSED`` lane (e.g. the root issue slipping into ``issues``) maps
    to ``"blocked"``, which -- mixed with a ``"success"``-mapped lane and no
    ``"conflict"``/``"inconclusive"`` entries -- falls through to the
    handler's final ``else: "partial"`` branch, not ``"success"`` and not
    the raw ``"blocked"`` value itself.
    """
    run = common.make_run(tmp_path, issue_ids=[LANE_A], root_issue_id=ROOT_ISSUE)
    monkeypatch.setattr(
        bc.coordinator_tracker,
        "claim_front",
        lambda *a, **k: [
            _lane(LANE_A, bc.direct_operation.APPLIED),
            _lane(
                ROOT_ISSUE,
                "REFUSED",
                error_code="COORDINATOR_TRACKER_ROOT_ISSUE_INELIGIBLE",
            ),
        ],
    )
    input_path = tmp_path / "tracker-update.json"
    _write_json(input_path, {"issues": [LANE_A, ROOT_ISSUE]})

    exit_code = bc.main(_argv(run, input_path))
    out = json.loads(capsys.readouterr().out)

    assert out["status"] == "partial"
    assert out["error_code"] == "COORDINATOR_TRACKER_ROOT_ISSUE_INELIGIBLE"
    assert len(out["coverage_gaps"]) == 1
    assert out["safe_next_action"] is not None
    assert exit_code == 1


def test_any_conflict_reports_conflict_and_exit_4_even_alongside_applied(
    tmp_path, monkeypatch, capsys
):
    run = common.make_run(
        tmp_path, issue_ids=[LANE_A, LANE_B], root_issue_id=ROOT_ISSUE
    )
    monkeypatch.setattr(
        bc.coordinator_tracker,
        "claim_front",
        lambda *a, **k: [
            _lane(LANE_A, bc.direct_operation.APPLIED),
            _lane(
                LANE_B, bc.direct_operation.CONFLICT, error_code="LANE_CLAIM_CONFLICT"
            ),
        ],
    )
    input_path = tmp_path / "tracker-update.json"
    _write_json(input_path, {"issues": [LANE_A, LANE_B]})

    exit_code = bc.main(_argv(run, input_path))
    out = json.loads(capsys.readouterr().out)

    assert out["status"] == "conflict"
    assert out["error_code"] == "LANE_CLAIM_CONFLICT"
    assert exit_code == 4


def test_unknown_without_conflict_reports_inconclusive_and_exit_5(
    tmp_path, monkeypatch, capsys
):
    run = common.make_run(
        tmp_path, issue_ids=[LANE_A, LANE_B], root_issue_id=ROOT_ISSUE
    )
    monkeypatch.setattr(
        bc.coordinator_tracker,
        "claim_front",
        lambda *a, **k: [
            _lane(LANE_A, bc.direct_operation.APPLIED),
            _lane(
                LANE_B,
                bc.direct_operation.UNKNOWN,
                error_code="COORDINATOR_TRACKER_OWNERSHIP_UNKNOWN",
            ),
        ],
    )
    input_path = tmp_path / "tracker-update.json"
    _write_json(input_path, {"issues": [LANE_A, LANE_B]})

    exit_code = bc.main(_argv(run, input_path))
    out = json.loads(capsys.readouterr().out)

    assert out["status"] == "inconclusive"
    assert out["error_code"] == "COORDINATOR_TRACKER_OWNERSHIP_UNKNOWN"
    assert exit_code == 5


def test_unknown_and_not_applied_without_conflict_prefers_inconclusive(
    tmp_path, monkeypatch, capsys
):
    """Priority order confirmation: ``inconclusive`` outranks a plain
    ``"blocked"``-mapped (``NOT_APPLIED``) entry when no ``"conflict"``
    entry is present at all.
    """
    run = common.make_run(
        tmp_path, issue_ids=[LANE_A, LANE_B], root_issue_id=ROOT_ISSUE
    )
    monkeypatch.setattr(
        bc.coordinator_tracker,
        "claim_front",
        lambda *a, **k: [
            _lane(
                LANE_A,
                bc.direct_operation.NOT_APPLIED,
                error_code="LANE_CLAIM_NOT_APPLIED",
            ),
            _lane(LANE_B, bc.direct_operation.UNKNOWN, error_code="LANE_CLAIM_UNKNOWN"),
        ],
    )
    input_path = tmp_path / "tracker-update.json"
    _write_json(input_path, {"issues": [LANE_A, LANE_B]})

    exit_code = bc.main(_argv(run, input_path))
    out = json.loads(capsys.readouterr().out)

    assert out["status"] == "inconclusive"
    assert exit_code == 5


def test_forwards_issues_and_actor_verbatim_to_claim_front(
    tmp_path, monkeypatch, capsys
):
    run = common.make_run(
        tmp_path, issue_ids=[LANE_A, LANE_B], root_issue_id=ROOT_ISSUE
    )
    captured = {}

    def fake_claim_front(context, *, ownership, issues, actor):
        captured["issues"] = list(issues)
        captured["actor"] = actor
        return [_lane(issue_id, bc.direct_operation.APPLIED) for issue_id in issues]

    monkeypatch.setattr(bc.coordinator_tracker, "claim_front", fake_claim_front)
    input_path = tmp_path / "tracker-update.json"
    _write_json(input_path, {"issues": [LANE_A, LANE_B]})

    exit_code = bc.main(_argv(run, input_path, actor="reviewer"))

    assert exit_code == 0
    assert captured == {"issues": [LANE_A, LANE_B], "actor": "reviewer"}


def test_missing_issues_field_exits_2_with_input_missing_fields(tmp_path, capsys):
    run = common.make_run(tmp_path, issue_ids=[], root_issue_id=ROOT_ISSUE)
    input_path = tmp_path / "tracker-update.json"
    _write_json(input_path, {})

    exit_code = bc.main(_argv(run, input_path))
    out = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert out["error_code"] == "INPUT_MISSING_FIELDS"


def _checkpoint_entry(
    run,
    issue_id,
    *,
    verification="passed",
    review="passed",
    integration="primary_integrated",
):
    return {
        "tracker_status_observed": "in_progress",
        "readiness": {"state": "ready", "reason": ""},
        "ownership": {
            "state": "held",
            "epoch": run["epochs"][issue_id],
            "token_sha256": "a" * 64,
            "actor": run["actor"],
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
            "record_sha256": "b" * 64,
        },
        "artifact": {"state": "verified", "lane_freeze_sha256": "c" * 64},
        "verification": {"state": verification, "record_sha256": "d" * 64},
        "review": {
            "state": review,
            "record_sha256": "e" * 64 if review == "passed" else None,
        },
        "integration": {
            "state": integration,
            "candidate_sha256": "f" * 64,
            "event_id": "1" * 64,
        },
        "gate": {"state": "none", "gate_id": None},
        "packet_sha256": "2" * 64,
        "result_sha256": "b" * 64,
        "worktree": None,
        "branch": None,
        "base_sha": None,
        "head_sha": None,
    }


def _accept_checkpoint(run, entries):
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
            "max_parallel": 3,
            "max_ready_fronts": 10,
            "max_worker_attempts_per_issue": 2,
            "max_nonprogress_rounds": 2,
        },
        "issues": entries,
        "operation_journal_path": str(run["run_directory"] / "operations.jsonl"),
        "issue_snapshot_sha256": "0" * 64,
        "ready_front_sha256": "0" * 64,
        "previous_checkpoint_sha256": bc.state.GENESIS_SHA256,
        "created_at": common.now(),
    }
    run["checkpoints"].accept(checkpoint)


def _applied(operation):
    return bc.direct_operation.DirectOperationResult(
        status=bc.direct_operation.APPLIED,
        caller_key=operation.caller_key,
        operation_id="3" * 64,
        effect_type=operation.effect_type,
        attempt_id="attempt-001",
        classification=bc.direct_operation.INTENDED_EFFECT_PRESENT,
        observed={"status": "closed"},
        marker_present=True,
        dispatched=True,
        error_code=None,
        prepared=None,
        resolution=None,
        evidence_path=None,
    )


def test_close_dispatches_only_verified_primary_integrated_lanes_in_a_mixed_batch(
    tmp_path, monkeypatch, capsys
):
    run = common.make_run(
        tmp_path, issue_ids=[LANE_A, LANE_B], root_issue_id=ROOT_ISSUE
    )
    _accept_checkpoint(
        run,
        {
            LANE_A: _checkpoint_entry(run, LANE_A),
            LANE_B: _checkpoint_entry(run, LANE_B, verification="failed"),
        },
    )
    dispatched = []

    def execute(_context, operation, **_kwargs):
        dispatched.append(operation)
        return _applied(operation)

    monkeypatch.setattr(bc.direct_operation, "execute", execute)
    input_path = tmp_path / "tracker-close.json"
    _write_json(
        input_path,
        {"action": "close", "issues": [LANE_A, LANE_B], "reason": "verified"},
    )

    exit_code = bc.main(_argv(run, input_path))
    out = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert out["status"] == "partial"
    assert out["error_code"] == "TRACKER_CLOSE_LANE_NOT_ELIGIBLE"
    assert [operation.issue_id for operation in dispatched] == [LANE_A]
    assert dispatched[0].effect_type == "TRACKER_CLOSE"
    assert dispatched[0].ownership_epoch == run["epochs"][LANE_A]


def test_close_requires_the_run_parent_actor_and_dispatches_nothing_for_a_worker(
    tmp_path, monkeypatch, capsys
):
    run = common.make_run(tmp_path, issue_ids=[LANE_A], root_issue_id=ROOT_ISSUE)
    _accept_checkpoint(run, {LANE_A: _checkpoint_entry(run, LANE_A)})
    called = False

    def execute(*_args, **_kwargs):
        nonlocal called
        called = True
        raise AssertionError("worker must not close")

    monkeypatch.setattr(bc.direct_operation, "execute", execute)
    input_path = tmp_path / "tracker-close.json"
    _write_json(
        input_path, {"action": "close", "issues": [LANE_A], "reason": "verified"}
    )

    exit_code = bc.main(_argv(run, input_path, actor="worker"))
    out = json.loads(capsys.readouterr().out)

    assert exit_code == 4
    assert out["error_code"] == "TRACKER_CLOSE_PARENT_REQUIRED"
    assert called is False


def test_successful_close_is_checkpointed_for_finish_recovery(
    tmp_path, monkeypatch, capsys
):
    run = common.make_run(tmp_path, issue_ids=[LANE_A], root_issue_id=ROOT_ISSUE)
    _accept_checkpoint(run, {LANE_A: _checkpoint_entry(run, LANE_A)})
    monkeypatch.setattr(
        bc.direct_operation,
        "execute",
        lambda _context, operation, **_kwargs: _applied(operation),
    )
    input_path = tmp_path / "tracker-close-checkpoint.json"
    _write_json(
        input_path, {"action": "close", "issues": [LANE_A], "reason": "verified"}
    )

    assert bc.main(_argv(run, input_path)) == 0
    capsys.readouterr()
    current = run["checkpoints"].current(rebuild_pointer=True).value
    assert current["issues"][LANE_A]["tracker_status_observed"] == "closed"
