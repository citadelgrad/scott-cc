"""Protect PR #8's frozen source bytes while consolidating current guidance."""

from pathlib import Path
import hashlib

import pytest

ROOT = Path(__file__).resolve().parents[2]
PLANS = ROOT / "docs/plans/2026-09-02-hermes-beads-skill"
# SHA256 of original c0af1a13fbad82b887869f3f63b16ef4f7f38b19 blobs.
FROZEN = {
    "baseline-results-v1.json": "a894f1f935de1bee789f8c06faee8c7574fa3b6d1157be51d8739736ffe260df",
    "benchmark-corpus-design-v1.json": "29963dcb172bd3d7030c45eda797959a5341b9c0067c168c7340e1f2dc454734",
    "discovery-benchmark-design-v2.json": "e03bc9cfbc520ccb4ed36c8b99f6ae0bc3796ba27919ed5d7af04e4abc7ee9cb",
    "source-baseline-v1.json": "24b39b6f8e75af3b2f09becc1af2d10a59a92a2af8222e6caeec3d4eaa1681c0",
    "release-decision-v1.md": "33c37b68c2097f0d26ce0e42299a8828f1e592bce78c48ac99d0494569d86ac2",
    "hermes-beads-skill-prd.md": "1108b94a4aec492460b686af20b2460c85e8c0f2306ca5418f1d4b017117e5f2",
    "hermes-beads-skill-spec.md": "c4e426ecdd1fec19ef1b9cf847cfac0d289030e938cfd6c2ea643725a370a734",
    "implementation-dag-v1.json": "e916cbb6e5a0eab484ed5859d697b68abbc58169e6aff2fd895c156a55b11931",
    "implementation-beads-v1.json": "7cc537f1038d0cb8c0ca9cbf85c546d3e695b878a35e1387a59cdf0870bfd63e",
}


@pytest.mark.parametrize("name,digest", FROZEN.items())
def test_frozen_planning_sources_retain_original_bytes(name, digest):
    assert hashlib.sha256((PLANS / name).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize(
    "name", ["implementation-dag-v1.json", "implementation-beads-v1.json"]
)
def test_archived_tracking_has_a_resolvable_original_path(name):
    original = PLANS / name
    assert original.is_symlink()
    assert original.resolve() == PLANS / "archive" / name
    assert hashlib.sha256(original.read_bytes()).hexdigest() == FROZEN[name]


def test_current_guidance_does_not_promote_historical_runtime():
    status = (ROOT / "docs/beads-architecture-status.md").read_text()
    assert "REJECT" in status
    assert "release_eligible=false" in status
    assert "No default-profile promotion" in status
    assert "not fresh evidence" in status
    index = (PLANS / "README.md").read_text()
    assert "not the current project status" in index
    assert "byte-for-byte at their original paths" in index
