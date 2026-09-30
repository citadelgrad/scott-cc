#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Preflight for the Graphiti setup. Prints one JSON report. Never prints a secret value.

preflight.py [--ports 48100,48101,48102]
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys

KEY_VARS = [
    "OPENAI_API_KEY",
    "GOOGLE_API_KEY",
    "ANTHROPIC_API_KEY",
    "GROQ_API_KEY",
    "VOYAGE_API_KEY",
]
TOOLS = ["docker", "uv", "jq", "git", "curl", "lsof", "doppler", "op", "direnv"]
AGENTS = ["claude", "codex", "hermes"]


def run(cmd: list[str], timeout: float = 8.0) -> tuple[int, str]:
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
        return r.returncode, (r.stdout + r.stderr).strip()
    except Exception as exc:  # noqa: BLE001 - report, do not raise
        return 1, str(exc)


def port_listener(port: int) -> str | None:
    """Name of the process listening on the TCP port, or None if free (uses lsof)."""
    code, out = run(["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-Fc"])
    for line in out.splitlines():
        if line.startswith("c"):
            return line[1:]
    return None if code in (0, 1) else "unknown"


def collect(ports: list[int]) -> dict:
    report: dict = {"os": platform.system(), "macos": platform.system() == "Darwin"}
    report["tools"] = {t: shutil.which(t) is not None for t in TOOLS}
    report["agents"] = {a: shutil.which(a) is not None for a in AGENTS}
    if report["tools"]["docker"]:
        code, _ = run(["docker", "info"], timeout=15)
        report["docker_running"] = code == 0
    else:
        report["docker_running"] = False
    report["keys_present"] = {
        k: bool(os.environ.get(k)) for k in KEY_VARS
    }  # presence only
    report["ports"] = {str(p): port_listener(p) for p in ports}
    report["ports_free"] = all(v is None for v in report["ports"].values())
    required = ["docker", "uv", "jq", "git", "curl", "lsof"]
    report["missing_required"] = [t for t in required if not report["tools"][t]]
    report["ok"] = bool(
        report["macos"]
        and report["docker_running"]
        and not report["missing_required"]
        and report["ports_free"]
    )
    return report


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--ports", default="48100,48101,48102")
    args = p.parse_args()
    report = collect([int(x) for x in args.ports.split(",") if x.strip()])
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
