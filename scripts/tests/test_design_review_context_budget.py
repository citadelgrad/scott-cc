"""Mechanical context-budget tests for design-review."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL_PATH = "plugins/review-panel/skills/design-review/SKILL.md"
SKILL = ROOT / SKILL_PATH
WORKFLOW = SKILL.parent / "references/workflow-builder.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_scope_is_rejected_before_parent_content_loading() -> None:
    skill = read(SKILL)
    assert "20 files" in skill
    assert "1,200 changed lines" in skill
    assert "design-review-scope.json" in skill
    assert "before the parent reads target content" in skill.lower()
    assert skill.index("SCOPE_TOO_LARGE") < skill.index("## Diagnostic Funnel")


def test_fanout_findings_and_validation_are_finite() -> None:
    skill = read(SKILL)
    workflow = read(WORKFLOW)
    assert "4 target workers concurrently" in skill
    assert "4 targets per batch" in skill
    assert "3 batches / 12 target assignments" in skill
    assert "40 candidate findings" in skill
    assert "one challenger per retained candidate" in skill
    assert "40 total\n  validator assignments" in skill
    assert "2-3 independent agents per finding" not in workflow


def test_manifests_and_synthesis_are_bounded() -> None:
    combined = read(SKILL) + read(WORKFLOW)
    assert "2 KiB" in combined
    assert "4 KiB" in combined
    assert "12 finding IDs" in combined
    assert "final-summary.json" in combined
    assert "SHA-256" in combined


def test_large_scope_has_no_same_context_fallback() -> None:
    combined = read(SKILL) + read(WORKFLOW)
    assert "ISOLATION_UNAVAILABLE" in combined
    assert "no same-context large-scope fallback" in combined
    assert "fall back to running the funnel per file" not in combined
    assert "not resumable" in combined
