"""Subprocess black-box tests for hooks/prefer_modern_tools.py.

Invoked as a subprocess (stdin JSON in, stdout JSON/exit-code out) rather
than imported, since hooks/ isn't a package and this is the same contract
Claude Code itself uses to call the hook.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HOOK_PATH = Path(__file__).resolve().parents[1] / "prefer_modern_tools.py"


def run_hook(payload) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=payload if isinstance(payload, str) else json.dumps(payload),
        capture_output=True,
        text=True,
    )


def bash_payload(command: str, **overrides) -> dict:
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }
    payload.update(overrides)
    return payload


def test_normal_rewrite_replaces_bare_tool_name():
    result = run_hook(bash_payload("ls -la"))

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["tool_input"]["command"] == "lsd -la"


def test_quoted_tool_name_is_not_rewritten():
    command = 'git commit -m "run ls first"'
    result = run_hook(bash_payload(command))

    # Nothing outside quotes changed, so the hook should be a silent no-op.
    assert result.returncode == 0
    assert result.stdout == ""


def test_quoted_tool_name_with_single_quotes_is_not_rewritten():
    command = "git commit -m 'run ls first'"
    result = run_hook(bash_payload(command))

    assert result.returncode == 0
    assert result.stdout == ""


def test_chained_command_rewrites_bare_token_outside_quotes():
    command = 'git commit -m "run ls first" && ls -la'
    result = run_hook(bash_payload(command))

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["tool_input"]["command"] == (
        'git commit -m "run ls first" && lsd -la'
    )


def test_chained_command_with_semicolon_and_pipe_rewrites_bare_tokens():
    command = "cat file.txt; grep foo file.txt | grep bar"
    result = run_hook(bash_payload(command))

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["tool_input"]["command"] == (
        "bat --style=plain --paging=never file.txt; rg foo file.txt | rg bar"
    )


def test_malformed_payload_missing_tool_input_fails_open():
    payload = {"tool_name": "Bash"}
    result = run_hook(payload)

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_malformed_payload_wrong_type_tool_input_fails_open():
    payload = {"tool_name": "Bash", "tool_input": "not-a-dict"}
    result = run_hook(payload)

    assert result.returncode == 0
    assert result.stdout == ""
    # Fails open (never blocks the tool call), but the exception is still
    # named on stderr rather than vanishing silently — see _guard_base.run_guard_main.
    assert "unhandled exception, failing open" in result.stderr


def test_non_json_payload_fails_open():
    result = run_hook("not json at all")

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_non_bash_tool_is_silent_noop():
    payload = bash_payload("ls -la")
    payload["tool_name"] = "Edit"

    result = run_hook(payload)

    assert result.returncode == 0
    assert result.stdout == ""
