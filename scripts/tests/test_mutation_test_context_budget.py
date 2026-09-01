"""Mechanical context-budget tests for the mutation-test orchestrator."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL_PATH = "plugins/mutation-testing/skills/mutation-test/SKILL.md"
SKILL = ROOT / SKILL_PATH
AGENT = ROOT / "plugins/mutation-testing/agents/test-quality-reviewer.md"
COMMAND = ROOT / "plugins/mutation-testing/commands/mutation-test.md"


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_target_and_mutation_ceiling_are_finite() -> None:
    skill = text(SKILL)
    assert "one source file" in skill
    assert "2,000 lines" in skill
    assert "5**, **15**, and **30" in skill
    assert "30 mutations is the absolute run ceiling" in skill
    assert "30+ mutations" not in skill


def test_batch_and_concurrency_bounds_are_mechanical() -> None:
    skill = text(SKILL)
    agent = text(AGENT)
    assert "5 mutations per batch" in skill
    assert "5 executor agents" in skill
    assert "6 batches / 30 total executor assignments" in skill
    assert "at most five Task calls" in agent


def test_stage_handoffs_and_final_summary_are_bounded_artifacts() -> None:
    skill = text(SKILL)
    agent = text(AGENT)
    command = text(COMMAND)
    assert "manifest of at most\n  **2 KiB**" in skill
    assert "at most **4 KiB** and **10 finding IDs**" in skill
    assert "artifact_path" in agent and "artifact_sha256" in agent
    assert "do not inline them" in agent
    assert "Never inline the detailed" in command


def test_isolation_fails_closed() -> None:
    combined = text(SKILL) + text(AGENT)
    assert "ISOLATION_UNAVAILABLE" in combined
    assert "ARTIFACT_CONTRACT_FAILED" in combined
    assert "never fall back to sequential" in combined.lower()
    assert "fallback to sequential mutations" not in combined


def test_batch_continuation_is_hash_bound_and_fresh() -> None:
    combined = text(SKILL) + text(AGENT)
    assert "checkpoint.json" in combined
    assert "MUTATION_TEST_FRESH_RESUME=1" in combined
    assert "claude -p" in combined
    assert "expected checkpoint SHA-256" in combined
    assert "atomically claim" in combined
    assert "reject mismatches or replay" in combined
