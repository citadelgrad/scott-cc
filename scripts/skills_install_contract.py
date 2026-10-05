"""Test support for real skills@1.7.0 installs, never an agent-home installer.

No fallback to npx/latest: missing prerequisites are errors, not skipped cases.
Only disposable sandboxes supplied by the caller are written.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.7.0"
AGENTS = ("codex", "hermes-agent", "claude-code", "gemini-cli", "pi")
PROJECT_PATHS = {
    "codex": ".agents/skills",
    "gemini-cli": ".agents/skills",
    "hermes-agent": ".hermes/skills",
    "claude-code": ".claude/skills",
    "pi": ".pi/skills",
}
GLOBAL_PATHS = {**PROJECT_PATHS, "pi": ".pi/agent/skills"}


def pinned_cli(root: Path = ROOT) -> list[str]:
    package = root / "node_modules/skills"
    if not (package / "package.json").is_file():
        raise RuntimeError("pinned installer missing: run npm ci --ignore-scripts")
    if json.loads((package / "package.json").read_text())["version"] != VERSION:
        raise RuntimeError(
            f"installer must be skills@{VERSION}; run npm ci --ignore-scripts"
        )
    node = shutil.which("node")
    if node is None:
        raise RuntimeError("Node >=22 is required for the real installer gate")
    return [str(Path(node).resolve()), str(package / "bin/cli.mjs")]


def sandbox_environment(base: Path) -> dict[str, str]:
    """Allowlist, not an ambient-environment copy (no tokens or loader overrides)."""
    base = base.resolve()
    paths = {
        "HOME": base / "home",
        "CODEX_HOME": base / "home/.codex",
        "HERMES_HOME": base / "home/.hermes",
        "CLAUDE_CONFIG_DIR": base / "home/.claude",
        "GEMINI_CLI_HOME": base / "home",
        "PI_CODING_AGENT_DIR": base / "home/.pi/agent",
        "XDG_CACHE_HOME": base / "cache",
        "XDG_CONFIG_HOME": base / "config",
        "XDG_DATA_HOME": base / "data",
        "XDG_STATE_HOME": base / "state",
        "TMPDIR": base / "tmp",
        "npm_config_cache": base / "npm-cache",
        "npm_config_prefix": base / "npm-prefix",
        "UV_CACHE_DIR": base / "uv-cache",
        "UV_TOOL_DIR": base / "uv-tools",
        "UV_PYTHON_INSTALL_DIR": base / "uv-python",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    safe_bin = base / "bin"
    safe_bin.mkdir(exist_ok=True)
    for name in ("node", "git"):
        executable = shutil.which(name)
        if executable is None:
            raise RuntimeError(f"{name} is required")
        link = safe_bin / name
        if not link.exists():
            link.symlink_to(Path(executable).resolve())
    env = {key: str(value) for key, value in paths.items()}
    env.update(
        {
            "PATH": str(safe_bin) + os.pathsep + os.defpath,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": str(base / "home/.gitconfig"),
            "GIT_TERMINAL_PROMPT": "0",
            "npm_config_userconfig": str(base / "home/.npmrc"),
            "npm_config_globalconfig": str(base / "home/global.npmrc"),
            "CI": "1",
            "DO_NOT_TRACK": "1",
            "DISABLE_TELEMETRY": "1",
            "NO_COLOR": "1",
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "LANG": "C.UTF-8",
        }
    )
    return env


class InstallSandbox:
    def __init__(self, base: Path):
        self.base = base.resolve()
        self.env = sandbox_environment(self.base)
        self.cwd = self.base / "project"
        self.cwd.mkdir(exist_ok=True)
        self.neutral = self.base / "neutral"
        self.neutral.mkdir(exist_ok=True)
        self.run(["git", "init", "--quiet", str(self.cwd)])

    def run(self, argv: list, *, neutral: bool = False, timeout: int = 120):
        return subprocess.run(
            [str(arg) for arg in argv],
            cwd=self.neutral if neutral else self.cwd,
            env=self.env,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )

    def destination(self, name: str, agent: str, scope: str) -> Path:
        base = Path(self.env["HOME"]) if scope == "global" else self.cwd
        return (
            base / (GLOBAL_PATHS if scope == "global" else PROJECT_PATHS)[agent] / name
        )

    def add(
        self,
        source: Path | str,
        name: str,
        agent: str,
        scope: str,
        *,
        copy: bool = True,
    ):
        args = pinned_cli() + [
            "add",
            str(source),
            "--skill",
            name,
            "--agent",
            agent,
            "--yes",
        ]
        if copy:
            args.append("--copy")
        if scope == "global":
            args.append("--global")
        return self.run(args)


def payload(root: Path) -> dict[str, str]:
    """Expected copied files; the exclusions match pinned skills' documented filter."""
    files = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if (
            set(relative.parts) & {".git", "__pycache__", "__pypackages__"}
            or path.name == "metadata.json"
        ):
            continue
        if path.is_symlink():
            raise AssertionError(f"package symlink is not allowed: {path}")
        if path.is_file():
            files[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return files


def assert_copy_install(
    box: InstallSandbox, source: Path, name: str, agent: str, scope: str
) -> Path:
    from scripts.verify_skills_distribution import package_asset_errors

    installed = box.destination(name, agent, scope)
    # Never rglob for a winner: a valid package at the wrong target is a failure.
    assert installed.is_dir() and not installed.is_symlink(), (
        f"missing exact copy target: {installed}"
    )
    expected = payload(source)
    actual = payload(installed)
    assert actual == expected, (
        f"payload mismatch at {installed}: missing={expected.keys() - actual.keys()}, extra={actual.keys() - expected.keys()}"
    )
    # Byte equality after installer filtering is not dependency completeness:
    # a linked metadata.json can be absent from BOTH filtered inventories.
    assert not (errors := package_asset_errors(installed)), errors
    observed = set(box.cwd.rglob("SKILL.md")) | set(
        Path(box.env["HOME"]).rglob("SKILL.md")
    )
    assert observed == {installed / "SKILL.md"}, (
        f"unexpected target/sibling packages: {observed}"
    )
    return installed


def run_installed_contract(box: InstallSandbox, installed: Path) -> None:
    """Bounded local-only operations, not model-backed behavioral certification."""
    name = installed.name
    if name == "adversarial-reviewer":
        script = installed / "scripts/adversarial_contract.py"
        report = installed / "tests/fixtures/clean-empty.json"
        commands = [
            [sys.executable, script, "doctor", "--skill-root", installed],
            [sys.executable, script, "validate", report],
            [
                sys.executable,
                script,
                "sarif",
                report,
                "--output",
                box.neutral / "report.sarif",
            ],
        ]
    elif name == "beads":
        commands = [
            [sys.executable, installed / "scripts/beads_skill_contract.py", "check"],
            [sys.executable, installed / "scripts/beads_coordinator.py", "--help"],
        ]
    else:
        commands = []
    if name == "beads":
        packet = box.neutral / "invalid-worker-packet.json"
        packet.write_text("{}")
        rejected = box.run(
            [
                sys.executable,
                installed / "scripts/validate_worker_packet.py",
                "validate",
                "--packet",
                packet,
                "--json",
            ],
            neutral=True,
        )
        assert rejected.returncode == 2, rejected.stdout + rejected.stderr
        assert json.loads(rejected.stdout) == {
            "status": "invalid",
            "error_code": "WORKER_PACKET_INVALID",
        }
    for command in commands:
        result = box.run(command, neutral=True)
        assert result.returncode == 0, result.stdout + result.stderr
