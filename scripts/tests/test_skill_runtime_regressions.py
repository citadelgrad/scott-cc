"""Runtime contracts exercised through real single-package copy installs.

Run npm ci --ignore-scripts to provision the locked installer. No source-copy
substitute is used. SKILLS_RUNTIME_SOURCE may point at a frozen baseline for
red/control runs. Browser tests below exercise only offline boundaries.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.skills_install_contract import pinned_cli

pytestmark = pytest.mark.installer

REPO = Path(__file__).resolve().parents[2]
SOURCE = Path(os.environ.get("SKILLS_RUNTIME_SOURCE", REPO))


def run(args, cwd, env, timeout=60):
    return subprocess.run(
        [str(arg) for arg in args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


@pytest.fixture
def installed(tmp_path):
    def install(relative):
        home = tmp_path / "home"
        cwd = tmp_path / "neutral"
        home.mkdir(exist_ok=True)
        cwd.mkdir(exist_ok=True)
        env = {
            "PATH": os.environ["PATH"],
            "HOME": str(home),
            "TMPDIR": str(tmp_path),
            "XDG_CACHE_HOME": str(home / ".cache"),
            "XDG_CONFIG_HOME": str(home / ".config"),
            "XDG_DATA_HOME": str(home / ".local/share"),
            "CODEX_HOME": str(home / ".codex"),
            "HERMES_HOME": str(home / ".hermes"),
            "CLAUDE_CONFIG_DIR": str(home / ".claude"),
            "GEMINI_CLI_HOME": str(home),
            "PI_CODING_AGENT_DIR": str(home / ".pi/agent"),
            "npm_config_cache": str(home / ".npm"),
            "UV_CACHE_DIR": str(home / ".uv"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "DO_NOT_TRACK": "1",
            "DISABLE_TELEMETRY": "1",
            "CI": "1",
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        }
        installer = pinned_cli()
        name = Path(relative).name
        result = run(
            [
                *installer,
                "add",
                SOURCE / relative,
                "--skill",
                name,
                "--agent",
                "hermes-agent",
                "--global",
                "--copy",
                "--yes",
            ],
            cwd,
            env,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        package = home / ".hermes/skills" / name
        assert (package / "SKILL.md").is_file()
        assert sorted(p.name for p in package.parent.iterdir()) == [name]
        assert not any(p.is_symlink() for p in package.rglob("*"))
        return package, cwd, env

    return install


def test_installed_beads_checker_requires_all_operational_assets(installed):
    package, cwd, env = installed("skills/beads")
    checker = package / "scripts/beads_skill_contract.py"
    assert run([sys.executable, checker, "check"], cwd, env).returncode == 0
    assets = sorted(
        p
        for directory in ("references", "scripts", "schemas", "evals")
        for p in (package / directory).rglob("*")
        if p.is_file()
    )
    assert len(assets) >= 65
    accepted = []
    for asset in assets:
        relative = asset.relative_to(package).as_posix()
        content = asset.read_bytes()
        asset.unlink()
        try:
            result = run([sys.executable, checker, "check"], cwd, env)
            if result.returncode == 0 or relative not in result.stdout + result.stderr:
                accepted.append(
                    (relative, result.returncode, result.stdout, result.stderr)
                )
        finally:
            asset.write_bytes(content)
    assert not accepted, accepted


@pytest.mark.parametrize(
    "relative,script,command,asset",
    [
        (
            "skills/beads",
            "beads_skill_contract.py",
            "check",
            "scripts/hermes_discovery_harness.py",
        ),
        (
            "skills/adversarial-reviewer",
            "adversarial_contract.py",
            "doctor",
            "references/control-backed-findings.md",
        ),
        (
            "plugins/review-panel/skills/adversarial-reviewer",
            "adversarial_contract.py",
            "doctor",
            "schemas/adversarial-report-v1.schema.json",
        ),
    ],
)
def test_installed_doctors_reject_escapes(installed, relative, script, command, asset):
    package, cwd, env = installed(relative)
    argv = [sys.executable, package / "scripts" / script, command]
    assert run(argv, cwd, env).returncode == 0
    original = (package / asset).read_bytes()
    outside = cwd / "outside.md"
    outside.write_bytes(original)
    (package / asset).unlink()
    (package / asset).symlink_to(outside)
    result = run(argv, cwd, env)
    assert result.returncode != 0, "external required symlink accepted"
    assert "escape" in result.stderr.lower() or "unsafe" in result.stderr.lower()
    (package / asset).unlink()
    (package / asset).write_bytes(original)

    entry = (
        package
        / "references"
        / ("sources.md" if command == "check" else "agent-contract.md")
    )
    text = entry.read_text()
    # Existing escape is as invalid as a missing link. A second-hop document
    # must be validated too, not only SKILL.md's immediate links.
    external = package.parent / "outside.md"
    external.write_text("outside the package")
    for target in (
        "../../outside.md",
        "../../%6futside.md",
        str(external),
        external.as_uri(),
    ):
        entry.write_text(text + f"\n[escape]({target})\n")
        result = run(argv, cwd, env)
        assert result.returncode != 0, target
        assert "escape" in result.stderr.lower() or "unsafe" in result.stderr.lower()
    entry.write_text(text + f"\n[escape][outside]\n[outside]: <{external}>\n")
    result = run(argv, cwd, env)
    assert result.returncode != 0
    entry.write_text(text)
    escaped_dir = package / "external-directory"
    escaped_dir.symlink_to(cwd, target_is_directory=True)
    result = run(argv, cwd, env)
    assert result.returncode != 0
    escaped_dir.unlink()
    entry.write_text(text + "\n[missing](missing-operational-reference.md)\n")
    result = run(argv, cwd, env)
    assert result.returncode != 0
    assert "missing-operational-reference.md" in result.stderr


def test_installed_browser_pytest_example_is_executable_in_strict_mode(installed):
    package, cwd, env = installed("plugins/browser-automation/skills/browser-use-e2e")
    text = (package / "SKILL.md").read_text()
    snippet = (
        text.split("### With Pytest", 1)[1].split("```python", 1)[1].split("```", 1)[0]
    )
    (cwd / "test_example.py").write_text(snippet)
    # Deterministic external-service doubles: this verifies snippet bindings and
    # actual pytest-asyncio lifecycle, NOT a browser or authentication result.
    (cwd / "browser_use.py").write_text("""
class Browser:
    def __init__(self, **kwargs): pass
    async def close(self): pass
    async def stop(self): pass
class ChatBrowserUse: pass
class Agent:
    def __init__(self, *, browser, **kwargs):
        assert isinstance(browser, Browser), type(browser)
    async def run(self, *, max_steps):
        assert max_steps == 50
        return self
    def is_successful(self): return True
""")
    (cwd / "conftest.py").write_text("def build_sensitive_data(): return {}\n")
    result = run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "pytest_asyncio.plugin",
            "--asyncio-mode=strict",
            "test_example.py",
        ],
        cwd,
        env,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    shutil.copyfile(package / "conftest.py", cwd / "conftest.py")
    (cwd / "test_fixture.py").write_text("""
import pytest
from browser_use import Browser
@pytest.mark.asyncio
async def test_fixture(browser):
    assert isinstance(browser, Browser)
""")
    result = run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "pytest_asyncio.plugin",
            "--asyncio-mode=strict",
            "test_fixture.py",
        ],
        cwd,
        env,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    for dependency in ("pytest", "pytest-asyncio", "pytest-html", "python-dotenv"):
        assert re.search(r"uv add[^\n]*" + dependency, text), dependency


def test_installed_browser_profile_missing_dependency_is_error(installed):
    package, cwd, env = installed("plugins/browser-automation/skills/browser-use-e2e")
    script = package / "setup_profile.py"
    for option in ("--help", "--list"):
        assert run([sys.executable, "-S", script, option], cwd, env).returncode == 0
    result = run([sys.executable, "-S", script, "--service", "github"], cwd, env)
    assert result.returncode != 0, result.stdout + result.stderr
    assert "browser-use not installed" in result.stderr
    assert "Profile saved" not in result.stdout


@pytest.mark.parametrize(
    "outcome",
    ["empty", "persisted", "start_failure", "navigation_failure", "shutdown_failure"],
)
def test_installed_browser_profile_success_requires_persistence(
    installed, monkeypatch, capsys, outcome
):
    package, cwd, _env = installed("plugins/browser-automation/skills/browser-use-e2e")
    spec = importlib.util.spec_from_file_location(
        "profile_under_test", package / "setup_profile.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "PROFILES_DIR", cwd / "profiles")
    calls = []

    class BrowserDouble:
        # Mirrors the actual browser-use 0.13 public session API. No service,
        # authentication, or live-model result is claimed by this boundary test.
        def __init__(self, *, user_data_dir, **kwargs):
            self.profile = Path(user_data_dir)

        async def start(self):
            calls.append("start")
            if outcome == "start_failure":
                raise RuntimeError("start failed")

        async def new_page(self, url=None):
            calls.append("navigate")
            if outcome == "navigation_failure":
                raise RuntimeError("navigation failed")

        async def stop(self):
            calls.append("stop")
            if outcome == "shutdown_failure":
                raise RuntimeError("shutdown failed")
            if outcome == "persisted":
                (self.profile / "Default").mkdir()
                (self.profile / "Default/Preferences").write_text(
                    '{"profile": {"name": "test"}}'
                )

    monkeypatch.setitem(
        sys.modules, "browser_use", SimpleNamespace(Browser=BrowserDouble)
    )
    monkeypatch.setattr("builtins.input", lambda prompt: "")
    monkeypatch.setattr(
        sys,
        "argv",
        ["setup_profile.py", "--url", "https://example.test", "--profile-name", "test"],
    )
    code = module.main()
    output = capsys.readouterr()
    assert "stop" in calls, calls
    if outcome == "persisted":
        assert code == 0, output
        assert "Profile saved" in output.out
        assert (cwd / "profiles/test/Default/Preferences").is_file()
    else:
        assert code != 0, output
        assert "Profile saved" not in output.out
        assert "Error:" in output.err


def test_installed_scaling_property_handles_former_float_counterexample(installed):
    package, cwd, env = installed("skills/property-based-testing")
    probe = """
import importlib.util, sys
spec = importlib.util.spec_from_file_location("examples", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.test_scaling_inputs_scales_sum.hypothesis.inner_test([1e308, -1e308], 2)
"""
    result = run([sys.executable, "-c", probe, package / "examples.py"], cwd, env)
    assert result.returncode == 0, result.stdout + result.stderr
    result = run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "_hypothesis_pytestplugin",
            "--hypothesis-seed=20261003",
            package / "examples.py",
        ],
        cwd,
        env,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "14 passed" in result.stdout


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
@pytest.mark.parametrize("trailing", [0, 1, 2])
@pytest.mark.parametrize(
    "pattern",
    [
        "---\nstatus: proposed\n---\n# Decision",
        "# Decision\n\n- Status: proposed",
        "# Decision\n\n## Status\n\nproposed\n\n## Context\ntext",
    ],
)
def test_installed_adr_status_is_byte_idempotent(installed, newline, trailing, pattern):
    package, cwd, env = installed("plugins/review-panel/skills/adr-skill")
    original = (pattern.replace("\n", newline) + newline * trailing).encode()
    document = cwd / "decision.md"
    document.write_bytes(original)
    argv = [
        shutil.which("node"),
        package / "scripts/set_adr_status.js",
        document,
        "--status",
        "accepted",
        "--json",
    ]
    result = run(argv, cwd, env)
    assert result.returncode == 0, result.stdout + result.stderr
    expected = original.replace(b"proposed", b"accepted")
    assert document.read_bytes() == expected
    assert json.loads(result.stdout)["changed"] is True
    mtime = document.stat().st_mtime_ns
    result = run(argv, cwd, env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert document.read_bytes() == expected
    assert json.loads(result.stdout)["changed"] is False
    assert document.stat().st_mtime_ns == mtime


def test_adversarial_runtime_mirror_is_byte_identical():
    def files(relative):
        directory = REPO / relative
        return {
            p.relative_to(directory).as_posix(): p.read_bytes()
            for p in directory.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts
        }

    assert files("skills/adversarial-reviewer") == files(
        "plugins/review-panel/skills/adversarial-reviewer"
    )


def test_installed_beads_excludes_custodian_scorer(installed):
    package, cwd, env = installed("skills/beads")
    for relative in (
        "scripts/evaluator.py",
        "scripts/evidence_adapter.py",
        "evals/source-contracts",
    ):
        assert not (package / relative).exists(), relative
    result = run(
        [sys.executable, package / "scripts/beads_skill_contract.py", "check"], cwd, env
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_installed_beads_custodian_entrypoint_is_explicit_and_fail_closed(installed):
    package, cwd, env = installed("skills/beads")
    launcher = package / "scripts/evaluate_skill.py"
    help_result = run([sys.executable, launcher, "--help"], cwd, env)
    assert help_result.returncode == 0
    assert "custodian" in help_result.stdout.lower()
    assert "evaluation/beads-skill/harness/evaluate_skill.py" in help_result.stdout
    # A sibling checkout-looking directory must not become an implicit import.
    fake = package.parents[2] / "evaluation/beads-skill/harness/evaluator.py"
    fake.parent.mkdir(parents=True)
    fake.write_text("raise RuntimeError('MUST NOT IMPORT')\n")
    result = run([sys.executable, launcher, "aggregate"], cwd, env)
    assert result.returncode == 2
    assert json.loads(result.stderr)["error_code"] == "CUSTODIAN_CHECKOUT_REQUIRED"
    assert "MUST NOT IMPORT" not in result.stdout + result.stderr


def test_custodian_evaluator_preserves_frozen_implementation_identity():
    manifest = json.loads(
        (REPO / "evaluation/beads-skill/manifests/release-v1.json").read_text()
    )
    evaluator = REPO / "evaluation/beads-skill/harness/evaluator.py"
    assert (
        hashlib.sha256(evaluator.read_bytes()).hexdigest()
        == manifest["verifier_sha256"]
    )
