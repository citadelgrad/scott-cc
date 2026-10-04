#!/usr/bin/env python3
"""Verify an explicitly supplied scott-cc maintainer checkout; never locate clones."""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    try:
        git = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            text=True,
            capture_output=True,
            check=True,
        )
        if Path(git.stdout.strip()).resolve() != root:
            raise ValueError("--repo-root must be the maintainer repository root")
        metadata = json.loads((root / ".claude-plugin/plugin.json").read_text())
        if metadata.get("name") != "scott-cc":
            raise ValueError("not a scott-cc maintainer repository")
        inputs = {
            "script": "scripts/catalog_seat_audit.py",
            "catalog": "plugins/review-panel/reviewers/persona-catalog.md",
            "design_review": "plugins/review-panel/skills/design-review/SKILL.md",
            "skills_dir": "plugins/review-panel/skills",
        }
        for key, relative in inputs.items():
            path = root / relative
            valid = path.is_dir() if key == "skills_dir" else path.is_file()
            if not valid or not path.resolve().is_relative_to(root):
                raise ValueError(f"missing/escaping maintainer input: {relative}")
            inputs[key] = str(path)
        print(json.dumps(inputs, indent=2))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"maintainer repository unavailable: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
