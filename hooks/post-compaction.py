#!/usr/bin/env python3
"""Re-inject a bounded active-plan summary after compaction or /clear."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

MAX_PLAN_BYTES = 65_536
MAX_ITEM_CHARS = 180
MAX_COMPLETED = 3
MAX_REMAINING = 4
PLAN_PATHS = (Path(".scott-cc/active-plan.md"), Path(".claude/plan.md"))
INACTIVE_STATUSES = {
    "archived",
    "cancelled",
    "closed",
    "complete",
    "completed",
    "done",
    "inactive",
}
STATUS_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(?:\*\*)?status(?:\*\*)?\s*:\s*([a-z_-]+)", re.IGNORECASE
)
CHECKBOX_RE = re.compile(r"^\s*[-*]\s*\[([ xX])\]\s*(.+?)\s*$")
BULLET_RE = re.compile(r"^\s*[-*]\s+(.+?)\s*$")
HEADING_RE = re.compile(r"^\s*#{1,6}\s+(.+?)\s*$")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def clean(value: str) -> str:
    value = CONTROL_RE.sub("", value).strip()
    value = re.sub(r"\s+", " ", value)
    if len(value) > MAX_ITEM_CHARS:
        return value[: MAX_ITEM_CHARS - 1].rstrip() + "…"
    return value


def section_kind(heading: str) -> str | None:
    normalized = clean(heading).lower().rstrip(":")
    if normalized in {"objective", "goal", "current objective"}:
        return "objective"
    if normalized in {"completed", "completed steps", "done"}:
        return "completed"
    if normalized in {"remaining", "remaining tasks", "next steps", "todo", "tasks"}:
        return "remaining"
    return None


def is_active(text: str) -> bool:
    for line in text.splitlines()[:30]:
        match = STATUS_RE.match(line)
        if match:
            return match.group(1).lower() not in INACTIVE_STATUSES
    return True


def summarize(text: str, relative_path: Path) -> str:
    objective = ""
    completed: list[str] = []
    remaining: list[str] = []
    fallback = ""
    section: str | None = None

    for raw_line in text.splitlines():
        line = clean(raw_line)
        if not line or STATUS_RE.match(line):
            continue

        heading = HEADING_RE.match(line)
        if heading:
            section = section_kind(heading.group(1))
            continue

        checkbox = CHECKBOX_RE.match(line)
        if checkbox:
            item = clean(checkbox.group(2))
            target = completed if checkbox.group(1).lower() == "x" else remaining
            if item and item not in target:
                target.append(item)
            continue

        bullet = BULLET_RE.match(line)
        if bullet and section in {"completed", "remaining"}:
            item = clean(bullet.group(1))
            target = completed if section == "completed" else remaining
            if item and item not in target:
                target.append(item)
            continue

        if section == "objective" and not objective:
            objective = line
        elif not fallback and not line.startswith("#"):
            fallback = line

    objective = objective or fallback or "Not recorded"
    completed = completed[:MAX_COMPLETED]
    remaining = remaining[:MAX_REMAINING]

    lines = [
        f"Active plan: {relative_path.as_posix()}",
        f"Objective: {objective}",
        "Completed:",
    ]
    lines.extend(f"- {item}" for item in (completed or ["None recorded"]))
    lines.append("Remaining:")
    lines.extend(f"- {item}" for item in (remaining or ["None recorded"]))
    lines.append(
        "Resume point: first remaining task; verify current repository state before acting."
    )
    return "\n".join(lines[:15])


def load_plan(root: Path) -> tuple[Path, str] | None:
    resolved_root = root.resolve()
    for relative_path in PLAN_PATHS:
        candidate = root / relative_path
        try:
            if not candidate.is_file() or candidate.is_symlink():
                continue
            if not candidate.resolve().is_relative_to(resolved_root):
                continue
            if candidate.stat().st_size > MAX_PLAN_BYTES:
                continue
            text = candidate.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        if is_active(text):
            return relative_path, text
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            return 0
        if payload.get("hook_event_name") != "SessionStart":
            return 0
        if payload.get("source") not in {"clear", "compact"}:
            return 0
        cwd = payload.get("cwd")
        if not isinstance(cwd, str):
            return 0
        root = Path(cwd)
        if not root.is_dir():
            return 0
        plan = load_plan(root)
        if plan is None:
            return 0
        relative_path, text = plan
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "SessionStart",
                        "additionalContext": summarize(text, relative_path),
                    }
                }
            )
        )
    except (OSError, TypeError, ValueError):
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
