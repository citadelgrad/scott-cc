"""Mechanical context-budget tests for triage-spine."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL_PATH = "plugins/triage/skills/triage-spine/SKILL.md"
SKILL = ROOT / SKILL_PATH


def skill() -> str:
    return SKILL.read_text(encoding="utf-8")


def test_item_scope_bounds_are_all_explicit() -> None:
    value = skill()
    assert "10 triage items per run" in value
    assert "8 affected paths" in value
    assert "16 KiB of evidence" in value
    assert "ITEM_BUDGET_EXCEEDED" in value
    assert "before item dispatch or side effects" in value


def test_each_item_runs_in_one_fresh_process() -> None:
    value = skill()
    assert "one item per fresh process" in value
    assert "no concurrent item" in value
    assert "10 item processes" in value
    assert "TRIAGE_SPINE_FRESH_ITEM=1" in value
    assert 'claude -p "/triage-spine --item-artifact' in value


def test_replay_claims_and_side_effects_are_content_hash_bound() -> None:
    value = skill()
    assert "RFC 8785-style canonical item JSON" in value
    assert "atomically create the claim directory" in value
    assert "CONTENT_HASH_CONFLICT" in value
    assert "checkpoint each\n  external side effect" in value.lower()
    assert "reproduce.json" in value
    assert "PAS request/result artifact paths and SHA-256" in value


def test_terminal_json_is_validated_fail_closed() -> None:
    value = skill()
    assert "jq -er '.result | fromjson'" in value
    assert "unknown terminal status" in value
    assert "MALFORMED_TERMINAL_JSON" in value
    assert "never infer status with `jq -r`" in value
    assert "status=$(jq -r" not in value


def test_manifests_and_run_summary_are_bounded() -> None:
    value = skill()
    assert "manifests of at most **2 KiB**" in value
    assert "summary is at\n  most **4 KiB**" in value
    assert "at most **10 item IDs/statuses**" in value
    assert "After at most 10 fresh item processes" in value
