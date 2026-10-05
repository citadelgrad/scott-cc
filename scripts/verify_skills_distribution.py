#!/usr/bin/env python3
"""Verify the cross-agent skills CLI distribution contract."""

from __future__ import annotations

import argparse
import json
import hashlib
import re
import sys
from pathlib import Path
from typing import cast
from urllib.parse import unquote, urlsplit

import yaml


class UniqueKeyLoader(yaml.SafeLoader):
    """YAML parsing must agree with the installer's duplicate-key rejection."""

    def construct_mapping(self, node, deep=False):
        keys = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str) or key in keys:
                raise ValueError(f"duplicate or non-string YAML key: {key!r}")
            keys.add(key)
        return super().construct_mapping(node, deep=deep)


def read_skill(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise ValueError("missing YAML frontmatter delimiters")
    header, body = text[4:].split("\n---\n", 1)
    # SafeLoader subclass only rejects keys; it never enables Python constructors.
    metadata = yaml.load(header, Loader=UniqueKeyLoader)
    if not isinstance(metadata, dict):
        raise ValueError("frontmatter must be a mapping")
    return metadata, body


def package_metadata_errors(path: Path, display: str | None = None) -> list[str]:
    label = display or str(path)
    try:
        metadata, body = read_skill(path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return [f"{label}: invalid frontmatter: {exc}"]
    errors = []
    name = metadata.get("name")
    if (
        not isinstance(name, str)
        or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)
        or len(name) > 64
    ):
        errors.append(
            f"{label}: name must be a lowercase kebab-case string of 1..64 characters"
        )
    if name != path.parent.name:
        errors.append(f"{label} name must be {path.parent.name!r}")
    description = metadata.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append(f"{label} is missing a description")
    elif len(description) > 1024:
        errors.append(f"{label}: description exceeds 1024 characters")
    if not body.strip():
        errors.append(f"{label}: missing or empty procedure body")
    return errors


def package_asset_errors(package: Path, *, boundary: Path | None = None) -> list[str]:
    """Follow literal Markdown resources from the installed entry, within one package.

    Fenced examples aren't dependencies. Remote documentation is informational.
    Symlinks are rejected before the real installer can dereference them.
    """
    errors = []
    root = (boundary or package).resolve()
    for path in package.rglob("*"):
        if path.is_symlink():
            errors.append(f"package symlink is not allowed: {path}")
    pending = [package / "SKILL.md"]
    seen = set()
    while pending:
        document = pending.pop()
        if document in seen or document.is_symlink():
            continue
        seen.add(document)
        if not document.is_file():
            errors.append(f"missing package asset: {document}")
            continue
        text = re.sub(
            r"(?ms)^ *(`{3,}|~{3,})[^\n]*\n.*?^ *\1[^\n]*$",
            "",
            document.read_text(encoding="utf-8"),
        )
        inline = re.findall(r"!?\[[^\]\n]*\]\((<[^>]+>|[^)\s]+)(?:\s+[^)]*)?\)", text)
        references = re.findall(r"(?m)^ *\[[^\]]+\]:\s*(<[^>]+>|\S+)", text)
        for raw in inline + references:
            value = raw.strip("<>")
            url = urlsplit(value)
            if url.scheme in {"https", "http", "mailto"} or not url.path:
                continue
            target = unquote(url.path)
            resolved = (document.parent / target).resolve()
            if (
                url.scheme
                or Path(target).is_absolute()
                or not resolved.is_relative_to(root)
            ):
                errors.append(f"package link escapes root: {document} -> {value}")
            elif not resolved.exists():
                errors.append(f"missing package asset: {document} -> {value}")
            elif resolved.suffix.lower() == ".md":
                pending.append(resolved)
    return errors


def skill_paths(root: Path) -> list[Path]:
    return sorted(
        path
        for base in (root / "skills", root / "plugins")
        if base.is_dir()
        for path in base.rglob("SKILL.md")
    )


# Workflow runtime requirements do not excuse missing package-local references.
PLUGIN_WORKFLOWS = {"triage-spine"}
SOURCE_WORKFLOWS = {"catalog-steward"}


def asset_boundary(root: Path, entry: Path) -> Path:
    return entry.parent


def inventory(root: Path) -> dict:
    paths = skill_paths(root) + sorted((root / ".agents/skills").rglob("SKILL.md"))
    packages = []
    for path in paths:
        relative = path.relative_to(root).as_posix()
        name = skill_metadata(path).get("name")
        scope = "consult package prerequisites; optional integrations are not bundled"
        if name in PLUGIN_WORKFLOWS:
            scope = "full workflow requires complete plugin and its external runtime"
        elif name in SOURCE_WORKFLOWS:
            scope = "source-repository maintenance; not a standalone workflow"
        if relative.startswith(".agents/"):
            scope = "repository-local development skill; excluded from published package inventory"
        row = {
            "path": relative,
            "name": name,
            "workflow_scope": scope,
            "runtime_certified": False,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        if relative == "skills/beads/SKILL.md":
            row["release_status"] = "REJECT: advanced swarm/runtime candidate"
        packages.append(row)
    return {
        "schema_version": 1,
        "installer": "skills@1.7.0",
        "packages": packages,
        "validation_errors": validate(root),
    }


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "skills.sh.json"
SKILLS_ROOT = ROOT / "skills"
AUTHORSHIP_PATH = ROOT / "SKILL-AUTHORSHIP.md"
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


def tree_hash(path: Path) -> str:
    digest = hashlib.sha256()
    for file_path in sorted(item for item in path.rglob("*") if item.is_file()):
        if "__pycache__" in file_path.parts or file_path.suffix == ".pyc":
            continue
        digest.update(file_path.relative_to(path).as_posix().encode() + b"\0")
        digest.update(hashlib.sha256(file_path.read_bytes()).digest())
    return digest.hexdigest()


def skill_metadata(path: Path) -> dict:
    try:
        return read_skill(path)[0]
    except (OSError, ValueError, yaml.YAMLError):
        return {}


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    manifest_path = root / "skills.sh.json"
    skills_root = root / "skills"
    authorship_path = root / "SKILL-AUTHORSHIP.md"
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

    installable_skill_paths = {
        path.relative_to(root).as_posix()
        for base in (root / "skills", root / "plugins")
        if base.is_dir()
        for path in base.rglob("SKILL.md")
    }

    if not authorship_path.is_file():
        errors.append("missing SKILL-AUTHORSHIP.md")
    else:
        authorship = authorship_path.read_text(encoding="utf-8")
        documented_paths = re.findall(
            r"^- `((?:skills|plugins)/[^`]+/SKILL\.md)`$",
            authorship,
            flags=re.MULTILINE,
        )
        duplicates = sorted(
            path for path in set(documented_paths) if documented_paths.count(path) > 1
        )
        if duplicates:
            errors.append(
                "SKILL-AUTHORSHIP.md duplicates skill paths: " + ", ".join(duplicates)
            )
        missing_authorship = sorted(installable_skill_paths - set(documented_paths))
        if missing_authorship:
            errors.append(
                "SKILL-AUTHORSHIP.md omits installable skills: "
                + ", ".join(missing_authorship)
            )
        stale_authorship = sorted(set(documented_paths) - installable_skill_paths)
        if stale_authorship:
            errors.append(
                "SKILL-AUTHORSHIP.md lists unknown skills: "
                + ", ".join(stale_authorship)
            )
        if "Scott Nixon" not in authorship:
            errors.append("SKILL-AUTHORSHIP.md must credit Scott Nixon")
        if "plugins/review-panel/CREDITS.md" not in authorship:
            errors.append(
                "SKILL-AUTHORSHIP.md must preserve the review-panel credits link"
            )

    for skill_name, skill_dir in sorted(skill_dirs.items()):
        if not (skill_dir / "SKILL.md").is_file():
            errors.append(f"skills/{skill_name} is missing SKILL.md")
    for path in skill_paths(root):
        errors.extend(package_metadata_errors(path, path.relative_to(root).as_posix()))
        errors.extend(
            package_asset_errors(path.parent, boundary=asset_boundary(root, path))
        )

    for path in (root / ".agents/skills").rglob("SKILL.md"):
        errors.extend(package_metadata_errors(path, path.relative_to(root).as_posix()))
        errors.extend(package_asset_errors(path.parent))
        if path.relative_to(root).as_posix() != ".agents/skills/beads/SKILL.md":
            errors.append(
                f"unclassified agent-local discovery entry: {path.relative_to(root)}"
            )

    identities: dict[str, list[Path]] = {}
    for path in skill_paths(root):
        name = skill_metadata(path).get("name")
        if isinstance(name, str):
            identities.setdefault(name, []).append(path.parent)
    for name, paths in identities.items():
        if len(paths) > 1 and len({tree_hash(path) for path in paths}) > 1:
            errors.append(
                f"duplicate install name {name!r} has unequal payloads: "
                + ", ".join(str(path.relative_to(root)) for path in paths)
            )

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

    plugin_adversarial = root / "plugins/review-panel/skills/adversarial-reviewer"
    portable_adversarial = root / "skills/adversarial-reviewer"
    if plugin_adversarial.is_dir() and portable_adversarial.is_dir():
        if tree_hash(plugin_adversarial) != tree_hash(portable_adversarial):
            errors.append(
                "portable adversarial-reviewer drift: skills/adversarial-reviewer "
                "must match the review-panel plugin source"
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory-json", action="store_true")
    args = parser.parse_args()
    if args.inventory_json:
        data = inventory(ROOT)
        print(json.dumps(data, indent=2))
        return int(bool(data["validation_errors"]))
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
