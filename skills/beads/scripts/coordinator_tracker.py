"""Guarded tracker facade: claim-front and root-pointer bootstrap ordering.

This module sits directly on top of :mod:`direct_operation` and owns two
things ``bootstrap_run`` itself cannot own because they are policy, not
mechanism:

* :func:`claim_front` — decide which lanes in a run are even eligible to be
  claimed (the root issue never is), acquire local ownership for each
  eligible lane, dispatch the native claim through the guarded four-way
  saga, and compensate (release) local ownership the moment the native
  tracker disagrees with what we intended.
* :func:`pointer_callbacks` — the :class:`coordinator_state.PointerCallbacks`
  pair that :func:`coordinator_state.bootstrap_run` needs to read and write
  the root run-pointer.  ``bootstrap_run`` only knows how to *sequence*
  ownership, checkpoint 2 and request-activation; it has no opinion on how a
  pointer is actually read from or written to the tracker.  That is exactly
  the seam this module fills.
* :func:`start_run` — a thin, ordering-preserving wrapper that builds the
  callbacks and calls ``coordinator_state.bootstrap_run`` with them, so a
  caller never has to remember to wire the two together correctly.

Every mutation here — the native claim, the native pointer publish — goes
through :func:`direct_operation.execute`.  Nothing in this module calls
``safe_bd.run_profile`` directly for a mutation; the one direct ``runner``
call in :func:`pointer_callbacks` is a plain tracker *read* (``issue_get``),
which ``direct_operation`` itself does not treat as a mutation either (see
its own ``_observe`` helper).
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

import beads_ownership
import coordinator_state as state
import direct_operation
import protected_action
import safe_bd
import schema_runtime

__all__ = [
    "FinishRunResult",
    "LaneClaimResult",
    "claim_front",
    "close_lanes",
    "finish_run",
    "pointer_callbacks",
    "resolve_harness_receipt",
    "start_run",
]

# The metadata key ``bootstrap_run`` publishes the run pointer under.  This is
# the tracker-side name for ``beads.run-pointer.v1``; it is not exported by
# ``coordinator_state`` or ``safe_bd``, so it lives here, next to the one
# module that reads and writes it.
_POINTER_METADATA_KEY = "hermes.beads_run.v1"

# Mirrors ``direct_operation._OBSERVATION_ERRORS`` exactly (that tuple is
# private, so it cannot be imported).  Any of these means "the tracker did
# not answer" rather than "the tracker answered no" — an unreadable
# observation, never a false absence.
_OBSERVATION_ERRORS = (safe_bd.SafeBdError, state.StateError, OSError)
_RUN_POINTER_FIELDS = frozenset(
    {
        "schema_version",
        "run_id",
        "checkpoint_generation",
        "checkpoint_sha256",
        "ownership_epoch",
        "status",
    }
)


def _valid_pointer(value: Any) -> bool:
    """Validate the closed six-field tracker discovery pointer."""
    return (
        isinstance(value, Mapping)
        and set(value) == _RUN_POINTER_FIELDS
        and value.get("schema_version") == "beads.run-pointer.v1"
        and isinstance(value.get("run_id"), str)
        and state.RUN_ID_RE.fullmatch(value["run_id"]) is not None
        and not isinstance(value.get("checkpoint_generation"), bool)
        and isinstance(value.get("checkpoint_generation"), int)
        and value["checkpoint_generation"] >= 1
        and isinstance(value.get("checkpoint_sha256"), str)
        and re.fullmatch(r"[0-9a-f]{64}", value["checkpoint_sha256"]) is not None
        and not isinstance(value.get("ownership_epoch"), bool)
        and isinstance(value.get("ownership_epoch"), int)
        and 0 <= value["ownership_epoch"] <= state.MAX_U64
        and value.get("status") in {"active", "terminal"}
    )


def _pointer_checkpoint_is_accepted(run_root: Path, pointer: Mapping[str, Any]) -> bool:
    """Bind a discovery pointer to an accepted immutable checkpoint."""
    if not _valid_pointer(pointer):
        return False
    try:
        run = state.guarded_path(run_root, str(pointer["run_id"]), must_exist=True)
        context = direct_operation.open_run(run)
        accepted = [
            event
            for event in context.journal.read().records
            if event.get("phase") == "CHECKPOINT_ACCEPTED"
            and event.get("generation") == pointer["checkpoint_generation"]
            and event.get("checkpoint_sha256") == pointer["checkpoint_sha256"]
        ]
        if len(accepted) != 1:
            return False
        checkpoint_path = Path(accepted[0]["checkpoint_path"])
        raw = state.validate_owner_file(checkpoint_path, root=run).read_bytes()
        return state.sha256_bytes(raw) == pointer["checkpoint_sha256"]
    except (KeyError, OSError, state.StateError):
        return False


# ---------------------------------------------------------------------------
# Pointer callbacks (AC-T12-003)
# ---------------------------------------------------------------------------


def _select_pointer(data: Any, *, issue_id: str) -> Any:
    """Dig the run-pointer value out of an ``issue_get`` payload.

    Returns the parsed pointer dict, :data:`direct_operation.ABSENT` when the
    issue exists but carries no pointer metadata yet, or ``None`` when the
    payload could not be read as a pointer at all (missing issue, wrong
    shape, or metadata that fails to parse as JSON) — an unusable
    observation, never a false absence.
    """
    issue = direct_operation.default_select(data, issue_id=issue_id)
    if not isinstance(issue, Mapping):
        return issue  # None (unusable) or ABSENT (issue itself missing).
    metadata = issue.get("metadata")
    raw = metadata.get(_POINTER_METADATA_KEY) if isinstance(metadata, Mapping) else None
    if raw is None:
        return direct_operation.ABSENT
    if not isinstance(raw, str):
        return None
    raw_bytes = raw.encode("utf-8")
    try:
        value = schema_runtime.strict_json_loads(raw_bytes, max_bytes=512)
    except schema_runtime.JsonLoadFailure:
        return None
    if not _valid_pointer(value) or state.canonical_payload_bytes(value) != raw_bytes:
        return None
    return value


def _pointer_observation(
    classification: str, observed: Any, *, intended: Mapping[str, object]
) -> state.PointerObservation:
    """Build a :class:`state.PointerObservation` that satisfies
    ``coordinator_state._validate_pointer_observation`` for every branch.

    That validator requires ``state_sha256`` to always be a valid 64-hex
    digest, requires an exact-match digest whenever ``observed_value`` is not
    ``None``, and — critically — requires ``state_sha256`` to equal the
    fixed genesis sentinel for ``prestate_unchanged`` rather than a computed
    hash of "nothing".  Tracing every call site in ``bootstrap_run`` shows
    the ``expected_before_sha256`` it compares against is always
    ``GENESIS_SHA256`` in practice (the first PREPARED write always records
    that value, and every later record inherits it verbatim), so hard-coding
    it here is not a shortcut, it is the actual contract.

    ``insufficient_observation`` carries no downstream constraint at all
    beyond "valid hex"; the genesis sentinel is reused there too, since no
    other value is externally agreed for "nothing was observed."
    """
    if classification == direct_operation.INTENDED_EFFECT_PRESENT:
        # A terminal short-circuit inside direct_operation.execute reports
        # classification without observed (observed=None) because it never
        # re-reads the tracker on a cached resolution.  We already know what
        # "present" means in that case: exactly the intended pointer.
        value = dict(observed) if isinstance(observed, Mapping) else dict(intended)
        digest = state.sha256_bytes(state.canonical_payload_bytes(value))
        return state.PointerObservation(classification, digest, value)
    if classification == direct_operation.CONFLICTING_EFFECT and isinstance(
        observed, Mapping
    ):
        value = dict(observed)
        digest = state.sha256_bytes(state.canonical_payload_bytes(value))
        return state.PointerObservation(classification, digest, value)
    # prestate_unchanged, insufficient_observation, or a conflicting_effect
    # whose evidence did not survive a terminal-shortcut replay: no field
    # constraint applies beyond a valid digest, so report the fixed sentinel.
    return state.PointerObservation(classification, state.GENESIS_SHA256, None)


def pointer_callbacks(
    request: state.StartRunInput,
    *,
    actor: str,
    runner: Callable[..., Any] | None = None,
    sensitive: Any = direct_operation.NO_SENSITIVE,
    crash_hook: Callable[[str], None] = state.NOOP_HOOK,
) -> state.PointerCallbacks:
    """Build the ``observe``/``publish`` pair ``bootstrap_run`` needs.

    ``request`` (not a ``RunContext``) is the only object the caller has
    *before* ``bootstrap_run`` creates the run directory, and it already
    carries the two things these closures need: ``repository_root`` (to
    read the tracker at all) and ``root_issue_id`` (which issue's metadata
    the pointer lives on).  ``publish`` opens its own
    :class:`direct_operation.RunContext` lazily, on each call, using the
    ``run_id`` embedded in the pointer dict it is given — by the time
    ``bootstrap_run`` calls ``publish`` the run directory already exists.
    """
    dispatch = runner if runner is not None else safe_bd.run_profile
    repository_root = Path(request.repository_root)
    root_issue_id = request.root_issue_id
    run_root = Path(request.run_root)

    def _read(pointer: Mapping[str, object]) -> tuple[Any, str]:
        try:
            result = dispatch(
                safe_bd.SafeBdRequest(
                    "issue_get", {"issue_id": root_issue_id}, repository_root, None
                ),
                sensitive=sensitive,
            )
        except _OBSERVATION_ERRORS:
            return None, direct_operation.INSUFFICIENT_OBSERVATION
        if getattr(result, "status", None) != "ok":
            return None, direct_operation.INSUFFICIENT_OBSERVATION
        observed = _select_pointer(result.data, issue_id=root_issue_id)
        if isinstance(observed, Mapping) and not _pointer_checkpoint_is_accepted(
            run_root, observed
        ):
            return None, direct_operation.INSUFFICIENT_OBSERVATION
        classification = direct_operation.classify_observation(
            observed, intended=dict(pointer), prestate=direct_operation.ABSENT
        )
        return observed, classification

    def observe(pointer: Mapping[str, object]) -> state.PointerObservation:
        observed, classification = _read(pointer)
        return _pointer_observation(classification, observed, intended=pointer)

    def publish(pointer: Mapping[str, object]) -> state.PointerObservation:
        run_directory = run_root / str(pointer["run_id"])
        context = direct_operation.open_run(run_directory, crash_hook=crash_hook)
        observed_before, _classification = _read(pointer)
        prestate = (
            dict(observed_before)
            if isinstance(observed_before, Mapping)
            and observed_before.get("status") == "terminal"
            else direct_operation.ABSENT
        )
        value = state.canonical_payload_bytes(dict(pointer)).decode("utf-8")
        raw_ownership_epoch = pointer.get("ownership_epoch")
        ownership_epoch = (
            None
            if isinstance(raw_ownership_epoch, bool)
            or not isinstance(raw_ownership_epoch, int)
            else raw_ownership_epoch
        )
        operation = direct_operation.DirectOperation(
            # Content-addressed: identical pointer content always maps to
            # the same caller key, so a retry with the same pointer always
            # converges on the same operation_id inside execute().
            caller_key=f"run-pointer/{state.sha256_bytes(state.canonical_payload_bytes(pointer))}",
            effect_type="TRACKER_RUN_POINTER",
            target_identity=f"bd://issue/{root_issue_id}#run-pointer",
            issue_id=root_issue_id,
            ownership_epoch=ownership_epoch,
            arguments={"issue_id": root_issue_id, "value": value},
            readback=direct_operation.Readback(
                profile="issue_get",
                arguments={"issue_id": root_issue_id},
                intended=dict(pointer),
                prestate=prestate,
                select=lambda data: _select_pointer(data, issue_id=root_issue_id),
            ),
            # The marker note exists to guard non-idempotent effects across
            # attempts a run's own journal cannot see.  TRACKER_RUN_POINTER is
            # a metadata *set*, safe to redispatch verbatim, and its caller
            # key is already content-addressed on the full pointer, so the
            # journal alone fully covers idempotency here; a marker comment
            # on the root issue for every bootstrap attempt would be noise
            # with no corresponding safety gap to close.
            marker_enabled=False,
        )
        result = direct_operation.execute(
            context, operation, actor=actor, runner=dispatch, sensitive=sensitive
        )
        return _pointer_observation(
            result.classification, result.observed, intended=pointer
        )

    return state.PointerCallbacks(observe=observe, publish=publish)


def start_run(
    request: state.StartRunInput,
    *,
    actor: str,
    now: str,
    runner: Callable[..., Any] | None = None,
    sensitive: Any = direct_operation.NO_SENSITIVE,
    run_id_factory: Callable[[], str] | None = None,
    secret_factory: Callable[[], bytes] | None = None,
    crash_hook: Callable[[str], None] = state.NOOP_HOOK,
) -> state.BootstrapResult:
    """Drive AC-T12-003's ordering gate: pointer publish, checkpoint 2, then
    request-active — in that order, every time, resumable at every step.

    This is deliberately thin.  The ordering itself (root-pointer
    publication and readback must reach APPLIED before checkpoint 2 is
    accepted, which must complete before the request mapping flips to
    "active") is enforced by ``coordinator_state.bootstrap_run`` alone; this
    wrapper's only job is to make sure ``bootstrap_run`` is never called
    without the matching pointer callbacks, so that guarantee can never be
    bypassed by a caller that forgets to wire the two together.
    """
    callbacks = pointer_callbacks(
        request, actor=actor, runner=runner, sensitive=sensitive, crash_hook=crash_hook
    )
    kwargs: dict[str, Any] = {"now": now, "crash_hook": crash_hook}
    if run_id_factory is not None:
        kwargs["run_id_factory"] = run_id_factory
    if secret_factory is not None:
        kwargs["secret_factory"] = secret_factory
    return state.bootstrap_run(request, callbacks, **kwargs)


def resolve_harness_receipt(
    context: direct_operation.RunContext,
    *,
    prepared: Mapping[str, Any],
    pending_action: Mapping[str, Any],
    receipt: Mapping[str, Any],
    sensitive: Any = direct_operation.NO_SENSITIVE,
) -> dict[str, Any]:
    """Persist a matching receipt for a non-protected harness-only action."""
    action = pending_action.get("action")
    if action not in {
        "hermes_dispatch",
        "hermes_control",
        "review_request",
        "durable_executor_launch",
    }:
        raise protected_action.ProtectedActionError("ACTION_RECEIPT_ROUTE_INVALID")
    sanitized = protected_action.validate_harness_receipt(
        pending_action, receipt, sensitive=sensitive
    )
    schema_runtime.require_valid(
        "operation-journal-event-v1.schema.json", dict(prepared)
    )
    if any(
        prepared.get(field) != pending_action.get(field)
        for field in ("operation_id", "run_id", "issue_id", "ownership_epoch")
    ):
        raise protected_action.ProtectedActionError("ACTION_PREPARED_MISMATCH")
    records = context.journal.read().records
    exact_prepared = [
        record
        for record in records
        if record.get("phase") == "PREPARED"
        and record.get("operation_id") == pending_action["operation_id"]
    ]
    if len(exact_prepared) != 1 or exact_prepared[0] != dict(prepared):
        raise protected_action.ProtectedActionError("ACTION_PREPARED_NOT_FOUND")
    if any(
        record.get("phase") == "RESOLUTION"
        and record.get("operation_id") == pending_action["operation_id"]
        for record in records
    ):
        raise protected_action.ProtectedActionError("OPERATION_ALREADY_RESOLVED")

    outcome = sanitized["outcome"]
    status = {
        "applied": direct_operation.APPLIED,
        "not_applied": direct_operation.NOT_APPLIED,
        "rejected": direct_operation.NOT_APPLIED,
        "unknown": direct_operation.UNKNOWN,
    }[outcome]
    if status == direct_operation.APPLIED and (
        sanitized.get("observed_sha256") != pending_action["target_sha256"]
    ):
        status = direct_operation.CONFLICT
    evidence_directory = context.run_directory / "_action_receipts"
    state.ensure_owner_directory(evidence_directory, root=context.run_directory)
    evidence_raw = state.canonical_bytes(sanitized)
    evidence_sha = state.sha256_bytes(evidence_raw)
    evidence_path = evidence_directory / (
        f"{pending_action['operation_id']}.{evidence_sha}.json"
    )
    state.atomic_write(
        evidence_path,
        evidence_raw,
        root=context.run_directory,
        max_bytes=direct_operation.MAX_EVIDENCE_BYTES,
    )
    resolution = direct_operation.resolution_event(
        dict(prepared),
        status=status,
        observed_post_state_sha256=sanitized.get("observed_sha256"),
        readback_evidence_path=evidence_path,
        readback_evidence_sha256=evidence_sha,
        timestamp=direct_operation.utc_now(),
        error_code=None
        if status == direct_operation.APPLIED
        else f"HARNESS_ACTION_{status}",
        template_id="harness_action_unresolved",
        field_path="/action",
    )
    context.journal.append(resolution, hook=context.crash_hook)
    return {
        "status": status,
        "classification": (
            direct_operation.INTENDED_EFFECT_PRESENT
            if status == direct_operation.APPLIED
            else direct_operation.PRESTATE_UNCHANGED
            if status == direct_operation.NOT_APPLIED
            else direct_operation.INSUFFICIENT_OBSERVATION
            if status == direct_operation.UNKNOWN
            else direct_operation.CONFLICTING_EFFECT
        ),
        "error_code": None
        if status == direct_operation.APPLIED
        else f"HARNESS_ACTION_{status}",
        "resolution": resolution,
        "receipt": sanitized,
    }


@dataclass(frozen=True)
class FinishRunResult:
    status: str
    classification: str | None
    error_code: str | None


def _terminal_request_mapping(
    request: state.StartRunInput, *, run_id: str, crash_hook
) -> None:
    root = Path(request.run_root)
    requests_root = root / "_requests"
    mapping_path = requests_root / f"{state.request_key(request.request_id)}.json"
    with state.exclusive_lock(requests_root / ".lock", root=root, hook=crash_hook):
        mapping = state._read_request_record(mapping_path, requests_root)
        if mapping["run_id"] != run_id:
            raise state.StateError("REQUEST_MAPPING_CONFLICT", status="conflict")
        if mapping["status"] == "terminal":
            return
        if mapping["status"] not in {"active", "recovery_required"}:
            raise state.StateError("REQUEST_NOT_ACTIVE", status="conflict")
        state._write_request_record(
            mapping_path,
            requests_root,
            {**mapping, "status": "terminal"},
            crash_hook,
        )


def _validate_finish_request(request: state.StartRunInput, *, run_id: str) -> str:
    """Bind finish's resupplied fields to the immutable start request."""
    root = Path(request.run_root)
    requests_root = root / "_requests"
    mapping_path = requests_root / f"{state.request_key(request.request_id)}.json"
    mapping = state._read_request_record(mapping_path, requests_root)
    start_input = state._validate_start_input(request)
    start_sha256 = state.sha256_bytes(state.canonical_payload_bytes(start_input))
    if mapping["run_id"] != run_id or mapping["start_input_v1_sha256"] != start_sha256:
        raise state.StateError("FINISH_REQUEST_MISMATCH", status="conflict")
    if mapping["status"] not in {"active", "recovery_required", "terminal"}:
        raise state.StateError("FINISH_REQUEST_NOT_ACTIVE", status="conflict")
    return str(mapping["status"])


def _owned_lanes_for_run(
    ownership: beads_ownership.OwnershipStore,
    *,
    run_id: str,
    root_issue_id: str,
) -> dict[str, dict[str, Any]]:
    """Enumerate every non-released ownership record belonging to this run."""
    ownership_root = ownership.run_root / "_ownership"
    if not ownership_root.exists():
        return {}
    lanes: dict[str, dict[str, Any]] = {}
    for directory in ownership_root.iterdir():
        if not directory.is_dir() or not re.fullmatch(r"[0-9a-f]{64}", directory.name):
            continue
        current_path = directory / "current.json"
        if not current_path.exists():
            continue
        raw = state.validate_owner_file(
            current_path, root=ownership.run_root
        ).read_bytes()
        value = schema_runtime.strict_json_loads(
            raw, max_bytes=state.MAX_MANIFEST_BYTES
        )
        schema_runtime.require_valid("ownership-record-v1.schema.json", value)
        if state.canonical_bytes(value) != raw:
            raise state.StateError(
                "FINISH_OWNERSHIP_RECORD_NONCANONICAL", status="conflict"
            )
        if (
            value["run_id"] == run_id
            and value["issue_id"] != root_issue_id
            and value["status"] != "released"
        ):
            lanes[value["issue_id"]] = value
    return lanes


def _frozen_pointer_prestate(
    context: direct_operation.RunContext,
    *,
    caller_key: str,
    terminal_pointer: Mapping[str, Any],
    observed_pointer: Mapping[str, Any],
) -> dict[str, Any]:
    """Recover the original active prestate for an idempotent finish retry."""
    if observed_pointer.get("status") == "active":
        return dict(observed_pointer)
    key_digest = state.sha256_bytes(
        state.canonical_payload_bytes(
            {"run_id": context.run_id, "caller_key": caller_key}
        )
    )
    path = direct_operation.operations_directory(context.run_directory) / (
        f"{key_digest}.intent.json"
    )
    try:
        raw = state.validate_owner_file(path, root=context.run_directory).read_bytes()
        intent = schema_runtime.strict_json_loads(
            raw, max_bytes=direct_operation.MAX_INTENT_BYTES
        )
        prestate = intent["readback"]["prestate"]
        intended = intent["readback"]["intended"]
    except (KeyError, OSError, state.StateError, schema_runtime.JsonLoadFailure) as exc:
        raise state.StateError(
            "FINISH_RETRY_EVIDENCE_INVALID", status="conflict"
        ) from exc
    if (
        state.canonical_bytes(intent) != raw
        or intended != dict(terminal_pointer)
        or not _valid_pointer(prestate)
        or prestate["status"] != "active"
        or prestate["run_id"] != context.run_id
        or prestate["ownership_epoch"] != terminal_pointer["ownership_epoch"]
    ):
        raise state.StateError("FINISH_RETRY_EVIDENCE_INVALID", status="conflict")
    return dict(prestate)


def _accept_phase_checkpoint(
    context: direct_operation.RunContext,
    checkpoint: Mapping[str, Any],
    *,
    phase: str,
    issues: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    current = context.checkpoints.current(rebuild_pointer=True)
    candidate = dict(checkpoint)
    candidate.update(
        generation=current.generation + 1,
        phase=phase,
        issues=dict(issues if issues is not None else checkpoint["issues"]),
        previous_checkpoint_sha256=current.generation_sha256,
        created_at=direct_operation.utc_now(),
    )
    return context.checkpoints.accept(candidate).value


def finish_run(
    request: state.StartRunInput,
    *,
    run_directory: Path,
    scope_issue_ids: Sequence[str],
    ownership_epoch: int,
    terminal_status: str,
    actor: str,
    runner: Callable[..., Any] | None = None,
    sensitive: Any = direct_operation.NO_SENSITIVE,
    crash_hook: Callable[[str], None] = state.NOOP_HOOK,
) -> FinishRunResult:
    """Complete active-to-terminal pointer succession without unsafe shortcuts."""
    dispatch = runner if runner is not None else safe_bd.run_profile
    run_directory = state.validate_owner_directory(
        Path(run_directory), root=Path(request.run_root)
    )
    context = direct_operation.open_run(run_directory, crash_hook=crash_hook)
    if context.run_id != run_directory.name:
        raise state.StateError("FINISH_RUN_ID_MISMATCH", status="conflict")
    request_status = _validate_finish_request(request, run_id=context.run_id)
    if tuple(scope_issue_ids) != request.scope_issue_ids:
        raise state.StateError("FINISH_REQUEST_MISMATCH", status="conflict")
    ownership = beads_ownership.OwnershipStore(
        Path(request.run_root), crash_hook=crash_hook
    )
    callbacks = pointer_callbacks(
        request,
        actor=actor,
        runner=dispatch,
        sensitive=sensitive,
        crash_hook=crash_hook,
    )
    with state.exclusive_lock(
        run_directory / "run.lock", root=run_directory, hook=crash_hook
    ):
        checkpoint = context.checkpoints.current(rebuild_pointer=True).value
        checkpoint_lanes = set(checkpoint["issues"]) - {request.root_issue_id}
        requested_lanes = set(request.scope_issue_ids)
        if checkpoint_lanes != requested_lanes:
            raise state.StateError(
                "FINISH_SCOPE_CHECKPOINT_MISMATCH", status="conflict"
            )
        owned_lanes = _owned_lanes_for_run(
            ownership, run_id=context.run_id, root_issue_id=request.root_issue_id
        )
        if not set(owned_lanes).issubset(checkpoint_lanes):
            raise state.StateError("FINISH_UNSCOPED_OWNERSHIP_HELD", status="conflict")
        if (
            checkpoint["phase"]
            in {
                "completed",
                "partially_completed",
                "blocked",
                "human_required",
                "budget_exhausted",
                "circuit_broken",
                "inconclusive",
                "cancelled",
                "error",
            }
            and checkpoint["phase"] != terminal_status
        ):
            raise state.StateError("FINISH_TERMINAL_STATUS_CONFLICT", status="conflict")
        for issue_id in sorted(checkpoint_lanes, key=state.issue_key):
            entry = checkpoint["issues"].get(issue_id)
            if not isinstance(entry, Mapping):
                raise state.StateError("FINISH_LANE_STATE_MISSING", status="conflict")
            attempt_state = entry.get("attempt", {}).get("state")
            if attempt_state not in {"joined", "failed", "cancelled", "unknown"}:
                raise state.StateError("FINISH_LANE_NONTERMINAL", status="conflict")
            if (
                terminal_status == "completed"
                and entry.get("tracker_status_observed") != "closed"
            ):
                raise state.StateError("FINISH_LANE_NOT_CLOSED", status="conflict")
            epoch = entry.get("ownership", {}).get("epoch")
            if not isinstance(epoch, int):
                raise state.StateError(
                    "FINISH_LANE_OWNERSHIP_INVALID", status="conflict"
                )
            held = ownership.inspect_readonly(issue_id)
            if held.disposition not in {"held", "released"}:
                raise state.StateError(
                    "FINISH_LANE_OWNERSHIP_INVALID", status="conflict"
                )
            if held.record is None or held.record.get("epoch") != epoch:
                raise state.StateError(
                    "FINISH_LANE_OWNERSHIP_INVALID", status="conflict"
                )

        if checkpoint["phase"] != terminal_status:
            if request_status != "active":
                raise state.StateError("FINISH_RETRY_NOT_RECONCILED", status="conflict")
            checkpoint = _accept_phase_checkpoint(
                context, checkpoint, phase=terminal_status
            )
        crash_hook("after_finish_checkpoint")

        checkpoint_ref = context.checkpoints.current(rebuild_pointer=True)
        terminal_pointer: dict[str, object] = {
            "schema_version": "beads.run-pointer.v1",
            "run_id": context.run_id,
            "checkpoint_generation": checkpoint_ref.generation,
            "checkpoint_sha256": checkpoint_ref.generation_sha256,
            "ownership_epoch": ownership_epoch,
            "status": "terminal",
        }
        with ownership.guarded_release(
            request.root_issue_id,
            run_directory,
            epoch=ownership_epoch,
            actor=actor,
            operation_id=_release_operation_id(
                run_id=context.run_id,
                issue_id=request.root_issue_id,
                actor=actor,
                epoch=ownership_epoch,
            ),
        ) as release_root:
            observation = callbacks.observe(terminal_pointer)
            observed_pointer = observation.observed_value
            pointer_is_terminal = observed_pointer == terminal_pointer
            pointer_is_active = (
                isinstance(observed_pointer, Mapping)
                and _valid_pointer(observed_pointer)
                and observed_pointer.get("run_id") == context.run_id
                and observed_pointer.get("ownership_epoch") == ownership_epoch
                and observed_pointer.get("status") == "active"
            )
            if not pointer_is_terminal and not pointer_is_active:
                return FinishRunResult(
                    direct_operation.UNKNOWN,
                    direct_operation.INSUFFICIENT_OBSERVATION,
                    "TERMINAL_POINTER_PRESTATE_INVALID",
                )

            value = state.canonical_payload_bytes(terminal_pointer).decode("utf-8")
            caller_key = (
                "run-pointer/"
                f"{state.sha256_bytes(state.canonical_payload_bytes(terminal_pointer))}"
            )
            assert isinstance(observed_pointer, Mapping)
            pointer_prestate = _frozen_pointer_prestate(
                context,
                caller_key=caller_key,
                terminal_pointer=terminal_pointer,
                observed_pointer=observed_pointer,
            )
            operation = direct_operation.DirectOperation(
                caller_key=caller_key,
                effect_type="TRACKER_RUN_POINTER",
                target_identity=f"bd://issue/{request.root_issue_id}#run-pointer",
                issue_id=request.root_issue_id,
                ownership_epoch=ownership_epoch,
                arguments={"issue_id": request.root_issue_id, "value": value},
                readback=direct_operation.Readback(
                    profile="issue_get",
                    arguments={"issue_id": request.root_issue_id},
                    intended=terminal_pointer,
                    prestate=pointer_prestate,
                    select=lambda data: _select_pointer(
                        data, issue_id=request.root_issue_id
                    ),
                ),
                marker_enabled=False,
            )
            pending = direct_operation.prepare(
                context,
                operation,
                actor=actor,
                runner=dispatch,
                sensitive=sensitive,
            )
            crash_hook("after_finish_pointer_prepared")

            # The tracker precondition is not a native CAS. Revalidate before any
            # ownership release so a cooperative finish does not mutate local
            # ownership after an external writer changed the root pointer.
            pre_release = callbacks.observe(terminal_pointer).observed_value
            if pre_release not in (pointer_prestate, terminal_pointer):
                return FinishRunResult(
                    direct_operation.CONFLICT,
                    direct_operation.CONFLICTING_EFFECT,
                    "TERMINAL_POINTER_PRESTATE_CHANGED",
                )

            for issue_id in sorted(checkpoint_lanes, key=state.issue_key):
                entry = checkpoint["issues"][issue_id]
                epoch = entry["ownership"]["epoch"]
                released = ownership.release(
                    issue_id,
                    run_directory,
                    epoch=epoch,
                    operation_id=_release_operation_id(
                        run_id=context.run_id,
                        issue_id=issue_id,
                        actor=actor,
                        epoch=epoch,
                    ),
                )
                if released.disposition != "released":
                    raise state.StateError(
                        "FINISH_LANE_RELEASE_UNCONFIRMED", status="unknown"
                    )
            crash_hook("after_finish_lane_releases")

            root_released = release_root()
            if root_released.disposition != "released":
                raise state.StateError(
                    "FINISH_ROOT_RELEASE_UNCONFIRMED", status="unknown"
                )
            crash_hook("after_finish_root_release_recorded")
            transition = direct_operation.resume(pending)
            if transition.status != direct_operation.APPLIED:
                return FinishRunResult(
                    transition.status, transition.classification, transition.error_code
                )
            crash_hook("after_finish_pointer")
        crash_hook("after_finish_root_lock_release")
        _terminal_request_mapping(request, run_id=context.run_id, crash_hook=crash_hook)
        crash_hook("after_finish_request_terminal")
        return FinishRunResult(
            direct_operation.APPLIED, transition.classification, None
        )


# ---------------------------------------------------------------------------
# Claim-front (AC-T12-001)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LaneClaimResult:
    """One lane's outcome from :func:`claim_front`.

    ``status`` is one of the four-way outcomes (``APPLIED``, ``NOT_APPLIED``,
    ``CONFLICT``, ``UNKNOWN``) or ``REFUSED`` for a lane that was never
    attempted at all — currently only the root issue.
    """

    issue_id: str
    status: str
    classification: str | None
    ownership_epoch: int | None
    error_code: str | None


def _release_operation_id(*, run_id: str, issue_id: str, actor: str, epoch: int) -> str:
    """A deterministic id for the compensating release, distinct from the
    paired acquire's id.

    ``beads_ownership._append_event`` treats operation_id reuse as a hard
    conflict unless the reused id's *own* prior event was a matching
    ``release_prepared`` -> ``released`` pair.  An acquire's own history
    event has ``status="active"``, so reusing the acquire's operation_id for
    the release call fails closed on the very first write.  Keying this id
    on a distinct ``effect_type`` guarantees it never collides with the
    acquire id derived from the same inputs.
    """
    payload = {"run_id": run_id, "issue_id": issue_id, "actor": actor, "epoch": epoch}
    return state.semantic_operation_id(
        {
            "schema": "beads.claim-front-ownership.v1",
            "effect_type": "CLAIM_FRONT_RELEASE",
            "target_identity": issue_id,
            "immutable_input_sha256": state.sha256_bytes(
                state.canonical_payload_bytes(payload)
            ),
            "ownership_epoch": epoch,
        }
    )


def _acquire_operation_id(*, run_id: str, issue_id: str, actor: str, epoch: int) -> str:
    payload = {"run_id": run_id, "issue_id": issue_id, "actor": actor, "epoch": epoch}
    return state.semantic_operation_id(
        {
            "schema": "beads.claim-front-ownership.v1",
            "effect_type": "OWNERSHIP_ACQUIRE",
            "target_identity": issue_id,
            "immutable_input_sha256": state.sha256_bytes(
                state.canonical_payload_bytes(payload)
            ),
            "ownership_epoch": epoch,
        }
    )


def _acquire_local_ownership(
    *,
    ownership: beads_ownership.OwnershipStore,
    context: direct_operation.RunContext,
    issue_id: str,
    actor: str,
) -> tuple[str, int | None]:
    """Inspect-then-branch local ownership acquire, mirroring
    ``coordinator_state.bootstrap_run``'s own root-ownership idiom exactly
    (not a fixed-epoch placeholder): reuse an already-held record for this
    run, otherwise acquire the next epoch, otherwise report the pre-existing
    disposition without ever calling ``acquire`` on a state it does not own.

    Returns ``("held", epoch)`` on success or ``(disposition, None)`` for
    every case where this lane must not be dispatched — ``"conflict"``
    (held by someone else, or a racing acquire), or ``"unknown"``.
    """
    try:
        inspected = ownership.inspect(issue_id)
    except beads_ownership.OwnershipError:
        return "unknown", None

    if inspected.disposition == "held":
        record = inspected.record
        if record is not None and record.get("run_id") == context.run_id:
            return "held", record["epoch"]
        return "conflict", None

    if inspected.disposition not in ("unheld", "released"):
        # "conflict" or "unknown" at the inspect stage: never acquire on top
        # of a state we do not understand.
        return inspected.disposition, None

    proposed_epoch = (inspected.record["epoch"] + 1) if inspected.record else 1
    operation_id = _acquire_operation_id(
        run_id=context.run_id, issue_id=issue_id, actor=actor, epoch=proposed_epoch
    )
    try:
        acquired = ownership.acquire(
            issue_id=issue_id,
            actor=actor,
            run_directory=context.run_directory,
            # bootstrap_run's own root-ownership acquire passes this same
            # fixed sentinel, not a computed digest of tracker state; there
            # is no other value this call site is defined against.
            tracker_state_sha256=state.GENESIS_SHA256,
            operation_id=operation_id,
            now=None,
        )
    except beads_ownership.OwnershipError:
        return "unknown", None

    if acquired.disposition != "held" or acquired.record is None:
        return "conflict", None
    return "held", acquired.record["epoch"]


def _select_claim_state(data: Any, *, issue_id: str) -> Any:
    """Project an issue readback onto all claim-relevant readiness fields."""
    observed = direct_operation.default_select(data, issue_id=issue_id)
    if not isinstance(observed, Mapping):
        return observed
    claim_state = dict(observed)
    claim_state.setdefault("blocked_by", [])
    claim_state.setdefault("defer_until", None)
    return claim_state


def _native_readiness(
    context: direct_operation.RunContext,
    issue_id: str,
    *,
    runner: Callable[..., Any],
    sensitive: Any,
) -> str:
    """Return ready/not_ready/unknown from complete native ready membership."""
    try:
        result = runner(
            safe_bd.SafeBdRequest(
                "ready_list",
                {"limit": 0, "sort": "priority"},
                context.repository_root,
                None,
            ),
            sensitive=sensitive,
        )
    except _OBSERVATION_ERRORS:
        return "unknown"
    if getattr(result, "status", None) != "ok" or not isinstance(result.data, list):
        return "unknown"
    matches = [
        record
        for record in result.data
        if isinstance(record, Mapping) and record.get("id") == issue_id
    ]
    if len(matches) > 1:
        return "unknown"
    if not matches:
        return "not_ready"
    record = matches[0]
    blocked_by = record.get("blocked_by", [])
    if (
        record.get("status") != "open"
        or not isinstance(blocked_by, list)
        or blocked_by
        or record.get("defer_until") is not None
    ):
        return "not_ready"
    return "ready"


def close_lanes(
    context: direct_operation.RunContext,
    *,
    ownership: beads_ownership.OwnershipStore,
    issues: Sequence[str],
    actor: str,
    reason: str,
    runner: Callable[..., Any] | None = None,
    sensitive: Any = direct_operation.NO_SENSITIVE,
) -> list[LaneClaimResult]:
    """Close only parent-owned, independently verified, integrated lanes.

    Eligibility comes exclusively from the current accepted checkpoint and is
    rechecked together with cooperative ownership immediately before each
    guarded close. Mixed batches remain issue-specific: an ineligible lane is
    refused without preventing an eligible sibling from closing.
    """
    dispatch = runner if runner is not None else safe_bd.run_profile
    results: list[LaneClaimResult] = []
    with state.exclusive_lock(
        context.run_directory / "run.lock",
        root=context.run_directory,
        hook=context.crash_hook,
    ):
        checkpoint = context.checkpoints.current(rebuild_pointer=True).value
        entries = checkpoint["issues"]
        root_entry = entries.get(context.manifest["root_issue_id"])
        root_actor = (
            root_entry.get("ownership", {}).get("actor")
            if isinstance(root_entry, Mapping)
            else None
        )
        if root_actor is not None and root_actor != actor:
            raise direct_operation.DirectOperationError(
                "TRACKER_CLOSE_PARENT_REQUIRED", status=direct_operation.CONFLICT
            )
        for issue_id in issues:
            entry = entries.get(issue_id)
            ownership_entry = (
                entry.get("ownership") if isinstance(entry, Mapping) else None
            )
            if (
                not isinstance(ownership_entry, Mapping)
                or ownership_entry.get("actor") != actor
            ):
                raise direct_operation.DirectOperationError(
                    "TRACKER_CLOSE_PARENT_REQUIRED", status=direct_operation.CONFLICT
                )
            eligible = (
                issue_id != context.manifest["root_issue_id"]
                and entry.get("worker_result", {}).get("state") == "accepted"
                and entry.get("worker_result", {}).get("outcome") == "completed"
                and entry.get("artifact", {}).get("state") == "verified"
                and entry.get("verification", {}).get("state") == "passed"
                and entry.get("review", {}).get("state") in {"passed", "not_required"}
                and entry.get("integration", {}).get("state") == "primary_integrated"
                and entry.get("gate", {}).get("state") in {"none", "resolved"}
            )
            if not eligible:
                results.append(
                    LaneClaimResult(
                        issue_id=issue_id,
                        status="REFUSED",
                        classification=None,
                        ownership_epoch=None,
                        error_code="TRACKER_CLOSE_LANE_NOT_ELIGIBLE",
                    )
                )
                continue
            epoch = ownership_entry.get("epoch")
            if isinstance(epoch, bool) or not isinstance(epoch, int):
                results.append(
                    LaneClaimResult(
                        issue_id=issue_id,
                        status=direct_operation.CONFLICT,
                        classification=None,
                        ownership_epoch=None,
                        error_code="TRACKER_CLOSE_OWNERSHIP_MISMATCH",
                    )
                )
                continue
            operation = direct_operation.DirectOperation(
                caller_key=f"tracker-close/{context.run_id}/{issue_id}/{epoch}",
                effect_type="TRACKER_CLOSE",
                target_identity=f"bd://issue/{issue_id}",
                issue_id=issue_id,
                ownership_epoch=epoch,
                arguments={"issue_id": issue_id, "reason": reason},
                readback=direct_operation.Readback(
                    profile="issue_get",
                    arguments={"issue_id": issue_id},
                    intended={"status": "closed"},
                    prestate={"status": entry["tracker_status_observed"]},
                ),
            )
            try:
                with ownership.guard(
                    issue_id,
                    context.run_directory,
                    epoch=epoch,
                    actor=actor,
                ):
                    outcome = direct_operation.execute(
                        context,
                        operation,
                        actor=actor,
                        runner=dispatch,
                        sensitive=sensitive,
                    )
            except beads_ownership.OwnershipError as exc:
                status = (
                    direct_operation.UNKNOWN
                    if exc.status == "unknown"
                    else direct_operation.CONFLICT
                )
                results.append(
                    LaneClaimResult(
                        issue_id=issue_id,
                        status=status,
                        classification=None,
                        ownership_epoch=epoch if isinstance(epoch, int) else None,
                        error_code="TRACKER_CLOSE_OWNERSHIP_MISMATCH",
                    )
                )
                continue
            if outcome.status == direct_operation.APPLIED:
                updated_entries = dict(checkpoint["issues"])
                updated_entry = dict(entry)
                updated_entry["tracker_status_observed"] = "closed"
                updated_entries[issue_id] = updated_entry
                checkpoint = _accept_phase_checkpoint(
                    context,
                    checkpoint,
                    phase=str(checkpoint["phase"]),
                    issues=updated_entries,
                )
                entries = checkpoint["issues"]
            results.append(
                LaneClaimResult(
                    issue_id=issue_id,
                    status=outcome.status,
                    classification=outcome.classification,
                    ownership_epoch=epoch,
                    error_code=outcome.error_code,
                )
            )
    return results


def claim_front(
    context: direct_operation.RunContext,
    *,
    ownership: beads_ownership.OwnershipStore,
    issues: Sequence[str],
    actor: str,
    runner: Callable[..., Any] | None = None,
    sensitive: Any = direct_operation.NO_SENSITIVE,
) -> list[LaneClaimResult]:
    """Claim every eligible lane in ``issues``, one guarded operation each.

    The root issue (``context.manifest["root_issue_id"]``) is never
    eligible: it is refused outright, with no ownership inspect and no
    dispatch, because the root is the coordination anchor, not a lane to
    claim.  For every other issue: acquire local ownership first (skipping
    the acquire if this run already holds it), then dispatch the native
    claim through :func:`direct_operation.execute` under that epoch. Native
    ready membership and the full blocker/defer state are revalidated both
    before local ownership and at the final dispatch seam. If the
    native tracker does not converge on what was intended (``NOT_APPLIED``
    or ``CONFLICT``), the local ownership just acquired is released again —
    holding it would leave this run believing it owns a lane the tracker
    disagrees about.  ``UNKNOWN`` never triggers a release: an unreadable
    post-effect probe means the claim's real outcome is unknown, and
    releasing ownership on top of that uncertainty could hand the lane to
    another run while the native claim may in fact have gone through.
    """
    dispatch = runner if runner is not None else safe_bd.run_profile
    root_issue_id = context.manifest["root_issue_id"]
    results: list[LaneClaimResult] = []

    for issue_id in issues:
        if issue_id == root_issue_id:
            results.append(
                LaneClaimResult(
                    issue_id=issue_id,
                    status="REFUSED",
                    classification=None,
                    ownership_epoch=None,
                    error_code="COORDINATOR_TRACKER_ROOT_ISSUE_INELIGIBLE",
                )
            )
            continue

        try:
            local = ownership.inspect(issue_id)
        except beads_ownership.OwnershipError:
            local = None
        if local is None or local.disposition == "unknown":
            results.append(
                LaneClaimResult(
                    issue_id=issue_id,
                    status=direct_operation.UNKNOWN,
                    classification=None,
                    ownership_epoch=None,
                    error_code="COORDINATOR_TRACKER_OWNERSHIP_UNKNOWN",
                )
            )
            continue
        if local.disposition == "conflict" or (
            local.disposition == "held"
            and (local.record is None or local.record.get("run_id") != context.run_id)
        ):
            results.append(
                LaneClaimResult(
                    issue_id=issue_id,
                    status=direct_operation.CONFLICT,
                    classification=None,
                    ownership_epoch=None,
                    error_code="COORDINATOR_TRACKER_OWNERSHIP_CONFLICT",
                )
            )
            continue

        readiness = _native_readiness(
            context,
            issue_id,
            runner=dispatch,
            sensitive=sensitive,
        )
        if readiness != "ready":
            unknown = readiness == "unknown"
            results.append(
                LaneClaimResult(
                    issue_id=issue_id,
                    status=(
                        direct_operation.UNKNOWN
                        if unknown
                        else direct_operation.CONFLICT
                    ),
                    classification=(
                        direct_operation.INSUFFICIENT_OBSERVATION
                        if unknown
                        else direct_operation.CONFLICTING_EFFECT
                    ),
                    ownership_epoch=None,
                    error_code=(
                        "COORDINATOR_TRACKER_READINESS_UNKNOWN"
                        if unknown
                        else "COORDINATOR_TRACKER_ISSUE_NOT_READY"
                    ),
                )
            )
            continue

        disposition, epoch = _acquire_local_ownership(
            ownership=ownership, context=context, issue_id=issue_id, actor=actor
        )
        if disposition != "held":
            status = "UNKNOWN" if disposition == "unknown" else "CONFLICT"
            results.append(
                LaneClaimResult(
                    issue_id=issue_id,
                    status=status,
                    classification=None,
                    ownership_epoch=None,
                    error_code=f"COORDINATOR_TRACKER_OWNERSHIP_{status}",
                )
            )
            continue

        # disposition == "held" guarantees epoch is set; the two are
        # correlated by _acquire_local_ownership's own contract, not by its
        # return type.
        assert epoch is not None

        operation = direct_operation.DirectOperation(
            caller_key=f"claim-front/{issue_id}",
            effect_type="TRACKER_CLAIM",
            target_identity=f"bd://issue/{issue_id}",
            issue_id=issue_id,
            ownership_epoch=epoch,
            arguments={"issue_id": issue_id},
            readback=direct_operation.Readback(
                profile="issue_get",
                arguments={"issue_id": issue_id},
                intended={
                    "status": "in_progress",
                    "assignee": actor,
                    "blocked_by": [],
                },
                prestate={
                    "status": "open",
                    "blocked_by": [],
                    "defer_until": None,
                },
                select=lambda data, issue_id=issue_id: _select_claim_state(
                    data, issue_id=issue_id
                ),
            ),
        )
        readiness_changed = False

        def guarded_dispatch(
            request: safe_bd.SafeBdRequest, *, sensitive: Any = None
        ) -> safe_bd.SafeBdResult:
            nonlocal readiness_changed
            if request.profile == "claim_exact":
                readiness = _native_readiness(
                    context,
                    issue_id,
                    runner=dispatch,
                    sensitive=sensitive,
                )
                if readiness != "ready":
                    readiness_changed = True
                    return safe_bd.SafeBdResult(
                        "beads.safe-bd-result.v1",
                        request.profile,
                        "native_error",
                        safe_bd.PINNED_BD_VERSION,
                        None,
                        None,
                        (),
                        "COORDINATOR_TRACKER_READINESS_CHANGED",
                    )
            return dispatch(request, sensitive=sensitive)

        try:
            with ownership.guard(
                issue_id,
                context.run_directory,
                epoch=epoch,
                actor=actor,
            ):
                outcome = direct_operation.execute(
                    context,
                    operation,
                    actor=actor,
                    runner=guarded_dispatch,
                    sensitive=sensitive,
                )
        except beads_ownership.OwnershipError:
            results.append(
                LaneClaimResult(
                    issue_id=issue_id,
                    status=direct_operation.CONFLICT,
                    classification=None,
                    ownership_epoch=epoch,
                    error_code="COORDINATOR_TRACKER_OWNERSHIP_CONFLICT",
                )
            )
            continue

        if readiness_changed:
            ownership.release(
                issue_id,
                context.run_directory,
                epoch=epoch,
                operation_id=_release_operation_id(
                    run_id=context.run_id, issue_id=issue_id, actor=actor, epoch=epoch
                ),
                now=None,
            )
            results.append(
                LaneClaimResult(
                    issue_id=issue_id,
                    status=direct_operation.CONFLICT,
                    classification=direct_operation.CONFLICTING_EFFECT,
                    ownership_epoch=epoch,
                    error_code="COORDINATOR_TRACKER_READINESS_CHANGED",
                )
            )
            continue

        if outcome.status in ("NOT_APPLIED", "CONFLICT"):
            ownership.release(
                issue_id,
                context.run_directory,
                epoch=epoch,
                operation_id=_release_operation_id(
                    run_id=context.run_id, issue_id=issue_id, actor=actor, epoch=epoch
                ),
                now=None,
            )

        results.append(
            LaneClaimResult(
                issue_id=issue_id,
                status=outcome.status,
                classification=outcome.classification,
                ownership_epoch=epoch,
                error_code=outcome.error_code,
            )
        )

    return results
