"""Tests for hooks/skill_xref_check.py.

Covers the pure function (`find_broken_references`) against synthetic
skill-directory fixtures, plus black-box subprocess tests of the CLI
wrapper for exit-code and output-shape guarantees (source file + missing
target both named in output).
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HOOK_PATH = Path(__file__).resolve().parents[1] / "skill_xref_check.py"

_spec = importlib.util.spec_from_file_location("skill_xref_check", HOOK_PATH)
assert _spec is not None and _spec.loader is not None
skill_xref_check = importlib.util.module_from_spec(_spec)
sys.modules["skill_xref_check"] = skill_xref_check  # dataclass needs module registered
_spec.loader.exec_module(skill_xref_check)

find_broken_references = skill_xref_check.find_broken_references


def make_skill(skills_root: Path, name: str, description_line: str) -> None:
    skill_dir = skills_root / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\n---\n\ndescription: {description_line}\n"
    )


def run_cli(skills_root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HOOK_PATH), str(skills_root)],
        capture_output=True,
        text=True,
    )


# --- pure function: find_broken_references ---------------------------------


def test_all_cross_references_resolve_returns_empty(tmp_path):
    skills_root = tmp_path / "skills"
    make_skill(
        skills_root,
        "red-flags",
        "Scans for smells. Not for depth (use deep-modules).",
    )
    make_skill(
        skills_root,
        "deep-modules",
        "Measures depth. Not for smells (use red-flags).",
    )

    assert find_broken_references(skills_root) == []


def test_reference_to_renamed_skill_is_reported(tmp_path):
    skills_root = tmp_path / "skills"
    make_skill(
        skills_root,
        "red-flags",
        "Scans for smells. Not for depth (use deep-modules-renamed).",
    )
    make_skill(skills_root, "deep-modules", "Measures depth.")

    broken = find_broken_references(skills_root)

    assert len(broken) == 1
    ref = broken[0]
    assert ref.target == "deep-modules-renamed"
    assert ref.source_file == skills_root / "red-flags" / "SKILL.md"


def test_reference_to_removed_skill_directory_is_reported(tmp_path):
    skills_root = tmp_path / "skills"
    make_skill(
        skills_root,
        "adversarial-reviewer",
        "Red-teams code. Not for design (use design-it-twice).",
    )
    # design-it-twice directory intentionally not created (simulates removal).

    broken = find_broken_references(skills_root)

    assert len(broken) == 1
    assert broken[0].target == "design-it-twice"


def test_multi_target_use_group_checks_each_name(tmp_path):
    skills_root = tmp_path / "skills"
    make_skill(
        skills_root,
        "adversarial-reviewer",
        "Not for constructive lenses (use design-review or red-flags).",
    )
    make_skill(skills_root, "design-review", "desc")
    # red-flags missing.

    broken = find_broken_references(skills_root)

    assert len(broken) == 1
    assert broken[0].target == "red-flags"


def test_backtick_wrapped_reference_is_parsed(tmp_path):
    skills_root = tmp_path / "skills"
    make_skill(
        skills_root,
        "data-steward",
        "Not for domain types (use `domain-modeling`).",
    )
    # domain-modeling missing.

    broken = find_broken_references(skills_root)

    assert len(broken) == 1
    assert broken[0].target == "domain-modeling"


def test_non_skill_shaped_use_phrase_is_ignored(tmp_path):
    skills_root = tmp_path / "skills"
    make_skill(
        skills_root,
        "review-panel",
        "Not for a single-lens check (use that skill directly).",
    )

    assert find_broken_references(skills_root) == []


def test_self_reference_is_not_flagged(tmp_path):
    skills_root = tmp_path / "skills"
    make_skill(
        skills_root,
        "solo-skill",
        "Not for something (use solo-skill).",
    )

    assert find_broken_references(skills_root) == []


def test_missing_skills_root_returns_empty(tmp_path):
    assert find_broken_references(tmp_path / "does-not-exist") == []


# --- CLI wrapper -------------------------------------------------------------


def test_cli_passes_with_exit_zero_when_all_references_resolve(tmp_path):
    skills_root = tmp_path / "skills"
    make_skill(
        skills_root,
        "red-flags",
        "Not for depth (use deep-modules).",
    )
    make_skill(skills_root, "deep-modules", "Not for smells (use red-flags).")

    result = run_cli(skills_root)

    assert result.returncode == 0
    assert "OK" in result.stdout


def test_cli_fails_with_source_file_and_missing_target_in_output(tmp_path):
    skills_root = tmp_path / "skills"
    make_skill(
        skills_root,
        "red-flags",
        "Not for depth (use deep-modules-renamed).",
    )

    result = run_cli(skills_root)

    assert result.returncode != 0
    assert "red-flags/SKILL.md" in result.stdout
    assert "deep-modules-renamed" in result.stdout


def test_cli_against_real_review_panel_skills_passes(tmp_path):
    real_skills_root = (
        Path(__file__).resolve().parents[2] / "plugins" / "review-panel" / "skills"
    )

    result = run_cli(real_skills_root)

    assert result.returncode == 0, result.stdout
