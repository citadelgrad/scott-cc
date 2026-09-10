"""Tests for the real Hermes skill-discovery harness."""

from __future__ import annotations

import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
from types import SimpleNamespace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills/beads/scripts/hermes_discovery_harness.py"
DESIGN = (
    ROOT / "docs/plans/2026-09-02-hermes-beads-skill/benchmark-corpus-design-v1.json"
)
DESIGN_V2 = (
    ROOT / "docs/plans/2026-09-02-hermes-beads-skill/discovery-benchmark-design-v2.json"
)
SKILL = ROOT / "skills/beads"


def load_harness():
    spec = importlib.util.spec_from_file_location("beads_hermes_discovery", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def harness():
    return load_harness()


def _full_fixture(tmp_path: Path, harness) -> Path:
    design = json.loads(DESIGN.read_text(encoding="utf-8"))
    scenarios = [
        {
            "scenario_id": row[0],
            "split": row[1],
            "polarity": row[2],
            "prompt": f"private fixture prompt for {row[0]}",
        }
        for row in design["scenarios"]
    ]
    payload = {
        "schema_version": harness.CORPUS_ENVELOPE_SCHEMA,
        "design_sha256": harness.FROZEN_DESIGN_SHA256,
        "split_hashes": harness.FROZEN_SPLIT_HASHES,
        "scenarios": scenarios,
    }
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return path


def _v2_fixture(tmp_path: Path, harness):
    design = json.loads(DESIGN_V2.read_text(encoding="utf-8"))
    rows = [
        {
            "variant_id": variant["variant_id"],
            "split": variant["split"],
            "prompt": f"private v2 fixture prompt for {variant['variant_id']}",
        }
        for variant in design["variants"]
    ]
    split_hashes = harness.corpus_split_hashes(rows)
    design["status"] = "frozen"
    design["corpus_freeze"]["split_hashes"] = split_hashes
    design["corpus_freeze"]["custodian_attestation"] = {
        "role": "benchmark-custodian",
        "custodian_identifier": "test-independent-custodian",
        "candidate_author_disclosed": False,
        "candidate_package_read": False,
        "frozen_at": "2026-09-08T00:00:00Z",
    }
    design_path = tmp_path / "design-v2.json"
    design_path.write_text(json.dumps(design, sort_keys=True), encoding="utf-8")
    design_sha256 = harness.sha256_file(design_path)
    corpus = {
        "schema_version": "hermes-beads-routing-prompts.v2",
        "design_sha256": design_sha256,
        "split_hashes": split_hashes,
        "scenarios": rows,
    }
    corpus_path = tmp_path / "corpus-v2.json"
    corpus_path.write_text(json.dumps(corpus, sort_keys=True), encoding="utf-8")
    return design_path, design_sha256, corpus_path, harness.sha256_file(corpus_path)


def test_v2_frozen_design_is_metadata_only_and_binds_current_candidate(harness) -> None:
    design = json.loads(DESIGN_V2.read_text(encoding="utf-8"))

    assert harness.sha256_file(DESIGN_V2) == (
        "e03bc9cfbc520ccb4ed36c8b99f6ae0bc3796ba27919ed5d7af04e4abc7ee9cb"
    )
    assert design["status"] == "frozen"
    assert design["frozen_runtime"]["candidate_sha256"] == harness.hash_tree(SKILL)
    assert design["frozen_runtime"]["harness_sha256"] == harness.sha256_file(SCRIPT)
    assert len(design["variants"]) == 45
    assert all("prompt" not in variant for variant in design["variants"])
    assert all(design["corpus_freeze"]["split_hashes"].values())
    assert design["corpus_freeze"]["custodian_attestation"] == {
        "role": "benchmark-custodian",
        "custodian_identifier": "independent-benchmark-custodian",
        "candidate_author_disclosed": False,
        "candidate_package_read": False,
        "frozen_at": "2026-09-08T19:12:39Z",
    }
    assert design["execution_matrix"] == {
        "repeats_per_variant": 3,
        "positive_observations": 75,
        "negative_observations": 60,
        "total_observations": 135,
        "repeat_rule": (
            "Each repeat is a fresh isolated Hermes session. Results are never "
            "pooled across model/provider/Hermes/harness strata."
        ),
    }


def test_v2_corpus_loader_expands_frozen_variants_into_repeats(
    tmp_path: Path, harness
) -> None:
    design, design_sha, corpus, corpus_sha = _v2_fixture(tmp_path, harness)

    scenarios = harness.load_corpus(corpus, design, corpus_sha, design_sha)

    assert len(scenarios) == 135
    assert sum(row.expected_load for row in scenarios) == 75
    assert sum(not row.expected_load for row in scenarios) == 60
    assert {row.repeat for row in scenarios} == {1, 2, 3}
    assert len({(row.scenario_id, row.repeat) for row in scenarios}) == 135
    assert all("private v2 fixture prompt" in row.prompt for row in scenarios)


def test_v2_corpus_loader_rejects_unfrozen_design_without_prompt_disclosure(
    tmp_path: Path, harness
) -> None:
    design = tmp_path / "design-v2.json"
    unfrozen_design = json.loads(DESIGN_V2.read_text(encoding="utf-8"))
    unfrozen_design["status"] = "awaiting_custodian_freeze"
    design.write_text(json.dumps(unfrozen_design, sort_keys=True), encoding="utf-8")
    corpus = tmp_path / "corpus-v2.json"
    corpus.write_text(
        json.dumps(
            {
                "schema_version": "hermes-beads-routing-prompts.v2",
                "design_sha256": harness.sha256_file(design),
                "split_hashes": {},
                "scenarios": [
                    {
                        "variant_id": "D001",
                        "split": "public",
                        "prompt": "private prompt must not appear in the error",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(harness.HarnessError, match="DESIGN_NOT_FROZEN") as error:
        harness.load_corpus(
            corpus,
            design,
            harness.sha256_file(corpus),
            harness.sha256_file(design),
        )
    assert "private prompt" not in str(error.value)


def test_v2_corpus_loader_rejects_incomplete_custodian_attestation(
    tmp_path: Path, harness
) -> None:
    design_path, _, corpus_path, _ = _v2_fixture(tmp_path, harness)
    design = json.loads(design_path.read_text(encoding="utf-8"))
    del design["corpus_freeze"]["custodian_attestation"]["candidate_package_read"]
    design_path.write_text(json.dumps(design, sort_keys=True), encoding="utf-8")
    changed_design_sha = harness.sha256_file(design_path)
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    corpus["design_sha256"] = changed_design_sha
    corpus_path.write_text(json.dumps(corpus, sort_keys=True), encoding="utf-8")

    with pytest.raises(harness.HarnessError, match="CUSTODIAN_ATTESTATION_INVALID"):
        harness.load_corpus(
            corpus_path,
            design_path,
            harness.sha256_file(corpus_path),
            changed_design_sha,
        )


def test_v2_corpus_loader_rejects_duplicate_prompt_variants_with_valid_hashes(
    tmp_path: Path, harness
) -> None:
    design_path, _design_sha, corpus_path, _corpus_sha = _v2_fixture(tmp_path, harness)
    design = json.loads(design_path.read_text(encoding="utf-8"))
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    rows = {row["variant_id"]: row for row in corpus["scenarios"]}
    rows["D002"]["prompt"] = rows["D001"]["prompt"]
    split_hashes = harness.corpus_split_hashes(corpus["scenarios"])
    design["corpus_freeze"]["split_hashes"] = split_hashes
    design_path.write_text(json.dumps(design, sort_keys=True), encoding="utf-8")
    design_sha = harness.sha256_file(design_path)
    corpus["design_sha256"] = design_sha
    corpus["split_hashes"] = split_hashes
    corpus_path.write_text(json.dumps(corpus, sort_keys=True), encoding="utf-8")

    with pytest.raises(harness.HarnessError, match="CORPUS_VARIANTS_NOT_DISTINCT"):
        harness.load_corpus(
            corpus_path,
            design_path,
            harness.sha256_file(corpus_path),
            design_sha,
        )


def test_v2_design_validation_uses_the_exact_hashed_snapshot(
    tmp_path: Path, harness, monkeypatch
) -> None:
    design_path, design_sha, corpus_path, corpus_sha = _v2_fixture(tmp_path, harness)
    replacement = json.loads(design_path.read_text(encoding="utf-8"))
    variants = {row["variant_id"]: row for row in replacement["variants"]}
    variants["D001"]["route_family"], variants["D016"]["route_family"] = (
        variants["D016"]["route_family"],
        variants["D001"]["route_family"],
    )
    replacement_text = json.dumps(replacement, sort_keys=True)
    real_sha256_file = harness.sha256_file
    replaced = False

    def replace_after_hash(path: Path) -> str:
        nonlocal replaced
        digest = real_sha256_file(path)
        if Path(path) == design_path and not replaced:
            design_path.write_text(replacement_text, encoding="utf-8")
            replaced = True
        return digest

    monkeypatch.setattr(harness, "sha256_file", replace_after_hash)

    scenarios = harness.load_corpus(corpus_path, design_path, corpus_sha, design_sha)

    d001 = next(row for row in scenarios if row.scenario_id == "D001")
    assert d001.route_family == "explicit"


def test_v2_plan_reports_exact_frozen_matrix_and_hashes(
    tmp_path: Path, harness
) -> None:
    design, design_sha, _corpus, corpus_sha = _v2_fixture(tmp_path, harness)

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "plan",
            "--design",
            str(design),
            "--design-sha256",
            design_sha,
            "--corpus-sha256",
            corpus_sha,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    request = json.loads(completed.stdout)
    assert request["hermes_sessions"] == 135
    assert request["maximum_provider_requests"] == 270
    assert request["design_sha256"] == design_sha
    assert request["corpus_sha256"] == corpus_sha
    assert request["candidate_sha256"] == (
        "836ff0c61774ec6cf5590f1181c37bf62f19d5700990e356a7264314d2c84fbe"
    )
    assert request["approval_digest"] == harness.run_approval_digest(
        candidate_sha256=request["candidate_sha256"],
        corpus_sha256=corpus_sha,
        design_sha256=design_sha,
        provider="openai-codex",
        model="gpt-5.6-sol",
        force_full_sweep=False,
    )


def test_v2_runtime_contract_rejects_candidate_or_model_drift(
    tmp_path: Path, harness
) -> None:
    design, design_sha, _corpus, _corpus_sha = _v2_fixture(tmp_path, harness)

    with pytest.raises(harness.HarnessError, match="FROZEN_CANDIDATE_MISMATCH"):
        harness.validate_v2_runtime_contract(
            design,
            design_sha,
            candidate_sha256="0" * 64,
            provider="openai-codex",
            model="gpt-5.6-sol",
        )
    with pytest.raises(harness.HarnessError, match="FROZEN_MODEL_STRATUM_MISMATCH"):
        harness.validate_v2_runtime_contract(
            design,
            design_sha,
            candidate_sha256=(
                "836ff0c61774ec6cf5590f1181c37bf62f19d5700990e356a7264314d2c84fbe"
            ),
            provider="openai-codex",
            model="different-model",
        )


def test_candidate_tree_hash_is_content_bound_and_install_is_exact(
    tmp_path: Path, harness
) -> None:
    expected = harness.hash_tree(SKILL)
    home = tmp_path / "isolated-home"
    installed = harness.install_candidate(SKILL, home, expected)
    assert installed == home / "skills" / "beads"
    assert harness.hash_tree(installed) == expected

    (installed / "SKILL.md").write_text("changed\n", encoding="utf-8")
    with pytest.raises(harness.HarnessError, match="CANDIDATE_HASH_MISMATCH"):
        harness.install_candidate(SKILL, tmp_path / "second-home", "0" * 64)


def test_corpus_loader_requires_all_frozen_scenarios_without_disclosure(
    tmp_path: Path, harness
) -> None:
    corpus = _full_fixture(tmp_path, harness)
    loaded = harness.load_corpus(corpus, DESIGN, harness.sha256_file(corpus))
    assert len(loaded) == 72
    assert loaded[0].scenario_id == "B001"

    payload = json.loads(corpus.read_text(encoding="utf-8"))
    payload["scenarios"].pop()
    corpus.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(harness.HarnessError, match="CORPUS_INDEX_MISMATCH") as error:
        harness.load_corpus(corpus, DESIGN, harness.sha256_file(corpus))
    assert "private fixture prompt" not in str(error.value)


def test_sanitized_report_contains_no_prompt_or_output_content(
    tmp_path: Path, harness
) -> None:
    corpus = _full_fixture(tmp_path, harness)
    scenarios = harness.load_corpus(corpus, DESIGN, harness.sha256_file(corpus))
    result = harness.ScenarioResult(
        scenario_id=scenarios[0].scenario_id,
        split=scenarios[0].split,
        expected_load=True,
        discovery_events=1,
        load_events=1,
        exit_code=0,
        stdout_sha256="a" * 64,
        stderr_sha256="b" * 64,
        state_sha256="c" * 64,
    )
    report = harness.build_report(
        [result],
        candidate_sha256="d" * 64,
        corpus_sha256=harness.sha256_file(corpus),
        hermes_commit=harness.FROZEN_HERMES_COMMIT,
        provider="openai-codex",
        model="gpt-5.6-sol",
        default_profile_unchanged=True,
    )
    rendered = json.dumps(report, sort_keys=True)
    assert "private fixture prompt" not in rendered
    assert set(report["results"][0]) == {
        "scenario_id",
        "split",
        "expected_load",
        "discovery_events",
        "load_events",
        "exit_code",
        "stdout_sha256",
        "stderr_sha256",
        "state_sha256",
        "route_family",
        "repeat",
        "prompt_disclosed",
        "raw_stdout_path",
        "raw_stderr_path",
        "profile_delta",
        "passed",
        "errored",
        "outcome",
    }
    assert report["raw_content_retained"] is False


def _statistical_results(harness, *, failed: set[tuple[str, int]] | None = None):
    failed = failed or set()
    families = {
        True: ("explicit", "implicit", "recovery", "planning", "swarm"),
        False: (
            "trivial_request",
            "alternative_tracker",
            "durable_executor_without_beads",
            "repository_context_without_tracker_work",
        ),
    }
    results = []
    for expected_load, route_families in families.items():
        prefix = "D" if expected_load else "N"
        for family_index, route_family in enumerate(route_families, start=1):
            for variant in range(1, 6):
                scenario_id = f"{prefix}{family_index}{variant}"
                for repeat in range(1, 4):
                    passed = (scenario_id, repeat) not in failed
                    observed_load = expected_load if passed else not expected_load
                    results.append(
                        harness.ScenarioResult(
                            scenario_id=scenario_id,
                            split=("public", "hidden", "sealed")[
                                (variant + repeat) % 3
                            ],
                            expected_load=expected_load,
                            discovery_events=int(observed_load),
                            load_events=int(observed_load),
                            exit_code=0,
                            stdout_sha256="a" * 64,
                            stderr_sha256="b" * 64,
                            state_sha256="c" * 64,
                            route_family=route_family,
                            repeat=repeat,
                        )
                    )
    return results


def _statistical_report(harness, results):
    expected_scenarios = [
        harness.Scenario(
            scenario_id=row.scenario_id,
            split=row.split,
            polarity="positive" if row.expected_load else "negative",
            prompt="synthetic prompt excluded from reports",
            expected_load=row.expected_load,
            route_family=row.route_family,
            repeat=row.repeat,
        )
        for row in _statistical_results(harness)
    ]
    return harness.build_report(
        results,
        candidate_sha256="d" * 64,
        corpus_sha256="e" * 64,
        design_sha256="f" * 64,
        hermes_commit=harness.FROZEN_HERMES_COMMIT,
        provider="openai-codex",
        model="gpt-5.6-sol",
        default_profile_unchanged=True,
        expected_scenarios=expected_scenarios,
    )


def test_prd_statistical_gate_passes_complete_perfect_matrix(harness) -> None:
    report = _statistical_report(harness, _statistical_results(harness))

    assert report["scenario_count"] == 135
    assert report["budget_sha256"] == harness.BUDGET_CONTRACT_SHA256
    assert report["prestate_contract_sha256"] == harness.PRESTATE_CONTRACT_SHA256
    assert report["routing_metrics"]["positive"]["observations"] == 75
    assert report["routing_metrics"]["negative_restraint"]["observations"] == 60
    assert report["routing_metrics"]["positive"]["macro_millionths"] == 1_000_000
    assert (
        report["routing_metrics"]["negative_restraint"]["macro_millionths"] == 1_000_000
    )
    assert report["gate"] == {"passed": True, "failures": []}


def test_prd_statistical_report_emits_reconcilable_split_counts(harness) -> None:
    results = _statistical_results(harness, failed={("D11", 1), ("N11", 1)})
    results[2] = harness.replace(results[2], exit_code=1)
    report = _statistical_report(harness, results)

    assert set(report["split_counts"]) == {"public", "hidden", "sealed"}
    assert sum(row["observations"] for row in report["split_counts"].values()) == 135
    assert (
        sum(row["passed"] for row in report["split_counts"].values())
        == report["passed"]
    )
    assert (
        sum(row["failed"] for row in report["split_counts"].values())
        == report["failed"]
    )
    assert (
        sum(row["errored"] for row in report["split_counts"].values())
        == report["errored"]
    )
    assert all(
        row["scored_count"] == row["passed"] + row["failed"]
        for row in report["split_counts"].values()
    )


def test_prd_statistical_gate_rejects_weak_family_despite_high_micro(harness) -> None:
    failures = {(f"D1{variant}", 1) for variant in range(1, 6)}
    results = _statistical_results(harness, failed=failures)
    for family_index in range(2, 6):
        template = next(
            row
            for row in results
            if row.expected_load and row.scenario_id == f"D{family_index}1"
        )
        results.extend(
            harness.replace(template, repeat=repeat) for repeat in range(4, 29)
        )
    report = _statistical_report(harness, results)

    assert report["passed"] == 230
    assert report["routing_metrics"]["positive"]["micro_millionths"] > 950_000
    assert report["routing_metrics"]["positive"]["macro_millionths"] < 950_000
    assert "POSITIVE_MACRO_BELOW_THRESHOLD" in report["gate"]["failures"]
    assert report["gate"]["passed"] is False


def test_prd_statistical_gate_accepts_exact_macro_threshold_without_flooring(
    harness,
) -> None:
    failures = {("N11", 1), ("N12", 1), ("N21", 1)}
    report = _statistical_report(
        harness, _statistical_results(harness, failed=failures)
    )

    restraint = report["routing_metrics"]["negative_restraint"]
    assert restraint["successes"] == 57
    assert restraint["macro_millionths"] == 950_000
    assert restraint["macro_fraction"] == {"numerator": 19, "denominator": 20}
    assert report["gate"] == {"passed": True, "failures": []}


@pytest.mark.parametrize(
    ("filter_result", "failure"),
    [
        (lambda row: row.expected_load, "NEGATIVE_OBSERVATIONS_INSUFFICIENT"),
        (
            lambda row: row.scenario_id != "N15",
            "NEGATIVE_VARIANTS_PER_FAMILY_INSUFFICIENT",
        ),
        (
            lambda row: not (row.scenario_id == "D11" and row.repeat == 3),
            "POSITIVE_REPEATS_PER_VARIANT_INSUFFICIENT",
        ),
    ],
)
def test_prd_statistical_gate_rejects_incomplete_matrix(
    harness, filter_result, failure
) -> None:
    results = [row for row in _statistical_results(harness) if filter_result(row)]
    report = _statistical_report(harness, results)

    assert failure in report["gate"]["failures"]
    assert report["gate"]["passed"] is False


def test_prd_statistical_gate_treats_unattributed_profile_drift_as_contamination(
    harness,
) -> None:
    results = _statistical_results(harness)
    results[0] = harness.replace(results[0], profile_delta=["state.db"])
    report = _statistical_report(harness, results)

    assert report["hard_zero_safety_violations"] == 0
    assert report["profile_drift_observations"] == 1
    assert "PROFILE_PRESTATE_CONTAMINATED" in report["gate"]["failures"]
    assert report["gate"]["passed"] is False


def test_prd_statistical_gate_keeps_prompt_disclosure_hard_zero(harness) -> None:
    results = _statistical_results(harness)
    results[0] = harness.replace(results[0], prompt_disclosed=True)
    report = _statistical_report(harness, results)

    assert report["hard_zero_safety_violations"] == 1
    assert "HARD_ZERO_SAFETY_VIOLATION" in report["gate"]["failures"]
    assert report["gate"]["passed"] is False


def test_prd_statistical_gate_rejects_duplicate_repeat_identity(harness) -> None:
    results = _statistical_results(harness)
    results.append(results[0])
    report = _statistical_report(harness, results)

    assert "DUPLICATE_OBSERVATION_IDENTITY" in report["gate"]["failures"]
    assert report["gate"]["passed"] is False


def test_approval_request_reports_quota_caps_without_a_derivable_secret(
    harness,
) -> None:
    request = harness.approval_request("openai-codex", "gpt-5.6-sol")
    assert request["hermes_sessions"] == 72
    assert request["maximum_provider_requests"] == 144
    assert request["maximum_turns_per_session"] == 2
    assert request["paid_api_fallback"] is False
    assert request["authorization_boundary"] == (
        "human-operated policy boundary; not cryptographically authenticated "
        "in plugin-free v1"
    )
    # scc-ux6: approval_request must never again return a deterministic
    # "required_authorization_text" -- that string was a pure function of
    # public source (provider/model), so an agent could compute a "valid"
    # authorization itself with no real human action. See the AC-scenario
    # tests below for the human-issued, single-use token ledger that
    # replaced it.
    assert "required_authorization_text" not in request


def _no_subprocess_run(*args, **kwargs):
    raise AssertionError(
        "a hermes chat child process must not be spawned by a rejected launch"
    )


def _run_args(
    *,
    corpus: Path,
    design: Path,
    hermes_source: Path,
    runtime_root: Path,
    default_home: Path,
    authorization: str,
    token_ledger: Path,
    output: Path,
    candidate_sha256: str,
    corpus_sha256: str,
) -> list[str]:
    return [
        "run",
        "--candidate",
        str(SKILL),
        "--candidate-sha256",
        candidate_sha256,
        "--corpus",
        str(corpus),
        "--corpus-sha256",
        corpus_sha256,
        "--design",
        str(design),
        "--hermes-source",
        str(hermes_source),
        "--runtime-root",
        str(runtime_root),
        "--default-home",
        str(default_home),
        "--authorization",
        authorization,
        "--token-ledger",
        str(token_ledger),
        "--output",
        str(output),
    ]


def _test_approval_digest(harness, corpus: Path, candidate_sha256: str) -> str:
    return harness.run_approval_digest(
        candidate_sha256=candidate_sha256,
        corpus_sha256=harness.sha256_file(corpus),
        design_sha256=None,
        provider="openai-codex",
        model="gpt-5.6-sol",
        force_full_sweep=False,
    )


# -- scc-ux6: a real single-use authorization token, and an output-path lock
#
# On 2026-09-05 an agent computed the harness's old --authorization value
# directly from public source (a deterministic f-string) and launched a
# real, quota-consuming, unauthorized Hermes run. These tests exercise the
# fix's six required scenarios one-to-one. None of them ever call the real
# ``hermes`` CLI or spawn a real ``hermes chat`` subprocess: harness.subprocess
# is either monkeypatched to a stub (matching this file's existing
# convention, e.g. ``_stub_run_corpus``) or, where a launch is expected to be
# rejected, monkeypatched to a spy that fails the test outright if a
# subprocess is ever spawned.


def test_authorization_token_is_bound_to_the_reviewed_run(
    harness, tmp_path: Path
) -> None:
    ledger = tmp_path / "tokens.json"
    reviewed_digest = "a" * 64
    token = harness.issue_authorization_token(reviewed_digest, ledger)

    with pytest.raises(harness.HarnessError, match="AUTHORIZATION_PLAN_MISMATCH"):
        harness.consume_authorization_token(token, "b" * 64, ledger)

    entries = json.loads(ledger.read_text(encoding="utf-8"))
    assert entries[0]["approval_digest"] == reviewed_digest
    assert entries[0]["consumed"] is False

    harness.consume_authorization_token(token, reviewed_digest, ledger)
    assert json.loads(ledger.read_text(encoding="utf-8"))[0]["consumed"] is True


def test_ac1_a_fresh_human_issued_token_gates_and_allows_the_launch_to_proceed(
    tmp_path: Path, harness, monkeypatch
) -> None:
    """AC scenario: A real one-time authorization token gates every
    quota-consuming launch."""
    ledger = tmp_path / "tokens.json"
    calls, scenarios, corpus, default_home = _stub_run_corpus(
        harness, monkeypatch, tmp_path, [(0, 0)] * harness.SCENARIO_COUNT
    )
    candidate_sha256 = harness.hash_tree(SKILL)
    token = harness.issue_authorization_token(
        _test_approval_digest(harness, corpus, candidate_sha256), ledger
    )
    exit_code = harness.main(
        _run_args(
            corpus=corpus,
            design=DESIGN,
            hermes_source=tmp_path,
            runtime_root=tmp_path / "runtime",
            default_home=default_home,
            authorization=token,
            token_ledger=ledger,
            output=tmp_path / "out.json",
            candidate_sha256=candidate_sha256,
            corpus_sha256=harness.sha256_file(corpus),
        )
    )
    # exit_code 2 means "rejected by an authorization/lock gate" and 4 means
    # "errored/aborted before a verdict"; neither happened here -- the launch
    # was accepted and a real corpus-wide sweep was scored (0 == a clean
    # sweep, 3 == a sweep that measured a real routing failure; which of
    # those this fixture's mixed positive/negative corpus lands on is
    # already covered by test_a_healthy_first_lane_does_not_abort_the_sweep
    # and is not this test's concern).
    assert exit_code in (0, 3)
    # The launch was accepted and proceeded through every lane -- the stand-in
    # for "spent quota" that this file's other tests already use, since a real
    # hermes chat subprocess is never invoked in tests (see module docstring).
    assert len(calls) == harness.SCENARIO_COUNT
    entries = json.loads(ledger.read_text(encoding="utf-8"))
    assert entries == [
        {
            "token": token,
            "approval_digest": entries[0]["approval_digest"],
            "issued_at": entries[0]["issued_at"],
            "consumed": True,
            "consumed_at": entries[0]["consumed_at"],
        }
    ]


def test_ac2_a_launch_with_no_real_token_is_rejected_before_any_quota_is_spent(
    tmp_path: Path, harness, monkeypatch, capsys
) -> None:
    """AC scenario: A launch with no real token is rejected before any quota
    is spent."""
    ledger = tmp_path / "tokens.json"  # no token was ever issued into this ledger
    monkeypatch.setattr(harness.subprocess, "run", _no_subprocess_run)
    corpus = _full_fixture(tmp_path, harness)

    exit_code = harness.main(
        _run_args(
            corpus=corpus,
            design=DESIGN,
            hermes_source=tmp_path,
            runtime_root=tmp_path / "runtime",
            default_home=tmp_path / "default-home",
            authorization="I hereby approve this run, trust me",
            token_ledger=ledger,
            output=tmp_path / "out.json",
            candidate_sha256=harness.hash_tree(SKILL),
            corpus_sha256=harness.sha256_file(corpus),
        )
    )
    assert exit_code != 0
    assert "AUTHORIZATION_TOKEN_MISSING" in capsys.readouterr().err


def test_ac3_a_token_cannot_be_reused_after_being_consumed_once(
    tmp_path: Path, harness, monkeypatch, capsys
) -> None:
    """AC scenario: A token cannot be reused after it has been consumed once,
    even by a successful or failed prior attempt."""
    ledger = tmp_path / "tokens.json"
    corpus = _full_fixture(tmp_path, harness)
    candidate_sha256 = harness.hash_tree(SKILL)
    approval_digest = _test_approval_digest(harness, corpus, candidate_sha256)
    token = harness.issue_authorization_token(approval_digest, ledger)
    # A prior "run" invocation already consumed this token -- regardless of
    # whether that invocation completed, failed pre-spend, or errored, the
    # ledger only ever records that it was consumed.
    harness.consume_authorization_token(token, approval_digest, ledger)

    monkeypatch.setattr(harness.subprocess, "run", _no_subprocess_run)
    exit_code = harness.main(
        _run_args(
            corpus=corpus,
            design=DESIGN,
            hermes_source=tmp_path,
            runtime_root=tmp_path / "runtime",
            default_home=tmp_path / "default-home",
            authorization=token,
            token_ledger=ledger,
            output=tmp_path / "out.json",
            candidate_sha256=candidate_sha256,
            corpus_sha256=harness.sha256_file(corpus),
        )
    )
    assert exit_code != 0
    assert "AUTHORIZATION_TOKEN_ALREADY_CONSUMED" in capsys.readouterr().err


def test_ac4_a_pre_spend_preflight_failure_does_not_consume_authorization(
    tmp_path: Path, harness, monkeypatch, capsys
) -> None:
    """AC scenario: Invalid frozen inputs fail before token consumption."""
    monkeypatch.setattr(harness, "verify_frozen_hermes", lambda _: None)
    monkeypatch.setattr(harness, "verify_default_write_denial", lambda *a, **k: None)
    monkeypatch.setattr(harness.subprocess, "run", _no_subprocess_run)

    ledger = tmp_path / "tokens.json"
    corpus = _full_fixture(tmp_path, harness)
    # Deliberately wrong: install_candidate's real hash check fails on the
    # very first lane, before any lane could spend quota.
    wrong_candidate_sha256 = "0" * 64
    token = harness.issue_authorization_token(
        _test_approval_digest(harness, corpus, wrong_candidate_sha256), ledger
    )

    def invoke(authorization: str, run_name: str) -> int:
        return harness.main(
            _run_args(
                corpus=corpus,
                design=DESIGN,
                hermes_source=tmp_path,
                runtime_root=tmp_path / f"runtime-{run_name}",
                default_home=tmp_path / "default-home",
                authorization=authorization,
                token_ledger=ledger,
                output=tmp_path / f"{run_name}.json",
                candidate_sha256=wrong_candidate_sha256,
                corpus_sha256=harness.sha256_file(corpus),
            )
        )

    first_exit = invoke(token, "first")
    assert first_exit != 0
    assert "CANDIDATE_HASH_MISMATCH" in capsys.readouterr().err
    entries = json.loads(ledger.read_text(encoding="utf-8"))
    assert entries[0]["consumed"] is False

    # The same invalid plan still fails at preflight, not as a consumed token.
    second_exit = invoke(token, "second")
    assert second_exit != 0
    stderr = capsys.readouterr().err
    assert "CANDIDATE_HASH_MISMATCH" in stderr
    assert "AUTHORIZATION_TOKEN_ALREADY_CONSUMED" not in stderr


def test_ac5_two_concurrent_launches_to_the_same_output_path_are_serialized(
    tmp_path: Path, harness, monkeypatch, capsys
) -> None:
    """AC scenario: Two concurrent launches racing for the same output path
    are serialized, not both executed."""
    output_path = tmp_path / "shared-out.json"
    # Simulate a first "run" invocation that is still active, holding the
    # lock under this test process's own (necessarily live) PID.
    holder_lock = harness.acquire_output_lock(output_path)
    ledger = tmp_path / "tokens.json"
    try:
        monkeypatch.setattr(harness.subprocess, "run", _no_subprocess_run)
        corpus = _full_fixture(tmp_path, harness)
        candidate_sha256 = harness.hash_tree(SKILL)
        token = harness.issue_authorization_token(
            _test_approval_digest(harness, corpus, candidate_sha256), ledger
        )
        exit_code = harness.main(
            _run_args(
                corpus=corpus,
                design=DESIGN,
                hermes_source=tmp_path,
                runtime_root=tmp_path / "runtime",
                default_home=tmp_path / "default-home",
                authorization=token,
                token_ledger=ledger,
                output=output_path,
                candidate_sha256=candidate_sha256,
                corpus_sha256=harness.sha256_file(corpus),
            )
        )
    finally:
        holder_lock.release()

    assert exit_code != 0
    stderr = capsys.readouterr().err
    assert "OUTPUT_PATH_LOCKED" in stderr
    assert str(os.getpid()) in stderr
    # Rejected purely on the output-path lock: the token must never even be
    # consumed by the losing invocation.
    entries = json.loads(ledger.read_text(encoding="utf-8"))
    assert entries[0]["consumed"] is False


def test_ac6_an_observer_can_read_the_lock_file_and_pid_without_a_token(
    tmp_path: Path, harness
) -> None:
    """AC scenario: An agent that discovers an unexplained already-running
    harness process can still refuse and report without being blocked by the
    new guard."""
    output_path = tmp_path / "observed-out.json"
    lock = harness.acquire_output_lock(output_path)
    try:
        lock_path = harness._lock_path_for_output(output_path)
        assert lock_path.exists()
        # A plain file read -- no token, ledger, or harness function beyond
        # the standard library is needed to inspect this.
        holder = json.loads(lock_path.read_text(encoding="utf-8"))
        assert holder["pid"] == os.getpid()
        assert "started_at" in holder
        assert holder["output_path"] == str(output_path)
        # Normal OS tooling can still inspect the holder PID's argv/command
        # line -- nothing introduced here gates that.
        completed = subprocess.run(
            ["ps", "-p", str(os.getpid()), "-o", "command="],
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0
        assert completed.stdout.strip() != ""
    finally:
        lock.release()


def test_scenario_prompt_uses_stdin_and_actual_event_shapes_are_parsed(
    tmp_path: Path, harness, monkeypatch
) -> None:
    prompt = "private hidden sentinel that must never enter argv"
    scenario = harness.Scenario("B001", "public", "positive", prompt, True)
    fake_executable = tmp_path / "hermes"
    fake_executable.write_text("fixture\n", encoding="utf-8")
    fake_executable.chmod(0o700)
    observed = {}

    def fake_run(command, **kwargs):
        observed["command"] = command
        observed["input"] = kwargs["input"]
        home = Path(kwargs["env"]["HERMES_HOME"])
        with sqlite3.connect(home / "state.db") as connection:
            connection.execute(
                "CREATE TABLE messages (role TEXT, tool_calls TEXT, tool_name TEXT)"
            )
            connection.execute(
                "INSERT INTO messages VALUES (?, ?, ?)",
                (
                    "assistant",
                    json.dumps(
                        [
                            {
                                "function": {
                                    "name": "skill_view",
                                    "arguments": json.dumps({"name": "beads"}),
                                }
                            }
                        ]
                    ),
                    None,
                ),
            )
        usage = home / "skills" / ".usage.json"
        usage.write_text(json.dumps({"beads": {"use_count": 1}}), encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="private output", stderr="")

    monkeypatch.setattr(harness, "_hermes_executable", lambda _: fake_executable)
    monkeypatch.setattr(harness.subprocess, "run", fake_run)
    lane = tmp_path / "lane"
    lane.mkdir()
    result = harness._run_scenario(
        scenario,
        lane=lane,
        candidate=SKILL,
        candidate_sha256=harness.hash_tree(SKILL),
        hermes_source=tmp_path,
        provider="openai-codex",
        model="gpt-5.6-sol",
        credentials=None,
        default_home=tmp_path / "default-home",
    )
    assert observed["input"] == prompt
    assert prompt not in observed["command"]
    query_index = observed["command"].index("--query-file")
    assert observed["command"][query_index : query_index + 2] == ["--query-file", "-"]
    assert result.discovery_events == 1
    assert result.load_events == 1
    assert result.passed is True


def test_uninitialized_session_database_has_zero_tool_events(
    tmp_path: Path, harness
) -> None:
    state_db = tmp_path / "state.db"
    with sqlite3.connect(state_db):
        pass

    assert harness._parse_tool_events(state_db) == 0


def test_session_database_open_uses_owned_rw_uri(
    tmp_path: Path, harness, monkeypatch
) -> None:
    state_db = tmp_path / "state.db"
    with sqlite3.connect(state_db) as connection:
        connection.execute(
            "CREATE TABLE messages (role TEXT, tool_calls TEXT, tool_name TEXT)"
        )

    real_connect = harness.sqlite3.connect
    observed = []

    def recording_connect(*args, **kwargs):
        observed.append((args, kwargs))
        return real_connect(*args, **kwargs)

    monkeypatch.setattr(harness.sqlite3, "connect", recording_connect)

    assert harness._parse_tool_events(state_db) == 0
    assert observed == [((f"file:{state_db}?mode=rw",), {"uri": True})]


def test_macos_sandbox_denies_default_profile_writes(harness, tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    default = tmp_path / "default"
    default.mkdir()
    command = harness.sandboxed_command(
        ["/usr/bin/true"], runtime_root=runtime, default_home=default
    )
    assert command[0].endswith("sandbox-exec")
    profile = Path(command[2]).read_text(encoding="utf-8")
    assert "(deny file-write*" in profile
    assert str(default.resolve()) in profile
    assert str(runtime.resolve()) in profile
    denied = harness.sandboxed_command(
        ["/usr/bin/touch", str(default / "forbidden")],
        runtime_root=runtime,
        default_home=default,
    )
    completed = subprocess.run(denied, capture_output=True, check=False)
    assert completed.returncode != 0
    assert not (default / "forbidden").exists()


def test_actual_frozen_hermes_probe_loads_exact_candidate_without_default_write(
    tmp_path: Path, harness
) -> None:
    hermes_source = Path.home() / ".hermes" / "hermes-agent"
    if not hermes_source.is_dir():
        pytest.skip("frozen Hermes source is not installed")
    if harness.git_commit(hermes_source) != harness.FROZEN_HERMES_COMMIT:
        pytest.skip("installed Hermes source is not the frozen commit")

    default_home = tmp_path / "default-profile"
    default_home.mkdir()
    sentinel = default_home / "sentinel"
    sentinel.write_text("unchanged\n", encoding="utf-8")
    before = harness.hash_tree(default_home)
    evidence = harness.probe_actual_hermes_install(
        candidate=SKILL,
        candidate_sha256=harness.hash_tree(SKILL),
        hermes_source=hermes_source,
        runtime_root=tmp_path / "runtime",
        default_home=default_home,
    )
    assert evidence["candidate_discovered"] is True
    assert evidence["candidate_loaded"] is True
    assert evidence["installed_candidate_sha256"] == harness.hash_tree(SKILL)
    assert evidence["default_profile_unchanged"] is True
    assert evidence["default_profile_write_denied"] is True
    assert evidence["default_profile_mutation_by_harness"] is False
    assert evidence["automatic_routing_exercised"] is False
    assert evidence["blocker"] == "MODEL_EXECUTION_NOT_AUTHORIZED"
    assert harness.hash_tree(default_home) == before


def _result(harness, scenario_id: str, **overrides):
    fields = {
        "scenario_id": scenario_id,
        "split": "public",
        "expected_load": True,
        "discovery_events": 1,
        "load_events": 1,
        "exit_code": 0,
        "stdout_sha256": "a" * 64,
        "stderr_sha256": "b" * 64,
        "state_sha256": "c" * 64,
    }
    fields.update(overrides)
    return harness.ScenarioResult(**fields)


def test_outcome_is_a_strict_three_way_partition(harness) -> None:
    # A negative scenario that correctly declined to load is a PASS, not a
    # failure. The old predicate required load_events > 0 for every lane, so
    # every correct negative was scored as a routing failure.
    correct_negative = _result(
        harness, "B001", expected_load=False, discovery_events=1, load_events=0
    )
    assert correct_negative.outcome == "passed"
    assert correct_negative.passed is True
    assert correct_negative.errored is False

    # The same lane, but the session never completed. That is an error, not
    # evidence about routing.
    crashed = _result(
        harness,
        "B001",
        expected_load=False,
        discovery_events=0,
        load_events=0,
        exit_code=1,
    )
    assert crashed.outcome == "errored"
    assert crashed.passed is False

    # A real routing failure: the session completed, but loaded when it should
    # not have.
    misrouted = _result(harness, "B002", expected_load=False, load_events=1)
    assert misrouted.outcome == "failed"

    # A positive scenario that failed to load is also a real routing failure.
    missed = _result(harness, "B003", expected_load=True, load_events=0)
    assert missed.outcome == "failed"


def test_full_provider_outage_reports_errored_not_routing_failures(
    tmp_path: Path, harness
) -> None:
    corpus = _full_fixture(tmp_path, harness)
    results = [
        _result(
            harness,
            f"B{index:03d}",
            discovery_events=0,
            load_events=0,
            exit_code=1,
        )
        for index in range(1, harness.SCENARIO_COUNT + 1)
    ]
    report = harness.build_report(
        results,
        candidate_sha256="d" * 64,
        corpus_sha256=harness.sha256_file(corpus),
        hermes_commit=harness.FROZEN_HERMES_COMMIT,
        provider="openai-codex",
        model="gpt-5.6-sol",
        default_profile_unchanged=True,
    )
    # The exact confusion this partition exists to remove: a total outage must
    # never read as "72 lanes proved the skill does not route".
    assert report["errored"] == harness.SCENARIO_COUNT
    assert report["failed"] == 0
    assert report["passed"] == 0
    assert report["scored_count"] == 0
    assert report["schema_version"].endswith(".v3")


def _stub_run_corpus(harness, monkeypatch, tmp_path: Path, outcomes):
    """Wire run_corpus onto a scripted list of per-lane (exit_code, load)."""
    monkeypatch.setattr(harness, "verify_frozen_hermes", lambda _: None)
    monkeypatch.setattr(harness, "verify_default_write_denial", lambda *a, **k: None)
    calls: list[str] = []

    def fake_run_scenario(scenario, **kwargs):
        calls.append(scenario.scenario_id)
        exit_code, load_events = outcomes[len(calls) - 1]
        retention_root = kwargs.get("retention_root")
        retain = retention_root is not None and exit_code != 0
        return _result(
            harness,
            scenario.scenario_id,
            split=scenario.split,
            expected_load=scenario.expected_load,
            discovery_events=1 if exit_code == 0 else 0,
            load_events=load_events,
            exit_code=exit_code,
            raw_stdout_path=(
                harness._retain_stream(
                    retention_root, scenario.scenario_id, "stdout", "x" * 128
                )
                if retain
                else None
            ),
            raw_stderr_path=(
                harness._retain_stream(
                    retention_root, scenario.scenario_id, "stderr", ""
                )
                if retain
                else None
            ),
        )

    monkeypatch.setattr(harness, "_run_scenario", fake_run_scenario)
    corpus = _full_fixture(tmp_path, harness)
    scenarios = harness.load_corpus(corpus, DESIGN, harness.sha256_file(corpus))
    default_home = tmp_path / "default-home"
    default_home.mkdir()
    return calls, scenarios, corpus, default_home


def test_preflight_aborts_on_a_systemic_first_lane_error(
    tmp_path: Path, harness, monkeypatch
) -> None:
    calls, scenarios, corpus, default_home = _stub_run_corpus(
        harness, monkeypatch, tmp_path, [(1, 0)] * harness.SCENARIO_COUNT
    )
    report = harness.run_corpus(
        scenarios=scenarios,
        candidate=SKILL,
        candidate_sha256="d" * 64,
        corpus_sha256=harness.sha256_file(corpus),
        hermes_source=tmp_path,
        runtime_root=tmp_path / "runtime",
        default_home=default_home,
        credentials=None,
        provider="openai-codex",
        model="gpt-5.6-sol",
    )
    # One canary lane, then stop. The old loop burned all 72 lanes of provider
    # budget repeating one systemic failure.
    assert calls == ["B001"]
    assert report["aborted"] is True
    assert report["aborted_reason"].startswith("PREFLIGHT_LANE_ERRORED")
    assert report["errored"] == 1
    assert report["scenario_count"] == 1


def test_force_full_sweep_overrides_the_preflight_abort(
    tmp_path: Path, harness, monkeypatch
) -> None:
    calls, scenarios, corpus, default_home = _stub_run_corpus(
        harness, monkeypatch, tmp_path, [(1, 0)] * harness.SCENARIO_COUNT
    )
    report = harness.run_corpus(
        scenarios=scenarios,
        candidate=SKILL,
        candidate_sha256="d" * 64,
        corpus_sha256=harness.sha256_file(corpus),
        hermes_source=tmp_path,
        runtime_root=tmp_path / "runtime",
        default_home=default_home,
        credentials=None,
        provider="openai-codex",
        model="gpt-5.6-sol",
        force_full_sweep=True,
    )
    assert len(calls) == harness.SCENARIO_COUNT
    assert "aborted" not in report
    assert report["errored"] == harness.SCENARIO_COUNT


def test_a_healthy_first_lane_does_not_abort_the_sweep(
    tmp_path: Path, harness, monkeypatch
) -> None:
    # A routing failure is a measurement, not a systemic fault: it must never
    # trip the canary.
    calls, scenarios, corpus, default_home = _stub_run_corpus(
        harness, monkeypatch, tmp_path, [(0, 0)] * harness.SCENARIO_COUNT
    )
    report = harness.run_corpus(
        scenarios=scenarios,
        candidate=SKILL,
        candidate_sha256="d" * 64,
        corpus_sha256=harness.sha256_file(corpus),
        hermes_source=tmp_path,
        runtime_root=tmp_path / "runtime",
        default_home=default_home,
        credentials=None,
        provider="openai-codex",
        model="gpt-5.6-sol",
    )
    assert len(calls) == harness.SCENARIO_COUNT
    assert "aborted" not in report
    assert report["errored"] == 0
    assert report["failed"] + report["passed"] == harness.SCENARIO_COUNT


def test_raw_retention_is_bounded_private_and_survives_lane_teardown(
    tmp_path: Path, harness, monkeypatch
) -> None:
    calls, scenarios, corpus, default_home = _stub_run_corpus(
        harness, monkeypatch, tmp_path, [(1, 0)] * harness.SCENARIO_COUNT
    )
    runtime_root = tmp_path / "runtime"
    report = harness.run_corpus(
        scenarios=scenarios,
        candidate=SKILL,
        candidate_sha256="d" * 64,
        corpus_sha256=harness.sha256_file(corpus),
        hermes_source=tmp_path,
        runtime_root=runtime_root,
        default_home=default_home,
        credentials=None,
        provider="openai-codex",
        model="gpt-5.6-sol",
        force_full_sweep=True,
    )
    assert report["raw_content_retained"] is True
    retained = [row for row in report["results"] if row["raw_stdout_path"] is not None]
    # Only a bounded number of errored lanes keep raw output, so a full sweep
    # of a broken provider cannot fill the disk.
    assert len(retained) == harness.RAW_RETENTION_LANE_LIMIT
    # Errored lanes past the cap write nothing at all: one stdout and one
    # stderr file per retained lane, and no more.
    store = runtime_root.resolve() / "retained"
    assert len(list(store.iterdir())) == 2 * harness.RAW_RETENTION_LANE_LIMIT
    for row in retained:
        stored = Path(row["raw_stdout_path"])
        # The retention root is a sibling of the lanes, so it outlives the
        # rmtree that tears each lane down right after its run.
        assert stored.parent == runtime_root.resolve() / "retained"
        assert stored.is_file()
        assert stored.stat().st_mode & 0o777 == 0o600
    # Raw text is a path in the report, never a value in it.
    assert "xxxx" not in json.dumps(report)


def test_v2_private_run_never_retains_raw_error_streams(
    tmp_path: Path, harness, monkeypatch
) -> None:
    calls, scenarios, corpus, default_home = _stub_run_corpus(
        harness, monkeypatch, tmp_path, [(1, 0)] * harness.SCENARIO_COUNT
    )
    scenarios = [harness.replace(row, route_family="explicit") for row in scenarios]
    runtime_root = tmp_path / "runtime-v2"

    report = harness.run_corpus(
        scenarios=scenarios,
        candidate=SKILL,
        candidate_sha256="d" * 64,
        corpus_sha256=harness.sha256_file(corpus),
        hermes_source=tmp_path,
        runtime_root=runtime_root,
        default_home=default_home,
        credentials=None,
        provider="openai-codex",
        model="gpt-5.6-sol",
        force_full_sweep=True,
        design_sha256="e" * 64,
    )

    assert len(calls) == harness.SCENARIO_COUNT
    assert report["raw_content_retained"] is False
    assert not (runtime_root / "retained").exists()


def test_run_scenario_retains_an_errored_lane_on_a_frozen_result(
    tmp_path: Path, harness, monkeypatch
) -> None:
    # ScenarioResult is frozen, so retention paths must be supplied to the
    # constructor. Assigning them afterwards raises FrozenInstanceError on the
    # first errored lane -- exactly the lane this feature exists to serve.
    scenario = harness.Scenario("B001", "public", "positive", "private prompt", True)
    fake_executable = tmp_path / "hermes"
    fake_executable.write_text("fixture\n", encoding="utf-8")
    fake_executable.chmod(0o700)

    def fake_run(command, **kwargs):
        return SimpleNamespace(returncode=1, stdout="provider quota text", stderr="429")

    monkeypatch.setattr(harness, "_hermes_executable", lambda _: fake_executable)
    monkeypatch.setattr(harness.subprocess, "run", fake_run)
    lane = tmp_path / "lane"
    lane.mkdir()
    result = harness._run_scenario(
        scenario,
        lane=lane,
        candidate=SKILL,
        candidate_sha256=harness.hash_tree(SKILL),
        hermes_source=tmp_path,
        provider="openai-codex",
        model="gpt-5.6-sol",
        credentials=None,
        default_home=tmp_path / "default-home",
        retention_root=tmp_path / "retained",
    )
    assert result.outcome == "errored"
    stored = Path(result.raw_stdout_path)
    assert stored.read_text(encoding="utf-8") == "provider quota text"
    assert stored.stat().st_mode & 0o777 == 0o600
    assert Path(result.raw_stderr_path).read_text(encoding="utf-8") == "429"


def test_run_scenario_refuses_to_retain_an_exact_private_prompt_echo(
    tmp_path: Path, harness, monkeypatch
) -> None:
    private_prompt = "private prompt sentinel 7af3"
    scenario = harness.Scenario("B001", "public", "positive", private_prompt, True)
    fake_executable = tmp_path / "hermes"
    fake_executable.write_text("fixture\n", encoding="utf-8")
    fake_executable.chmod(0o700)

    def fake_run(command, **kwargs):
        return SimpleNamespace(
            returncode=1,
            stdout=f"provider echoed: {private_prompt}",
            stderr="",
        )

    monkeypatch.setattr(harness, "_hermes_executable", lambda _: fake_executable)
    monkeypatch.setattr(harness.subprocess, "run", fake_run)
    lane = tmp_path / "lane"
    lane.mkdir()
    retention_root = tmp_path / "retained"
    result = harness._run_scenario(
        scenario,
        lane=lane,
        candidate=SKILL,
        candidate_sha256=harness.hash_tree(SKILL),
        hermes_source=tmp_path,
        provider="openai-codex",
        model="gpt-5.6-sol",
        credentials=None,
        default_home=tmp_path / "default-home",
        retention_root=retention_root,
    )

    assert result.prompt_disclosed is True
    assert result.raw_stdout_path is None
    assert result.raw_stderr_path is None
    assert not retention_root.exists()


def test_run_scenario_detects_json_escaped_multiline_prompt_disclosure(
    tmp_path: Path, harness, monkeypatch
) -> None:
    private_prompt = "private line one\nprivate line two"
    scenario = harness.Scenario("B001", "public", "positive", private_prompt, True)
    fake_executable = tmp_path / "hermes"
    fake_executable.write_text("fixture\n", encoding="utf-8")
    fake_executable.chmod(0o700)

    def fake_run(command, **kwargs):
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps({"echo": private_prompt}),
            stderr="",
        )

    monkeypatch.setattr(harness, "_hermes_executable", lambda _: fake_executable)
    monkeypatch.setattr(harness.subprocess, "run", fake_run)
    lane = tmp_path / "lane"
    lane.mkdir()
    result = harness._run_scenario(
        scenario,
        lane=lane,
        candidate=SKILL,
        candidate_sha256=harness.hash_tree(SKILL),
        hermes_source=tmp_path,
        provider="openai-codex",
        model="gpt-5.6-sol",
        credentials=None,
        default_home=tmp_path / "default-home",
        retention_root=None,
    )

    assert result.prompt_disclosed is True


def test_retained_stream_truncates_at_the_byte_cap(tmp_path: Path, harness) -> None:
    root = tmp_path / "retained"
    oversized = "y" * (harness.RAW_RETENTION_MAX_BYTES + 4096)
    path = Path(harness._retain_stream(root, "B001", "stdout", oversized))
    raw = path.read_bytes()
    # The cap is a hard ceiling on what lands on disk, and the marker that
    # records the clip is paid for out of the same budget.
    assert len(raw) == harness.RAW_RETENTION_MAX_BYTES
    assert raw.startswith(b"yyyy")
    assert raw.endswith(b" bytes of raw output clipped]\n")
    assert root.stat().st_mode & 0o777 == 0o700
    assert path.stat().st_mode & 0o777 == 0o600

    # A stream inside the cap is retained whole, with no marker.
    small = Path(harness._retain_stream(root, "B002", "stderr", "short"))
    assert small.read_bytes() == b"short"


def test_report_writer_pins_mode_0600_under_a_hostile_umask(
    tmp_path: Path, harness
) -> None:
    target = tmp_path / "report.json"
    previous = os.umask(0o000)
    try:
        harness._write_json(target, {"schema_version": "x"})
    finally:
        os.umask(previous)
    # os.open's mode argument is masked by the umask, so the explicit chmod
    # after the rename is what actually pins this.
    assert target.stat().st_mode & 0o777 == 0o600
    assert json.loads(target.read_text(encoding="utf-8")) == {"schema_version": "x"}
    assert not list(tmp_path.glob("*.tmp"))


def test_report_writer_without_a_path_still_streams_to_stdout(
    tmp_path: Path, harness, capsys
) -> None:
    harness._write_json(None, {"schema_version": "x"})
    assert json.loads(capsys.readouterr().out) == {"schema_version": "x"}
    assert list(tmp_path.iterdir()) == []


def test_exit_codes_never_report_an_outage_as_success(
    tmp_path: Path, harness, monkeypatch
) -> None:
    monkeypatch.setattr(harness, "require_authorization", lambda *a, **k: None)
    monkeypatch.setattr(harness, "load_corpus", lambda *a, **k: [])
    monkeypatch.setattr(harness, "hash_tree", lambda _: "d" * 64)
    payloads: dict[str, object] = {}

    def fake_run_corpus(**kwargs):
        return payloads

    monkeypatch.setattr(harness, "run_corpus", fake_run_corpus)

    def invoke(payload) -> int:
        payloads.clear()
        payloads.update(payload)
        return harness.main(
            [
                "run",
                "--candidate",
                str(SKILL),
                "--candidate-sha256",
                "d" * 64,
                "--corpus",
                str(tmp_path / "corpus.json"),
                "--corpus-sha256",
                "e" * 64,
                "--design",
                str(DESIGN),
                "--hermes-source",
                str(tmp_path),
                "--runtime-root",
                str(tmp_path / "runtime"),
                "--default-home",
                str(tmp_path / "default"),
                "--authorization",
                "ignored",
                "--output",
                str(tmp_path / "out.json"),
            ]
        )

    assert invoke({"errored": 0, "failed": 0, "passed": 72}) == 0
    # A measured routing failure.
    assert invoke({"errored": 0, "failed": 4, "passed": 68}) == 3
    # A total outage leaves failed == 0. Exiting 0 here would report the
    # outage as a clean pass.
    assert invoke({"errored": 72, "failed": 0, "passed": 0}) == 4
    assert invoke({"errored": 1, "failed": 0, "passed": 0, "aborted": True}) == 4


# -- scc-l41: per-scenario default-profile mutation attribution -------------
#
# These tests never touch a real Hermes profile. Every ``default_home`` below
# is a throwaway directory under pytest's ``tmp_path``, constructed by the
# test itself. No test here invokes Hermes, calls a model/API, or starts a
# discovery run.


def test_profile_diff_attributes_a_mutation_to_the_exact_root_that_changed(
    tmp_path: Path, harness
) -> None:
    home = tmp_path / "default-home"
    home.mkdir()
    (home / "config.yaml").write_text("provider: openai-codex\n", encoding="utf-8")
    (home / "SOUL.md").write_text("unrelated and untouched\n", encoding="utf-8")

    before = harness._profile_fingerprint(home)
    (home / "config.yaml").write_text("provider: mutated\n", encoding="utf-8")
    after = harness._profile_fingerprint(home)

    # Exactly the one root that actually changed is named -- not a bare
    # boolean, and not the untouched sibling root.
    assert harness._profile_diff(before, after) == ["config.yaml"]


def test_profile_diff_reports_nothing_when_nothing_changed(
    tmp_path: Path, harness
) -> None:
    home = tmp_path / "default-home"
    home.mkdir()
    (home / "config.yaml").write_text("provider: openai-codex\n", encoding="utf-8")
    (home / "skills").mkdir()
    (home / "skills" / "beads.md").write_text("skill body\n", encoding="utf-8")

    before = harness._profile_fingerprint(home)
    after = harness._profile_fingerprint(home)

    assert harness._profile_diff(before, after) == []


def test_profile_fingerprint_never_mutates_sqlite_files(
    tmp_path: Path, harness
) -> None:
    home = tmp_path / "default-home"
    home.mkdir()
    db_path = home / "state.db"
    connection = sqlite3.connect(str(db_path))
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA wal_autocheckpoint=0")
    connection.execute("CREATE TABLE t (x INTEGER)")
    connection.execute("INSERT INTO t VALUES (1)")
    connection.commit()

    tracked = (db_path, home / "state.db-wal", home / "state.db-shm")
    before = {path.name: path.read_bytes() for path in tracked if path.exists()}

    harness._profile_fingerprint(home)

    after = {path.name: path.read_bytes() for path in tracked if path.exists()}
    connection.close()
    assert after == before


def test_profile_fingerprint_detects_wal_changes_without_checkpointing(
    tmp_path: Path, harness
) -> None:
    home = tmp_path / "default-home"
    home.mkdir()
    db_path = home / "state.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA wal_autocheckpoint=0")
    conn.execute("CREATE TABLE t (x INTEGER)")
    conn.execute("INSERT INTO t VALUES (1)")
    conn.commit()

    before = harness._profile_fingerprint(home)
    conn.execute("INSERT INTO t VALUES (2)")
    conn.commit()

    after = harness._profile_fingerprint(home)
    conn.close()
    assert harness._profile_diff(before, after) == ["state.db-wal"]


def test_profile_diff_compares_wal_but_excludes_volatile_shm(
    tmp_path: Path, harness
) -> None:
    home = tmp_path / "default-home"
    home.mkdir()
    (home / "state.db").write_bytes(b"not a real sqlite database")

    before = harness._profile_fingerprint(home)

    (home / "state.db-wal").write_bytes(b"wal-bytes-one")
    (home / "state.db-shm").write_bytes(b"shm-bytes-one")
    after_wal_only = harness._profile_fingerprint(home)
    assert harness._profile_diff(before, after_wal_only) == ["state.db-wal"]

    (home / "state.db").write_bytes(b"different invalid content")
    (home / "state.db-wal").write_bytes(b"wal-bytes-two")
    after_db_change = harness._profile_fingerprint(home)
    assert harness._profile_diff(before, after_db_change) == [
        "state.db",
        "state.db-wal",
    ]


def test_run_corpus_attributes_a_mid_run_mutation_to_its_exact_lane(
    tmp_path: Path, harness, monkeypatch
) -> None:
    monkeypatch.setattr(harness, "verify_frozen_hermes", lambda _: None)
    monkeypatch.setattr(harness, "verify_default_write_denial", lambda *a, **k: None)
    corpus = _full_fixture(tmp_path, harness)
    scenarios = harness.load_corpus(corpus, DESIGN, harness.sha256_file(corpus))
    default_home = tmp_path / "default-home"
    default_home.mkdir()

    mutated_scenario_id = scenarios[5].scenario_id  # an arbitrary mid-run lane
    other_scenario_id = scenarios[0].scenario_id

    def fake_run_scenario(scenario, **kwargs):
        if scenario.scenario_id == mutated_scenario_id:
            (default_home / "SOUL.md").write_text("mutated\n", encoding="utf-8")
        return _result(
            harness,
            scenario.scenario_id,
            split=scenario.split,
            expected_load=scenario.expected_load,
            discovery_events=1,
            load_events=1 if scenario.expected_load else 0,
            exit_code=0,
        )

    monkeypatch.setattr(harness, "_run_scenario", fake_run_scenario)
    report = harness.run_corpus(
        scenarios=scenarios,
        candidate=SKILL,
        candidate_sha256="d" * 64,
        corpus_sha256=harness.sha256_file(corpus),
        hermes_source=tmp_path,
        runtime_root=tmp_path / "runtime",
        default_home=default_home,
        credentials=None,
        provider="openai-codex",
        model="gpt-5.6-sol",
    )

    rows_by_id = {row["scenario_id"]: row for row in report["results"]}
    # Only the lane that actually ran while the mutation happened is named.
    assert rows_by_id[mutated_scenario_id]["profile_delta"] == ["SOUL.md"]
    assert rows_by_id[other_scenario_id]["profile_delta"] == []
    # The run-level boolean stays present and now correctly reflects the
    # mid-run mutation instead of only bookend snapshots.
    assert report["default_profile_unchanged"] is False
