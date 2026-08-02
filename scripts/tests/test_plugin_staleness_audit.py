"""Tests for scripts/plugin_staleness_audit.py.

Builds a throwaway git repo per test with controllable commit dates (via
GIT_COMMITTER_DATE/GIT_AUTHOR_DATE) so the staleness rule's date-based
branches can be exercised deterministically, then imports the script's
pure functions directly against that repo.
"""

from __future__ import annotations

import datetime
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "plugin_staleness_audit.py"

spec = importlib.util.spec_from_file_location("plugin_staleness_audit", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
plugin_staleness_audit = importlib.util.module_from_spec(spec)
sys.modules["plugin_staleness_audit"] = plugin_staleness_audit
spec.loader.exec_module(plugin_staleness_audit)


def _run_git(repo_root: Path, *args: str, env: dict[str, str] | None = None) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )


def _commit(
    repo_root: Path, rel_path: str, *, content: str, when: datetime.datetime
) -> None:
    target = repo_root / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    iso = when.isoformat()
    env = {
        "GIT_AUTHOR_DATE": iso,
        "GIT_COMMITTER_DATE": iso,
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    }
    import os

    full_env = {**os.environ, **env}
    _run_git(repo_root, "add", rel_path)
    _run_git(repo_root, "commit", "-m", f"commit {rel_path} @ {iso}", env=full_env)


def init_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _run_git(repo_root, "init", "-q")
    _run_git(repo_root, "config", "user.email", "test@example.com")
    _run_git(repo_root, "config", "user.name", "Test")
    return repo_root


def test_derive_status_stable_when_active_and_frequent(tmp_path, monkeypatch):
    repo_root = init_repo(tmp_path)
    now = datetime.datetime.now().astimezone()
    for i in range(3):
        _commit(
            repo_root,
            "plugins/foo/file.txt",
            content=f"v{i}",
            when=now - datetime.timedelta(days=30 - i),
        )

    monkeypatch.setattr(plugin_staleness_audit, "ROOT", repo_root)
    status = plugin_staleness_audit.derive_status("plugins/foo", now=now)

    assert status == "stable"


def test_derive_status_experimental_when_too_few_commits(tmp_path, monkeypatch):
    repo_root = init_repo(tmp_path)
    now = datetime.datetime.now().astimezone()
    _commit(
        repo_root,
        "plugins/foo/file.txt",
        content="v0",
        when=now - datetime.timedelta(days=1),
    )

    monkeypatch.setattr(plugin_staleness_audit, "ROOT", repo_root)
    status = plugin_staleness_audit.derive_status("plugins/foo", now=now)

    assert status == "experimental"


def test_derive_status_unmaintained_when_stale_even_with_many_commits(
    tmp_path, monkeypatch
):
    repo_root = init_repo(tmp_path)
    now = datetime.datetime.now().astimezone()
    for i in range(3):
        _commit(
            repo_root,
            "plugins/foo/file.txt",
            content=f"v{i}",
            when=now - datetime.timedelta(days=200 - i),
        )

    monkeypatch.setattr(plugin_staleness_audit, "ROOT", repo_root)
    status = plugin_staleness_audit.derive_status("plugins/foo", now=now)

    assert status == "unmaintained"


def test_derive_status_unmaintained_takes_precedence_over_low_commit_count(
    tmp_path, monkeypatch
):
    """Age dominates commit count: a single ancient commit is
    'unmaintained', not 'experimental', matching how research-tools /
    performance-optimization / mutation-testing were classified in the
    scc-ncs.17 rollout despite having only 1-2 commits.
    """
    repo_root = init_repo(tmp_path)
    now = datetime.datetime.now().astimezone()
    _commit(
        repo_root,
        "plugins/foo/file.txt",
        content="v0",
        when=now - datetime.timedelta(days=170),
    )

    monkeypatch.setattr(plugin_staleness_audit, "ROOT", repo_root)
    status = plugin_staleness_audit.derive_status("plugins/foo", now=now)

    assert status == "unmaintained"


def test_derive_status_experimental_in_maintenance_gap(tmp_path, monkeypatch):
    repo_root = init_repo(tmp_path)
    now = datetime.datetime.now().astimezone()
    for i in range(3):
        _commit(
            repo_root,
            "plugins/foo/file.txt",
            content=f"v{i}",
            when=now - datetime.timedelta(days=77 - i),
        )

    monkeypatch.setattr(plugin_staleness_audit, "ROOT", repo_root)

    assert (
        plugin_staleness_audit.derive_status("plugins/foo", now=now) == "experimental"
    )


def test_main_fails_on_drift_and_passes_when_in_sync(tmp_path, monkeypatch, capsys):
    repo_root = init_repo(tmp_path)
    now = datetime.datetime.now().astimezone()
    _commit(
        repo_root,
        "plugins/foo/file.txt",
        content="v0",
        when=now - datetime.timedelta(days=1),
    )

    marketplace_dir = repo_root / ".claude-plugin"
    marketplace_dir.mkdir()
    marketplace_json = marketplace_dir / "marketplace.json"
    marketplace_json.write_text(
        json.dumps(
            {
                "plugins": [
                    {"name": "foo", "source": "plugins/foo", "status": "stable"},
                ]
            }
        )
    )

    monkeypatch.setattr(plugin_staleness_audit, "ROOT", repo_root)
    monkeypatch.setattr(plugin_staleness_audit, "MARKETPLACE_JSON", marketplace_json)
    monkeypatch.setattr(
        plugin_staleness_audit.datetime,
        "datetime",
        type(
            "FixedDatetime",
            (datetime.datetime,),
            {"now": staticmethod(lambda tz=None: now)},
        ),
    )

    # main() -> fail() -> sys.exit(1) on drift, matching scripts/verify_plugin.py's
    # fail-fast convention (raises SystemExit rather than returning non-zero).
    with pytest.raises(SystemExit) as exc_info:
        plugin_staleness_audit.main()

    assert exc_info.value.code == 1  # 1 commit -> experimental, but declared "stable"
    out = capsys.readouterr().out
    assert "STALE: foo" in out


def test_main_passes_when_declared_status_matches_rule(tmp_path, monkeypatch, capsys):
    repo_root = init_repo(tmp_path)
    now = datetime.datetime.now().astimezone()
    _commit(
        repo_root,
        "plugins/foo/file.txt",
        content="v0",
        when=now - datetime.timedelta(days=1),
    )

    marketplace_dir = repo_root / ".claude-plugin"
    marketplace_dir.mkdir()
    marketplace_json = marketplace_dir / "marketplace.json"
    marketplace_json.write_text(
        json.dumps(
            {
                "plugins": [
                    {"name": "foo", "source": "plugins/foo", "status": "experimental"},
                ]
            }
        )
    )

    monkeypatch.setattr(plugin_staleness_audit, "ROOT", repo_root)
    monkeypatch.setattr(plugin_staleness_audit, "MARKETPLACE_JSON", marketplace_json)
    monkeypatch.setattr(
        plugin_staleness_audit.datetime,
        "datetime",
        type(
            "FixedDatetime",
            (datetime.datetime,),
            {"now": staticmethod(lambda tz=None: now)},
        ),
    )

    exit_code = plugin_staleness_audit.main()

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "OK:" in out
