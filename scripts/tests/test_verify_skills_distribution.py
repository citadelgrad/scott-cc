"""Regression tests for the cross-agent skills distribution contract."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

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

    (tmp_path / "SKILL-AUTHORSHIP.md").write_text(
        "# Skill Authorship and Provenance\n\n"
        "Scott Nixon is the author or adaptation author. Original creators are retained in "
        "[credits](plugins/review-panel/CREDITS.md).\n\n"
        + "\n".join(f"- `skills/{name}/SKILL.md`" for name in skill_names)
        + "\n",
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


def test_authorship_inventory_must_cover_every_installable_skill(
    tmp_path: Path,
) -> None:
    write_repo(tmp_path)
    authorship = tmp_path / "SKILL-AUTHORSHIP.md"
    authorship.write_text(
        authorship.read_text(encoding="utf-8").replace(
            "- `skills/beta/SKILL.md`\n", ""
        ),
        encoding="utf-8",
    )

    errors = verify.validate(tmp_path)

    assert (
        "SKILL-AUTHORSHIP.md omits installable skills: skills/beta/SKILL.md" in errors
    )


def test_authorship_inventory_preserves_scott_and_upstream_credit(
    tmp_path: Path,
) -> None:
    write_repo(tmp_path)
    authorship = tmp_path / "SKILL-AUTHORSHIP.md"
    authorship.write_text(
        authorship.read_text(encoding="utf-8")
        .replace("Scott Nixon", "Anonymous")
        .replace("plugins/review-panel/CREDITS.md", "credits.md"),
        encoding="utf-8",
    )

    errors = verify.validate(tmp_path)

    assert "SKILL-AUTHORSHIP.md must credit Scott Nixon" in errors
    assert "SKILL-AUTHORSHIP.md must preserve the review-panel credits link" in errors


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


@pytest.mark.parametrize(
    "link",
    ["references/missing.md", "../outside.md", "%2e%2e/outside.md", "/absolute.md"],
)
def test_required_local_links_must_exist_inside_the_package(tmp_path, link):
    write_repo(tmp_path)
    entry = tmp_path / "skills/alpha/SKILL.md"
    (tmp_path / "skills/outside.md").write_text("outside the package")
    entry.write_text(entry.read_text() + f"\nRead [required]({link}).\n")
    assert any(
        "asset" in error or "link" in error for error in verify.validate(tmp_path)
    )


def test_source_symlink_cannot_be_silently_dereferenced_by_installer(tmp_path):
    write_repo(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("sensitive canary")
    (tmp_path / "skills/alpha/leak.txt").symlink_to(outside)
    assert any("symlink" in error for error in verify.validate(tmp_path))


def test_duplicate_install_names_require_equal_whole_payloads(tmp_path):
    write_repo(tmp_path)
    mirror = tmp_path / "plugins/example/skills/alpha"
    mirror.mkdir(parents=True)
    original = tmp_path / "skills/alpha"
    (mirror / "SKILL.md").write_bytes((original / "SKILL.md").read_bytes())
    (mirror / "reference.md").write_text("missing in portable package")
    assert any("duplicate install name" in error for error in verify.validate(tmp_path))
    (original / "reference.md").write_text("missing in portable package")
    assert not any(
        "duplicate install name" in error for error in verify.validate(tmp_path)
    )


@pytest.mark.parametrize("location", ["skills/alpha", "plugins/test/skills/deep/alpha"])
@pytest.mark.parametrize(
    "header,body",
    [
        ("name: alpha\ndescription: null", "Procedure"),
        ("name: alpha\ndescription: []", "Procedure"),
        ("name: alpha\ndescription: true", "Procedure"),
        ("name: alpha\ndescription: 42", "Procedure"),
        ("name: alpha\ndescription: {key: value}", "Procedure"),
        ("name: alpha\ndescription: [invalid", "Procedure"),
        ("name: alpha\ndescription: ok\ndescription: duplicate", "Procedure"),
        ("name: alpha\ndescription: '   '", "Procedure"),
        ("name: alpha\ndescription: " + "x" * 1025, "Procedure"),
        ("name: alpha\ndescription: ok\nmetadata:\n  a: 1\n  a: 2", "Procedure"),
        ("name: ../escape\ndescription: ok", "Procedure"),
        ("name: alpha\ndescription: ok", "  \n"),
    ],
)
def test_all_package_metadata_and_bodies_fail_closed(tmp_path, location, header, body):
    write_repo(tmp_path)
    skill = tmp_path / location / "SKILL.md"
    skill.parent.mkdir(parents=True, exist_ok=True)
    skill.write_text(f"---\n{header}\n---\n{body}\n")
    errors = verify.validate(tmp_path)
    assert any(
        location + "/SKILL.md" in error
        and "authorship" not in error
        and "SKILL-AUTHORSHIP" not in error
        for error in errors
    ), errors
