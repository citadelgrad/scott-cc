#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, NoReturn

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_JSON = ROOT / ".claude-plugin" / "plugin.json"
MARKETPLACE_JSON = ROOT / ".claude-plugin" / "marketplace.json"
HOOKS_JSON = ROOT / "hooks" / "hooks.json"

COMMAND_PATH_RE = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\s\"']+)")


def fail(message: str) -> NoReturn:
    print(f"FAIL: {message}")
    sys.exit(1)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        fail(f"missing required file: {path}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path}: {exc}")


def iter_hook_commands(payload: object, hooks_json: Path) -> list[str]:
    commands: list[str] = []
    if not isinstance(payload, dict):
        fail(f"expected object in {hooks_json}")
    hooks = payload.get("hooks")  # ty: ignore[invalid-argument-type]
    if not isinstance(hooks, dict):
        fail(f"expected 'hooks' object in {hooks_json}")
    for event_name, entries in hooks.items():
        if not isinstance(entries, list):
            fail(f"expected list for hooks.{event_name} in {hooks_json}")
        for entry in entries:
            if not isinstance(entry, dict):
                fail(
                    f"expected object entries under hooks.{event_name} in {hooks_json}"
                )
            nested = entry.get("hooks")
            if not isinstance(nested, list):
                fail(f"expected list for hooks.{event_name}[].hooks in {hooks_json}")
            for hook in nested:
                if not isinstance(hook, dict):
                    fail(
                        f"expected object hook under hooks.{event_name} in {hooks_json}"
                    )
                command = hook.get("command")
                if isinstance(command, str):
                    commands.append(command)
    return commands


def empty_skill_bodies(root: Path) -> list[Path]:
    """Return skill files whose YAML frontmatter has no procedure body."""
    empty: list[Path] = []
    skill_roots = [root / "skills", root / "plugins"]
    for skill_root in skill_roots:
        if not skill_root.exists():
            continue
        for skill_path in skill_root.rglob("SKILL.md"):
            lines = skill_path.read_text(encoding="utf-8").splitlines()
            if not lines or lines[0] != "---":
                empty.append(skill_path)
                continue
            try:
                frontmatter_end = lines.index("---", 1)
            except ValueError:
                empty.append(skill_path)
                continue
            if not any(line.strip() for line in lines[frontmatter_end + 1 :]):
                empty.append(skill_path)
    return empty


def main() -> int:
    plugin = load_json(PLUGIN_JSON)
    marketplace = load_json(MARKETPLACE_JSON)
    hooks = load_json(HOOKS_JSON)

    if not isinstance(plugin, dict):
        fail(f"expected object in {PLUGIN_JSON}")
    if not isinstance(marketplace, dict):
        fail(f"expected object in {MARKETPLACE_JSON}")

    marketplace_plugins = marketplace.get("plugins")
    if not isinstance(marketplace_plugins, list) or not marketplace_plugins:
        fail(f"expected non-empty plugins array in {MARKETPLACE_JSON}")

    root_plugin = marketplace_plugins[0]
    if not isinstance(root_plugin, dict):
        fail(f"expected first plugin entry to be an object in {MARKETPLACE_JSON}")

    for field in ("name", "description", "version"):
        plugin_value = plugin.get(field)
        marketplace_value = root_plugin.get(field)
        if plugin_value != marketplace_value:
            fail(
                f"root {field} mismatch: plugin.json has {plugin_value!r}, "
                f"marketplace.json has {marketplace_value!r}"
            )

    hook_manifests = [(ROOT, HOOKS_JSON, hooks)]
    for entry in marketplace_plugins[1:]:
        if not isinstance(entry, dict):
            fail(f"expected plugin entry to be an object in {MARKETPLACE_JSON}")
        name = entry.get("name")
        source = entry.get("source")
        if not isinstance(source, str):
            fail(f"expected string 'source' for plugin {name!r} in {MARKETPLACE_JSON}")
        sub_plugin_json = ROOT / source / ".claude-plugin" / "plugin.json"
        sub_plugin = load_json(sub_plugin_json)
        if not isinstance(sub_plugin, dict):
            fail(f"expected object in {sub_plugin_json}")
        sub_name = sub_plugin.get("name")
        sub_version = sub_plugin.get("version")
        if sub_name != name:
            fail(
                f"name mismatch: {sub_plugin_json} has {sub_name!r}, marketplace.json has {name!r}"
            )
        marketplace_sub_version = entry.get("version")
        if sub_version != marketplace_sub_version:
            fail(
                f"version mismatch: {sub_plugin_json} has {sub_version!r}, marketplace.json has {marketplace_sub_version!r}"
            )

        sub_plugin_root = ROOT / source
        sub_hooks_json = sub_plugin_root / "hooks" / "hooks.json"
        if sub_hooks_json.exists():
            hook_manifests.append(
                (sub_plugin_root, sub_hooks_json, load_json(sub_hooks_json))
            )

    missing_paths: list[str] = []
    referenced_paths: list[str] = []
    for plugin_root, hooks_json, hook_payload in hook_manifests:
        for command in iter_hook_commands(hook_payload, hooks_json):
            for rel_path in COMMAND_PATH_RE.findall(command):
                display_path = str((plugin_root / rel_path).relative_to(ROOT))
                referenced_paths.append(display_path)
                if not (plugin_root / rel_path).exists():
                    missing_paths.append(display_path)

    if missing_paths:
        unique_missing = ", ".join(sorted(set(missing_paths)))
        fail(f"missing hook file reference(s): {unique_missing}")

    empty_skills = empty_skill_bodies(ROOT)
    if empty_skills:
        display_paths = ", ".join(
            str(path.relative_to(ROOT)) for path in sorted(empty_skills)
        )
        fail(f"skill files have missing or empty procedure bodies: {display_paths}")

    if not referenced_paths:
        print(
            "OK: plugin manifests parse cleanly; no CLAUDE_PLUGIN_ROOT hook file references found"
        )
    else:
        refs = ", ".join(sorted(set(referenced_paths)))
        print(
            "OK: plugin manifests parse cleanly; versions match; hook file references exist: "
            + refs
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
