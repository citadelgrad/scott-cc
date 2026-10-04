"""Installed-layout contracts for individually selected skill payloads.

Run npm ci --ignore-scripts to provision the locked skills installer.
No network, provider, actual agent profile or source-tree fallback is used.
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.skills_install_contract import pinned_cli

pytestmark = pytest.mark.installer

ROOT = Path(__file__).resolve().parents[2]
PANEL = "plugins/review-panel/skills/"
AGENTS = {
    "hermes-agent": ".hermes/skills",
    "codex": ".agents/skills",
    "claude-code": ".claude/skills",
    "gemini-cli": ".agents/skills",
    "pi": ".pi/agent/skills",
}


def run(args, cwd, env=None):
    return subprocess.run(
        [str(arg) for arg in args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        timeout=90,
        check=False,
    )


@pytest.fixture
def install(tmp_path):
    installer = pinned_cli()

    def perform(package, agent="hermes-agent"):
        sandbox = tmp_path / (Path(package).name + "-" + agent)
        home, cwd = sandbox / "home", sandbox / "cwd"
        home.mkdir(parents=True)
        cwd.mkdir()
        env = {
            "PATH": os.environ["PATH"],
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(home / ".config"),
            "XDG_CACHE_HOME": str(home / ".cache"),
            "XDG_DATA_HOME": str(home / ".local/share"),
            "CODEX_HOME": str(home / ".codex"),
            "CLAUDE_CONFIG_DIR": str(home / ".claude"),
            "HERMES_HOME": str(home / ".hermes"),
            "PI_CODING_AGENT_DIR": str(home / ".pi/agent"),
            "TMPDIR": str(sandbox),
            "DISABLE_TELEMETRY": "1",
            "DO_NOT_TRACK": "1",
            "CI": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        result = run(
            [
                *installer,
                "add",
                ROOT / package,
                "--skill",
                Path(package).name,
                "--agent",
                agent,
                "--global",
                "--copy",
                "--yes",
            ],
            cwd,
            env,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        installed = home / AGENTS[agent] / Path(package).name
        assert (installed / "SKILL.md").is_file(), result.stdout
        assert not any(p.is_symlink() for p in installed.rglob("*"))
        assert [p.name for p in installed.parent.iterdir()] == [installed.name]
        assert payload(installed) == payload(ROOT / package), (
            "installer omitted or changed payload files"
        )
        return installed, cwd, env

    return perform


REFERENCE_PACKAGES = {
    "plugins/security-suite/skills/plan-security-review": [
        "security-advisor.md",
        "security-suite.md",
    ],
    "plugins/triage/skills/triage-spine": ["foundry-recipes.md"],
    **{
        PANEL + "mental-models-" + name: [
            "reviewers/mental-models-catalog.md",
            "contracts/reviewer-output.md",
        ]
        for name in ("adversarial", "economics", "simplifier", "systems")
    },
    PANEL + "data-steward": [
        "formats/DATA-MODEL-FORMAT.md",
        "contracts/reviewer-output.md",
    ],
    PANEL + "domain-modeling": ["formats/CONTEXT-FORMAT.md", "formats/ADR-FORMAT.md"],
    PANEL + "grill-my-taste": ["formats/TASTE-FORMAT.md"],
    PANEL + "grill-the-schema": [
        "formats/DATA-MODEL-FORMAT.md",
        "formats/ADR-FORMAT.md",
    ],
    PANEL + "grill-with-docs": ["formats/CONTEXT-FORMAT.md", "formats/ADR-FORMAT.md"],
    PANEL + "improve-codebase-architecture": [
        "formats/CONTEXT-FORMAT.md",
        "formats/ADR-FORMAT.md",
    ],
    PANEL + "taste-review": ["formats/TASTE-FORMAT.md", "contracts/reviewer-output.md"],
}


@pytest.mark.parametrize("package,resources", REFERENCE_PACKAGES.items())
def test_format_and_catalog_packages_are_closed(install, package, resources):
    installed, cwd, env = install(package)
    for resource in resources:
        assert (installed / "references" / resource).is_file(), resource
    command = [sys.executable, installed / "scripts/package_contract.py", "doctor"]
    result = run(command, cwd, env)
    assert result.returncode == 0, result.stderr
    (installed / "references" / resources[0]).unlink()
    missing = run(command, cwd, env)
    assert missing.returncode != 0 and resources[0] in missing.stderr


def test_catalog_steward_verifies_explicit_maintainer_inputs(install):
    installed, cwd, env = install(PANEL + "catalog-steward")
    script = installed / "scripts/maintainer_inputs.py"
    assert script.is_file(), "portable steward needs an explicit repo-input preflight"
    missing = run([sys.executable, script], cwd, env)
    assert missing.returncode != 0
    unrelated = run([sys.executable, script, "--repo-root", cwd], cwd, env)
    assert unrelated.returncode != 0 and "maintainer" in unrelated.stderr
    correct = run([sys.executable, script, "--repo-root", ROOT], cwd, env)
    assert correct.returncode == 0, correct.stderr
    inputs = json.loads(correct.stdout)
    assert Path(inputs["catalog"]).is_file()
    assert Path(inputs["script"]).is_file()


def test_delegate_first_has_honest_native_and_sequential_contract():
    text = (ROOT / "skills/delegate-first/SKILL.md").read_text()
    assert "## Capability preflight" in text
    assert "sequential" in text and "not independent" in text
    assert "**Required:** A Claude Code release" not in text
    assert 'subagent_type: "fork"' not in text
    assert "[worker-adapters.md](references/worker-adapters.md)" in text
    adapter = (ROOT / "skills/delegate-first/references/worker-adapters.md").read_text()
    for requirement in (
        "live tool schema",
        "inherited",
        "fresh",
        "unsupported",
        "artifact",
    ):
        assert requirement in adapter


WORKER_PACKAGES = {
    "plugins/mutation-testing/skills/mutation-test": [
        "test-quality-reviewer",
        "test-saboteur",
        "test-executor",
        "test-auditor",
        "test-refactor-specialist",
    ],
    "plugins/variant-explorer/skills/explore-variants": [
        "blind-builder",
        "variant-judge",
    ],
}


@pytest.mark.parametrize("package,roles", WORKER_PACKAGES.items())
def test_worker_prompts_ship_with_portable_dispatch(install, package, roles):
    installed, cwd, env = install(package)
    for role in roles:
        assert (installed / "prompts" / (role + ".md")).is_file(), role
    assert (installed / "references/worker-adapters.md").is_file()
    text = (installed / "SKILL.md").read_text()
    assert "## Capability preflight" in text
    assert "sequential" in text and "unsupported" in text
    command = [sys.executable, installed / "scripts/package_contract.py", "doctor"]
    assert run(command, cwd, env).returncode == 0
    (installed / "prompts" / (roles[0] + ".md")).unlink()
    result = run(command, cwd, env)
    assert result.returncode != 0 and roles[0] in result.stderr


@pytest.mark.parametrize("agent", AGENTS)
def test_panel_runtime_operates_without_plugin_tree(install, agent):
    installed, cwd, env = install(PANEL + "review-panel", agent)
    for asset in (
        "scripts/workspace",
        "scripts/review-package",
        "scripts/checkpoint-claim",
        "resources/reviewers/persona-catalog.md",
        "resources/contracts/reviewer-output.md",
        "resources/agents/clean-room-alternative.md",
    ):
        assert (installed / asset).is_file(), asset
    command = [sys.executable, installed / "scripts/package_contract.py", "doctor"]
    assert run(command, cwd, env).returncode == 0
    assert run(["git", "init", "-q", cwd], cwd, env).returncode == 0
    (cwd / "sample.py").write_text("value = 1\n")
    assert run(["git", "add", "sample.py"], cwd, env).returncode == 0
    commit = run(
        [
            "git",
            "-c",
            "user.name=Package Test",
            "-c",
            "user.email=test@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-qm",
            "fixture",
        ],
        cwd,
        env,
    )
    assert commit.returncode == 0, commit.stderr
    (cwd / "sample.py").write_text("value = 2\n")
    workspace = run(["bash", installed / "scripts/workspace"], cwd, env)
    assert workspace.returncode == 0, workspace.stderr
    artifacts = Path(workspace.stdout.strip())
    output = artifacts / "review.diff"
    result = run(
        ["bash", installed / "scripts/review-package", "--worktree", output], cwd, env
    )
    assert result.returncode == 0, result.stderr
    assert "-value = 1" in output.read_text() and "+value = 2" in output.read_text()
    checkpoint = artifacts / "checkpoint.json"
    checkpoint.write_text(json.dumps({"checkpoint_id": "portable-test"}))
    digest = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    claim = [
        sys.executable,
        installed / "scripts/checkpoint-claim",
        checkpoint,
        "fresh-session",
        digest,
    ]
    assert run(claim, cwd, env).returncode == 0
    replay = run(claim, cwd, env)
    assert replay.returncode != 0 and "checkpoint_already_consumed" in replay.stderr
    (installed / "resources/reviewers/persona-catalog.md").unlink()
    missing = run(command, cwd, env)
    assert missing.returncode != 0 and "persona-catalog" in missing.stderr


def test_tdd_payloads_are_identical_and_preserve_both_contracts():
    canonical = payload(ROOT / "skills/tdd")
    assert canonical == payload(ROOT / PANEL / "tdd"), (
        "same install name must have one byte-identical payload"
    )
    text = canonical["SKILL.md"].decode()
    assert "DO NOT write or modify implementation code until" in text
    assert "No observed, relevant failure means no implementation edit." in text
    for name in (
        "tests.md",
        "mocking.md",
        "deep-modules.md",
        "interface-design.md",
        "refactoring.md",
    ):
        assert name in canonical and f"]({name})" in text
    assert "test-design-quality axis only" in text


def markdown_links(path):
    """Operational markdown links, excluding fenced illustrative documents."""
    fence = None
    for line in path.read_text().splitlines():
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence:
            continue
        line = re.sub(r"`+[^`]*`+", "", line)
        for target in re.findall(r"\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)", line):
            if not target.startswith(("https://", "http://", "mailto:", "#")):
                yield target.split("#", 1)[0]


CLOSED_PACKAGES = (
    list(REFERENCE_PACKAGES)
    + list(WORKER_PACKAGES)
    + [
        PANEL + "review-panel",
        PANEL + "catalog-steward",
        "skills/tdd",
        PANEL + "tdd",
        "skills/delegate-first",
    ]
)


def assert_local_links(directory):
    errors = []
    for path in directory.rglob("*.md"):
        for target in markdown_links(path):
            # These literal output-document placeholders are not package dependencies.
            if target == "NNNN-title.md" and path.parent.as_posix().endswith(
                "/assets/templates"
            ):
                continue
            resolved = (path.parent / target).resolve()
            if (
                not resolved.is_relative_to(directory.resolve())
                or not resolved.is_file()
            ):
                errors.append(f"{path.relative_to(directory)} -> {target}")
    assert not errors, "\n".join(errors)


@pytest.mark.parametrize("package", CLOSED_PACKAGES)
def test_operational_markdown_links_stay_in_package(package):
    assert_local_links(ROOT / package)


@pytest.mark.parametrize("agent", AGENTS)
@pytest.mark.parametrize("package", CLOSED_PACKAGES)
def test_individual_installer_preserves_entire_closed_payload(install, package, agent):
    installed, cwd, env = install(package, agent)
    assert_local_links(installed)
    doctor = installed / "scripts/package_contract.py"
    if doctor.exists():
        result = run([sys.executable, doctor, "doctor"], cwd, env)
        assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "asset",
    [
        "resources/skills/adversarial-reviewer/schemas/adversarial-report-v1.schema.json",
        "resources/agents/clean-room-alternative.md",
        "scripts/review-package",
    ],
)
def test_panel_rejects_missing_transitive_assets(install, asset):
    installed, cwd, env = install(PANEL + "review-panel")
    (installed / asset).unlink()
    result = run(
        [sys.executable, installed / "scripts/package_contract.py", "doctor"], cwd, env
    )
    assert result.returncode != 0 and asset in result.stderr


def test_installed_adversarial_runtime_is_transitively_complete(install):
    installed, cwd, env = install(PANEL + "review-panel")
    seat = installed / "resources/skills/adversarial-reviewer"
    script = seat / "scripts/adversarial_contract.py"
    result = run([sys.executable, script, "doctor"], cwd, env)
    assert result.returncode == 0, result.stdout + result.stderr
    fixture = seat / "tests/fixtures/clean-empty.json"
    result = run([sys.executable, script, "validate", fixture], cwd, env)
    assert result.returncode == 0, result.stdout + result.stderr


def test_manifest_doctor_rejects_source_drift_and_symlink(install, tmp_path):
    package = PANEL + "mental-models-adversarial"
    installed, cwd, env = install(package)
    source_root = tmp_path / "explicit-source-control"
    manifest = json.loads((installed / "package-manifest.json").read_text())
    for entry in manifest["copies"].values():
        target = source_root / entry["source"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / entry["source"], target)
    command = [
        sys.executable,
        installed / "scripts/package_contract.py",
        "doctor",
        "--source-root",
        source_root,
    ]
    assert run(command, cwd, env).returncode == 0
    source = source_root / "plugins/review-panel/reviewers/mental-models-catalog.md"
    source.write_text(source.read_text() + "\nDrift probe.\n")
    drift = run(command, cwd, env)
    assert drift.returncode != 0 and "source drift" in drift.stderr
    target = installed / "references/reviewers/mental-models-catalog.md"
    target.unlink()
    target.symlink_to(source)
    escaped = run(command[:3], cwd, env)
    assert escaped.returncode != 0 and "escapes" in escaped.stderr


@pytest.mark.parametrize(
    "package",
    list(REFERENCE_PACKAGES) + list(WORKER_PACKAGES) + [PANEL + "review-panel"],
)
def test_bundled_copies_match_maintained_sources(package):
    directory = ROOT / package
    manifest = json.loads((directory / "package-manifest.json").read_text())
    assert manifest["copies"], "resources must have source provenance"
    for target, entry in manifest["copies"].items():
        expected = (ROOT / entry["source"]).read_bytes()
        for old, new in entry.get("replacements", []):
            expected = expected.replace(old.encode(), new.encode())
        actual = (directory / target).read_bytes()
        assert actual == expected, (
            f"source drift: {package}/{target} != {entry['source']}"
        )
        assert hashlib.sha256(actual).hexdigest() == entry["sha256"]
    assert set(manifest["required"]) == set(payload(directory)) - {
        "package-manifest.json"
    }


def test_panel_bundles_every_catalog_seat_and_structural_lens():
    directory = ROOT / PANEL / "review-panel"
    resource_map = json.loads((directory / "resource-map.json").read_text())
    catalog = (ROOT / "plugins/review-panel/reviewers/persona-catalog.md").read_text()
    cast_lines = re.findall(r"\*\*Casts:\*\*([^\n]*)", catalog)
    skill_names = {
        name
        for line in cast_lines
        for name in re.findall(r"skills/([^/]+)/SKILL.md", line)
    }
    skill_names.update(
        (
            "ponytail-audit",
            "complexity-recognition",
            "module-boundaries",
            "deep-modules",
            "abstraction-quality",
            "information-hiding",
            "general-vs-special",
            "pull-complexity-down",
            "error-design",
            "naming-obviousness",
            "comments-docs",
            "red-flags",
        )
    )
    for name in skill_names:
        assert (directory / resource_map[f"skills/{name}/SKILL.md"]).is_file(), name
    assert (directory / resource_map["security-suite:security-engineer"]).is_file()
    assert list(directory.rglob("SKILL.md")) == [directory / "SKILL.md"], (
        "resource snapshots must not create discoverable packages"
    )


def payload(directory):
    return {
        p.relative_to(directory).as_posix(): p.read_bytes()
        for p in directory.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }


@pytest.mark.parametrize("agent", AGENTS)
def test_init_templates_work_from_installed_package(install, agent):
    installed, cwd, env = install("skills/init", agent)
    template = installed / "templates/CLAUDE.md"
    assert template.is_file(), (
        "init must bundle its templates, not require CLAUDE_PLUGIN_ROOT"
    )
    assert template.read_bytes() == (ROOT / "templates/CLAUDE.md").read_bytes()
    other = installed / "templates/.pre-commit-config.yaml"
    assert (
        other.read_bytes() == (ROOT / "templates/.pre-commit-config.yaml").read_bytes()
    )
    result = run(
        [sys.executable, installed / "scripts/scaffold.py", "copy", "CLAUDE.md", cwd],
        cwd,
        env,
    )
    assert result.returncode == 0, result.stderr
    assert (cwd / "CLAUDE.md").read_bytes() == template.read_bytes()
    refused = run(
        [sys.executable, installed / "scripts/scaffold.py", "copy", "CLAUDE.md", cwd],
        cwd,
        env,
    )
    assert refused.returncode != 0, "existing user files must not be overwritten"
    template.unlink()
    missing = run(
        [sys.executable, installed / "scripts/scaffold.py", "doctor"], cwd, env
    )
    assert missing.returncode != 0 and "CLAUDE.md" in missing.stderr
