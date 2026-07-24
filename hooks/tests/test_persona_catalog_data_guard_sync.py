"""Cross-file consistency check: persona-catalog.md's Data Steward glob
snapshot must match hooks/data_layer_guard.py's DEFAULT_GLOBS exactly.

Why this test exists (scc-ncs.14): the data-steward review seat's cast-when
trigger pattern list in persona-catalog.md used to be hand-maintained prose,
completely independent of the actual glob source hooks/data_layer_guard.py
reads (DEFAULT_GLOBS, optionally overridden by a repo-root .data-guard.json).
A human customizing the interactive hook's defaults could silently narrow the
unattended-run backstop's documented coverage, since the two lists could
drift apart with nothing to notice or flag it.

This test parses the single source of truth (DEFAULT_GLOBS) and the
convenience snapshot block persona-catalog.md embeds between the
`DATA-STEWARD-GLOBS-SNAPSHOT` markers, and fails loudly if they diverge.
A comment saying "keep in sync" is not enough — this makes it mechanical.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parents[1]
HOOK_PATH = HOOKS_DIR / "data_layer_guard.py"
PERSONA_CATALOG_PATH = (
    HOOKS_DIR.parents[0]
    / "plugins"
    / "review-panel"
    / "reviewers"
    / "persona-catalog.md"
)

SNAPSHOT_START = "<!-- DATA-STEWARD-GLOBS-SNAPSHOT:START -->"
SNAPSHOT_END = "<!-- DATA-STEWARD-GLOBS-SNAPSHOT:END -->"


def _load_default_globs() -> list[str]:
    """Import hooks/data_layer_guard.py by path and return its DEFAULT_GLOBS.

    hooks/ isn't a package, so we load the module directly from its file path
    rather than importing it normally.
    """
    spec = importlib.util.spec_from_file_location("data_layer_guard", HOOK_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return list(module.DEFAULT_GLOBS)


def _extract_snapshot_globs() -> list[str]:
    """Parse the fenced code block between the snapshot markers in
    persona-catalog.md and return its lines as a list of glob strings.
    """
    text = PERSONA_CATALOG_PATH.read_text()

    start_idx = text.find(SNAPSHOT_START)
    end_idx = text.find(SNAPSHOT_END)
    assert start_idx != -1 and end_idx != -1 and start_idx < end_idx, (
        "persona-catalog.md is missing the "
        f"{SNAPSHOT_START} ... {SNAPSHOT_END} snapshot block for the Data "
        "Steward seat's cast-when trigger patterns. This block is required "
        "so this test can validate it against hooks/data_layer_guard.py's "
        "DEFAULT_GLOBS (see scc-ncs.14)."
    )

    between = text[start_idx:end_idx]
    fence_match = re.search(r"```\n(.*?)```", between, re.DOTALL)
    assert fence_match is not None, (
        "Could not find a fenced code block inside the "
        "DATA-STEWARD-GLOBS-SNAPSHOT markers in persona-catalog.md."
    )

    lines = [line.strip() for line in fence_match.group(1).splitlines()]
    return [line for line in lines if line]


def test_persona_catalog_snapshot_matches_default_globs():
    default_globs = _load_default_globs()
    snapshot_globs = _extract_snapshot_globs()

    assert snapshot_globs == default_globs, (
        "plugins/review-panel/reviewers/persona-catalog.md's Data Steward "
        "glob snapshot has drifted from hooks/data_layer_guard.py's "
        "DEFAULT_GLOBS (the canonical source). Update the snapshot block "
        "between the DATA-STEWARD-GLOBS-SNAPSHOT markers in "
        "persona-catalog.md to match DEFAULT_GLOBS exactly.\n"
        f"DEFAULT_GLOBS:      {default_globs}\n"
        f"persona-catalog.md: {snapshot_globs}"
    )
