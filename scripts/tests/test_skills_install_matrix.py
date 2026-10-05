"""Real pinned installer contracts. `-m 'not installer'` is only the fast subset."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from scripts.skills_install_contract import (
    AGENTS,
    ROOT,
    InstallSandbox,
    assert_copy_install,
    pinned_cli,
    run_installed_contract,
)
from scripts.verify_skills_distribution import skill_paths

PACKAGES = [path.parent.relative_to(ROOT).as_posix() for path in skill_paths(ROOT)]
# Root SKILL.md wins discovery over a same-name plugin mirror. Equality is a static gate.
SOURCES = {Path(path).name: path for path in sorted(PACKAGES)}


@pytest.mark.installer
@pytest.mark.parametrize("name", ["lib-upgrades", "prod-errors"])
@pytest.mark.parametrize("agent", AGENTS)
def test_nested_detectors_are_selectable_from_repository(tmp_path, name, agent):
    box = InstallSandbox(tmp_path)
    result = box.add(ROOT, name, agent, "project")
    assert result.returncode == 0, result.stdout + result.stderr
    assert_copy_install(box, ROOT / SOURCES[name], name, agent, "project")


@pytest.mark.installer
@pytest.mark.parametrize("relative", PACKAGES)
@pytest.mark.parametrize("agent", AGENTS)
@pytest.mark.parametrize("scope", ["project", "global"])
def test_every_physical_package_copies_to_exact_target(
    tmp_path, relative, agent, scope
):
    source = ROOT / relative
    box = InstallSandbox(tmp_path)
    result = box.add(source, source.name, agent, scope)
    assert result.returncode == 0, result.stdout + result.stderr
    installed = assert_copy_install(box, source, source.name, agent, scope)
    run_installed_contract(box, installed)


@pytest.mark.installer
@pytest.mark.parametrize("name", sorted(SOURCES))
@pytest.mark.parametrize("agent", AGENTS)
def test_every_repository_selection_has_canonical_payload(tmp_path, name, agent):
    box = InstallSandbox(tmp_path)
    result = box.add(ROOT, name, agent, "project")
    assert result.returncode == 0, result.stdout + result.stderr
    assert_copy_install(box, ROOT / SOURCES[name], name, agent, "project")


@pytest.mark.installer
def test_repository_list_is_exact_inventory_not_a_partial_success(tmp_path):
    assert PACKAGES, "inventory cannot be empty"
    box = InstallSandbox(tmp_path)
    result = box.run(pinned_cli() + ["add", str(ROOT), "--list"])
    assert result.returncode == 0, result.stdout + result.stderr
    clean = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout)
    names = re.findall(r"^│    ([a-z0-9]+(?:-[a-z0-9]+)*)\s*$", clean, re.M)
    assert set(names) == set(SOURCES), clean
    assert len(names) == len(set(names)), "duplicate discovery entries"


@pytest.mark.installer
@pytest.mark.parametrize(
    "mutation", ["wrong-target", "missing", "truncated", "extra", "external-symlink"]
)
def test_real_installed_payload_faults_are_detected(tmp_path, mutation):
    source = ROOT / "skills/adversarial-reviewer"
    box = InstallSandbox(tmp_path)
    result = box.add(
        source,
        source.name,
        "codex" if mutation == "wrong-target" else "hermes-agent",
        "project",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    installed = box.destination(source.name, "hermes-agent", "project")
    asset = installed / "references/control-backed-findings.md"
    if mutation == "missing":
        asset.unlink()
    elif mutation == "truncated":
        asset.write_text("truncated")
    elif mutation == "extra":
        (installed / "unexpected").write_text("unexpected")
    elif mutation == "external-symlink":
        asset.unlink()
        asset.symlink_to(source / "references/control-backed-findings.md")
    with pytest.raises(AssertionError):
        assert_copy_install(box, source, source.name, "hermes-agent", "project")


@pytest.mark.installer
@pytest.mark.parametrize(
    "header",
    [
        "description: null",
        "description: []",
        "description: 7",
        "description: true",
        "description: {a: b}",
        "description: [bad",
        "description: first\ndescription: second",
    ],
)
def test_real_installer_rejects_invalid_yaml(tmp_path, header):
    source = tmp_path / "source/alpha"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text(f"---\nname: alpha\n{header}\n---\nProcedure\n")
    box = InstallSandbox(tmp_path / "box")
    result = box.add(source, "alpha", "codex", "project")
    assert result.returncode != 0, result.stdout + result.stderr
    assert not list(box.cwd.rglob("SKILL.md"))


@pytest.mark.installer
@pytest.mark.parametrize("asset", ["metadata.json", "data.json"])
def test_required_filtered_resource_fails_installed_closure(tmp_path, asset):
    source = tmp_path / "source/alpha"
    source.mkdir(parents=True)
    (source / asset).write_text('{"required": true}\n')
    (source / "SKILL.md").write_text(
        f"---\nname: alpha\ndescription: required resource fixture\n---\nRead [data]({asset}).\n"
    )
    box = InstallSandbox(tmp_path / "box")
    result = box.add(source, "alpha", "hermes-agent", "project")
    assert result.returncode == 0, result.stdout + result.stderr
    if asset == "metadata.json":
        with pytest.raises(AssertionError, match="metadata.json"):
            assert_copy_install(box, source, "alpha", "hermes-agent", "project")
    else:
        assert_copy_install(box, source, "alpha", "hermes-agent", "project")


@pytest.mark.installer
@pytest.mark.parametrize(
    "asset",
    [
        "references/guide.md",
        "schemas/report.json",
        "prompts/task.md",
        "scripts/check.py",
    ],
)
def test_real_install_detects_missing_each_asset_category(tmp_path, asset):
    from scripts.verify_skills_distribution import package_asset_errors

    source = tmp_path / "source/alpha"
    required = source / asset
    required.parent.mkdir(parents=True)
    required.write_text("required artifact")
    (source / "SKILL.md").write_text(
        f"---\nname: alpha\ndescription: asset fixture\n---\nRead [required]({asset}).\n"
    )
    box = InstallSandbox(tmp_path / "box")
    result = box.add(source, "alpha", "hermes-agent", "project")
    assert result.returncode == 0, result.stdout + result.stderr
    installed = assert_copy_install(box, source, "alpha", "hermes-agent", "project")
    assert package_asset_errors(installed) == []
    (installed / asset).unlink()
    assert any(asset in error for error in package_asset_errors(installed))
    with pytest.raises(AssertionError, match="payload mismatch"):
        assert_copy_install(box, source, "alpha", "hermes-agent", "project")


def test_sandbox_drops_ambient_credentials_and_loader_overrides(tmp_path, monkeypatch):
    from scripts.skills_install_contract import sandbox_environment

    for key in (
        "NODE_OPTIONS",
        "PYTHONPATH",
        "GH_TOKEN",
        "ANTHROPIC_API_KEY",
        "HTTPS_PROXY",
    ):
        monkeypatch.setenv(key, "canary-do-not-inherit")
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "forbidden"))
    env = sandbox_environment(tmp_path / "box")
    assert "canary-do-not-inherit" not in json.dumps(env)
    assert env["HERMES_HOME"] != str(tmp_path / "forbidden")
    assert not (tmp_path / "forbidden").exists()


def test_missing_or_wrong_installer_version_is_a_hard_error(tmp_path):
    with pytest.raises(RuntimeError, match="npm ci"):
        pinned_cli(tmp_path)
    metadata = tmp_path / "node_modules/skills/package.json"
    metadata.parent.mkdir(parents=True)
    metadata.write_text('{"version":"0.0.0"}')
    with pytest.raises(RuntimeError, match="must be skills@1.7.0"):
        pinned_cli(tmp_path)
