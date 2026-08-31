"""Black-box tests for one-shot review-panel checkpoint claims."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "plugins"
    / "review-panel"
    / "scripts"
    / "checkpoint-claim"
)


def digest(checkpoint: Path) -> str:
    return hashlib.sha256(checkpoint.read_bytes()).hexdigest()


def run_claim(
    checkpoint: Path, session_id: str, expected_sha256: str | None = None
) -> subprocess.CompletedProcess[str]:
    if (
        checkpoint.parent.name == "workspace"
        and checkpoint.parent.parent.name == ".review-panel"
    ):
        cwd = checkpoint.parent.parent.parent
    else:
        cwd = checkpoint.parent
    return subprocess.run(
        [
            str(SCRIPT),
            str(checkpoint),
            session_id,
            expected_sha256 or digest(checkpoint),
        ],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def test_checkpoint_can_be_claimed_exactly_once(tmp_path: Path) -> None:
    workspace = tmp_path / ".review-panel" / "workspace"
    workspace.mkdir(parents=True)
    checkpoint = workspace / "round2.json"
    checkpoint.write_text('{"checkpoint_id":"run-round-2"}')

    first = run_claim(checkpoint, "session-b")
    second = run_claim(checkpoint, "session-b")

    assert first.returncode == 0
    assert json.loads(first.stdout)["resumed_by_session_id"] == "session-b"
    assert second.returncode == 3
    assert "checkpoint_already_consumed" in second.stderr
    claim = json.loads(
        (workspace / "checkpoint-claims" / f"{digest(checkpoint)}.claim").read_text()
    )
    assert claim == {
        "checkpoint_id": "run-round-2",
        "checkpoint_sha256": digest(checkpoint),
        "resumed_by_session_id": "session-b",
    }


def test_checkpoint_copy_and_hard_link_share_the_same_claim(tmp_path: Path) -> None:
    workspace = tmp_path / ".review-panel" / "workspace"
    workspace.mkdir(parents=True)
    original = workspace / "round2.json"
    original.write_text('{"checkpoint_id":"immutable-round-2"}')
    copied = workspace / "copied.json"
    copied.write_bytes(original.read_bytes())
    hard_link = workspace / "linked.json"
    hard_link.hardlink_to(original)

    assert run_claim(original, "session-b").returncode == 0
    assert run_claim(copied, "session-c").returncode == 3
    assert run_claim(hard_link, "session-d").returncode == 3

    mutated = workspace / "mutated.json"
    mutated.write_text('{"checkpoint_id":"changed-round-2"}')
    mismatch = run_claim(mutated, "session-e", digest(original))
    assert mismatch.returncode == 2
    assert "checkpoint_hash_mismatch" in mismatch.stderr


def test_checkpoint_claim_rejects_missing_symlink_and_unsafe_session(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / ".review-panel" / "workspace"
    workspace.mkdir(parents=True)
    missing = run_claim(workspace / "missing.json", "session-b", "0" * 64)
    assert missing.returncode == 2

    target = workspace / "target.json"
    target.write_text('{"checkpoint_id":"target"}')
    link = workspace / "link.json"
    link.symlink_to(target)
    symlink = run_claim(link, "session-b")
    assert symlink.returncode == 2

    unsafe = run_claim(target, "$(touch nope)")
    assert unsafe.returncode == 2
    assert not (tmp_path / "nope").exists()

    outside = tmp_path / "outside.json"
    outside.write_text('{"checkpoint_id":"outside"}')
    assert run_claim(outside, "session-b").returncode == 2
