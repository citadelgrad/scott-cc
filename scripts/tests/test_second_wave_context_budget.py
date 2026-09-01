"""Mechanical context budgets for second-wave HARDEN skills."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILLS = {
    "plugins/browser-automation/skills/browser-use/SKILL.md": (
        "2 named sessions", "20 tabs total", "100 browser actions", "--max-steps 50",
        "15-minute", "3 retries", "2 KiB", "browser-checkpoint.json",
    ),
    "plugins/browser-automation/skills/browser-use-e2e/SKILL.md": (
        "50 agent steps", "15\n  minutes", "20 assertions", "2 browser tests",
        "2 retries", "2 KiB", "not resumable", "max_steps=50", "timeout=900",
    ),
    "plugins/review-panel/skills/ponytail-audit/SKILL.md": (
        "200 files / 30,000 lines", "20 files per batch", "4 batches concurrently",
        "10\n  batches / 200 file assignments", "2 KiB", "20 ranked findings / 4 KiB",
    ),
    "plugins/review-panel/skills/improve-codebase-architecture/SKILL.md": (
        "150 files / 25,000 lines", "15 files per batch", "3 batches concurrently",
        "10 batches / 150 file assignments", "30 candidate opportunities", "10 ranked candidates / 4",
    ),
    "plugins/triage/skills/detectors/prod-errors/SKILL.md": (
        "50 MiB or 100,000 lines", "24 hours", "10,000 lines per batch",
        "2 batches concurrently", "100 distinct error fingerprints", "20 triage-item summaries / 4 KiB",
    ),
    "plugins/review-panel/skills/grill-with-docs/SKILL.md": (
        "50 source/doc files or\n  10,000 lines", "10 human questions", "10 decision IDs",
        "2 KiB", "grill-with-docs-checkpoint.json", "fresh session",
    ),
    "plugins/review-panel/skills/grill-my-taste/SKILL.md": (
        "5–8 forced choices", "100 commits / 20 qualifying diffs", "8 human questions",
        "8 candidates", "2 KiB", "grill-my-taste-checkpoint.json", "fresh session",
    ),
    "plugins/review-panel/skills/grill-the-schema/SKILL.md": (
        "50\n  schema/source files or 10,000 lines", "10 human questions", "10 decision IDs",
        "2 KiB", "grill-the-schema-checkpoint.json", "fresh session",
    ),
}


def test_every_second_wave_skill_declares_each_exact_bound() -> None:
    for relative_path, markers in SKILLS.items():
        value = (ROOT / relative_path).read_text(encoding="utf-8")
        for marker in markers:
            assert marker in value, f"{relative_path} is missing {marker!r}"


def test_browser_media_and_history_are_artifact_backed() -> None:
    browser = (ROOT / next(iter(SKILLS))).read_text(encoding="utf-8")
    e2e = (ROOT / "plugins/browser-automation/skills/browser-use-e2e/SKILL.md").read_text(encoding="utf-8")
    assert "Never return inline base64 media" in browser
    assert "never inline media or full history" in e2e
    assert "Take screenshot (outputs base64)" not in browser


def test_repo_and_log_scans_fail_closed_instead_of_truncating() -> None:
    paths = (
        "plugins/review-panel/skills/ponytail-audit/SKILL.md",
        "plugins/review-panel/skills/improve-codebase-architecture/SKILL.md",
        "plugins/triage/skills/detectors/prod-errors/SKILL.md",
    )
    combined = "\n".join((ROOT / path).read_text(encoding="utf-8") for path in paths)
    assert combined.count("`SCOPE_TOO_LARGE`") == 2
    assert "LOG_SCOPE_TOO_LARGE" in combined
    assert "silently truncate" in combined
    assert "append" in combined and "JSONL" in combined


def test_conversational_workflows_are_hash_bound_and_question_limited() -> None:
    paths = tuple(path for path in SKILLS if "grill-" in path)
    for path in paths:
        value = (ROOT / path).read_text(encoding="utf-8")
        assert "SHA-256" in value
        assert "continuation manifest" in " ".join(value.lower().split())
        assert "Never continue" in value
