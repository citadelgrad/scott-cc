from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PAS_SKILL = ROOT / "skills" / "pas-pipeline"
ASSET = PAS_SKILL / "assets" / "codex-pipeline.dot"
REFERENCE = PAS_SKILL / "references" / "provider-and-dot-authoring.md"


def test_pas_skill_documents_provider_and_model_detection() -> None:
    skill = (PAS_SKILL / "SKILL.md").read_text(encoding="utf-8")
    reference = REFERENCE.read_text(encoding="utf-8")

    assert "codex login status" in reference
    assert "codex debug models" in reference
    assert 'llm_provider="codex"' in skill
    assert 'llm_provider="hermes"' in skill
    assert "Omit `model` and `llm_model` by default" in skill


def test_codex_asset_has_consistent_conditional_labels() -> None:
    dot = ASSET.read_text(encoding="utf-8")

    assert 'llm_provider="codex"' in dot
    assert not re.search(r"^\s*(?:model|llm_model)\s*=", dot, re.MULTILINE)
    assert dot.count('shape="Mdiamond"') == 1
    assert dot.count('shape="Msquare"') == 1

    for label in ("PASS", "FAIL"):
        assert f'label="{label}"' in dot
        assert f'condition="preferred_label={label}"' in dot
        assert re.search(rf"\b{label}\b", dot)


@pytest.mark.skipif(shutil.which("pas") is None, reason="PAS CLI is not installed")
def test_codex_asset_passes_pas_validation() -> None:
    result = subprocess.run(
        ["pas", "validate", str(ASSET)],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Pipeline is valid" in result.stdout
