#!/usr/bin/env python3
"""Explain the explicit custodian boundary for installed Beads packages."""

from __future__ import annotations

import argparse
import json
import sys

CUSTODIAN_COMMAND = "uv run python evaluation/beads-skill/harness/evaluate_skill.py"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Evaluation is custodian-only, not part of the installed operational skill. "
            "From an explicit scott-cc source checkout outside the evaluated-agent "
            f"filesystem, run: {CUSTODIAN_COMMAND}. "
            "No neighboring checkout is searched or imported."
        ),
    )
    parser.parse_known_args(argv)
    print(
        json.dumps(
            {
                "status": "unavailable",
                "error_code": "CUSTODIAN_CHECKOUT_REQUIRED",
                "command": CUSTODIAN_COMMAND,
            }
        ),
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
