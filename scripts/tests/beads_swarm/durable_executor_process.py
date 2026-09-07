#!/usr/bin/env python3
"""Minimal durable executor fixture: filesystem return only, no Beads access."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        return 2
    handoff_path, result_path = map(Path, args)
    handoff_raw = handoff_path.read_bytes()
    handoff = json.loads(handoff_raw)
    isolation = Path(handoff["isolation_target"])
    artifact = isolation / "durable-executor.patch"
    payload = b"durable executor result\n"
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
