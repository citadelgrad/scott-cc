#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
# ruff: noqa: BLE001  (hooks must never raise: blind excepts are the fail-silent contract)
"""Push current Graphiti facts into the agent context.

Works for:
  Claude Code / Codex  UserPromptSubmit (prompt, cwd) and SessionStart (source, cwd)
                       -> plain stdout
  Hermes               pre_llm_call (extra.user_message, cwd) -> {"context": ...} JSON

Fails silent and fast (exit 0, no output) if Graphiti is down.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    try:
        import graphiti_common as g  # ty: ignore[unresolved-import]

        event = data.get("hook_event_name", "")
        hermes = event == "pre_llm_call" or "extra" in data
        cwd = data.get("cwd") or ""
        repo = g.repo_name(cwd)

        if hermes:
            prompt = (data.get("extra") or {}).get("user_message") or ""
            query = str(prompt)
        elif event == "SessionStart" or "source" in data and "prompt" not in data:
            if data.get("source") not in (None, "startup", "resume", "compact"):
                return 0
            query = f"Current conventions, tooling, dependencies, preferences and decisions for the {repo} project"
        else:
            query = str(data.get("prompt") or "")

        query = g.strip_injected(query)
        if len(query) < 8 or query.startswith("/"):
            return 0
        if not g.healthy(1.0):
            return 0
        text = g.format_facts(g.current_facts(query, repo, limit=8, timeout=4.0), repo)
        if not text:
            return 0
        if hermes:
            print(json.dumps({"context": text}))
        else:
            print(text)
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
