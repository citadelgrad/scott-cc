"""Mechanical context-budget tests for explore-variants."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL_PATH = "plugins/variant-explorer/skills/explore-variants/SKILL.md"
SKILL = ROOT / SKILL_PATH


def skill() -> str:
    return SKILL.read_text(encoding="utf-8")


def test_input_and_builder_caps_are_preserved() -> None:
    value = skill()
    assert "64 KiB each" in value
    assert "clamp N>6 to **6**" in value
    assert "5 builders concurrently" in value
    assert "6 builder assignments" in value
    assert "refuse N=1" in value


def test_judge_and_scorecard_caps_are_finite() -> None:
    value = skill()
    assert "3 judges concurrently / 3 judge assignments" in value
    assert "scores at most\n  **6 variants**" in value
    assert "at most **6 scorecards**" in value
    assert "scorecard summary is at most **1 KiB**" in value
    assert "shortlist is at most **6 KiB**" in value


def test_builder_and_judge_detail_is_artifact_only() -> None:
    value = skill()
    assert "run-manifest.json" in value
    assert "manifest of at most **2\n  KiB**" in value
    assert "not inline content" in value
    assert "artifact path and hash" in value
    assert "SHA-256" in value


def test_malformed_judges_fail_closed() -> None:
    value = skill()
    assert "JUDGE_MALFORMED" in value
    assert "contributes no score" in value
    assert "zero valid judge output" in value
    assert "stop before ranking" in value


def test_human_boundary_has_hash_bound_checkpoint() -> None:
    value = skill()
    assert "decision-checkpoint.json" in value
    assert "Atomically claim its SHA-256" in value
    assert "No worktree cleanup occurs before the checkpoint" in value
    assert "cleanup_state: pending" in value
    assert "reject hash mismatch" in value
