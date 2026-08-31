"""Black-box tests for exposing Claude's session ID to skills."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOOK_PATH = ROOT / "plugins" / "review-panel" / "hooks" / "session-identity.py"
ROOT_HOOKS_JSON = ROOT / "hooks" / "hooks.json"
PLUGIN_HOOKS_JSON = ROOT / "plugins" / "review-panel" / "hooks" / "hooks.json"


def run_hook(tmp_path: Path, payload: dict | str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["CLAUDE_ENV_FILE"] = str(tmp_path / "claude-env")
    return subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=payload if isinstance(payload, str) else json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env=env,
    )


def test_session_start_persists_valid_session_id(tmp_path: Path) -> None:
    result = run_hook(
        tmp_path,
        {"hook_event_name": "SessionStart", "session_id": "abc-123"},
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert (
        tmp_path / "claude-env"
    ).read_text() == "export REVIEW_PANEL_SESSION_ID=abc-123\n"


def test_malformed_or_unsafe_input_fails_closed_without_env_write(
    tmp_path: Path,
) -> None:
    for payload in (
        "not-json",
        {"hook_event_name": "PreToolUse", "session_id": "abc-123"},
        {"hook_event_name": "SessionStart", "session_id": "$(touch nope)"},
        {"hook_event_name": "SessionStart"},
    ):
        result = run_hook(tmp_path, payload)
        assert result.returncode == 0
        assert result.stdout == ""

    assert not (tmp_path / "claude-env").exists()


def test_hook_is_registered_for_every_session_start() -> None:
    root_groups = json.loads(ROOT_HOOKS_JSON.read_text())["hooks"]["SessionStart"]
    root_registrations = [
        hook
        for group in root_groups
        if "matcher" not in group
        for hook in group["hooks"]
    ]
    assert [hook["command"] for hook in root_registrations] == [
        "python3 ${CLAUDE_PLUGIN_ROOT}/plugins/review-panel/hooks/session-identity.py"
    ]

    plugin_groups = json.loads(PLUGIN_HOOKS_JSON.read_text())["hooks"]["SessionStart"]
    plugin_registrations = [hook for group in plugin_groups for hook in group["hooks"]]
    assert [hook["command"] for hook in plugin_registrations] == [
        "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/session-identity.py"
    ]
