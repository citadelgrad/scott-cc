"""Checkout gates are not replaced by passing fixture tests."""

import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "script", ["verify_skills_distribution.py", "verify_plugin.py"]
)
def test_current_checkout_contract_entrypoints(script):
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_inventory_accounts_for_every_source_and_runtime_boundary():
    import json

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/verify_skills_distribution.py"),
            "--inventory-json",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    data = json.loads(result.stdout)
    expected = {
        str(path.relative_to(ROOT))
        for base in ["skills", "plugins", ".agents/skills"]
        for path in (ROOT / base).rglob("SKILL.md")
    }
    assert {row["path"] for row in data["packages"]} == expected
    assert len(data["packages"]) == len(expected)
    assert all(row["runtime_certified"] is False for row in data["packages"])
    beads = next(
        row for row in data["packages"] if row["path"] == "skills/beads/SKILL.md"
    )
    assert beads["release_status"] == "REJECT: advanced swarm/runtime candidate"


def test_current_checkout_orchestration_static_contract():
    from scripts.verify_orchestration_contracts import verify

    # Optional external CLIs are not portable package contents. No runtime-ready claim.
    assert verify(ROOT, check_cli=False) == []


@pytest.mark.parametrize(
    "hook_id", ["plugin-manifest-contract", "skills-distribution-contract"]
)
def test_precommit_covers_every_distribution_change_including_deletions(hook_id):
    config = yaml.safe_load((ROOT / ".pre-commit-config.yaml").read_text())
    hook = next(
        h for repo in config["repos"] for h in repo["hooks"] if h["id"] == hook_id
    )
    assert hook.get("always_run") is True, (
        "deleted paths are absent from pre-commit's file list"
    )
    assert hook["entry"].startswith("uv run "), "YAML dependency must use locked Python"
    for path in [
        "skills/alpha/SKILL.md",
        "skills/alpha/scripts/run.py",
        "plugins/triage/skills/detectors/a/references/a.md",
        "plugins/test/hooks/hooks.json",
        "SKILL-AUTHORSHIP.md",
        ".agents/skills/beads/SKILL.md",
        "package-lock.json",
        "scripts/tests/test_skills_install_matrix.py",
    ]:
        assert re.search(hook["files"], path), path


@pytest.mark.parametrize(
    "relative",
    [
        "README.md",
        "QUICK-START.md",
        "PUBLISHING.md",
        "docs/skills-cli.md",
        "docs/setup-architecture.md",
    ],
)
def test_plugin_docs_distinguish_marketplace_registration_from_install(relative):
    text = (ROOT / relative).read_text()
    assert "/plugin marketplace add citadelgrad/scott-cc" in text
    assert "/plugin install scott-cc@scott-cc" in text
    assert "/plugin install citadelgrad/" not in text
    assert "/plugin install /path/" not in text
    assert "/plugin marketplace add citadelgrad/scott-cc/<name>" not in text


def test_marketplace_core_count_matches_distributed_packages():
    import json

    marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    core = next(p for p in marketplace["plugins"] if p["name"] == "scott-cc")
    count = len(list((ROOT / "skills").glob("*/SKILL.md")))
    assert f"{count} skills" in core["description"]
