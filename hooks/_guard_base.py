#!/usr/bin/env python3
"""
Shared scaffolding for this repo's root-level PreToolUse "guard" hooks
(data_layer_guard.py, prefer_modern_tools.py, and future hooks/*.py guards).

Not imported by plugins/*/hooks/*.py (e.g. security-suite's secret_scan.py) —
those are self-contained, independently-distributed plugins and must not
depend on a module that only ships with this repo's root-level hooks/.

Provides:
  - find_repo_root(start)      — walk up from `start` to the nearest .git dir
  - load_json_override(...)    — read a repo-root JSON override file, falling
                                  back to a default when absent/invalid
  - is_unattended_noop(payload) — True when the hook is running unattended
                                  (permission_mode == "bypassPermissions"),
                                  since a confirm/ask prompt has no human to
                                  answer it in that context
  - run_guard_main(main_fn)    — fail-open wrapper: runs main_fn() and turns
                                  any unhandled exception into a silent
                                  `sys.exit(0)` (no stack trace, no non-zero
                                  exit), so a bug in a guard hook can never
                                  block the tool call it's guarding.

Guard hooks are convenience/confirmation layers, never hard blocks — an
unhandled exception here must never be mistaken by Claude Code for a "deny".
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Callable


def find_repo_root(start: str) -> Path | None:
    """Walk up from `start` looking for the nearest ancestor containing .git."""
    path = Path(start).resolve()
    for candidate in (path, *path.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def load_json_override(
    repo_root: Path,
    filename: str,
    key: str,
    default: list[str],
) -> list[str]:
    """Load a list-of-strings override from a repo-root JSON file.

    Looks for `repo_root / filename`, parses it as JSON, and returns
    `data[key]` if it is present and is a list of strings. Falls back to
    `default` if the file is missing, unreadable, not valid JSON, or the
    key's value isn't a list of strings.
    """
    override_path = repo_root / filename
    if override_path.exists():
        try:
            data = json.loads(override_path.read_text())
            values = data.get(key)
            if isinstance(values, list) and all(isinstance(v, str) for v in values):
                return values
        except (json.JSONDecodeError, OSError):
            pass
    return default


def is_unattended_noop(payload: dict) -> bool:
    """True when the hook should silently no-op because there's no human.

    Unattended/mode:agent contexts (permission_mode == "bypassPermissions",
    i.e. --dangerously-skip-permissions) have no human to answer a confirm
    prompt — guard hooks that only ever "ask" should defer entirely to
    whatever hard-enforcement mechanism (e.g. a review seat) covers the
    unattended case, rather than trying to prompt.
    """
    return payload.get("permission_mode") == "bypassPermissions"


def run_guard_main(main_fn: Callable[[], None]) -> None:
    """Run `main_fn()`, converting any unhandled exception into exit(0).

    Guard hooks are advisory/confirmation layers, not hard blocks: a bug
    inside one must never propagate as a stack trace or non-zero exit that
    could be mistaken for (or accidentally behave like) a deny decision. The
    exception is still named on stderr first, so a silently-broken guard
    shows up in logs instead of vanishing without a trace.
    """
    try:
        main_fn()
    except Exception as exc:
        print(
            f"{sys.argv[0]}: unhandled exception, failing open: {exc!r}",
            file=sys.stderr,
        )
        sys.exit(0)
