"""Regression tests for repository-local orchestration contracts."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "verify_orchestration_contracts.py"
spec = importlib.util.spec_from_file_location(
    "verify_orchestration_contracts", SCRIPT_PATH
)
assert spec is not None and spec.loader is not None
contracts = importlib.util.module_from_spec(spec)
sys.modules["verify_orchestration_contracts"] = contracts
spec.loader.exec_module(contracts)


def test_repository_orchestration_contracts_resolve() -> None:
    assert contracts.verify(check_cli=False) == []


def test_broken_markdown_links_reports_only_missing_local_targets(
    tmp_path: Path,
) -> None:
    existing = tmp_path / "existing.md"
    existing.write_text("# Existing\n")
    source = tmp_path / "source.md"
    source.write_text(
        "[ok](existing.md) [anchor](#section) "
        "[web](https://example.com) [missing](missing.md)"
    )

    assert contracts.broken_markdown_links(source) == ["missing.md"]


def test_component_name_reads_frontmatter(tmp_path: Path) -> None:
    component = tmp_path / "agent.md"
    component.write_text("---\nname: example-agent\n---\n")

    assert contracts.component_name(component) == "example-agent"


def test_mutation_handoff_dry_run_preserves_payload_contracts() -> None:
    fixture_path = (
        contracts.ROOT / "plugins/mutation-testing/tests/fixtures/contract-handoff.json"
    )
    fixture = json.loads(fixture_path.read_text())
    handoffs = fixture["handoffs"]

    assert [handoff["subagent_type"] for handoff in handoffs] == [
        "mutation-testing:test-saboteur",
        "mutation-testing:test-executor",
        "mutation-testing:test-executor",
        "mutation-testing:test-auditor",
        "mutation-testing:test-refactor-specialist",
    ]

    completed = handoffs[1]["output"]
    assert completed["status"] == "COMPLETED"
    assert completed["test_results"]["failed"] == 1
    assert set(completed["test_outcomes"].values()) == {"passed", "failed"}

    auditor = handoffs[3]
    assert auditor["input"]["source_file"] == fixture["request"]["target"]
    assert auditor["input"]["test_file"] == fixture["request"]["test_file"]
    audit = auditor["output"]
    assert audit["mutations_total"] == 2
    assert audit["mutations_evaluated"] == 1
    assert audit["mutation_score"] == (
        audit["mutations_caught"] / audit["mutations_evaluated"]
    )
    assert audit["execution_gaps"] == [
        {
            "mutation_id": "mut-002",
            "status": "INVALID_MUTATION",
            "reason": "SyntaxError: invalid syntax",
        }
    ]
