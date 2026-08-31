"""Context-budget contract tests for the review-panel orchestrator."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "plugins" / "review-panel"
SKILL = PANEL / "skills" / "review-panel" / "SKILL.md"
COMMAND = PANEL / "commands" / "review-panel.md"
REFS = PANEL / "skills" / "review-panel" / "references"


def read(path: Path) -> str:
    return path.read_text()


def normalized(path: Path) -> str:
    return re.sub(r"\s+", " ", read(path).replace("*", "")).lower()


def test_command_requires_just_in_time_reference_loading() -> None:
    command = normalized(COMMAND)

    assert "one at a time, just-in-time" in command
    assert "never preload all references" in command


def test_setup_rejects_oversized_monolithic_targets_before_cast() -> None:
    skill = read(SKILL)
    normalized_skill = normalized(SKILL)

    assert "scope_too_large" in skill
    assert "25 files" in skill
    assert "1,500 changed lines" in skill
    assert "for every tier source" in normalized_skill
    assert skill.index("scope_too_large") < skill.index("## The 7-stage loop")


def test_one_invocation_cannot_chain_review_targets() -> None:
    skill = read(SKILL)
    command = read(COMMAND)

    assert "exactly one review target" in skill
    assert "Never chain a second panel" in skill
    assert "Terminal-state hard stop" in command
    assert "make no more tool calls" in command


def test_every_bulky_stage_uses_artifacts_and_bounded_manifests() -> None:
    skill = read(SKILL)
    cast_spawn = read(REFS / "cast-and-spawn.md")
    merge_validate = read(REFS / "merge-and-validate.md")
    fix_rereview = read(REFS / "fix-and-rereview.md")

    assert "Artifact-only parent contract" in skill
    assert "2 KiB" in skill
    for stage in ("CAST", "SPAWN", "MERGE", "VALIDATE", "FIX", "RE-REVIEW"):
        assert stage in skill
    assert "seat-artifacts" in cast_spawn
    assert "merged-findings.json" in merge_validate
    assert "validated-findings.json" in merge_validate
    assert "fix-report.json" in fix_rereview
    assert "rereview-report.json" in fix_rereview
    assert "artifact_packaging_unavailable" in skill
    assert "subagents_unavailable" in cast_spawn


def test_supplementary_seats_and_validator_dispatches_are_finitely_bounded() -> None:
    cast_spawn = normalized(REFS / "cast-and-spawn.md")
    merge_validate = normalized(REFS / "merge-and-validate.md")

    assert "at most 2 supplementary seats" in cast_spawn
    assert "at most 8 total seats" in cast_spawn
    assert "at most 5 findings" in merge_validate
    assert "at most 5 concurrent validator subagents" in merge_validate
    assert "$workspace/agent-types.json" in cast_spawn
    assert "at most 12 entries" in cast_spawn
    assert "agent_type_scan_truncated" in cast_spawn


def test_dirty_full_round_checkpoints_and_stops_for_fresh_context_resume() -> None:
    command = read(COMMAND)
    converge = normalized(REFS / "converge-and-pipeline.md")
    dual_mode = read(REFS / "dual-mode-contract.md")

    assert "--resume" in command
    assert "every dirty round that is allowed to continue" in converge
    assert "medium round 1" in converge
    assert "status `checkpointed`" in converge
    assert "must not dispatch the next spawn" in converge
    assert "fresh claude code orchestration context" in converge
    assert "checkpointed" in dual_mode


def test_scope_preflight_uses_a_bounded_artifact_not_per_file_parent_output() -> None:
    skill = normalized(SKILL)

    assert "$workspace/scope.json" in skill
    assert "scope resolver" in skill
    assert "never captures per-file" in skill


def test_validation_has_a_hard_total_bound_and_one_parent_manifest() -> None:
    merge_validate = normalized(REFS / "merge-and-validate.md")

    assert "at most 25 total validator assignments" in merge_validate
    assert "critical multiplier" in merge_validate
    assert "at most 5 total validator batches" in merge_validate
    assert "one bounded validate manifest" in merge_validate
    assert "finding_scope_too_large" in merge_validate


def test_checkpoints_are_bounded_and_reference_sovereignty_artifacts() -> None:
    converge = normalized(REFS / "converge-and-pipeline.md")

    assert "checkpoint itself is at most 2 kib" in converge
    assert "sovereignty_artifact_path" in converge
    assert "never embeds findings" in converge


def test_final_synthesis_does_not_reload_detailed_artifacts_into_parent() -> None:
    dual_mode = normalized(REFS / "dual-mode-contract.md")

    assert "final synthesis worker" in dual_mode
    assert "final-summary.json" in dual_mode
    assert "at most 4 kib" in dual_mode
    assert "parent never reads the detailed report artifact" in dual_mode


def test_merge_pipeline_operates_on_artifact_paths_only() -> None:
    converge = normalized(REFS / "converge-and-pipeline.md")

    assert "artifact-path barrier" in converge
    assert "parent never fingerprints" in converge


def test_resume_fails_closed_without_a_fresh_process_marker() -> None:
    command = normalized(COMMAND)
    skill = normalized(SKILL)
    dual_mode = normalized(REFS / "dual-mode-contract.md")

    assert "review_panel_fresh_resume=1" in command
    assert "fresh_context_unverifiable" in command
    assert "origin_session_id" in command
    assert "review_panel_session_id" in command
    assert "claude -p" in command
    assert "--checkpoint-sha256 hex" in command
    assert "checkpoint_hash_mismatch" in command
    assert "--checkpoint-sha256 <sha256>" in command
    assert "--checkpoint-sha256 <sha256>" in dual_mode
    assert "review_panel_fresh_resume=1" in skill
    assert "fresh_context_unverifiable" in skill
    assert "checkpoint_already_consumed" in command
    assert "scripts/checkpoint-claim" in skill


def test_checkpoint_references_cast_artifact_and_capped_status_stays_blocking() -> None:
    converge = normalized(REFS / "converge-and-pipeline.md")
    dual_mode = normalized(REFS / "dual-mode-contract.md")

    assert "cast_artifact_path" in converge
    assert "never embed the cast list" in converge
    assert "top-level status is `capped`" in converge
    assert "combined sovereignty-plus-cap case, `status` is `capped`" in dual_mode
    assert "checkpoint_id" in converge
    assert "progress_artifact_path" in converge
    assert "last-three-round history" in converge


def test_skipped_fixes_remain_unresolved_and_foundry_fails_closed() -> None:
    fix_rereview = normalized(REFS / "fix-and-rereview.md")
    converge = normalized(REFS / "converge-and-pipeline.md")
    dual_mode = normalized(REFS / "dual-mode-contract.md")

    assert "fix.applied=false" in fix_rereview
    assert "unresolved_skipped_count == 0" in converge
    assert "unknown status" in dual_mode
    assert "jq -er" in dual_mode
    assert '"finding_counts"' in dual_mode
    assert ".finding_counts.unresolved == 0" in dual_mode
    assert ".convergence.final_round_clean == true" in dual_mode
    assert ".checkpoint.resume_prompt" in dual_mode


def test_merge_and_sovereignty_checks_stay_out_of_parent_context() -> None:
    merge_validate = normalized(REFS / "merge-and-validate.md")
    fix_rereview = normalized(REFS / "fix-and-rereview.md")

    assert "merge worker performs these per-finding reads" in merge_validate
    assert "never performs quote verification itself" in merge_validate
    assert "sovereignty guard worker" in fix_rereview
    assert "$workspace/sovereignty-guard.json" in fix_rereview
    assert "bounded pass/fail manifest" in fix_rereview


def test_terminal_human_output_cannot_restart_or_expand_in_parent() -> None:
    command = normalized(COMMAND)
    dual_mode = normalized(REFS / "dual-mode-contract.md")

    assert "never offer or run an additional in-conversation round" in dual_mode
    assert "at most five finding ids" in dual_mode
    assert "complete sign-off list" in dual_mode
    assert "fresh process, never continued in this parent conversation" in command
