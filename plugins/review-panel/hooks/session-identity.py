#!/usr/bin/env python3
"""Expose the current Claude session ID to review-panel commands."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import Path

SESSION_ID_RE = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if (
            not isinstance(payload, dict)
            or payload.get("hook_event_name") != "SessionStart"
        ):
            return 0

        session_id = payload.get("session_id")
        env_file = os.environ.get("CLAUDE_ENV_FILE")
        if (
            not isinstance(session_id, str)
            or not SESSION_ID_RE.fullmatch(session_id)
            or not env_file
        ):
            return 0

        with Path(env_file).open("a", encoding="utf-8") as handle:
            handle.write(f"export REVIEW_PANEL_SESSION_ID={shlex.quote(session_id)}\n")
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
