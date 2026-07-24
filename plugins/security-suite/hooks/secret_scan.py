#!/usr/bin/env python3
"""
PreToolUse hook: scan proposed Write/Edit/Bash content for likely secrets
before the tool runs, mirroring the well-known gitleaks default rule set
(the same engine the root .pre-commit-config.yaml wires up at commit time)
so this plugin owns an always-on, zero-dependency first line of defense
during the edit itself rather than only at commit.

Interactive/planning-time convenience only — never a hard block. On a match
we surface an "ask" permission decision (same contract as
hooks/data_layer_guard.py) naming the file and the matched rule, but we
NEVER print the matched secret value itself: every message is built from
redact() output only. Always a silent no-op in unattended contexts
(permission_mode == "bypassPermissions") for the same reason
data_layer_guard.py is — a confirm prompt needs a human to answer it.

Patterns cover common high-signal secret formats (cloud provider keys,
private key headers, generic API-key/token assignments, JWTs, Slack/GitHub
tokens). This is a cheap pattern-matching pass, not a replacement for
gitleaks/entropy analysis in CI — see .pre-commit-config.yaml for the
authoritative gitleaks gate at commit time.
"""

import json
import re
import sys

# ponytail: rule name -> compiled pattern. Ordered roughly by specificity so
# a more specific rule (e.g. aws-access-key-id) wins over a generic fallback
# when a string could match more than one.
RULES: list[tuple[str, re.Pattern[str]]] = [
    ("aws-access-key-id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    (
        "private-key-header",
        re.compile(
            r"-----BEGIN\s+("
            r"RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----"
        ),
    ),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    (
        "jwt",
        re.compile(
            r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
        ),
    ),
    (
        "generic-api-key-assignment",
        re.compile(
            r"(?i)\b(api[_-]?key|secret|token|password|passwd|pwd)\b"
            r"\s*[:=]\s*['\"]?([A-Za-z0-9_\-/+]{16,})['\"]?"
        ),
    ),
]

# Fields inside tool_input that may carry content worth scanning, across
# Write/Edit/MultiEdit/NotebookEdit/Bash tool shapes.
CONTENT_FIELDS = ("content", "new_string", "command", "new_source")


def redact(value: str) -> str:
    """Never echo a raw secret: show enough to identify it, nothing more."""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}"


def find_matches(text: str) -> list[tuple[str, str]]:
    """Return (rule_name, redacted_value) pairs. Never returns raw matches."""
    findings: list[tuple[str, str]] = []
    matched_spans: list[tuple[int, int]] = []

    for rule_name, pattern in RULES:
        for m in pattern.finditer(text):
            span = m.span()
            # Skip overlaps with an already-matched (more specific) rule.
            if any(span[0] < e and span[1] > s for s, e in matched_spans):
                continue
            matched_spans.append(span)
            findings.append((rule_name, redact(m.group(0))))

    return findings


def extract_content(tool_input: dict) -> list[str]:
    chunks = []
    for field in CONTENT_FIELDS:
        value = tool_input.get(field)
        if isinstance(value, str):
            chunks.append(value)

    # MultiEdit-style: {"edits": [{"new_string": "..."}, ...]}
    edits = tool_input.get("edits")
    if isinstance(edits, list):
        for edit in edits:
            if isinstance(edit, dict) and isinstance(edit.get("new_string"), str):
                chunks.append(edit["new_string"])

    return chunks


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    if payload.get("tool_name") not in ("Write", "Edit", "MultiEdit", "Bash"):
        sys.exit(0)

    # Unattended/mode:agent contexts have no human to answer a confirm prompt —
    # same rationale as data_layer_guard.py.
    if payload.get("permission_mode") == "bypassPermissions":
        sys.exit(0)

    tool_input = payload.get("tool_input", {})
    target = (
        tool_input.get("file_path") or tool_input.get("notebook_path") or "(command)"
    )

    all_findings: list[tuple[str, str]] = []
    for chunk in extract_content(tool_input):
        all_findings.extend(find_matches(chunk))

    if not all_findings:
        sys.exit(0)

    rule_names = sorted({name for name, _ in all_findings})
    redacted_samples = ", ".join(f"{name}={value}" for name, value in all_findings)

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": (
                        f"Possible secret detected in {target}: "
                        f"matched rule(s) {', '.join(rule_names)}. "
                        f"Redacted match(es): {redacted_samples}. "
                        "Confirm to proceed only if this is not a real secret."
                    ),
                }
            }
        )
    )
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
