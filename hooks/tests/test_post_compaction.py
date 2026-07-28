"""Black-box tests for active-plan context re-injection."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HOOK_PATH = Path(__file__).resolve().parents[1] / "post-compaction.py"
HOOKS_JSON = Path(__file__).resolve().parents[1] / "hooks.json"


def run_hook(cwd: Path, payload: dict | str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=payload if isinstance(payload, str) else json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def session_payload(cwd: Path, source: str = "compact") -> dict:
    return {
        "cwd": str(cwd),
        "hook_event_name": "SessionStart",
        "source": source,
    }


def test_missing_plan_is_silent(tmp_path: Path):
    result = run_hook(tmp_path, session_payload(tmp_path))

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_compact_reinjects_objective_completed_and_remaining(tmp_path: Path):
    plan = tmp_path / ".claude" / "plan.md"
    plan.parent.mkdir()
    plan.write_text(
        """# Active Plan
Status: active

## Objective
Ship reliable plan recovery.

## Tasks
- [x] Inspect hook contracts
- [x] Define bounded output
- [ ] Implement the hook
- [ ] Run verification
"""
    )

    result = run_hook(tmp_path, session_payload(tmp_path))

    assert result.returncode == 0
    output = json.loads(result.stdout)
    context = output["additionalContext"]
    assert "Active plan: .claude/plan.md" in context
    assert "Objective: Ship reliable plan recovery." in context
    assert "Completed:" in context
    assert "- Inspect hook contracts" in context
    assert "Remaining:" in context
    assert "- Implement the hook" in context
    assert len(context.splitlines()) <= 15


def test_active_plan_path_takes_precedence(tmp_path: Path):
    claude_plan = tmp_path / ".claude" / "plan.md"
    claude_plan.parent.mkdir()
    claude_plan.write_text("## Objective\nWrong plan\n")
    scott_plan = tmp_path / ".scott-cc" / "active-plan.md"
    scott_plan.parent.mkdir()
    scott_plan.write_text("## Objective\nPreferred plan\n- [ ] Continue safely\n")

    result = run_hook(tmp_path, session_payload(tmp_path, source="clear"))

    output = json.loads(result.stdout)
    assert ".scott-cc/active-plan.md" in output["additionalContext"]
    assert "Preferred plan" in output["additionalContext"]
    assert "Wrong plan" not in output["additionalContext"]


def test_explicitly_inactive_plan_is_silent(tmp_path: Path):
    plan = tmp_path / ".claude" / "plan.md"
    plan.parent.mkdir()
    plan.write_text("Status: completed\n## Objective\nOld work\n")

    result = run_hook(tmp_path, session_payload(tmp_path))

    assert result.returncode == 0
    assert result.stdout == ""


def test_non_recovery_session_is_silent(tmp_path: Path):
    plan = tmp_path / ".scott-cc" / "active-plan.md"
    plan.parent.mkdir()
    plan.write_text("## Objective\nDo work\n")

    result = run_hook(tmp_path, session_payload(tmp_path, source="startup"))

    assert result.returncode == 0
    assert result.stdout == ""


def test_malformed_input_fails_open(tmp_path: Path):
    result = run_hook(tmp_path, "not-json")

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_oversized_plan_fails_open(tmp_path: Path):
    plan = tmp_path / ".scott-cc" / "active-plan.md"
    plan.parent.mkdir()
    plan.write_text("## Objective\n" + ("x" * 70_000))

    result = run_hook(tmp_path, session_payload(tmp_path))

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_hook_is_registered_for_compaction_and_clear():
    hooks = json.loads(HOOKS_JSON.read_text())["hooks"]["SessionStart"]
    registrations = [
        hook
        for group in hooks
        if group.get("matcher") in {"compact", "clear"}
        for hook in group["hooks"]
    ]

    assert len(registrations) == 2
    assert all(hook["type"] == "command" for hook in registrations)
    assert all("hooks/post-compaction.py" in hook["command"] for hook in registrations)
