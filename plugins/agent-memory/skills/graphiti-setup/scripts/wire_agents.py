#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Wire Claude Code, Codex CLI and Hermes Agent to a Graphiti MCP server.

  wire_agents.py --agents auto [--url http://127.0.0.1:48100] [--dry-run]
  wire_agents.py --agents claude,codex --remove

What it does for each selected agent (all edits are merges, never overwrites):
  * copies the hook scripts to a stable dir (default ~/.local/share/graphiti-hooks)
  * writes ~/.config/graphiti-hooks/config.json with the server URL
  * backs up every file it edits as <file>.bak-graphiti (once; an existing backup is kept)
  * registers the MCP server (claude/codex via their CLI, hermes via config.yaml)
  * adds the hooks (UserPromptSubmit, SessionStart, SessionEnd; hermes: pre_llm_call,
    post_llm_call, on_session_finalize) and keeps all existing hooks
  * appends a marked Memory pointer to CLAUDE.md / AGENTS.md / SOUL.md
  * --remove strips exactly what this script added.
Exit code 0 on success, 1 when an agent could not be wired (others still run).
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import tomllib

HERE = Path(__file__).resolve().parent
HOOK_FILES = ("graphiti_common.py", "graphiti_context.py", "graphiti_ingest.py")
MARK_START = "<!-- graphiti-memory:start -->"
MARK_END = "<!-- graphiti-memory:end -->"
POINTER = f"""{MARK_START}
## Memory
Project facts live in Graphiti (MCP server `graphiti`, group_id = repo name).
Current facts for each prompt arrive in <graphiti-facts>. They win over older notes.
Before you change tooling, dependencies or conventions, call search_memory_facts.
When the user corrects you, call add_memory.
Do not save project facts in MEMORY.md.
{MARK_END}
"""

HOME = Path.home()


def log(msg: str) -> None:
    print(msg)


def backup(path: Path, dry: bool) -> None:
    bak = path.with_name(path.name + ".bak-graphiti")
    if path.exists() and not bak.exists():
        log(f"  backup {path} -> {bak.name}")
        if not dry:
            shutil.copy2(path, bak)


def install_hooks(dest: Path, dry: bool) -> None:
    log(f"hooks: copy {', '.join(HOOK_FILES)} -> {dest}")
    if dry:
        return
    dest.mkdir(parents=True, exist_ok=True)
    for name in HOOK_FILES:
        shutil.copy2(HERE / name, dest / name)


def write_hook_config(url: str, dry: bool) -> None:
    """Record the server URL where the hooks look for it (GRAPHITI_URL env still wins)."""
    path = HOME / ".config/graphiti-hooks/config.json"
    log(f"hooks: write server url to {path}")
    if dry:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"url": url}) + "\n")


def is_ours(command: str) -> bool:
    return "graphiti_context.py" in command or "graphiti_ingest.py" in command


def merge_json_hooks(path: Path, hooks_dir: Path, dry: bool, remove: bool) -> None:
    """Merge (or remove) our three hook entries in a Claude/Codex style JSON file."""
    ctx = f"uv run --script {hooks_dir}/graphiti_context.py"
    ing = f"uv run --script {hooks_dir}/graphiti_ingest.py"
    data = json.loads(path.read_text()) if path.exists() else {}
    hooks = data.setdefault("hooks", {})
    wanted = {
        "UserPromptSubmit": {
            "hooks": [{"type": "command", "command": ctx, "timeout": 10}]
        },
        "SessionStart": {
            "matcher": "startup|resume|compact",
            "hooks": [{"type": "command", "command": ctx, "timeout": 10}],
        },
        "SessionEnd": {"hooks": [{"type": "command", "command": ing, "timeout": 5}]},
    }
    for event, entry in wanted.items():
        groups = hooks.get(event, [])
        groups = [
            g
            for g in groups
            if not any(is_ours(h.get("command", "")) for h in g.get("hooks", []))
        ]
        if not remove:
            groups.append(entry)
        if groups:
            hooks[event] = groups
        else:
            hooks.pop(event, None)
    if not hooks:
        data.pop("hooks", None)
    text = json.dumps(data, indent=2) + "\n"
    json.loads(text)  # validate
    log(f"  {'remove from' if remove else 'merge into'} {path}")
    if not dry:
        backup(path, dry)
        path.write_text(text)


def edit_pointer(path: Path, dry: bool, remove: bool) -> None:
    text = path.read_text() if path.exists() else ""
    if MARK_START in text and MARK_END in text:
        head, rest = text.split(MARK_START, 1)
        tail = rest.split(MARK_END, 1)[1]
        text = (
            (head.rstrip("\n") + "\n" + tail.lstrip("\n")).lstrip("\n")
            if remove
            else text
        )
        if not remove:
            log(f"  pointer already in {path}")
            return
    elif remove:
        log(f"  no pointer in {path}")
        return
    else:
        text = text + ("" if text.endswith("\n") or not text else "\n") + "\n" + POINTER
    log(f"  {'remove pointer from' if remove else 'append pointer to'} {path}")
    if not dry:
        backup(path, dry)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


def sh(cmd: list[str], dry: bool) -> bool:
    log("  $ " + " ".join(cmd))
    if dry:
        return True
    r = subprocess.run(
        cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL, check=False
    )
    if r.returncode != 0:
        log(f"  FAILED ({r.returncode}): {(r.stdout + r.stderr).strip()[:300]}")
    return r.returncode == 0


def wire_claude(url: str, hooks_dir: Path, dry: bool, remove: bool) -> bool:
    log("claude:")
    if remove:
        sh(["claude", "mcp", "remove", "--scope", "user", "graphiti"], dry)
    else:
        backup(HOME / ".claude.json", dry)
        sh(
            [
                "claude",
                "mcp",
                "add",
                "--scope",
                "user",
                "--transport",
                "http",
                "graphiti",
                url + "/mcp",
            ],
            dry,
        )
    merge_json_hooks(HOME / ".claude/settings.json", hooks_dir, dry, remove)
    edit_pointer(HOME / ".claude/CLAUDE.md", dry, remove)
    return True


def wire_codex(url: str, hooks_dir: Path, dry: bool, remove: bool) -> bool:
    log("codex:")
    if remove:
        sh(["codex", "mcp", "remove", "graphiti"], dry)
    else:
        backup(HOME / ".codex/config.toml", dry)
        sh(["codex", "mcp", "add", "graphiti", "--url", url + "/mcp"], dry)
    merge_json_hooks(HOME / ".codex/hooks.json", hooks_dir, dry, remove)
    edit_pointer(HOME / ".codex/AGENTS.md", dry, remove)
    cfg = HOME / ".codex/config.toml"
    if cfg.exists() and not dry:
        tomllib.loads(cfg.read_text())  # validate
        log("  config.toml parses")
    return True


def hermes_blocks(hooks_dir: Path) -> dict[str, str]:
    ctx = f"uv run --script {hooks_dir}/graphiti_context.py"
    ing = f"uv run --script {hooks_dir}/graphiti_ingest.py"
    return {
        "pre_llm_call": f"  pre_llm_call:\n    - command: {ctx}\n      timeout: 10\n",
        "post_llm_call": f"  post_llm_call:\n    - command: {ing}\n      timeout: 5\n",
        "on_session_finalize": f"  on_session_finalize:\n    - command: {ing}\n      timeout: 5\n",
    }


def edit_hermes_yaml(
    path: Path, url: str, hooks_dir: Path, dry: bool, remove: bool
) -> bool:
    """Line-based merge that keeps comments and every existing key (no YAML round trip)."""
    text = path.read_text() if path.exists() else ""
    lines = text.splitlines(keepends=True)
    if remove:
        out: list[str] = []
        skip_indent = None
        for line in lines:
            stripped = line.strip()
            indent = len(line) - len(line.lstrip())
            if skip_indent is not None:
                if stripped and indent <= skip_indent:
                    skip_indent = None
                else:
                    continue
            if stripped == "graphiti:" and indent == 2:
                skip_indent = 2
                continue
            if (
                stripped.rstrip(":")
                in ("pre_llm_call", "post_llm_call", "on_session_finalize")
                and indent == 2
            ):
                # drop the event block only when it holds our command
                block = _block_after(lines, lines.index(line))
                if any(is_ours(b) for b in block):
                    skip_indent = 2
                    continue
            out.append(line)
        new = "".join(out)
    else:
        blocks = hermes_blocks(hooks_dir)
        for event in blocks:
            if any(ln.startswith(f"  {event}:") for ln in lines):
                log(
                    f"  hermes hooks.{event} already exists: merge by hand (not edited)"
                )
                return False
        new = text
        if not new.endswith("\n") and new:
            new += "\n"
        if any(ln.startswith("hooks:") for ln in lines):
            idx = next(i for i, ln in enumerate(lines) if ln.startswith("hooks:"))
            if lines[idx].strip() != "hooks:":
                log(
                    "  hermes 'hooks:' is not a block mapping: merge by hand (not edited)"
                )
                return False
            lines.insert(idx + 1, "".join(blocks.values()))
            new = "".join(lines)
        else:
            new += "hooks:\n" + "".join(blocks.values())
        entry = f"  graphiti:\n    url: {url}/mcp\n    enabled: true\n"
        new_lines = new.splitlines(keepends=True)
        if any(ln.startswith("mcp_servers:") for ln in new_lines):
            idx = next(
                i for i, ln in enumerate(new_lines) if ln.startswith("mcp_servers:")
            )
            if new_lines[idx].strip() != "mcp_servers:":
                log(
                    "  hermes 'mcp_servers:' is not a block mapping: merge by hand (not edited)"
                )
                return False
            if any(ln.strip() == "graphiti:" for ln in new_lines):
                log("  hermes mcp_servers.graphiti already exists: not edited")
            else:
                new_lines.insert(idx + 1, entry)
            new = "".join(new_lines)
        else:
            new += "mcp_servers:\n" + entry
    log(f"  {'remove from' if remove else 'merge into'} {path}")
    if not dry:
        backup(path, dry)
        path.write_text(new)
    return True


def _block_after(lines: list[str], idx: int) -> list[str]:
    base = len(lines[idx]) - len(lines[idx].lstrip())
    out = []
    for line in lines[idx + 1 :]:
        if line.strip() and len(line) - len(line.lstrip()) <= base:
            break
        out.append(line)
    return out


def wire_hermes(url: str, hooks_dir: Path, dry: bool, remove: bool) -> bool:
    log("hermes:")
    home = Path(HOME / ".hermes")
    ok = edit_hermes_yaml(home / "config.yaml", url, hooks_dir, dry, remove)
    edit_pointer(home / "SOUL.md", dry, remove)
    if ok and not remove:
        log(
            '  next: run `hermes --accept-hooks -z "ping"` once (or keep hooks_auto_accept: true), '
            "then `hermes hooks doctor`"
        )
    return ok


AGENT_WIRING = {"claude": wire_claude, "codex": wire_codex, "hermes": wire_hermes}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument(
        "--agents", default="auto", help="auto | comma list of claude,codex,hermes"
    )
    p.add_argument(
        "--url", default="http://127.0.0.1:48100", help="Graphiti base URL (no /mcp)"
    )
    p.add_argument("--hooks-dir", default=str(HOME / ".local/share/graphiti-hooks"))
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--remove", action="store_true", help="undo what this script added")
    args = p.parse_args(argv)

    agents = (
        [a for a in AGENT_WIRING if shutil.which(a)]
        if args.agents == "auto"
        else args.agents.split(",")
    )
    bad = [a for a in agents if a not in AGENT_WIRING]
    if bad:
        sys.exit(f"unknown agent(s): {', '.join(bad)}")
    if not agents:
        log("no supported agent found on PATH (claude, codex, hermes)")
        return 1
    hooks_dir = Path(args.hooks_dir).expanduser()
    if not args.remove:
        install_hooks(hooks_dir, args.dry_run)
        write_hook_config(args.url.rstrip("/"), args.dry_run)
    failed = []
    for agent in agents:
        if not AGENT_WIRING[agent](
            args.url.rstrip("/"), hooks_dir, args.dry_run, args.remove
        ):
            failed.append(agent)
    if args.remove:
        log(f"hooks dir kept: {hooks_dir} (delete by hand if unwanted)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
