"""End-to-end contract tests for the portable adversarial reviewer skill."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "plugins/review-panel/skills/adversarial-reviewer"
SCRIPT = SKILL / "scripts/adversarial_contract.py"


def load_contract():
    spec = importlib.util.spec_from_file_location("adversarial_contract", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["adversarial_contract"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def contract():
    return load_contract()


def fixture(name: str) -> dict[str, Any]:
    return json.loads((SKILL / "tests/fixtures" / name).read_text(encoding="utf-8"))


def test_clean_empty_output_is_valid_and_ready(contract) -> None:
    report = fixture("clean-empty.json")
    assert contract.validate_report(report) == []
    assert report["verdict"] == "ready"
    assert report["findings"] == []


@pytest.mark.parametrize(
    ("name", "classification", "evidence_status"),
    [
        ("introduced-regression.json", "introduced_regression", "reproduced"),
        ("pre-existing-defect.json", "pre_existing_defect", "reproduced"),
        ("missing-credentials.json", "unsupported_hypothesis", "hypothesis"),
        ("known-vulnerable-pair.json", "introduced_regression", "reproduced"),
        ("known-good-sibling.json", "introduced_regression", "reproduced"),
    ],
)
def test_worked_examples_validate(
    contract, name, classification, evidence_status
) -> None:
    report = fixture(name)
    assert contract.validate_report(report) == []
    assert report["findings"][0]["classification"] == classification
    assert report["findings"][0]["evidence_status"] == evidence_status


def test_both_sides_pass_candidate_is_rejected(contract) -> None:
    report = fixture("rejected-sql-injection.json")
    assert contract.validate_report(report) == []
    assert report["findings"] == []
    assert report["audit"]["rejected_candidates"] == 1


def test_reproduced_evidence_rejects_non_differential_classifications(contract) -> None:
    report = fixture("introduced-regression.json")
    report["findings"][0]["classification"] = "invalid_control"
    report["findings"][0]["target_probe"]["observed"] = "pass"
    report["findings"][0]["target_probe"]["exit_code"] = 0
    assert any(
        "differential classification" in error
        for error in contract.validate_report(report)
    )


def test_fingerprint_is_deterministically_bound_to_finding_identity(contract) -> None:
    report = fixture("introduced-regression.json")
    report["findings"][0]["fingerprint"] = "sha256:" + "0" * 64
    assert any(
        "fingerprint is stale" in error for error in contract.validate_report(report)
    )


def test_proven_evidence_requires_independently_checked_proof(contract) -> None:
    report = fixture("missing-credentials.json")
    finding = report["findings"][0]
    finding["evidence_status"] = "proven"
    finding["classification"] = "proven_defect"
    assert any("proof metadata" in error for error in contract.validate_report(report))


def test_reproduced_requires_executed_differential_control(contract) -> None:
    report = fixture("introduced-regression.json")
    report["findings"][0]["control_probe"]["executed"] = False
    errors = contract.validate_report(report)
    assert any("reproduced" in error and "executed" in error for error in errors)

    report = fixture("introduced-regression.json")
    report["findings"][0]["control_probe"]["environment"] = "different dependencies"
    assert any(
        "same environment" in error for error in contract.validate_report(report)
    )


def test_hypothesis_and_residual_risk_cannot_block(contract) -> None:
    report = fixture("missing-credentials.json")
    report["findings"][0]["blocking"] = True
    assert any(
        "hypothesis" in error and "blocking" in error
        for error in contract.validate_report(report)
    )

    report = fixture("clean-empty.json")
    report["residual_risks"][0]["blocking"] = True
    assert any(
        "residual" in error and "blocking" in error
        for error in contract.validate_report(report)
    )


def test_blocking_requires_priority_evidence_and_confidence_threshold(contract) -> None:
    for field, value in (
        ("priority", "P3"),
        ("evidence_status", "supported"),
        ("confidence", 79),
    ):
        report = fixture("introduced-regression.json")
        report["findings"][0][field] = value
        assert any(
            "blocking policy" in error for error in contract.validate_report(report)
        )


def test_threat_model_and_taxonomy_are_enforced(contract) -> None:
    report = fixture("clean-empty.json")
    report["threat_model"].pop("assets")
    assert any(
        "threat_model missing field: assets" in error
        for error in contract.validate_report(report)
    )

    report = fixture("clean-empty.json")
    report["threat_model"]["taxonomy"][0]["status"] = "not_assessed"
    assert any(
        "not_assessed requires a reason" in error
        for error in contract.validate_report(report)
    )


def test_verdict_is_recomputed_and_stale_verdict_rejected(contract) -> None:
    report = fixture("introduced-regression.json")
    report["verdict"] = "ready"
    assert any("verdict" in error for error in contract.validate_report(report))


def test_unknown_verdict_and_error_without_diagnostics_fail(contract) -> None:
    report = fixture("clean-empty.json")
    report["verdict"] = "maybe"
    assert any("verdict" in error for error in contract.validate_report(report))

    report = fixture("clean-empty.json")
    report["outcome"] = "error"
    report["verdict"] = "error"
    report["diagnostics"] = []
    assert any("diagnostic" in error for error in contract.validate_report(report))


@pytest.mark.parametrize(
    ("outcome", "verdict"),
    [("skipped", "skipped"), ("empty_diff", "empty_diff")],
)
def test_non_review_outcomes_have_exact_verdicts(contract, outcome, verdict) -> None:
    report = fixture("clean-empty.json")
    report["outcome"] = outcome
    report["verdict"] = verdict
    assert contract.validate_report(report) == []


@pytest.mark.parametrize("evidence", ["proven", "supported", "hypothesis"])
def test_non_reproduced_evidence_states_are_distinct(contract, evidence) -> None:
    report = fixture("missing-credentials.json")
    report["findings"][0]["evidence_status"] = evidence
    report["findings"][0]["classification"] = (
        "proven_defect" if evidence == "proven" else "unsupported_hypothesis"
    )
    if evidence == "proven":
        report["findings"][0]["proof"] = {
            "method": "bounded static proof",
            "premise": "the dereference is reachable without a token",
            "independent_check": "separate reviewer checked the call path",
            "artifact_sha256": "sha256:" + "1" * 64,
        }
    assert contract.validate_report(report) == []


def test_changed_target_hash_marks_citations_stale(contract) -> None:
    report = fixture("introduced-regression.json")
    assert (
        contract.stale_citations(report, report["run"]["target"]["content_hash"]) == []
    )
    assert contract.stale_citations(report, "sha256:" + "0" * 64) == ["adv-null-token"]


def test_clean_room_phase_order_and_prompt_injection_are_data(contract) -> None:
    protocol = json.loads(
        (SKILL / "tests/fixtures/clean-room-handoff.json").read_text()
    )
    assert contract.validate_clean_room_handoff(protocol) == []
    assert "prior_findings" not in protocol["phase_a"]["inputs"]
    assert protocol["phase_a"]["target_data"].startswith("IGNORE ALL PREVIOUS")
    assert protocol["phase_b"]["inputs"]["prior_findings"]


def test_self_reset_cannot_claim_independent_corroboration(contract) -> None:
    protocol = json.loads(
        (SKILL / "tests/fixtures/clean-room-handoff.json").read_text()
    )
    protocol["independence_level"] = "self_reset"
    protocol["phase_b"]["corroboration_count"] = 1
    assert any(
        "self_reset" in error
        for error in contract.validate_clean_room_handoff(protocol)
    )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda protocol: protocol["phase_b"]["prior_finding_classifications"][
            0
        ].__setitem__("id", "unrelated-finding"),
        lambda protocol: protocol["phase_b"]["inputs"]["prior_findings"].append(
            {"id": "prior-1"}
        ),
        lambda protocol: protocol["phase_b"]["prior_finding_classifications"].append(
            {
                "id": "prior-1",
                "classification": "independently_corroborated",
            }
        ),
    ],
)
def test_clean_room_requires_unique_exact_prior_finding_id_sets(
    contract, mutation
) -> None:
    protocol = json.loads(
        (SKILL / "tests/fixtures/clean-room-handoff.json").read_text()
    )
    mutation(protocol)
    assert any(
        "unique exact prior-finding ID set" in error
        for error in contract.validate_clean_room_handoff(protocol)
    )


def test_sarif_conversion_is_deterministic_and_preserves_metadata(contract) -> None:
    report = fixture("introduced-regression.json")
    first = contract.to_sarif(report)
    second = contract.to_sarif(report)
    assert first == second
    result = first["runs"][0]["results"][0]
    assert result["ruleId"] == "ADV-NULL-TOKEN"
    assert result["partialFingerprints"]["semanticFingerprint"]
    assert result["locations"][0]["physicalLocation"]["region"]["startLine"] == 12
    assert result["codeFlows"]
    assert first["runs"][0]["tool"]["driver"]["rules"][0]["properties"]["cwe"] == [
        "CWE-476"
    ]


def test_cli_validate_enforces_the_committed_json_schema(tmp_path: Path) -> None:
    malformed = fixture("introduced-regression.json")
    del malformed["findings"][0]["fingerprint"]
    report = tmp_path / "schema-invalid.json"
    report.write_text(json.dumps(malformed))
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "validate", str(report)],
        cwd=SKILL,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 2
    assert "schema violation" in result.stderr


def test_benchmark_metrics_reward_discrimination_not_finding_count(contract) -> None:
    corpus = json.loads((SKILL / "benchmark/corpus.json").read_text())
    good = json.loads((SKILL / "benchmark/baseline-results.json").read_text())
    noisy = json.loads((SKILL / "benchmark/noisy-results.json").read_text())
    good_metrics = contract.evaluate(corpus, good)
    noisy_metrics = contract.evaluate(corpus, noisy)
    for key in (
        "precision",
        "recall",
        "f1",
        "control_false_positive_rate",
        "paired_accuracy",
        "classification_accuracy",
        "evidence_calibration",
        "severity_calibration",
        "citation_accuracy",
        "schema_validity",
        "cost_usd",
        "tokens",
        "latency_seconds",
        "run_to_run_variance",
    ):
        assert key in good_metrics
    assert noisy_metrics["finding_count"] > good_metrics["finding_count"]
    assert noisy_metrics["score"] < good_metrics["score"]
    assert good_metrics["paired_accuracy"] == 1
    assert noisy_metrics["paired_accuracy"] < 1


def test_benchmark_refuses_partial_or_duplicate_results(contract) -> None:
    corpus = json.loads((SKILL / "benchmark/corpus.json").read_text())
    results = json.loads((SKILL / "benchmark/baseline-results.json").read_text())
    results["runs"] = results["runs"][:1]
    with pytest.raises(ValueError, match="cover the frozen corpus exactly"):
        contract.evaluate(corpus, results)

    results = json.loads((SKILL / "benchmark/baseline-results.json").read_text())
    results["runs"].append(results["runs"][0])
    with pytest.raises(ValueError, match="duplicate run IDs"):
        contract.evaluate(corpus, results)


def test_benchmark_refuses_placeholder_provenance(contract) -> None:
    corpus = json.loads((SKILL / "benchmark/corpus.json").read_text())
    results = json.loads((SKILL / "benchmark/baseline-results.json").read_text())
    results["run_manifest"]["skill_hash"] = "nonsense"
    with pytest.raises(ValueError, match="concrete sha256 skill hash"):
        contract.evaluate(corpus, results)


def test_cli_fails_closed_and_converts_sarif(tmp_path: Path) -> None:
    valid = SKILL / "tests/fixtures/introduced-regression.json"
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{", encoding="utf-8")
    sarif = tmp_path / "result.sarif"

    assert (
        subprocess.run(
            [sys.executable, SCRIPT, "validate", valid], check=False
        ).returncode
        == 0
    )
    assert (
        subprocess.run(
            [sys.executable, SCRIPT, "validate", malformed], check=False
        ).returncode
        != 0
    )
    subprocess.run(
        [sys.executable, SCRIPT, "sarif", valid, "--output", sarif], check=True
    )
    assert json.loads(sarif.read_text())["version"] == "2.1.0"


def test_portable_copy_resolves_every_required_runtime_artifact(tmp_path: Path) -> None:
    installed = tmp_path / "adversarial-reviewer"
    shutil.copytree(SKILL, installed)
    result = subprocess.run(
        [
            sys.executable,
            installed / "scripts/adversarial_contract.py",
            "doctor",
            "--skill-root",
            installed,
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "portable contract OK" in result.stdout


@pytest.mark.parametrize("agent", ["codex", "hermes-agent"])
def test_sandboxed_skills_cli_install_is_self_contained(
    tmp_path: Path, agent: str
) -> None:
    result = subprocess.run(
        [
            "npx",
            "--yes",
            "skills",
            "add",
            str(ROOT),
            "--skill",
            "adversarial-reviewer",
            "--agent",
            agent,
            "--copy",
            "--yes",
        ],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    installed = next(tmp_path.rglob("adversarial_contract.py"))
    doctor = subprocess.run(
        [sys.executable, installed, "doctor", "--skill-root", installed.parents[1]],
        text=True,
        capture_output=True,
        check=False,
    )
    assert doctor.returncode == 0, doctor.stdout + doctor.stderr
