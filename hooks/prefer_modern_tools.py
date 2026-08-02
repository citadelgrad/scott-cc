#!/usr/bin/env python3
"""
PreToolUse hook: rewrite legacy CLI commands to faster modern equivalents.

Safe near-drop-ins only (>90% flag compat). Non-compatible tools (fd, dust,
procs, choose) are documented in CLAUDE.md for the model to invoke natively
with their own syntax — auto-rewriting those would break flag semantics.

Rewrite table:
  grep / egrep → rg      (rg respects .gitignore; use -u/-uu to opt out)
  cat          → bat     (--style=plain --paging=never for scriptable output)
  ls           → lsd     (same -l/-a/-h/-1 flags supported)
"""

import json
import re
import sys

from _guard_base import run_guard_main

# ponytail: conservative set — only tools where flag compat covers agent use cases
REWRITES = [
    # egrep before grep so we don't turn 'egrep' into 'rrg'
    (r"(?<![/\w])egrep\b", "rg"),
    (r"(?<![/\w])grep\b", "rg"),
    # cat → bat (plain, no interactive pager)
    (r"(?<![/\w])cat\b", "bat --style=plain --paging=never"),
    # ls → lsd (superset of ls flags)
    (r"(?<![/\w])ls\b", "lsd"),
    # ps common patterns only — procs has incompatible flag syntax for everything else
    (r"(?<![/\w])ps\s+aux\b", "procs"),
    (r"(?<![/\w])ps\s+-ef\b", "procs"),
    (r"(?<![/\w])ps\s+-e\b", "procs"),
]

COMMAND_PREFIX_RE = re.compile(
    r"^\s*(?:(?:[A-Za-z_][A-Za-z0-9_]*=\S+|"
    r"(?:sudo|env|command|builtin|time)(?:\s+-\S+)*)\s+)*$"
)


def _quote_mask(cmd: str) -> list[bool]:
    """Per-character mask; True where the character sits inside a quoted
    string (single or double). Doesn't handle backslash-escaping of quotes
    inside double quotes, but that's rare enough in agent-issued commands
    that skipping the whole quoted span either way is the safe behavior.
    """
    mask = [False] * len(cmd)
    quote_char: str | None = None
    for i, ch in enumerate(cmd):
        if quote_char is None:
            if ch in ("'", '"'):
                quote_char = ch
                mask[i] = True
        else:
            mask[i] = True
            if ch == quote_char:
                quote_char = None
    return mask


def _is_command_position(cmd: str, start: int, quote_mask: list[bool]) -> bool:
    """Return whether ``start`` follows a shell command boundary or wrapper."""
    boundary = -1
    for index in range(start - 1, -1, -1):
        if not quote_mask[index] and cmd[index] in ";&|(\n":
            boundary = index
            break
    return COMMAND_PREFIX_RE.fullmatch(cmd[boundary + 1 : start]) is not None


def rewrite(cmd: str) -> str:
    # Raw regex rewriting is only safe for uncomplicated shell commands. Keep
    # heredocs, substitutions, comments, multiline scripts, and escaped shell
    # syntax untouched rather than risk changing data or nested program text.
    unsafe_syntax = ("\n", "\r", "`", "$(", "<(", ">(", "<<", "\\")
    if any(token in cmd for token in unsafe_syntax):
        return cmd

    initial_mask = _quote_mask(cmd)
    if any(ch == "#" and not initial_mask[index] for index, ch in enumerate(cmd)):
        return cmd

    for pattern, replacement in REWRITES:
        mask = _quote_mask(cmd)

        def _sub(m: re.Match, mask=mask, replacement=replacement) -> str:
            # Skip quoted strings and argument/subcommand positions. A token
            # such as ``grep`` is only a tool invocation at the start of a
            # shell command (possibly after wrappers such as sudo/env), not in
            # ``git grep`` or ``printf run grep``.
            if any(mask[m.start() : m.end()]) or not _is_command_position(
                cmd, m.start(), mask
            ):
                return m.group(0)
            return replacement

        cmd = re.sub(pattern, _sub, cmd)
    return cmd


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    # Claude Code + Codex use 'Bash'; Hermes uses 'terminal'
    if payload.get("tool_name") not in ("Bash", "terminal"):
        sys.exit(0)

    tool_input = payload.get("tool_input") or {}
    original = tool_input.get("command", "")
    rewritten = rewrite(original)

    if rewritten != original:
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "updatedInput": {**tool_input, "command": rewritten},
                    }
                }
            )
        )

    sys.exit(0)


if __name__ == "__main__":
    run_guard_main(main)
