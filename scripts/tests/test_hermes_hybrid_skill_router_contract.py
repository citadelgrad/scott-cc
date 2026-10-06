from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError
from jsonschema.protocols import Validator


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "docs" / "schemas"


def _validator(filename: str) -> Validator:
    schema = json.loads((SCHEMA_DIR / filename).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _metadata() -> dict:
    return {
        "schema_version": "hermes.skill-routing.v1",
        "aliases": ["beads", "bd"],
        "capabilities": ["issue_tracking", "durable_work"],
        "positive_intents": [
            {
                "id": "tracked_work_lifecycle",
                "terms": ["claim issue", "close issue", "next ready work"],
                "capabilities": ["issue_tracking"],
                "required_context": ["repository"],
            }
        ],
        "negative_intents": [
            {
                "id": "unrelated_small_request",
                "terms": ["one-off calculation", "prose rewrite"],
                "effect": "suppress",
            }
        ],
        "conflicts": ["profile/alternative-tracker"],
        "required_context": ["repository"],
        "priority": 20,
        "hard_routes": [
            {
                "id": "explicit_beads_alias",
                "kind": "explicit_invocation",
                "aliases": ["beads", "bd"],
            },
            {
                "id": "repo_issue_tracker",
                "kind": "repository_policy_key",
                "policy_key": "issue_tracker",
            },
        ],
    }


def _receipt() -> dict:
    digest = "a" * 64
    return {
        "schema_version": "hermes.skill-routing-receipt.v1",
        "decision_id": "route_0123456789abcdef",
        "request_ref": f"hmac:{'b' * 64}",
        "router": {"version": "1.0.0", "config_digest": digest},
        "registry": {
            "digest": digest,
            "policy_digest": None,
            "eligible_count": 71,
            "invalid_metadata_count": 0,
        },
        "route_class": "retrieval",
        "outcome": "selected",
        "confidence_millionths": 950000,
        "candidates": [
            {
                "skill_id": "profile/beads",
                "source_tier": "profile",
                "metadata_status": "valid",
                "score_millionths": 950000,
                "evidence_ids": ["tracked_work_lifecycle"],
                "decision": "selected",
            }
        ],
        "selected": [
            {
                "skill_id": "profile/beads",
                "reason_code": "retrieval_accept",
                "load_state": "loaded",
            }
        ],
        "classifier": None,
        "budgets": {
            "candidate_k": 1,
            "selected_count": 1,
            "routing_input_tokens": 0,
            "routing_output_tokens": 0,
            "routing_cost_usd_micros": 0,
            "routing_api_calls": 0,
            "routing_rate_limit_requests": 0,
            "routing_rate_limit_input_tokens": 0,
            "routing_rate_limit_output_tokens": 0,
            "total_latency_ms": 7,
            "within_budget": True,
        },
        "cache": {
            "registry": "hit",
            "query": "miss",
            "classifier": "not_applicable",
        },
        "errors": [],
    }


def _project_policy() -> dict:
    return {
        "schema_version": "hermes.project-skill-routes.v1",
        "rules": [
            {
                "id": "tracked_work_mutation",
                "policy_key": "issue_tracker",
                "when": {
                    "operation_any": [
                        "create_issue",
                        "claim_issue",
                        "update_issue",
                        "close_issue",
                    ]
                },
                "require": ["project/beads"],
            }
        ],
    }


def test_router_schemas_are_valid_draft_2020_12() -> None:
    _validator("hermes-skill-routing-v1.schema.json")
    _validator("hermes-skill-routing-receipt-v1.schema.json")
    _validator("hermes-project-skill-routes-v1.schema.json")


def test_routing_metadata_accepts_complete_v1_contract() -> None:
    _validator("hermes-skill-routing-v1.schema.json").validate(_metadata())


@pytest.mark.parametrize(
    ("mutation", "value"),
    [
        ("unknown_version", "hermes.skill-routing.v2"),
        ("unknown_field", True),
        ("regex_term", "(?s).*"),
        ("unknown_context", "ambient_repository_name"),
    ],
)
def test_routing_metadata_fails_closed_on_unsupported_input(
    mutation: str, value: object
) -> None:
    candidate = _metadata()
    if mutation == "unknown_version":
        candidate["schema_version"] = value
    elif mutation == "unknown_field":
        candidate["instructions"] = value
    elif mutation == "regex_term":
        candidate["positive_intents"][0]["terms"] = [value]
    else:
        candidate["required_context"] = [value]

    with pytest.raises(ValidationError):
        _validator("hermes-skill-routing-v1.schema.json").validate(candidate)


def test_routing_metadata_rejects_unbounded_candidate_data() -> None:
    candidate = _metadata()
    candidate["aliases"] = [f"alias-{index}" for index in range(17)]

    with pytest.raises(ValidationError):
        _validator("hermes-skill-routing-v1.schema.json").validate(candidate)


def test_project_policy_accepts_operation_scoped_required_skill() -> None:
    _validator("hermes-project-skill-routes-v1.schema.json").validate(_project_policy())


@pytest.mark.parametrize(
    "mutation",
    [
        "unknown_version",
        "repository_presence_only",
        "unbounded_required_skills",
        "bare_skill_identity",
    ],
)
def test_project_policy_fails_closed_without_bounded_operation_rule(
    mutation: str,
) -> None:
    policy = _project_policy()
    if mutation == "unknown_version":
        policy["schema_version"] = "hermes.project-skill-routes.v2"
    elif mutation == "repository_presence_only":
        policy["rules"][0]["when"] = {"repository_contains": ".beads"}
    elif mutation == "unbounded_required_skills":
        policy["rules"][0]["require"] = [f"skill-{index}" for index in range(4)]
    else:
        policy["rules"][0]["require"] = ["beads"]

    with pytest.raises(ValidationError):
        _validator("hermes-project-skill-routes-v1.schema.json").validate(policy)


def test_receipt_accepts_content_free_route_evidence() -> None:
    _validator("hermes-skill-routing-receipt-v1.schema.json").validate(_receipt())


def test_receipt_structurally_requires_classifier_usage_fields() -> None:
    receipt = _receipt()
    receipt["classifier"] = {
        "used": True,
        "provider_id": "openai",
        "model_id": "gpt-5-mini",
        "api_call_count": 1,
        "rate_limit_debit": {
            "requests": 1,
            "input_tokens": 100,
            "output_tokens": 10,
        },
        "candidate_count": 2,
        "input_tokens": 100,
        "output_tokens": 10,
        "latency_ms": 200,
        "cost_usd_micros": 500,
        "cache_hit": False,
        "verdict": "select",
        "confidence_millionths": 900000,
    }
    receipt["budgets"]["routing_input_tokens"] = 100
    receipt["budgets"]["routing_output_tokens"] = 10
    receipt["budgets"]["routing_cost_usd_micros"] = 500
    receipt["budgets"]["routing_api_calls"] = 1
    receipt["budgets"]["routing_rate_limit_requests"] = 1
    receipt["budgets"]["routing_rate_limit_input_tokens"] = 100
    receipt["budgets"]["routing_rate_limit_output_tokens"] = 10

    validator = _validator("hermes-skill-routing-receipt-v1.schema.json")
    validator.validate(receipt)

    for required_field in (
        "provider_id",
        "api_call_count",
        "rate_limit_debit",
        "cost_usd_micros",
    ):
        invalid = _receipt()
        invalid["classifier"] = dict(receipt["classifier"])
        del invalid["classifier"][required_field]
        with pytest.raises(ValidationError):
            validator.validate(invalid)

    for required_field in (
        "routing_cost_usd_micros",
        "routing_api_calls",
        "routing_rate_limit_requests",
        "routing_rate_limit_input_tokens",
        "routing_rate_limit_output_tokens",
    ):
        invalid = _receipt()
        del invalid["budgets"][required_field]
        with pytest.raises(ValidationError):
            validator.validate(invalid)


@pytest.mark.parametrize(
    "forbidden_field", ["raw_prompt", "rationale", "skill_body", "path"]
)
def test_receipt_rejects_content_bearing_fields(forbidden_field: str) -> None:
    receipt = _receipt()
    receipt[forbidden_field] = "private content"

    with pytest.raises(ValidationError):
        _validator("hermes-skill-routing-receipt-v1.schema.json").validate(receipt)


def test_receipt_enforces_candidate_and_selection_bounds() -> None:
    validator = _validator("hermes-skill-routing-receipt-v1.schema.json")
    receipt = _receipt()
    receipt["candidates"] = receipt["candidates"] * 13
    with pytest.raises(ValidationError):
        validator.validate(receipt)

    receipt = _receipt()
    receipt["selected"] = receipt["selected"] * 4
    with pytest.raises(ValidationError):
        validator.validate(receipt)
