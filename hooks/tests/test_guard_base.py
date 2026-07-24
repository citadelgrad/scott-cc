"""Unit tests for hooks/_guard_base.py.

Unlike the subprocess black-box tests for the guard hooks themselves,
_guard_base.py is imported directly here: it's a shared library module,
not a hook entry point with its own stdin/stdout contract.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from _guard_base import (  # noqa: E402
    find_repo_root,
    is_unattended_noop,
    load_json_override,
    run_guard_main,
)


def init_repo(tmp_path: Path) -> Path:
    (tmp_path / ".git").mkdir()
    return tmp_path


# -- find_repo_root -----------------------------------------------------


def test_find_repo_root_returns_dir_containing_git(tmp_path):
    repo_root = init_repo(tmp_path)

    assert find_repo_root(str(repo_root)) == repo_root


def test_find_repo_root_walks_up_from_nested_dir(tmp_path):
    repo_root = init_repo(tmp_path)
    nested = repo_root / "a" / "b" / "c"
    nested.mkdir(parents=True)

    assert find_repo_root(str(nested)) == repo_root


def test_find_repo_root_returns_none_when_no_git_dir_found(tmp_path):
    # tmp_path has no .git anywhere in its ancestry within the sandbox,
    # but real ancestors above it might have one on some machines/CI setups,
    # so only assert the "found" case elsewhere and check for a graceful
    # None-or-ancestor result here.
    lonely = tmp_path / "no_git_here"
    lonely.mkdir()

    result = find_repo_root(str(lonely))

    assert result is None or (result / ".git").exists()


# -- load_json_override ---------------------------------------------------


def test_load_json_override_returns_default_when_file_missing(tmp_path):
    repo_root = init_repo(tmp_path)

    result = load_json_override(repo_root, ".foo.json", "things", ["default"])

    assert result == ["default"]


def test_load_json_override_returns_override_when_valid(tmp_path):
    repo_root = init_repo(tmp_path)
    (repo_root / ".foo.json").write_text('{"things": ["a", "b"]}')

    result = load_json_override(repo_root, ".foo.json", "things", ["default"])

    assert result == ["a", "b"]


def test_load_json_override_falls_back_on_invalid_json(tmp_path):
    repo_root = init_repo(tmp_path)
    (repo_root / ".foo.json").write_text("{not valid json")

    result = load_json_override(repo_root, ".foo.json", "things", ["default"])

    assert result == ["default"]


def test_load_json_override_falls_back_when_key_missing(tmp_path):
    repo_root = init_repo(tmp_path)
    (repo_root / ".foo.json").write_text('{"other_key": ["a"]}')

    result = load_json_override(repo_root, ".foo.json", "things", ["default"])

    assert result == ["default"]


def test_load_json_override_falls_back_when_value_not_list_of_strings(tmp_path):
    repo_root = init_repo(tmp_path)
    (repo_root / ".foo.json").write_text('{"things": [1, 2, 3]}')

    result = load_json_override(repo_root, ".foo.json", "things", ["default"])

    assert result == ["default"]


def test_load_json_override_falls_back_when_value_not_a_list(tmp_path):
    repo_root = init_repo(tmp_path)
    (repo_root / ".foo.json").write_text('{"things": "not-a-list"}')

    result = load_json_override(repo_root, ".foo.json", "things", ["default"])

    assert result == ["default"]


# -- is_unattended_noop ---------------------------------------------------


def test_is_unattended_noop_true_for_bypass_permissions():
    assert is_unattended_noop({"permission_mode": "bypassPermissions"}) is True


def test_is_unattended_noop_false_when_absent():
    assert is_unattended_noop({}) is False


def test_is_unattended_noop_false_for_other_modes():
    assert is_unattended_noop({"permission_mode": "default"}) is False


# -- run_guard_main ---------------------------------------------------


def test_run_guard_main_runs_main_fn_normally(capsys):
    calls = []

    def main_fn():
        calls.append(1)

    run_guard_main(main_fn)

    assert calls == [1]


def test_run_guard_main_swallows_unhandled_exception_as_exit_zero():
    def main_fn():
        raise RuntimeError("boom")

    # Fail-open: the RuntimeError itself never propagates. sys.exit(0) inside
    # the handler still raises SystemExit(0), which is the same "clean exit
    # code 0, no stack trace" contract used at the process boundary in
    # data_layer_guard.py / prefer_modern_tools.py's __main__ blocks.
    try:
        run_guard_main(main_fn)
        raise AssertionError("expected SystemExit")
    except SystemExit as exc:
        assert exc.code == 0


def test_run_guard_main_exits_zero_on_explicit_sys_exit():
    def main_fn():
        sys.exit(0)

    try:
        run_guard_main(main_fn)
        raise AssertionError("expected SystemExit")
    except SystemExit as exc:
        assert exc.code == 0
