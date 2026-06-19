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


def iter_hook_commands(payload: object) -> list[str]:
    commands: list[str] = []
    if not isinstance(payload, dict):
        fail(f"expected object in {HOOKS_JSON}")
    hooks = payload.get("hooks")  # ty: ignore[invalid-argument-type]
    if not isinstance(hooks, dict):
        fail(f"expected 'hooks' object in {HOOKS_JSON}")
    for event_name, entries in hooks.items():
        if not isinstance(entries, list):
            fail(f"expected list for hooks.{event_name} in {HOOKS_JSON}")
        for entry in entries:
            if not isinstance(entry, dict):
                fail(
                    f"expected object entries under hooks.{event_name} in {HOOKS_JSON}"
                )
            nested = entry.get("hooks")
            if not isinstance(nested, list):
                fail(f"expected list for hooks.{event_name}[].hooks in {HOOKS_JSON}")
            for hook in nested:
                if not isinstance(hook, dict):
                    fail(
                        f"expected object hook under hooks.{event_name} in {HOOKS_JSON}"
                    )
                command = hook.get("command")
                if isinstance(command, str):
                    commands.append(command)
    return commands


def main() -> int:
    plugin = load_json(PLUGIN_JSON)
    marketplace = load_json(MARKETPLACE_JSON)
    hooks = load_json(HOOKS_JSON)

    if not isinstance(plugin, dict):
        fail(f"expected object in {PLUGIN_JSON}")
    if not isinstance(marketplace, dict):
        fail(f"expected object in {MARKETPLACE_JSON}")

    plugin_version = plugin.get("version")
    marketplace_plugins = marketplace.get("plugins")
    if not isinstance(marketplace_plugins, list) or not marketplace_plugins:
        fail(f"expected non-empty plugins array in {MARKETPLACE_JSON}")

    root_plugin = marketplace_plugins[0]
    if not isinstance(root_plugin, dict):
        fail(f"expected first plugin entry to be an object in {MARKETPLACE_JSON}")

    marketplace_version = root_plugin.get("version")
    if plugin_version != marketplace_version:
        fail(
            f"version mismatch: plugin.json has {plugin_version!r}, marketplace.json has {marketplace_version!r}"
        )

    missing_paths: list[str] = []
    referenced_paths: list[str] = []
    for command in iter_hook_commands(hooks):
        for rel_path in COMMAND_PATH_RE.findall(command):
            referenced_paths.append(rel_path)
            if not (ROOT / rel_path).exists():
                missing_paths.append(rel_path)

    if missing_paths:
        unique_missing = ", ".join(sorted(set(missing_paths)))
        fail(f"hooks.json references missing plugin file(s): {unique_missing}")

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
