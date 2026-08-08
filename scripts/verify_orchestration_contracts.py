#!/usr/bin/env python3
"""Verify repository-local orchestration component and payload contracts."""

from __future__ import annotations

import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Component:
    path: str
    name: str | None = None


COMPONENTS = (
    # review-panel orchestrator, stage contracts, catalog seats, and helpers
    Component("plugins/review-panel/commands/review-panel.md", "review-panel"),
    Component("plugins/review-panel/skills/review-panel/SKILL.md", "review-panel"),
    Component("plugins/review-panel/reviewers/persona-catalog.md"),
    Component("plugins/review-panel/contracts/reviewer-output.md"),
    Component("plugins/review-panel/scripts/review-package"),
    Component("plugins/review-panel/scripts/workspace"),
    *(
        Component(f"plugins/review-panel/skills/review-panel/references/{name}.md")
        for name in (
            "cast-and-spawn",
            "merge-and-validate",
            "fix-and-rereview",
            "converge-and-pipeline",
            "dual-mode-contract",
            "design-lineage",
            "lite-mode",
        )
    ),
    *(
        Component(f"plugins/review-panel/skills/{name}/SKILL.md", name)
        for name in (
            "adversarial-reviewer",
            "ponytail-review",
            "ponytail-audit",
            "design-review",
            "domain-modeling",
            "code-evolution",
            "design-it-twice",
            "tdd",
            "data-steward",
            "taste-review",
            "mental-models-adversarial",
            "mental-models-simplifier",
            "mental-models-systems",
            "mental-models-economics",
        )
    ),
    Component(
        "plugins/review-panel/agents/clean-room-alternative.md",
        "clean-room-alternative",
    ),
    Component(
        "plugins/security-suite/agents/security-engineer.md", "security-engineer"
    ),
    # design-review's complete diagnostic funnel
    *(
        Component(f"plugins/review-panel/skills/{name}/SKILL.md", name)
        for name in (
            "complexity-recognition",
            "module-boundaries",
            "deep-modules",
            "abstraction-quality",
            "information-hiding",
            "general-vs-special",
            "pull-complexity-down",
            "error-design",
            "naming-obviousness",
            "comments-docs",
            "red-flags",
        )
    ),
    # variant-explorer
    Component(
        "plugins/variant-explorer/commands/explore-variants.md", "explore-variants"
    ),
    Component(
        "plugins/variant-explorer/skills/explore-variants/SKILL.md",
        "explore-variants",
    ),
    Component("plugins/variant-explorer/agents/blind-builder.md", "blind-builder"),
    Component("plugins/variant-explorer/agents/variant-judge.md", "variant-judge"),
    Component("skills/acceptance-criteria/SKILL.md", "acceptance-criteria"),
    # mutation-testing
    Component("plugins/mutation-testing/commands/mutation-test.md", "mutation-test"),
    Component(
        "plugins/mutation-testing/skills/mutation-test/SKILL.md", "mutation-test"
    ),
    *(
        Component(f"plugins/mutation-testing/agents/{name}.md", name)
        for name in (
            "test-quality-reviewer",
            "test-saboteur",
            "test-executor",
            "test-auditor",
            "test-refactor-specialist",
        )
    ),
    Component("plugins/mutation-testing/tests/fixtures/contract-handoff.json"),
    # triage-spine
    Component("plugins/triage/skills/triage-spine/SKILL.md", "triage-spine"),
    Component("plugins/triage/skills/detectors/lib-upgrades/SKILL.md", "lib-upgrades"),
    Component("plugins/triage/skills/detectors/prod-errors/SKILL.md", "prod-errors"),
    Component("plugins/triage/skills/triage-spine/references/detector-registry.md"),
    Component("plugins/triage/docs/foundry-recipes.md"),
    Component("skills/pas-pipeline/SKILL.md", "pas-pipeline"),
    # delegate-first runtime adapter
    Component("commands/delegate-first.md", "delegate-first"),
    Component("skills/delegate-first/SKILL.md", "delegate-first"),
)

MARKDOWN_LINK = re.compile(r"\[[^]]*]\(([^)]+)\)")
FRONTMATTER_NAME = re.compile(r"(?m)^name:\s*['\"]?([^'\"\n]+)")
MUTATION_AGENT_NAMES = (
    "test-quality-reviewer",
    "test-saboteur",
    "test-executor",
    "test-auditor",
    "test-refactor-specialist",
)


def component_name(path: Path) -> str | None:
    """Return a Markdown component's frontmatter name, if present."""
    match = FRONTMATTER_NAME.search(path.read_text(encoding="utf-8"))
    return match.group(1).strip() if match else None


def broken_markdown_links(path: Path) -> list[str]:
    """Return missing local Markdown links from one document."""
    missing: list[str] = []
    for raw_target in MARKDOWN_LINK.findall(path.read_text(encoding="utf-8")):
        target = raw_target.split("#", 1)[0].strip().strip("<>")
        if not target or "://" in target or target.startswith(("mailto:", "/")):
            continue
        if not (path.parent / target).resolve().exists():
            missing.append(target)
    return missing


def verify(root: Path = ROOT, *, check_cli: bool = True) -> list[str]:
    """Return all orchestration contract violations under *root*."""
    errors: list[str] = []
    seen: set[str] = set()
    for component in COMPONENTS:
        if component.path in seen:
            continue
        seen.add(component.path)
        path = root / component.path
        if not path.exists():
            errors.append(f"missing component: {component.path}")
            continue
        if component.name is not None:
            actual_name = component_name(path)
            if actual_name != component.name:
                errors.append(
                    f"component name mismatch: {component.path}: "
                    f"expected {component.name!r}, got {actual_name!r}"
                )
        if path.suffix == ".md":
            for target in broken_markdown_links(path):
                errors.append(f"broken link: {component.path} -> {target}")

    mutation_root = root / "plugins/mutation-testing"
    mutation_text = "\n".join(
        path.read_text(encoding="utf-8") for path in mutation_root.rglob("*.md")
    )
    if "scott-cc:test-" in mutation_text:
        errors.append("mutation-testing contains stale scott-cc:test-* agent namespace")
    for name in MUTATION_AGENT_NAMES:
        if f"mutation-testing:{name}" not in mutation_text:
            errors.append(f"mutation-testing agent is never referenced: {name}")

    executor = (mutation_root / "agents/test-executor.md").read_text(encoding="utf-8")
    auditor = (mutation_root / "agents/test-auditor.md").read_text(encoding="utf-8")
    orchestrator = (mutation_root / "agents/test-quality-reviewer.md").read_text(
        encoding="utf-8"
    )
    for field in ('"status"', '"test_results"', '"test_outcomes"', '"failures"'):
        for label, text in (
            ("executor", executor),
            ("auditor", auditor),
            ("orchestrator", orchestrator),
        ):
            if field not in text:
                errors.append(f"mutation {label} contract missing field: {field}")
    for context_field in ("Source File:", "Test File:"):
        if context_field not in orchestrator:
            errors.append(f"auditor dispatch missing context: {context_field}")

    if check_cli:
        for command in ("bd", "claude", "git", "jq", "pas"):
            if shutil.which(command) is None:
                errors.append(f"external command unavailable: {command}")

    return errors


def main() -> int:
    errors = verify()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    unique_components = len({component.path for component in COMPONENTS})
    print(
        "OK: "
        f"{unique_components} orchestration components resolve; "
        "mutation payload schemas and external CLI surface agree"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
