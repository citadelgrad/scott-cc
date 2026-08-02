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


def rewritten_input(output: dict) -> dict:
    hook_output = output["hookSpecificOutput"]
    assert hook_output["hookEventName"] == "PreToolUse"
    assert "permissionDecision" not in hook_output
    return hook_output["updatedInput"]


def test_normal_rewrite_replaces_bare_tool_name():
    result = run_hook(bash_payload("ls -la"))

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert rewritten_input(output)["command"] == "lsd -la"


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
    assert rewritten_input(output)["command"] == (
        'git commit -m "run ls first" && lsd -la'
    )


def test_chained_command_with_semicolon_and_pipe_rewrites_bare_tokens():
    command = "cat file.txt; grep foo file.txt | grep bar"
    result = run_hook(bash_payload(command))

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert rewritten_input(output)["command"] == (
        "bat --style=plain --paging=never file.txt; rg foo file.txt | rg bar"
    )


def test_git_subcommands_are_not_rewritten():
    for command in ("git grep needle", "git ls-files", "git cat-file -p HEAD"):
        result = run_hook(bash_payload(command))

        assert result.returncode == 0
        assert result.stdout == ""


def test_unquoted_command_arguments_are_not_rewritten():
    result = run_hook(bash_payload("printf run ls grep cat"))

    assert result.returncode == 0
    assert result.stdout == ""


def test_common_command_wrappers_still_rewrite_the_wrapped_command():
    for command, expected in (
        ("sudo grep needle file", "sudo rg needle file"),
        ("env MODE=test grep needle file", "env MODE=test rg needle file"),
        ("MODE=test grep needle file", "MODE=test rg needle file"),
    ):
        result = run_hook(bash_payload(command))

        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert rewritten_input(output)["command"] == expected


def test_complex_shell_syntax_is_left_untouched():
    for command in (
        "cat <<'EOF'\ngrep literal\nEOF",
        "printf '%s' $(grep needle file)",
        "diff <(grep one a) <(grep two b)",
        "grep needle file # ; ls is comment text",
        r"grep needle file\ name",
    ):
        result = run_hook(bash_payload(command))

        assert result.returncode == 0
        assert result.stdout == ""


def test_rewrite_preserves_other_tool_input_fields():
    payload = bash_payload("grep needle file")
    payload["tool_input"]["timeout"] = 120_000

    result = run_hook(payload)

    output = json.loads(result.stdout)
    assert rewritten_input(output) == {
        "command": "rg needle file",
        "timeout": 120_000,
    }


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
