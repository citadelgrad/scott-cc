#!/usr/bin/env python3
"""Check/copy bundled init templates without relying on a plugin installation."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ("CLAUDE.md", ".pre-commit-config.yaml")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="verify both package-local templates")
    copy = sub.add_parser("copy", help="create one template; never overwrite")
    copy.add_argument("template", choices=TEMPLATES)
    copy.add_argument("destination", type=Path, help="existing project directory")
    args = parser.parse_args()
    try:
        for name in TEMPLATES:
            source = ROOT / "templates" / name
            if not source.is_file() or source.is_symlink():
                raise ValueError(f"missing or unsafe bundled template: {name}")
        if args.command == "copy":
            source = ROOT / "templates" / args.template
            destination = args.destination / args.template
            with destination.open("xb") as output:
                output.write(source.read_bytes())
            print(destination.resolve())
        else:
            print("init templates OK")
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
