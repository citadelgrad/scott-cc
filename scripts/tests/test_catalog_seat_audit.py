"""Tests for scripts/catalog_seat_audit.py.

Uses small synthetic tmp_path fixtures for isolated unit tests of each
parsing/audit rule, plus one test that runs against the real, checked-in
plugins/review-panel catalog/skills/design-review files and asserts the
mandated boundary condition (the catalog is clean — Epic B, scc-6lj.5,
closed the previously known adr-skill/grill-my-taste/grill-the-schema
gaps, so a regression here means a real skill went undocumented again).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "catalog_seat_audit.py"
REPO_ROOT = SCRIPT_PATH.resolve().parents[1]

spec = importlib.util.spec_from_file_location("catalog_seat_audit", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
catalog_seat_audit = importlib.util.module_from_spec(spec)
sys.modules["catalog_seat_audit"] = catalog_seat_audit
spec.loader.exec_module(catalog_seat_audit)


def make_skill_dir(skills_dir: Path, name: str) -> None:
    skill_dir = skills_dir / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(f"# {name}\n")


CATALOG_TEMPLATE = """# Reviewer Persona Catalog

## Excluded from Individual Casting (left to `design-review` funnel or live-scan)

{excluded_bullets}

If any of these are separately installed, live-scan may still surface them.

---

## Seat Summary Table

| Seat | Casts | Cast-when | Model tier |
|---|---|---|---|
{seat_rows}

**Fail-closed reminder:** ambiguity resolves to casting.
"""


def make_catalog(*, seat_rows: str, excluded_bullets: str) -> str:
    return CATALOG_TEMPLATE.format(
        seat_rows=seat_rows, excluded_bullets=excluded_bullets
    )


DESIGN_REVIEW_TEMPLATE = """---
name: design-review
---

# Design Review Orchestrator

Apply **{lenses}** in sequence.
"""


def make_design_review(lens_names: list[str]) -> str:
    return DESIGN_REVIEW_TEMPLATE.format(lenses="**, **".join(lens_names))


def test_correctly_catalogued_skill_produces_no_finding(tmp_path):
    skills_dir = tmp_path / "skills"
    make_skill_dir(skills_dir, "tdd")
    catalog_text = make_catalog(
        seat_rows="| Test-Design | `tdd` | Diff adds tests | Mid-tier |",
        excluded_bullets="",
    )
    design_review_text = make_design_review([])

    report = catalog_seat_audit.audit(catalog_text, skills_dir, design_review_text)

    assert report.findings == []
    assert report.clean is True


def test_correctly_excluded_skill_produces_no_finding(tmp_path):
    skills_dir = tmp_path / "skills"
    make_skill_dir(skills_dir, "diagnose")
    catalog_text = make_catalog(
        seat_rows="",
        excluded_bullets="- **`diagnose`** — a symptom-routing decision tree, not seat-shaped.",
    )
    design_review_text = make_design_review([])

    report = catalog_seat_audit.audit(catalog_text, skills_dir, design_review_text)

    assert report.findings == []


def test_uncatalogued_and_unexcluded_skill_produces_undocumented_finding(tmp_path):
    skills_dir = tmp_path / "skills"
    make_skill_dir(skills_dir, "adr-skill")
    catalog_text = make_catalog(seat_rows="", excluded_bullets="")
    design_review_text = make_design_review([])

    report = catalog_seat_audit.audit(catalog_text, skills_dir, design_review_text)

    assert len(report.findings) == 1
    finding = report.findings[0]
    assert finding.kind == "undocumented"
    assert finding.subject == "adr-skill"


def test_catalogued_seat_with_missing_directory_produces_missing_target(tmp_path):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    catalog_text = make_catalog(
        seat_rows="| Test-Design | `tdd` | Diff adds tests | Mid-tier |",
        excluded_bullets="",
    )
    design_review_text = make_design_review([])

    report = catalog_seat_audit.audit(catalog_text, skills_dir, design_review_text)

    assert len(report.findings) == 1
    finding = report.findings[0]
    assert finding.kind == "missing_target"
    assert finding.subject == "tdd"


def test_catalogued_seat_targeting_agents_md_file_produces_no_missing_target(tmp_path):
    plugin_dir = tmp_path / "review-panel"
    skills_dir = plugin_dir / "skills"
    skills_dir.mkdir(parents=True)
    agents_dir = plugin_dir / "agents"
    agents_dir.mkdir()
    (agents_dir / "clean-room-alternative.md").write_text("# clean room\n")

    catalog_text = make_catalog(
        seat_rows="| Fresh-Eyes | `clean-room-alternative` | Always | Top-tier |",
        excluded_bullets="",
    )
    design_review_text = make_design_review([])

    report = catalog_seat_audit.audit(catalog_text, skills_dir, design_review_text)

    assert report.findings == []


def test_plugin_own_orchestrator_dir_produces_no_undocumented_finding(tmp_path):
    plugin_dir = tmp_path / "review-panel"
    skills_dir = plugin_dir / "skills"
    skills_dir.mkdir(parents=True)
    make_skill_dir(skills_dir, "review-panel")
    catalog_text = make_catalog(seat_rows="", excluded_bullets="")
    design_review_text = make_design_review([])

    report = catalog_seat_audit.audit(catalog_text, skills_dir, design_review_text)

    assert report.findings == []


def test_lens_added_to_design_review_but_not_claimed_produces_lens_drift_added(
    tmp_path,
):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    catalog_text = make_catalog(
        seat_rows="",
        excluded_bullets=(
            "- **`module-boundaries`** — subsumed by design-review's funnel, not a "
            "standalone seat."
        ),
    )
    design_review_text = make_design_review(["module-boundaries", "deep-modules"])

    report = catalog_seat_audit.audit(catalog_text, skills_dir, design_review_text)

    assert len(report.findings) == 1
    finding = report.findings[0]
    assert finding.kind == "lens_drift_added"
    assert finding.subject == "deep-modules"


def test_lens_claimed_but_removed_from_design_review_produces_lens_drift_removed(
    tmp_path,
):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    catalog_text = make_catalog(
        seat_rows="",
        excluded_bullets=(
            "- **`module-boundaries`, `deep-modules`** — subsumed by design-review's "
            "funnel, not a standalone seat."
        ),
    )
    design_review_text = make_design_review(["module-boundaries"])

    report = catalog_seat_audit.audit(catalog_text, skills_dir, design_review_text)

    assert len(report.findings) == 1
    finding = report.findings[0]
    assert finding.kind == "lens_drift_removed"
    assert finding.subject == "deep-modules"


def test_fully_consistent_fixture_produces_zero_findings_and_exit_0(tmp_path):
    skills_dir = tmp_path / "skills"
    make_skill_dir(skills_dir, "tdd")
    make_skill_dir(skills_dir, "diagnose")
    catalog_text = make_catalog(
        seat_rows="| Test-Design | `tdd` | Diff adds tests | Mid-tier |",
        excluded_bullets=(
            "- **`module-boundaries`** — subsumed by design-review's funnel, not a "
            "standalone seat.\n"
            "- **`diagnose`** — a symptom-routing decision tree, not seat-shaped."
        ),
    )
    design_review_text = make_design_review(["module-boundaries"])

    report = catalog_seat_audit.audit(catalog_text, skills_dir, design_review_text)

    assert report.findings == []
    assert report.clean is True

    out_path = tmp_path / "report.md"
    out_path.write_text(catalog_seat_audit.render_report(report))
    rendered = out_path.read_text()
    assert "Status: CLEAN" in rendered


def test_real_repo_files_produce_zero_findings():
    catalog_text = (REPO_ROOT / catalog_seat_audit.DEFAULT_CATALOG).read_text()
    skills_dir = REPO_ROOT / catalog_seat_audit.DEFAULT_SKILLS_DIR
    design_review_text = (
        REPO_ROOT / catalog_seat_audit.DEFAULT_DESIGN_REVIEW
    ).read_text()

    report = catalog_seat_audit.audit(catalog_text, skills_dir, design_review_text)

    assert report.findings == []
    assert report.clean is True


def test_real_repo_main_exits_0_and_never_modifies_source_files(tmp_path):
    catalog_path = REPO_ROOT / catalog_seat_audit.DEFAULT_CATALOG
    skills_dir = REPO_ROOT / catalog_seat_audit.DEFAULT_SKILLS_DIR
    design_review_path = REPO_ROOT / catalog_seat_audit.DEFAULT_DESIGN_REVIEW

    catalog_before = catalog_path.read_text()
    design_review_before = design_review_path.read_text()
    skill_dir_names_before = sorted(p.name for p in skills_dir.iterdir())

    out_path = tmp_path / "report.md"
    exit_code = catalog_seat_audit.main(
        [
            "--catalog",
            str(catalog_path),
            "--skills-dir",
            str(skills_dir),
            "--design-review",
            str(design_review_path),
            "--out",
            str(out_path),
        ]
    )

    assert exit_code == 0
    assert catalog_path.read_text() == catalog_before
    assert design_review_path.read_text() == design_review_before
    assert sorted(p.name for p in skills_dir.iterdir()) == skill_dir_names_before


def test_missing_catalog_path_exits_nonzero_with_readable_message(tmp_path, capsys):
    out_path = tmp_path / "report.md"

    with pytest.raises(SystemExit) as exc_info:
        catalog_seat_audit.main(
            [
                "--catalog",
                str(tmp_path / "does-not-exist.md"),
                "--skills-dir",
                str(tmp_path),
                "--design-review",
                str(tmp_path / "does-not-exist-2.md"),
                "--out",
                str(out_path),
            ]
        )

    assert exc_info.value.code == 1
    out = capsys.readouterr().out
    assert "FAIL:" in out
    assert "does-not-exist.md" in out


def test_report_json_block_matches_findings_exactly(tmp_path):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    catalog_text = make_catalog(
        seat_rows="| Test-Design | `tdd` | Diff adds tests | Mid-tier |",
        excluded_bullets="",
    )
    design_review_text = make_design_review([])

    report = catalog_seat_audit.audit(catalog_text, skills_dir, design_review_text)
    rendered = catalog_seat_audit.render_report(report)

    json_block = rendered.split("```json\n", 1)[1].rsplit("```", 1)[0]
    payload = json.loads(json_block)

    assert payload == {
        "findings": [
            {"kind": f.kind, "subject": f.subject, "detail": f.detail}
            for f in report.findings
        ]
    }
    assert payload["findings"][0]["kind"] == "missing_target"
    assert payload["findings"][0]["subject"] == "tdd"
