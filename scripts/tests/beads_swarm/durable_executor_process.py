#!/usr/bin/env python3
"""Minimal durable executor fixture: filesystem return only, no Beads access."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "skills" / "beads" / "scripts"))

import safe_bd  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        return 2
    handoff_path, result_path = map(Path, args)
    handoff_raw = handoff_path.read_bytes()
    handoff = json.loads(handoff_raw)
    isolation = Path(handoff["isolation_target"])
    artifact = isolation / "durable-executor.patch"
    try:
        safe_bd.SafeBdRequest(
            "close_exact",
            {
                "issue_id": handoff["scope_issue_ids"][0],
                "actor": handoff["executor_identity"],
                "reason": "executor must not own lifecycle",
            },
            isolation.resolve(),
            safe_bd.WorkerScope(frozenset(handoff["scope_issue_ids"])),
        )
    except safe_bd.SafeBdError as exc:
        mutation_attempt = {
            "profile": "close_exact",
            "dispatched": False,
            "error_code": str(exc),
        }
    else:  # pragma: no cover - a production capability regression
        mutation_attempt = {
            "profile": "close_exact",
            "dispatched": True,
            "error_code": None,
        }
    payload = (
        json.dumps(mutation_attempt, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    artifact.write_bytes(payload)
    artifact.chmod(0o600)
    result = {
        "schema_version": "beads.durable-executor-result.v1",
        "handoff_id": handoff["handoff_id"],
        "run_id": handoff["run_id"],
        "executor_identity": handoff["executor_identity"],
        "issues": [dict(item) for item in handoff["held_ownership"]],
        "handoff_sha256": hashlib.sha256(handoff_raw).hexdigest(),
        "status": "completed",
        "artifact": {
            "type": "patch",
            "path": str(artifact),
            "size_bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        },
        "commands": [],
        "blockers": [],
        "skipped_checks": [],
        "residual_risks": [],
        "beads_mutated": False,
    }
    result_path.write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")), encoding="utf-8"
    )
    result_path.chmod(0o600)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
