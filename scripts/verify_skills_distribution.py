#!/usr/bin/env python3
"""Verify the cross-agent skills CLI distribution contract."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "skills.sh.json"
SKILLS_ROOT = ROOT / "skills"
DOC_PATHS = (
    ROOT / "README.md",
    ROOT / "QUICK-START.md",
    ROOT / "docs" / "skills-cli.md",
)
EXPECTED_SCHEMA = "https://skills.sh/schemas/skills.sh.schema.json"
REQUIRED_DOC_TEXT = (
    "npx skills add citadelgrad/scott-cc",
    "codex",
    "hermes-agent",
)


def load_manifest(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as exc:
        return f"invalid JSON: {exc}"


def skill_metadata(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        return {}
    frontmatter = text.split("\n---\n", 1)[0][4:]
    lines = frontmatter.splitlines()
    metadata: dict[str, str] = {}
    for index, line in enumerate(lines):
        if not line.startswith(("name:", "description:")):
            continue
        key, value = line.split(":", 1)
        value = value.strip().strip("\"'")
        if value in {">", ">-", "|", "|-"}:
            continuation: list[str] = []
            for next_line in lines[index + 1 :]:
                if next_line and not next_line[0].isspace():
                    break
                if next_line.strip():
                    continuation.append(next_line.strip())
            value = " ".join(continuation)
        metadata[key] = value
    return metadata


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    manifest_path = root / "skills.sh.json"
    skills_root = root / "skills"
    doc_paths = (
        root / "README.md",
        root / "QUICK-START.md",
        root / "docs" / "skills-cli.md",
    )
    manifest = load_manifest(manifest_path)

    if manifest is None:
        return ["missing skills.sh.json"]
    if isinstance(manifest, str):
        return [f"skills.sh.json {manifest}"]
    if not isinstance(manifest, dict):
        return ["skills.sh.json must contain a JSON object"]
    manifest = cast(dict[str, object], manifest)
    if manifest.get("$schema") != EXPECTED_SCHEMA:
        errors.append(f"skills.sh.json must use schema {EXPECTED_SCHEMA}")

    skill_dirs = (
        {path.name: path for path in skills_root.iterdir() if path.is_dir()}
        if skills_root.is_dir()
        else {}
    )
    if not skill_dirs:
        errors.append("skills/ must contain at least one skill directory")

    for skill_name, skill_dir in sorted(skill_dirs.items()):
        skill_path = skill_dir / "SKILL.md"
        if not skill_path.is_file():
            errors.append(f"skills/{skill_name} is missing SKILL.md")
            continue
        metadata = skill_metadata(skill_path)
        if metadata.get("name") != skill_name:
            errors.append(f"skills/{skill_name}/SKILL.md name must be {skill_name!r}")
        if not metadata.get("description"):
            errors.append(f"skills/{skill_name}/SKILL.md is missing a description")

    grouped: list[str] = []
    groupings = manifest.get("groupings")
    if not isinstance(groupings, list):
        errors.append("skills.sh.json groupings must be a list")
    else:
        for index, grouping in enumerate(groupings):
            if not isinstance(grouping, dict):
                errors.append(f"skills.sh.json groupings[{index}] must be an object")
                continue
            grouping = cast(dict[str, object], grouping)
            names = grouping.get("skills")
            if not isinstance(names, list) or not all(
                isinstance(name, str) for name in names
            ):
                errors.append(
                    f"skills.sh.json groupings[{index}].skills must be a string list"
                )
                continue
            grouped.extend(cast(list[str], names))

    duplicates = sorted({name for name in grouped if grouped.count(name) > 1})
    if duplicates:
        errors.append(
            f"skills.sh.json groups duplicate skills: {', '.join(duplicates)}"
        )
    unknown = sorted(set(grouped) - set(skill_dirs))
    if unknown:
        errors.append(
            f"skills.sh.json groups unknown root skills: {', '.join(unknown)}"
        )
    ungrouped = sorted(set(skill_dirs) - set(grouped))
    if ungrouped:
        errors.append(
            f"skills.sh.json leaves root skills ungrouped: {', '.join(ungrouped)}"
        )

    for doc_path in doc_paths:
        if not doc_path.is_file():
            errors.append(
                f"missing installation documentation: {doc_path.relative_to(root)}"
            )
            continue
        text = doc_path.read_text(encoding="utf-8")
        missing = [value for value in REQUIRED_DOC_TEXT if value not in text]
        if missing:
            errors.append(
                f"{doc_path.relative_to(root)} is missing: {', '.join(missing)}"
            )

    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    skill_count = sum(1 for path in SKILLS_ROOT.iterdir() if path.is_dir())
    print(
        f"OK: skills CLI distribution contract is valid ({skill_count} grouped root skills)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
