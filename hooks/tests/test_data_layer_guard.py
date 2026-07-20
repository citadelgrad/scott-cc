"""Subprocess black-box tests for hooks/data_layer_guard.py.

Invoked as a subprocess (stdin JSON in, stdout JSON/exit-code out) rather
than imported, since hooks/ isn't a package and this is the same contract
Claude Code itself uses to call the hook.
"""

from __future__ import annotations

import datetime
import json
import subprocess
import sys
from pathlib import Path

HOOK_PATH = Path(__file__).resolve().parents[1] / "data_layer_guard.py"


def run_hook(repo_root: Path, payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )


def init_repo(tmp_path: Path) -> Path:
    (tmp_path / ".git").mkdir()
    return tmp_path


def edit_payload(repo_root: Path, rel_path: str, **overrides) -> dict:
    payload = {
        "tool_name": "Edit",
        "cwd": str(repo_root),
        "tool_input": {"file_path": str(repo_root / rel_path)},
    }
    payload.update(overrides)
    return payload


def test_non_edit_tool_is_silent_noop(tmp_path):
    repo_root = init_repo(tmp_path)
    (repo_root / "migrations").mkdir()
    (repo_root / "migrations" / "0001_init.sql").write_text("-- migration")

    payload = edit_payload(repo_root, "migrations/0001_init.sql")
    payload["tool_name"] = "Bash"

    result = run_hook(repo_root, payload)

    assert result.returncode == 0
    assert result.stdout == ""


def test_bypass_permissions_is_silent_noop_even_on_matching_path(tmp_path):
    repo_root = init_repo(tmp_path)
    (repo_root / "migrations").mkdir()
    (repo_root / "migrations" / "0001_init.sql").write_text("-- migration")

    payload = edit_payload(
        repo_root, "migrations/0001_init.sql", permission_mode="bypassPermissions"
    )

    result = run_hook(repo_root, payload)

    assert result.returncode == 0
    assert result.stdout == ""


def test_matching_path_without_data_model_asks(tmp_path):
    repo_root = init_repo(tmp_path)
    (repo_root / "migrations").mkdir()
    (repo_root / "migrations" / "0001_init.sql").write_text("-- migration")

    payload = edit_payload(repo_root, "migrations/0001_init.sql")

    result = run_hook(repo_root, payload)

    assert result.returncode == 0
    output = json.loads(result.stdout)
    hook_output = output["hookSpecificOutput"]
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["permissionDecision"] == "ask"
    assert "migrations/0001_init.sql" in hook_output["permissionDecisionReason"]
    assert "**/migrations/**" in hook_output["permissionDecisionReason"]


def test_matching_path_with_todays_change_log_entry_is_silent_noop(tmp_path):
    repo_root = init_repo(tmp_path)
    (repo_root / "migrations").mkdir()
    (repo_root / "migrations" / "0001_init.sql").write_text("-- migration")

    today = datetime.date.today().isoformat()
    (repo_root / "DATA-MODEL.md").write_text(
        f"# Data Model\n\n## Change log\n\n- {today} did the thing\n"
    )

    payload = edit_payload(repo_root, "migrations/0001_init.sql")

    result = run_hook(repo_root, payload)

    assert result.returncode == 0
    assert result.stdout == ""


def test_non_matching_path_is_silent_noop(tmp_path):
    repo_root = init_repo(tmp_path)
    (repo_root / "src").mkdir()
    (repo_root / "src" / "app.ts").write_text("console.log('hi')")

    payload = edit_payload(repo_root, "src/app.ts")

    result = run_hook(repo_root, payload)

    assert result.returncode == 0
    assert result.stdout == ""


def test_data_guard_override_replaces_default_globs(tmp_path):
    repo_root = init_repo(tmp_path)
    (repo_root / ".data-guard.json").write_text(
        json.dumps({"globs": ["**/custom_dir/**"]})
    )
    (repo_root / "custom_dir").mkdir()
    (repo_root / "custom_dir" / "file.py").write_text("x = 1")
    (repo_root / "migrations").mkdir()
    (repo_root / "migrations" / "0001_init.sql").write_text("-- migration")

    override_match = run_hook(repo_root, edit_payload(repo_root, "custom_dir/file.py"))
    default_glob_now_ignored = run_hook(
        repo_root, edit_payload(repo_root, "migrations/0001_init.sql")
    )

    assert override_match.returncode == 0
    output = json.loads(override_match.stdout)
    assert output["hookSpecificOutput"]["permissionDecision"] == "ask"
    assert (
        "**/custom_dir/**" in output["hookSpecificOutput"]["permissionDecisionReason"]
    )

    assert default_glob_now_ignored.returncode == 0
    assert default_glob_now_ignored.stdout == ""
