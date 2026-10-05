#!/usr/bin/env python3
"""
PreToolUse hook: warn-and-confirm on Edit/Write/NotebookEdit to data-layer
paths (migrations, schemas, ORM models) that lack a same-day DATA-MODEL.md
change-log entry.

Interactive/planning-time convenience only — never a hard block, and always
a silent no-op in unattended contexts (permission_mode == "bypassPermissions",
i.e. --dangerously-skip-permissions / mode:agent), since a confirm prompt
needs a human to answer it. Unattended sovereignty enforcement is the
data-steward review seat's job, not this hook's.

Default data-layer globs (overridable via a repo-root .data-guard.json
with a {"globs": [...]} shape, which replaces this default set):
"""

import datetime
import json
import sys
from fnmatch import fnmatchcase
from functools import lru_cache
from pathlib import Path

from _guard_base import (
    find_repo_root,
    is_unattended_noop,
    load_json_override,
    run_guard_main,
)

DEFAULT_GLOBS = [
    "**/migrations/**",
    "**/models/**",
    "*.sql",
    "**/schema.*",
    "prisma/schema.prisma",
    "**/alembic/**",
]


def load_globs(repo_root: Path) -> list[str]:
    return load_json_override(repo_root, ".data-guard.json", "globs", DEFAULT_GLOBS)


def matches_glob(rel_path: str, pattern: str) -> bool:
    if "/" not in pattern:
        return fnmatchcase(Path(rel_path).name, pattern)

    path_parts = tuple(rel_path.split("/"))
    pattern_parts = tuple(pattern.split("/"))

    @lru_cache(maxsize=None)
    def match(path_index: int, pattern_index: int) -> bool:
        if pattern_index == len(pattern_parts):
            return path_index == len(path_parts)

        component = pattern_parts[pattern_index]
        if component == "**":
            return match(path_index, pattern_index + 1) or (
                path_index < len(path_parts) and match(path_index + 1, pattern_index)
            )

        return (
            path_index < len(path_parts)
            and fnmatchcase(path_parts[path_index], component)
            and match(path_index + 1, pattern_index + 1)
        )

    return match(0, 0)


def matches_data_layer(rel_path: str, globs: list[str]) -> str | None:
    for pattern in globs:
        if matches_glob(rel_path, pattern):
            return pattern
    return None


def has_todays_change_log_entry(repo_root: Path) -> bool:
    data_model = repo_root / "DATA-MODEL.md"
    if not data_model.exists():
        return False

    today = datetime.date.today().isoformat()
    in_change_log = False
    for line in data_model.read_text().splitlines():
        if line.strip().startswith("## Change log"):
            in_change_log = True
            continue
        if in_change_log and line.startswith("## "):
            break
        if in_change_log and line.strip().startswith(f"- {today}"):
            return True
    return False


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    if payload.get("tool_name") not in ("Edit", "Write", "NotebookEdit"):
        sys.exit(0)

    # Unattended/mode:agent contexts have no human to answer a confirm prompt —
    # defer entirely to the data-steward review seat's enforcement instead.
    if is_unattended_noop(payload):
        sys.exit(0)

    tool_input = payload.get("tool_input", {})
    target = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not target:
        sys.exit(0)

    cwd = payload.get("cwd", ".")
    repo_root = find_repo_root(cwd)
    if repo_root is None:
        sys.exit(0)

    try:
        target_path = Path(target)
        if not target_path.is_absolute():
            target_path = Path(cwd) / target_path
        rel_path = str(target_path.resolve().relative_to(repo_root))
    except ValueError:
        sys.exit(0)

    globs = load_globs(repo_root)
    matched = matches_data_layer(rel_path, globs)
    if matched is None:
        sys.exit(0)

    if has_todays_change_log_entry(repo_root):
        sys.exit(0)

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": (
                        f"{rel_path} matches data-layer pattern '{matched}' but "
                        "DATA-MODEL.md has no dated Change log entry for today. "
                        "Add one (see DATA-MODEL-FORMAT.md) or confirm to proceed anyway."
                    ),
                }
            }
        )
    )
    sys.exit(0)


if __name__ == "__main__":
    run_guard_main(main)
