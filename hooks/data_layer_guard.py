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
from pathlib import Path

DEFAULT_GLOBS = [
    "**/migrations/**",
    "**/models/**",
    "*.sql",
    "**/schema.*",
    "prisma/schema.prisma",
    "**/alembic/**",
]


def find_repo_root(start: str) -> Path | None:
    path = Path(start).resolve()
    for candidate in (path, *path.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def load_globs(repo_root: Path) -> list[str]:
    override_path = repo_root / ".data-guard.json"
    if override_path.exists():
        try:
            data = json.loads(override_path.read_text())
            globs = data.get("globs")
            if isinstance(globs, list) and all(isinstance(g, str) for g in globs):
                return globs
        except (json.JSONDecodeError, OSError):
            pass
    return DEFAULT_GLOBS


def matches_glob(rel_path: str, pattern: str) -> bool:
    if "/" not in pattern:
        return Path(rel_path).match(pattern)

    core = pattern
    any_prefix = core.startswith("**/")
    if any_prefix:
        core = core[len("**/") :]
    any_suffix = core.endswith("/**")
    if any_suffix:
        core = core[: -len("/**")]

    parts = rel_path.split("/")
    core_parts = core.split("/")
    n = len(core_parts)

    if any_prefix and any_suffix:
        return any(
            all(Path(parts[i + j]).match(core_parts[j]) for j in range(n))
            for i in range(len(parts) - n + 1)
        )
    if any_prefix:
        return len(parts) >= n and all(
            Path(parts[len(parts) - n + j]).match(core_parts[j]) for j in range(n)
        )
    if any_suffix:
        return len(parts) >= n and all(
            Path(parts[j]).match(core_parts[j]) for j in range(n)
        )
    return len(parts) == n and all(
        Path(parts[j]).match(core_parts[j]) for j in range(n)
    )


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
    if payload.get("permission_mode") == "bypassPermissions":
        sys.exit(0)

    tool_input = payload.get("tool_input", {})
    target = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not target:
        sys.exit(0)

    repo_root = find_repo_root(payload.get("cwd", "."))
    if repo_root is None:
        sys.exit(0)

    try:
        rel_path = str(Path(target).resolve().relative_to(repo_root))
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
    try:
        main()
    except Exception:
        sys.exit(0)
