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


def rewrite(cmd: str) -> str:
    for pattern, replacement in REWRITES:
        cmd = re.sub(pattern, replacement, cmd)
    return cmd


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    # Claude Code + Codex use 'Bash'; Hermes uses 'terminal'
    if payload.get("tool_name") not in ("Bash", "terminal"):
        sys.exit(0)

    original = payload["tool_input"].get("command", "")
    rewritten = rewrite(original)

    if rewritten != original:
        print(json.dumps({"tool_input": {"command": rewritten}}))

    sys.exit(0)


if __name__ == "__main__":
    main()
