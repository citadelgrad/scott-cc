#!/usr/bin/env python3
"""Bounded out-of-process worker used by the swarm conformance harness."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "skills" / "beads" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import lane_snapshot  # noqa: E402
import safe_bd  # noqa: E402
import worker_result  # noqa: E402


def _identity(path: Path, artifact_type: str) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "type": artifact_type,
        "path": str(path),
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def execute(job_path: Path) -> dict[str, Any]:
    job = json.loads(job_path.read_text(encoding="utf-8"))
    if job["behavior"].startswith("sleep_exit:"):
        job_path.with_suffix(".pid").write_text(str(os.getpid()), encoding="ascii")
        time.sleep(float(job["behavior"].partition(":")[2]))
        return {"status": "slept"}
    if job["behavior"].startswith("flood_output:"):
        byte_count = int(job["behavior"].partition(":")[2])
        sys.stdout.write("x" * byte_count)
        sys.stderr.write("y" * byte_count)
        return {"status": "flooded"}
    packet_path = Path(job["packet_path"])
    packet_raw = packet_path.read_bytes()
    packet = json.loads(packet_raw)
    worktree = Path(packet["repository"]["worktree"])
    outbox = Path(packet["verification"]["worker_outbox"])
    os.chdir(worktree)

    context = worker_result.initialize_attempt(
        packet_raw,
        expected_packet_sha256=hashlib.sha256(packet_raw).hexdigest(),
        ownership_epoch=job["ownership_epoch"],
    )
    evidence = worker_result.run_declared_command(
        context,
        command_index=0,
        sensitive_values_file=Path(job["sensitive_values_file"]),
    )

    target = worktree / job["changed_path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(job["content"], encoding="utf-8")
    if job["behavior"] == "child_tracker_mutation":
        # Exercise the production safe transport's worker capability gate with
        # a real lifecycle profile. Construction must fail before any bd
        # process can be dispatched.
        safe_bd.SafeBdRequest(
            "close_exact",
            {
                "issue_id": packet["issue"]["id"],
                "actor": "child",
                "reason": "forbidden child close",
            },
            worktree.resolve(),
            safe_bd.WorkerScope(frozenset({packet["issue"]["id"]})),
        )

    snapshot = lane_snapshot.capture(
        worktree, packet["repository"]["base_sha"], exclude=outbox
    )
    record = outbox / "command-000.json"
    safe_result = evidence["safe_result"]
    artifact_paths = [
        (record, "command_evidence"),
        (Path(safe_result["stdout_log"]["path"]), "stdout_log"),
        (Path(safe_result["stderr_log"]["path"]), "stderr_log"),
    ]
    outside = [path for path in snapshot.changed_paths if path.startswith(".beads/")]
    status = (
        "failed"
        if job["behavior"] == "failed"
        else "cancelled"
        if job["behavior"] == "cancelled"
        else "completed"
    )
    candidate = {
        "schema_version": "beads.worker-execution-result.v1",
        "run_id": packet["run_id"],
        "attempt_id": packet["attempt_id"],
        "issue_id": packet["issue"]["id"],
        "packet_sha256": hashlib.sha256(packet_raw).hexdigest(),
        "status": status,
        "repository": {
            "worktree": str(worktree),
            "branch": packet["repository"]["branch"],
            "base_sha": packet["repository"]["base_sha"],
            "head_sha": snapshot.head_sha,
        },
        "lane_state": snapshot.lane_state,
        "changes": {
            "paths": list(snapshot.changed_paths),
            "outside_allowed_scope": outside,
        },
        "verification": [
            {
                "command": json.dumps(evidence["argv"], separators=(",", ":")),
                "exit_code": safe_result["exit_code"],
                "started_at": safe_result["started_at"],
                "finished_at": safe_result["finished_at"],
                "log_path": str(record),
                "log_sha256": hashlib.sha256(record.read_bytes()).hexdigest(),
            }
        ],
        "acceptance_evidence": [
            {
                "acceptance_id": packet["issue"]["acceptance_ids"][0],
                "status": "supported" if status == "completed" else "failed",
                "evidence_paths": [str(record)],
            }
        ],
        "artifacts": [_identity(path, kind) for path, kind in artifact_paths],
        "blockers": [],
        "errors": [
            {
                "code": "WORKER_FAILED",
                "template_id": "bounded_worker_failure",
                "field_path": "/status",
                "parameters": [],
            }
        ]
        if status == "failed"
        else [],
        "cancellation_reason": (
            "cancelled by conformance fixture" if status == "cancelled" else None
        ),
        "skipped_checks": [],
        "residual_risks": [],
        "summary": "bounded child process result",
        "integration_mode": packet["scope"]["integration_mode"],
        "worker_frozen_artifact": None,
    }
    receipt = worker_result.finalize_attempt(
        context,
        candidate,
        sensitive_values_file=Path(job["sensitive_values_file"]),
    )
    if job["behavior"] == "missing_evidence":
        record.unlink()
    return {"status": "published", "receipt": receipt}


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print('{"status":"invalid","error_code":"JOB_ARGUMENT_REQUIRED"}')
        return 2
    try:
        result = execute(Path(args[0]))
    except Exception as exc:  # child boundary reports only typed class/message
        print(
            json.dumps(
                {"status": "refused", "error": str(exc), "type": type(exc).__name__},
                sort_keys=True,
            )
        )
        return 3
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
