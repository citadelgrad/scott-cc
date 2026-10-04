"""Documented alternatives avoid, but do not repair, upstream lifecycle defects."""

import re
from pathlib import Path

import pytest

from scripts.skills_install_contract import (
    AGENTS,
    ROOT,
    InstallSandbox,
    payload,
    pinned_cli,
)


def entry_paths(box):
    # Include symlinks explicitly: Path.rglob does not descend into linked directories.
    return {
        str(path.relative_to(box.base)): path.is_symlink()
        for base in (box.cwd, Path(box.env["HOME"]))
        for path in base.rglob("*")
        if path.name == "acceptance-criteria" and (path.is_dir() or path.is_symlink())
    }


@pytest.mark.installer
@pytest.mark.parametrize("agent", AGENTS)
@pytest.mark.parametrize("scope", ["project", "global"])
@pytest.mark.parametrize("copy", [False, True], ids=["symlink", "copy"])
def test_explicit_reinstall_preserves_target_scope_and_mode(
    tmp_path, agent, scope, copy
):
    box = InstallSandbox(tmp_path / "box")
    source = tmp_path / "source/acceptance-criteria"
    source.mkdir(parents=True)
    skill = source / "SKILL.md"
    skill.write_text(
        "---\nname: acceptance-criteria\ndescription: lifecycle fixture\n---\nVersion one\n"
    )
    (source / "obsolete.txt").write_text("remove on replacement")
    first = box.add(source, source.name, agent, scope, copy=copy)
    assert first.returncode == 0, first.stdout + first.stderr
    before = entry_paths(box)
    installed = box.destination(source.name, agent, scope)
    was_symlink = installed.is_symlink()
    skill.write_text(skill.read_text().replace("Version one", "Version two"))
    (source / "obsolete.txt").unlink()
    second = box.add(source, source.name, agent, scope, copy=copy)
    assert second.returncode == 0, second.stdout + second.stderr
    assert entry_paths(box) == before, (
        "reinstall expanded targets or changed copy/symlink mode"
    )
    assert installed.is_symlink() == was_symlink
    assert payload(installed) == payload(source)
    assert "Version two" in (installed / "SKILL.md").read_text()


@pytest.mark.installer
@pytest.mark.parametrize("copy", [False, True], ids=["symlink", "copy"])
def test_documented_quarantine_preserves_every_unselected_agent(tmp_path, copy):
    box = InstallSandbox(tmp_path)
    # The upstream defect reproduces when global detector homes do not exist.
    for key in (
        "CODEX_HOME",
        "HERMES_HOME",
        "CLAUDE_CONFIG_DIR",
        "PI_CODING_AGENT_DIR",
    ):
        Path(box.env[key]).rmdir()
    (Path(box.env["HOME"]) / ".pi").rmdir()
    argv = pinned_cli() + [
        "add",
        str(ROOT),
        "--skill",
        "acceptance-criteria",
        "--agent",
        *AGENTS,
        "--yes",
    ]
    if copy:
        argv.append("--copy")
    result = box.run(argv)
    assert result.returncode == 0, result.stdout + result.stderr
    others = {
        a: payload(box.destination("acceptance-criteria", a, "project"))
        for a in AGENTS
        if a != "hermes-agent"
    }
    text = (ROOT / "docs/skills-cli.md").read_text()
    section = text.split("<!-- BEGIN SAFE HERMES QUARANTINE -->")[1].split(
        "<!-- END SAFE HERMES QUARANTINE -->"
    )[0]
    match = re.search(r"```bash\n(.*?)```", section, re.S)
    assert match is not None, "safe quarantine documentation must include a script"
    script = match.group(1)
    removed = box.run(["bash", "-c", script])
    assert removed.returncode == 0, removed.stdout + removed.stderr
    target = box.destination("acceptance-criteria", "hermes-agent", "project")
    assert not target.exists() and not target.is_symlink()
    for agent, original in others.items():
        assert (
            payload(box.destination("acceptance-criteria", agent, "project"))
            == original
        )
    # Already-absent target must fail, not emit a false success during cleanup.
    again = box.run(["bash", "-c", script])
    assert again.returncode != 0
