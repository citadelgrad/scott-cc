#!/usr/bin/env python3
"""Validate adversarial-reviewer reports, export SARIF, and score frozen runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, cast

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "1.0.0"
VERDICTS = {"ready", "ready_with_fixes", "not_ready", "error", "skipped", "empty_diff"}
EVIDENCE = {"reproduced", "proven", "supported", "hypothesis"}
CLASSIFICATIONS = {
    "introduced_regression",
    "pre_existing_defect",
    "invalid_control",
    "non_differential",
    "unsupported_hypothesis",
    "proven_defect",
}
IMPACTS = {"catastrophic", "high", "medium", "low", "unknown"}
LIKELIHOODS = {"certain", "likely", "possible", "unlikely", "unknown"}
PRIORITIES = {"P0", "P1", "P2", "P3", "P4"}
TAXONOMY_STATUSES = {"examined", "applicable", "not_applicable", "not_assessed"}
CITATION_KINDS = {"current_code", "deleted_diff", "prose_design"}
PRIOR_FINDING_RESULTS = {
    "independently_corroborated",
    "contradicted",
    "partially_matched",
    "not_evaluated",
}
THREAT_MODEL_FIELDS = {
    "assets",
    "actors",
    "entry_points",
    "trust_boundaries",
    "privileges",
    "security_objectives",
    "deployment_assumptions",
    "abuse_cases",
    "unknowns",
    "out_of_scope",
    "taxonomy",
}
REQUIRED_ARTIFACTS = (
    "SKILL.md",
    "schemas/adversarial-report-v1.schema.json",
    "references/agent-contract.md",
    "references/clean-room-protocol.md",
    "references/control-backed-findings.md",
    "references/threat-model-taxonomy.md",
    "references/benchmark-methodology.md",
    "scripts/adversarial_contract.py",
    "benchmark/corpus.json",
    "benchmark/baseline-results.json",
)
HEX_SHA256_PREFIX = "sha256:"


def _probe_failed(probe: dict[str, Any]) -> bool:
    return bool(probe.get("executed")) and probe.get("observed") == "fail"


def _probe_passed(probe: dict[str, Any]) -> bool:
    return bool(probe.get("executed")) and probe.get("observed") == "pass"


def _stable_fingerprint(finding: dict[str, Any]) -> str:
    citation = finding.get("citation", {})
    identity = "\x1f".join(
        str(value)
        for value in (
            finding.get("rule_id", ""),
            citation.get("kind", ""),
            citation.get("path", ""),
            citation.get("commit", ""),
            citation.get("start_line", ""),
            citation.get("target_hash", ""),
        )
    )
    return HEX_SHA256_PREFIX + hashlib.sha256(identity.encode()).hexdigest()


def derive_verdict(report: dict[str, Any]) -> str:
    outcome = report.get("outcome", "completed")
    if outcome in {"error", "skipped", "empty_diff"}:
        return outcome
    blocking = [
        finding for finding in report.get("findings", []) if finding.get("blocking")
    ]
    if blocking:
        return "not_ready"
    if report.get("findings"):
        return "ready_with_fixes"
    return "ready"


def validate_report(report: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(report, dict):
        return ["report must be a JSON object"]
    report = cast(dict[str, Any], report)
    required = {
        "schema_version",
        "outcome",
        "verdict",
        "run",
        "scope",
        "threat_model",
        "findings",
        "residual_risks",
        "diagnostics",
        "audit",
    }
    for field in sorted(required - report.keys()):
        errors.append(f"missing required field: {field}")
    if report.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if report.get("verdict") not in VERDICTS:
        errors.append("verdict is unknown")
    if report.get("outcome") == "error" and not report.get("diagnostics"):
        errors.append("error outcome requires at least one diagnostic")
    run = report.get("run")
    if not isinstance(run, dict):
        errors.append("run must be an object")
    else:
        for field in (
            "repository",
            "base_sha",
            "head_sha",
            "reviewed_paths",
            "model",
            "prompt",
            "tools",
            "limitations",
            "target",
        ):
            if field not in run:
                errors.append(f"run missing field: {field}")
        target = run.get("target", {})
        if (
            not isinstance(target, dict)
            or not target.get("content_hash")
            or not target.get("kind")
        ):
            errors.append("run target requires content_hash and kind")
    scope = report.get("scope")
    if not isinstance(scope, dict):
        errors.append("scope must be an object")
    else:
        for mandatory in ("bugs", "security", "hostile_input"):
            if scope.get(mandatory, {}).get("status") != "examined":
                errors.append(f"mandatory scope {mandatory} must be examined")
        existing = scope.get("existing_findings", {})
        if existing.get("status") not in {"examined", "not_applicable"}:
            errors.append("existing_findings scope must be examined or not_applicable")
        if existing.get("status") == "not_applicable" and not existing.get("reason"):
            errors.append("not_applicable existing_findings scope requires a reason")
    threat_model = report.get("threat_model")
    if not isinstance(threat_model, dict):
        errors.append("threat_model must be an object")
    elif threat_model.get("applicability") == "not_applicable":
        if not threat_model.get("reason"):
            errors.append("not_applicable threat_model requires a reason")
    else:
        for field in sorted(THREAT_MODEL_FIELDS - threat_model.keys()):
            errors.append(f"threat_model missing field: {field}")
        taxonomy = threat_model.get("taxonomy", [])
        if not isinstance(taxonomy, list):
            errors.append("threat_model taxonomy must be an array")
        else:
            for index, item in enumerate(taxonomy):
                if not isinstance(item, dict):
                    errors.append(f"taxonomy[{index}] must be an object")
                    continue
                item = cast(dict[str, Any], item)
                if item.get("status") not in TAXONOMY_STATUSES:
                    errors.append(f"taxonomy[{index}] has unknown status")
                elif item.get("status") in {
                    "not_applicable",
                    "not_assessed",
                } and not item.get("reason"):
                    errors.append(
                        f"taxonomy[{index}] {item['status']} requires a reason"
                    )
    findings = report.get("findings", [])
    if not isinstance(findings, list):
        errors.append("findings must be an array")
        findings = []
    for index, finding in enumerate(findings):
        prefix = f"finding[{index}]"
        if not isinstance(finding, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in (
            "id",
            "rule_id",
            "title",
            "impact",
            "likelihood",
            "confidence",
            "priority",
            "evidence_status",
            "classification",
            "blocking",
            "blocking_reason",
            "preconditions",
            "citation",
            "target_probe",
            "control_probe",
        ):
            if field not in finding:
                errors.append(f"{prefix} missing field: {field}")
        evidence = finding.get("evidence_status")
        if evidence not in EVIDENCE:
            errors.append(f"{prefix} has unknown evidence_status")
        if finding.get("classification") not in CLASSIFICATIONS:
            errors.append(f"{prefix} has unknown classification")
        if finding.get("impact") not in IMPACTS:
            errors.append(f"{prefix} has unknown impact")
        if finding.get("likelihood") not in LIKELIHOODS:
            errors.append(f"{prefix} has unknown likelihood")
        if finding.get("priority") not in PRIORITIES:
            errors.append(f"{prefix} has unknown priority")
        confidence = finding.get("confidence")
        if (
            not isinstance(confidence, int)
            or isinstance(confidence, bool)
            or not 0 <= confidence <= 100
        ):
            errors.append(f"{prefix} confidence must be an integer from 0 to 100")
        if evidence == "hypothesis" and finding.get("blocking"):
            errors.append(f"{prefix} hypothesis cannot be blocking")
        if finding.get("blocking") and not (
            finding.get("priority") in {"P0", "P1"}
            and evidence in {"reproduced", "proven"}
            and isinstance(confidence, int)
            and confidence >= 80
        ):
            errors.append(f"{prefix} does not meet the default blocking policy")
        if evidence == "reproduced":
            target = finding.get("target_probe", {})
            control = finding.get("control_probe", {})
            if not (target.get("executed") and control.get("executed")):
                errors.append(
                    f"{prefix} reproduced evidence requires both probes executed"
                )
            classification = finding.get("classification")
            if classification == "introduced_regression" and not (
                _probe_failed(target) and _probe_passed(control)
            ):
                errors.append(
                    f"{prefix} introduced reproduced finding requires target fail/control pass"
                )
            if classification == "pre_existing_defect" and not (
                _probe_failed(target) and _probe_failed(control)
            ):
                errors.append(
                    f"{prefix} pre-existing reproduced finding requires both probes fail"
                )
            if classification not in {"introduced_regression", "pre_existing_defect"}:
                errors.append(
                    f"{prefix} reproduced evidence requires an introduced-regression "
                    "or pre-existing differential classification"
                )
            for field in ("command", "environment"):
                if target.get(field) != control.get(field):
                    errors.append(
                        f"{prefix} reproduced evidence requires the same {field} "
                        "for target and control"
                    )
        if evidence == "proven":
            proof = finding.get("proof")
            if not isinstance(proof, dict) or not all(
                proof.get(field)
                for field in (
                    "method",
                    "premise",
                    "independent_check",
                    "artifact_sha256",
                )
            ):
                errors.append(
                    f"{prefix} proven evidence requires complete independently checked proof metadata"
                )
        citation = finding.get("citation", {})
        if (
            not isinstance(citation, dict)
            or not citation.get("target_hash")
            or not citation.get("kind")
        ):
            errors.append(f"{prefix} citation requires kind and target_hash")
        elif citation.get("kind") not in CITATION_KINDS:
            errors.append(f"{prefix} citation has unknown kind")
        elif citation["kind"] == "current_code" and not all(
            citation.get(field) for field in ("commit", "path", "start_line")
        ):
            errors.append(
                f"{prefix} current-code citation requires commit, path, and start_line"
            )
        elif citation["kind"] == "deleted_diff" and not all(
            citation.get(field)
            for field in ("commit", "path", "diff_side", "hunk", "start_line")
        ):
            errors.append(f"{prefix} deleted-diff citation is incomplete")
        elif citation["kind"] == "prose_design" and not (
            citation.get("path")
            and (citation.get("section") or citation.get("start_line"))
        ):
            errors.append(
                f"{prefix} prose/design citation requires path and section or line"
            )
        if finding.get("fingerprint") != _stable_fingerprint(finding):
            errors.append(
                f"{prefix} fingerprint is stale or not deterministically derived"
            )
    for index, risk in enumerate(report.get("residual_risks", [])):
        if isinstance(risk, dict) and risk.get("blocking"):
            errors.append(f"residual risk[{index}] cannot be blocking")
    expected = derive_verdict(report)
    if report.get("verdict") in VERDICTS and report.get("verdict") != expected:
        errors.append(f"verdict is stale or contradictory: expected {expected}")
    return errors


def stale_citations(report: dict[str, Any], current_hash: str) -> list[str]:
    return [
        finding["id"]
        for finding in report.get("findings", [])
        if finding.get("citation", {}).get("target_hash") != current_hash
    ]


def validate_clean_room_handoff(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return ["clean-room handoff must be an object"]
    payload = cast(dict[str, Any], payload)
    errors: list[str] = []
    level = payload.get("independence_level")
    if level not in {"process_isolated", "prompt_blinded", "self_reset"}:
        errors.append("unknown independence_level")
    phase_a = payload.get("phase_a", {})
    phase_b = payload.get("phase_b", {})
    if "prior_findings" in phase_a.get("inputs", {}):
        errors.append("Phase A must not receive prior_findings")
    if not phase_a.get("frozen_artifact", {}).get("sha256"):
        errors.append("Phase A output must be frozen before Phase B")
    if not phase_b.get("inputs", {}).get("phase_a_artifact_sha256"):
        errors.append("Phase B must identify the frozen Phase A artifact")
    elif phase_b["inputs"]["phase_a_artifact_sha256"] != phase_a.get(
        "frozen_artifact", {}
    ).get("sha256"):
        errors.append("Phase B artifact digest must match frozen Phase A output")
    prior_findings = phase_b.get("inputs", {}).get("prior_findings", [])
    classifications = phase_b.get("prior_finding_classifications", [])
    prior_ids = [item.get("id") for item in prior_findings if isinstance(item, dict)]
    classification_ids = [
        item.get("id") for item in classifications if isinstance(item, dict)
    ]
    if (
        len(prior_ids) != len(prior_findings)
        or len(classification_ids) != len(classifications)
        or any(not item for item in prior_ids + classification_ids)
        or len(prior_ids) != len(set(prior_ids))
        or len(classification_ids) != len(set(classification_ids))
        or set(prior_ids) != set(classification_ids)
    ):
        errors.append("Phase B requires a unique exact prior-finding ID set")
    if any(
        not isinstance(item, dict)
        or item.get("classification") not in PRIOR_FINDING_RESULTS
        for item in classifications
    ):
        errors.append("Phase B has an unknown prior-finding classification")
    if level == "self_reset" and phase_b.get("corroboration_count", 0):
        errors.append("self_reset is non-independent and cannot claim corroboration")
    return errors


def _sarif_level(priority: str) -> str:
    return {
        "P0": "error",
        "P1": "error",
        "P2": "warning",
        "P3": "note",
        "P4": "note",
    }.get(priority, "warning")


def to_sarif(report: dict[str, Any]) -> dict[str, Any]:
    rules: dict[str, dict[str, Any]] = {}
    results: list[dict[str, Any]] = []
    for finding in sorted(report.get("findings", []), key=lambda item: item["id"]):
        rule_id = finding["rule_id"]
        rules[rule_id] = {
            "id": rule_id,
            "name": finding["title"],
            "helpUri": finding.get("help_uri", "https://cwe.mitre.org/"),
            "properties": {"cwe": finding.get("cwe", [])},
        }
        citation = finding["citation"]
        location = {
            "physicalLocation": {
                "artifactLocation": {"uri": citation["path"]},
                "region": {
                    "startLine": citation.get("start_line", 1),
                    "endLine": citation.get("end_line", citation.get("start_line", 1)),
                },
            }
        }
        result: dict[str, Any] = {
            "ruleId": rule_id,
            "level": _sarif_level(finding["priority"]),
            "message": {"text": finding["title"]},
            "locations": [location],
            "partialFingerprints": {"semanticFingerprint": finding["fingerprint"]},
            "properties": {
                "evidence_status": finding["evidence_status"],
                "classification": finding["classification"],
                "suppression": finding.get("suppression", "none"),
            },
        }
        related = finding.get("related_locations", [])
        if related:
            result["codeFlows"] = [
                {
                    "threadFlows": [
                        {
                            "locations": [
                                {
                                    "location": {
                                        "physicalLocation": {
                                            "artifactLocation": {"uri": loc["path"]},
                                            "region": {"startLine": loc["line"]},
                                        }
                                    }
                                }
                                for loc in related
                            ]
                        }
                    ]
                }
            ]
        else:
            result["codeFlows"] = []
        results.append(result)
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "adversarial-reviewer",
                        "version": SCHEMA_VERSION,
                        "rules": [rules[key] for key in sorted(rules)],
                    }
                },
                "results": results,
            }
        ],
    }


def evaluate(corpus: dict[str, Any], results: dict[str, Any]) -> dict[str, float | int]:
    examples = {item["id"]: item for item in corpus["examples"]}
    runs = results["runs"]
    expected_ids = set(examples)
    actual_ids = [run["id"] for run in runs]
    if len(actual_ids) != len(set(actual_ids)):
        raise ValueError("benchmark results contain duplicate run IDs")
    if set(actual_ids) != expected_ids:
        missing = sorted(expected_ids - set(actual_ids))
        unknown = sorted(set(actual_ids) - expected_ids)
        raise ValueError(
            "benchmark results must cover the frozen corpus exactly; "
            f"missing={missing}, unknown={unknown}"
        )
    manifest = results.get("run_manifest", {})
    if manifest.get("corpus_version") != corpus.get("corpus_version"):
        raise ValueError("benchmark corpus version mismatch")
    if manifest.get("budget") != corpus.get("budget"):
        raise ValueError("benchmark run budget differs from the frozen budget")
    skill_hash = manifest.get("skill_hash")
    if (
        not isinstance(skill_hash, str)
        or not skill_hash.startswith(HEX_SHA256_PREFIX)
        or len(skill_hash) != 71
    ):
        raise ValueError("benchmark run requires a concrete sha256 skill hash")
    if manifest.get("model") != corpus.get("budget", {}).get("model"):
        raise ValueError("benchmark model differs from the frozen budget")
    repeat = manifest.get("repeat")
    if not isinstance(repeat, int) or isinstance(repeat, bool) or repeat < 1:
        raise ValueError("benchmark repeat must be a positive integer")
    tp = fp = fn = tn = class_ok = evidence_ok = severity_ok = citation_ok = valid = (
        findings
    ) = 0
    costs: list[float] = []
    latencies: list[float] = []
    tokens = 0
    for run in runs:
        expected = examples[run["id"]]
        predicted = bool(run["finding"])
        actual = bool(expected["positive"])
        tp += int(predicted and actual)
        fp += int(predicted and not actual)
        fn += int(not predicted and actual)
        tn += int(not predicted and not actual)
        findings += int(run.get("finding_count", int(predicted)))

        class_ok += int(run.get("classification") == expected.get("classification"))
        evidence_ok += int(
            run.get("evidence_status") == expected.get("evidence_status")
        )
        severity_ok += int(run.get("severity") == expected.get("severity"))
        citation_ok += int(run.get("citation_valid", False))
        valid += int(run.get("schema_valid", False))
        costs.append(float(run.get("cost_usd", 0)))
        latencies.append(float(run.get("latency_seconds", 0)))
        tokens += int(run.get("tokens", 0))
    n = max(len(runs), 1)
    predictions = {run["id"]: bool(run["finding"]) for run in runs}
    pairs: dict[str, list[dict[str, Any]]] = {}
    for example in examples.values():
        pairs.setdefault(example["pair"], []).append(example)
    scored_pairs = [members for members in pairs.values() if len(members) >= 2]
    paired = sum(
        all(
            predictions.get(member["id"]) == bool(member["positive"])
            for member in members
        )
        for members in scored_pairs
    )
    paired_accuracy = paired / max(len(scored_pairs), 1)
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-12)
    control_fpr = fp / max(fp + tn, 1)
    variance = sum((value - sum(latencies) / n) ** 2 for value in latencies) / n
    score = (
        0.35 * precision
        + 0.25 * recall
        + 0.25 * paired_accuracy
        + 0.15 * (1 - control_fpr)
    )
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "control_false_positive_rate": control_fpr,
        "paired_accuracy": paired_accuracy,
        "classification_accuracy": class_ok / n,
        "evidence_calibration": evidence_ok / n,
        "severity_calibration": severity_ok / n,
        "citation_accuracy": citation_ok / n,
        "schema_validity": valid / n,
        "cost_usd": sum(costs),
        "tokens": tokens,
        "latency_seconds": sum(latencies),
        "run_to_run_variance": variance,
        "finding_count": findings,
        "score": score,
    }


def doctor(skill_root: Path = SKILL_ROOT) -> list[str]:
    errors: list[str] = [
        f"missing portable artifact: {path}"
        for path in REQUIRED_ARTIFACTS
        if not (skill_root / path).is_file()
    ]
    for markdown in skill_root.rglob("*.md"):
        text = markdown.read_text(encoding="utf-8")
        for token in text.split("](")[1:]:
            target = token.split(")", 1)[0].split("#", 1)[0].strip("<>")
            if (
                target
                and "://" not in target
                and not target.startswith(("#", "/"))
                and not (markdown.parent / target).resolve().exists()
            ):
                errors.append(
                    f"broken portable link: {markdown.relative_to(skill_root)} -> {target}"
                )
    try:
        schema = load_json(skill_root / "schemas/adversarial-report-v1.schema.json")
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            errors.append("adversarial report schema must declare JSON Schema 2020-12")
    except (OSError, json.JSONDecodeError, AttributeError) as exc:
        errors.append(f"invalid adversarial report schema: {exc}")
    return errors


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def schema_errors(report: Any, skill_root: Path = SKILL_ROOT) -> list[str]:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return ["JSON Schema validation unavailable: install jsonschema>=4.26"]
    schema = load_json(skill_root / "schemas/adversarial-report-v1.schema.json")
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        return [f"invalid bundled JSON Schema: {exc}"]
    return [
        "schema violation at "
        + ("/".join(str(part) for part in error.absolute_path) or "$")
        + f": {error.message}"
        for error in sorted(
            Draft202012Validator(schema).iter_errors(report),
            key=lambda item: tuple(str(part) for part in item.absolute_path),
        )
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("report", type=Path)
    validate.add_argument("--current-target-hash")
    sarif = sub.add_parser("sarif")
    sarif.add_argument("report", type=Path)
    sarif.add_argument("--output", type=Path)
    evaluate_parser = sub.add_parser("evaluate")
    evaluate_parser.add_argument("results", type=Path)
    evaluate_parser.add_argument(
        "--corpus", type=Path, default=SKILL_ROOT / "benchmark/corpus.json"
    )
    evaluate_parser.add_argument("--output", type=Path)
    doctor_parser = sub.add_parser("doctor")
    doctor_parser.add_argument("--skill-root", type=Path, default=SKILL_ROOT)
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            errors = doctor(args.skill_root)
            if errors:
                print("\n".join(errors), file=sys.stderr)
                return 2
            print("portable contract OK")
            return 0
        report = load_json(args.report if args.command != "evaluate" else args.results)
        if args.command == "validate":
            errors = schema_errors(report) + validate_report(report)
            if args.current_target_hash:
                errors.extend(
                    f"stale citation: {item}"
                    for item in stale_citations(report, args.current_target_hash)
                )
            if errors:
                print("\n".join(errors), file=sys.stderr)
                return 2
            print("valid")
            return 0
        if args.command == "sarif":
            errors = schema_errors(report) + validate_report(report)
            if errors:
                print("\n".join(errors), file=sys.stderr)
                return 2
            payload = to_sarif(report)
        else:
            payload = evaluate(load_json(args.corpus), report)
        rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
        return 0
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"infrastructure error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
