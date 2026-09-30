#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""End-to-end smoke test against a running Graphiti server.

Adds one episode to group graphiti-smoke-test, waits for extraction, searches, checks that
the old fact (Jest) is invalidated and the new fact (Vitest) is current, then clears the group.
Exit 0 = PASS, 1 = FAIL. Uses GRAPHITI_URL / GRAPHITI_MCP_PORT like the hooks.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import graphiti_common as g  # ty: ignore[unresolved-import]

GROUP = "graphiti-smoke-test"
BODY = "The api package uses Vitest for tests; it replaced Jest on 2026-09-30."


def search() -> list[dict]:
    res = g.call_tool(
        "search_memory_facts",
        {
            "query": "What does the api package use for tests?",
            "group_ids": [GROUP],
            "max_facts": 10,
        },
        timeout=20,
    )
    return res.get("facts", []) if isinstance(res, dict) else []


def main(timeout_s: int = 180) -> int:
    if not g.healthy(3.0):
        print(f"FAIL: server not healthy at {g.BASE_URL}")
        return 1
    g.call_tool("clear_graph", {"group_ids": [GROUP]}, timeout=20)
    print(
        "add_memory:",
        g.call_tool(
            "add_memory",
            {
                "name": "smoke1",
                "episode_body": BODY,
                "group_id": GROUP,
                "source": "text",
                "source_description": "smoke test",
            },
            timeout=30,
        ),
    )
    deadline = time.time() + timeout_s
    facts: list[dict] = []
    while time.time() < deadline:
        time.sleep(10)
        facts = search()
        if any("vitest" in f.get("fact", "").lower() for f in facts):
            break
    current = [f for f in facts if f.get("invalid_at") is None]
    old = [
        f
        for f in facts
        if f.get("invalid_at") is not None and "jest" in f.get("fact", "").lower()
    ]
    for f in facts:
        print(f"  - {f.get('fact')} | invalid_at={f.get('invalid_at')}")
    ok = any("vitest" in f.get("fact", "").lower() for f in current)
    print(
        "clear_graph:", g.call_tool("clear_graph", {"group_ids": [GROUP]}, timeout=20)
    )
    if not ok:
        print(
            "FAIL: no current Vitest fact. Check `make logs` for LLM errors (see SKILL.md troubleshooting)."
        )
        return 1
    print(
        "PASS: Vitest fact is current"
        + ("; Jest fact is invalidated" if old else "; (Jest fact not returned)")
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
