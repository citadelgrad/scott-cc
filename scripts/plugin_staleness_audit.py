#!/usr/bin/env python3
"""Re-derive each plugin's maturity status and flag drift from marketplace.json.

Implements the staleness rule documented in commit 063443d
(scc-ncs.17): for each plugin's ``source`` path, look at its git history
of commits touching that path.

- unmaintained: 90+ days since the last commit touching that path
  (age check takes precedence over commit count)
- experimental: fewer than 3 commits, or 3+ commits with the latest activity
  between 60 and 90 days ago
- stable: 3+ commits AND last commit within 60 days

This is the gate `run:` command wired into foundry.yaml's
`plugin-staleness-audit` profile (scc-ncs.18): it re-computes status from
git log and fails (non-zero exit) if any plugin's declared "status" field
in .claude-plugin/marketplace.json no longer matches what the rule
currently computes.
"""

from __future__ import annotations

import datetime
import json
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE_JSON = ROOT / ".claude-plugin" / "marketplace.json"

STABLE_MIN_COMMITS = 3
STABLE_MAX_AGE_DAYS = 60
UNMAINTAINED_MIN_AGE_DAYS = 90


def fail(message: str) -> NoReturn:
    print(f"FAIL: {message}")
    sys.exit(1)


def load_marketplace() -> dict:
    try:
        payload = json.loads(MARKETPLACE_JSON.read_text())
    except FileNotFoundError:
        fail(f"missing required file: {MARKETPLACE_JSON}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {MARKETPLACE_JSON}: {exc}")
    if not isinstance(payload, dict):
        fail(f"expected object in {MARKETPLACE_JSON}")
    return payload


def commit_count(source: str) -> int:
    result = subprocess.run(
        ["git", "log", "--oneline", "--", source],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    return len(lines)


def last_commit_age_days(source: str, *, now: datetime.datetime) -> float | None:
    result = subprocess.run(
        ["git", "log", "-1", "--format=%cI", "--", source],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    timestamp = result.stdout.strip()
    if not timestamp:
        return None
    last_commit = datetime.datetime.fromisoformat(timestamp)
    return (now - last_commit).total_seconds() / 86400.0


def derive_status(source: str, *, now: datetime.datetime) -> str:
    """Apply the scc-ncs.17 staleness rule, in the precedence used to
    classify the original plugin set (commit 063443d):

    1. 90+ days since the last commit -> unmaintained (age dominates; this
       is why research-tools/performance-optimization/mutation-testing,
       which have only 1-2 commits, were still called "unmaintained"
       rather than "experimental").
    2. Otherwise, fewer than 3 commits -> experimental (too new/unproven).
    3. Otherwise, 3+ commits and activity within 60 days -> stable; activity
       between 60 and 90 days -> experimental pending renewed maintenance.
    """
    age_days = last_commit_age_days(source, now=now)
    if age_days is None or age_days >= UNMAINTAINED_MIN_AGE_DAYS:
        return "unmaintained"

    count = commit_count(source)
    if count < STABLE_MIN_COMMITS:
        return "experimental"

    if age_days <= STABLE_MAX_AGE_DAYS:
        return "stable"

    return "experimental"


def main() -> int:
    marketplace = load_marketplace()
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        fail(f"expected non-empty plugins array in {MARKETPLACE_JSON}")

    now = datetime.datetime.now().astimezone()
    mismatches: list[str] = []

    for entry in plugins:
        if not isinstance(entry, dict):
            fail(f"expected plugin entry to be an object in {MARKETPLACE_JSON}")
        name = entry.get("name")
        source = entry.get("source")
        declared_status = entry.get("status")
        if not isinstance(source, str):
            fail(f"expected string 'source' for plugin {name!r} in {MARKETPLACE_JSON}")
        if not isinstance(declared_status, str):
            mismatches.append(f"{name}: missing 'status' field")
            continue

        computed_status = derive_status(source, now=now)
        if computed_status != declared_status:
            mismatches.append(
                f"{name}: declared status={declared_status!r} but rule "
                f"currently computes {computed_status!r}"
            )

    if mismatches:
        for mismatch in mismatches:
            print(f"STALE: {mismatch}")
        fail(
            f"{len(mismatches)} plugin(s) have a stale/incorrect 'status' field "
            f"in {MARKETPLACE_JSON.relative_to(ROOT)}; update per the staleness "
            "rule (see scripts/plugin_staleness_audit.py docstring)"
        )

    print(f"OK: all {len(plugins)} plugin status field(s) match the staleness rule")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
