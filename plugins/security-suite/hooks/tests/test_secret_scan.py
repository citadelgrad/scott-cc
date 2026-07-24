"""Subprocess black-box tests for plugins/security-suite/hooks/secret_scan.py.

Invoked as a subprocess (stdin JSON in, stdout JSON/exit-code out) rather
than imported, since hooks/ isn't a package and this is the same contract
Claude Code itself uses to call the hook. Mirrors the conventions in
hooks/tests/test_data_layer_guard.py.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HOOK_PATH = Path(__file__).resolve().parents[1] / "secret_scan.py"

# Built from parts (not a contiguous literal) so this test fixture doesn't
# itself trip gitleaks' own aws-access-token rule at commit time — it's a
# fake value assembled at runtime purely to match the AKIA[0-9A-Z]{16} shape.
AWS_KEY = "AKIA" + "ABCDEFGHIJKLMNOP"
PRIVATE_KEY_BLOCK = (
    "-----BEGIN RSA PRIVATE KEY-----\n"
    + "MIIEpAIBAAKCAQEA"
    + "\n-----END RSA PRIVATE KEY-----"
)


def run_hook(payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )


def write_payload(file_path: str, content: str, **overrides) -> dict:
    payload = {
        "tool_name": "Write",
        "cwd": "/repo",
        "tool_input": {"file_path": file_path, "content": content},
    }
    payload.update(overrides)
    return payload


def test_non_matching_tool_is_silent_noop():
    payload = write_payload("config.py", f"AWS_KEY = '{AWS_KEY}'")
    payload["tool_name"] = "Read"

    result = run_hook(payload)

    assert result.returncode == 0
    assert result.stdout == ""


def test_bypass_permissions_is_silent_noop_even_on_matching_secret():
    payload = write_payload(
        "config.py", f"AWS_KEY = '{AWS_KEY}'", permission_mode="bypassPermissions"
    )

    result = run_hook(payload)

    assert result.returncode == 0
    assert result.stdout == ""


def test_aws_key_is_detected_with_file_path_and_rule_name():
    payload = write_payload("src/config.py", f"AWS_KEY = '{AWS_KEY}'")

    result = run_hook(payload)

    assert result.returncode == 0
    output = json.loads(result.stdout)
    hook_output = output["hookSpecificOutput"]
    assert hook_output["hookEventName"] == "PreToolUse"
    assert hook_output["permissionDecision"] == "ask"
    reason = hook_output["permissionDecisionReason"]
    assert "src/config.py" in reason
    assert "aws-access-key-id" in reason


def test_private_key_is_detected():
    payload = write_payload("id_rsa", PRIVATE_KEY_BLOCK)

    result = run_hook(payload)

    assert result.returncode == 0
    output = json.loads(result.stdout)
    reason = output["hookSpecificOutput"]["permissionDecisionReason"]
    assert "private-key-header" in reason


def test_bash_command_with_secret_is_detected():
    payload = {
        "tool_name": "Bash",
        "cwd": "/repo",
        "tool_input": {"command": f"export AWS_ACCESS_KEY_ID={AWS_KEY}"},
    }

    result = run_hook(payload)

    assert result.returncode == 0
    output = json.loads(result.stdout)
    reason = output["hookSpecificOutput"]["permissionDecisionReason"]
    assert "aws-access-key-id" in reason


def test_clean_input_is_silent_noop_and_does_not_block():
    payload = write_payload("src/app.py", "def add(a, b):\n    return a + b\n")

    result = run_hook(payload)

    assert result.returncode == 0
    assert result.stdout == ""


def test_output_never_contains_raw_secret_value():
    payload = write_payload("src/config.py", f"AWS_KEY = '{AWS_KEY}'")

    result = run_hook(payload)

    assert result.returncode == 0
    assert AWS_KEY not in result.stdout
    assert AWS_KEY not in result.stderr


def test_output_never_contains_raw_private_key_material():
    payload = write_payload("id_rsa", PRIVATE_KEY_BLOCK)

    result = run_hook(payload)

    assert result.returncode == 0
    assert "MIIEpAIBAAKCAQEA" not in result.stdout
    assert "MIIEpAIBAAKCAQEA" not in result.stderr


def test_output_never_contains_raw_generic_secret_value():
    secret_value = "sup3rSecretTokenValue1234567890"
    payload = write_payload("src/settings.py", f"api_key = '{secret_value}'")

    result = run_hook(payload)

    assert result.returncode == 0
    assert secret_value not in result.stdout
    assert secret_value not in result.stderr
    output = json.loads(result.stdout)
    reason = output["hookSpecificOutput"]["permissionDecisionReason"]
    assert "generic-api-key-assignment" in reason
