"""Regression tests for the cross-agent skills distribution contract."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "verify_skills_distribution.py"
spec = importlib.util.spec_from_file_location("verify_skills_distribution", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
verify = importlib.util.module_from_spec(spec)
sys.modules["verify_skills_distribution"] = verify
spec.loader.exec_module(verify)


def write_repo(tmp_path: Path, *, grouped_skills: list[str] | None = None) -> None:
    skill_names = ["alpha", "beta"]
    for skill_name in skill_names:
        skill_path = tmp_path / "skills" / skill_name / "SKILL.md"
        skill_path.parent.mkdir(parents=True)
        skill_path.write_text(
            f"---\nname: {skill_name}\ndescription: Use when testing {skill_name}.\n---\n\n# {skill_name}\n",
            encoding="utf-8",
        )

    manifest = {
        "$schema": verify.EXPECTED_SCHEMA,
        "notGrouped": "bottom",
        "groupings": [
            {
                "title": "Test",
                "description": "Test skills.",
                "skills": grouped_skills if grouped_skills is not None else skill_names,
            }
        ],
    }
    (tmp_path / "skills.sh.json").write_text(json.dumps(manifest), encoding="utf-8")

    for relative_path in ("README.md", "QUICK-START.md", "docs/skills-cli.md"):
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "npx skills add citadelgrad/scott-cc\n--agent codex --agent hermes-agent\n",
            encoding="utf-8",
        )


def test_valid_distribution_contract_passes(tmp_path: Path) -> None:
    write_repo(tmp_path)

    assert verify.validate(tmp_path) == []


def test_duplicate_and_unknown_grouped_skills_fail(tmp_path: Path) -> None:
    write_repo(tmp_path, grouped_skills=["alpha", "alpha", "missing"])

    errors = verify.validate(tmp_path)

    assert "skills.sh.json groups duplicate skills: alpha" in errors
    assert "skills.sh.json groups unknown root skills: missing" in errors
    assert "skills.sh.json leaves root skills ungrouped: beta" in errors


def test_skill_name_must_match_directory(tmp_path: Path) -> None:
    write_repo(tmp_path)
    (tmp_path / "skills" / "alpha" / "SKILL.md").write_text(
        "---\nname: wrong\ndescription: Use when testing.\n---\n\n# Wrong\n",
        encoding="utf-8",
    )

    assert "skills/alpha/SKILL.md name must be 'alpha'" in verify.validate(tmp_path)


def test_empty_folded_description_fails(tmp_path: Path) -> None:
    write_repo(tmp_path)
    (tmp_path / "skills" / "alpha" / "SKILL.md").write_text(
        "---\nname: alpha\ndescription: >-\n---\n\n# Alpha\n",
        encoding="utf-8",
    )

    assert "skills/alpha/SKILL.md is missing a description" in verify.validate(tmp_path)


def test_installation_docs_are_required(tmp_path: Path) -> None:
    write_repo(tmp_path)
    (tmp_path / "README.md").write_text("Claude plugin only\n", encoding="utf-8")

    errors = verify.validate(tmp_path)

    assert any(error.startswith("README.md is missing:") for error in errors)


def test_portable_adversarial_reviewer_must_match_plugin_source(tmp_path: Path) -> None:
    write_repo(tmp_path)
    plugin_skill = (
        tmp_path / "plugins/review-panel/skills/adversarial-reviewer" / "SKILL.md"
    )
    plugin_skill.parent.mkdir(parents=True)
    plugin_skill.write_text("canonical\n", encoding="utf-8")
    portable_skill = tmp_path / "skills/adversarial-reviewer/SKILL.md"
    portable_skill.parent.mkdir(parents=True)
    portable_skill.write_text("drifted\n", encoding="utf-8")

    errors = verify.validate(tmp_path)

    assert any("portable adversarial-reviewer drift" in error for error in errors)
