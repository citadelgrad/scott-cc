#!/usr/bin/env python3
"""Verify the installed payload; optional explicit source-root drift check."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def confined(root, relative):
    path = root / relative
    if Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError(f"unsafe manifest path: {relative}")
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"path escapes package: {relative}")
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"missing or unsafe package asset: {relative}")
    return path


def check(source_root=None):
    manifest = json.loads((ROOT / "package-manifest.json").read_text())
    if manifest.get("version") != 1 or not manifest.get("required"):
        raise ValueError("invalid package manifest")
    for relative in manifest["required"]:
        confined(ROOT, relative)
    for relative, entry in manifest["copies"].items():
        data = confined(ROOT, relative).read_bytes()
        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError(f"bundled asset changed: {relative}")
        if source_root is not None:
            expected = confined(source_root, entry["source"]).read_bytes()
            for old, new in entry.get("replacements", []):
                expected = expected.replace(old.encode(), new.encode())
            if data != expected:
                raise ValueError(f"source drift: {relative} != {entry['source']}")
    return len(manifest["required"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["doctor"])
    parser.add_argument(
        "--source-root",
        type=Path,
        help="maintainer-only explicit repository for drift checks",
    )
    args = parser.parse_args()
    try:
        count = check(args.source_root)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"package contract failed: {exc}", file=sys.stderr)
        return 2
    print(f"package contract OK: {count} required files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
