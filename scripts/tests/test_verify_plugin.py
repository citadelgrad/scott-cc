"""Regression tests for the root plugin/marketplace contract."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "verify_plugin.py"
spec = importlib.util.spec_from_file_location("verify_plugin", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
verify_plugin = importlib.util.module_from_spec(spec)
sys.modules["verify_plugin"] = verify_plugin
spec.loader.exec_module(verify_plugin)


def write_contract(tmp_path: Path, *, marketplace_description: str) -> None:
    plugin = {
        "name": "scott-cc",
        "description": "accurate inventory",
        "version": "5.1.0",
    }
    marketplace = {
        "plugins": [
            {
                **plugin,
                "source": "./",
                "description": marketplace_description,
            }
        ]
    }
    hooks = {"hooks": {}}

    plugin_path = tmp_path / "plugin.json"
    marketplace_path = tmp_path / "marketplace.json"
    hooks_path = tmp_path / "hooks.json"
    plugin_path.write_text(json.dumps(plugin))
    marketplace_path.write_text(json.dumps(marketplace))
    hooks_path.write_text(json.dumps(hooks))

    setattr(verify_plugin, "ROOT", tmp_path)
    setattr(verify_plugin, "PLUGIN_JSON", plugin_path)
    setattr(verify_plugin, "MARKETPLACE_JSON", marketplace_path)
    setattr(verify_plugin, "HOOKS_JSON", hooks_path)


def test_matching_root_metadata_passes(tmp_path: Path) -> None:
    write_contract(tmp_path, marketplace_description="accurate inventory")

    assert verify_plugin.main() == 0


def test_empty_skill_bodies_detects_frontmatter_only_skill(tmp_path: Path) -> None:
    empty_skill = tmp_path / "plugins" / "example" / "skills" / "empty" / "SKILL.md"
    empty_skill.parent.mkdir(parents=True)
    empty_skill.write_text("---\nname: empty\ndescription: Empty by mistake\n---\n")

    healthy_skill = tmp_path / "skills" / "healthy" / "SKILL.md"
    healthy_skill.parent.mkdir(parents=True)
    healthy_skill.write_text(
        "---\nname: healthy\ndescription: Has a procedure\n---\n\n# Procedure\n"
    )

    assert verify_plugin.empty_skill_bodies(tmp_path) == [empty_skill]


def test_root_description_drift_fails(tmp_path: Path) -> None:
    write_contract(tmp_path, marketplace_description="stale inventory")

    with pytest.raises(SystemExit) as exc_info:
        verify_plugin.main()

    assert exc_info.value.code == 1


def test_subplugin_hook_missing_target_fails(tmp_path: Path) -> None:
    write_contract(tmp_path, marketplace_description="accurate inventory")
    marketplace = json.loads(verify_plugin.MARKETPLACE_JSON.read_text())
    marketplace["plugins"].append(
        {
            "name": "security-suite",
            "source": "plugins/security-suite",
            "version": "1.0.0",
        }
    )
    verify_plugin.MARKETPLACE_JSON.write_text(json.dumps(marketplace))

    plugin_root = tmp_path / "plugins" / "security-suite"
    manifest_dir = plugin_root / ".claude-plugin"
    hooks_dir = plugin_root / "hooks"
    manifest_dir.mkdir(parents=True)
    hooks_dir.mkdir()
    (manifest_dir / "plugin.json").write_text(
        json.dumps({"name": "security-suite", "version": "1.0.0"})
    )
    (hooks_dir / "hooks.json").write_text(
        json.dumps(
            {
                "hooks": {
                    "PreToolUse": [
                        {
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/missing.py",
                                }
                            ]
                        }
                    ]
                }
            }
        )
    )

    with pytest.raises(SystemExit) as exc_info:
        verify_plugin.main()

    assert exc_info.value.code == 1
