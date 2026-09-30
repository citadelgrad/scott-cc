"""Offline tests for the graphiti-setup hook scripts (no Graphiti server, no real network)."""

from __future__ import annotations

import importlib
import io
import json
import re
import subprocess
import sys
import urllib.error
from pathlib import Path

import pytest

SKILL = (
    Path(__file__).resolve().parents[2] / "plugins/agent-memory/skills/graphiti-setup"
)
SCRIPTS = SKILL / "scripts"
FAKE_KEY = (
    "sk-" + "A1b2C3d4E5f6G7h8I9j0"
)  # built at runtime so no secret-looking literal sits in the file


@pytest.fixture()
def mods(monkeypatch, tmp_path):
    """Fresh graphiti_common / graphiti_context / graphiti_ingest with isolated state."""
    monkeypatch.setenv("GRAPHITI_HOOK_STATE", str(tmp_path / "state"))
    monkeypatch.setenv("GRAPHITI_HOOK_CONFIG", str(tmp_path / "none.json"))
    monkeypatch.delenv("GRAPHITI_URL", raising=False)
    monkeypatch.delenv("GRAPHITI_MCP_PORT", raising=False)
    monkeypatch.syspath_prepend(str(SCRIPTS))
    for name in ("graphiti_common", "graphiti_context", "graphiti_ingest"):
        sys.modules.pop(name, None)
    common = importlib.import_module("graphiti_common")
    context = importlib.import_module("graphiti_context")
    ingest = importlib.import_module("graphiti_ingest")
    return common, context, ingest


def run_context(mods, monkeypatch, capsys, payload, facts=None, up=True):
    common, context, _ = mods
    calls = []
    monkeypatch.setattr(common, "healthy", lambda timeout=1.0: up)

    def fake_call(name, arguments, timeout=4.0):
        calls.append((name, arguments))
        return {"facts": facts or []}

    monkeypatch.setattr(common, "call_tool", fake_call)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    assert context.main() == 0
    return capsys.readouterr().out, calls


def fact(text, invalid=None, valid="2026-09-01T00:00:00Z"):
    return {"fact": text, "invalid_at": invalid, "valid_at": valid}


# ---- input shapes -------------------------------------------------------------------------


def test_claude_user_prompt_submit_prints_plain_text(mods, monkeypatch, capsys):
    out, calls = run_context(
        mods,
        monkeypatch,
        capsys,
        {
            "hook_event_name": "UserPromptSubmit",
            "prompt": "which test runner do we use?",
            "cwd": "/work/my-api",
        },
        facts=[fact("api uses Vitest")],
    )
    assert out.startswith('<graphiti-facts repo="my-api">')
    assert "api uses Vitest (since 2026-09-01)" in out
    assert calls[0][1]["group_ids"] == ["my-api"]
    assert calls[0][1]["query"] == "which test runner do we use?"


def test_codex_session_start_uses_generic_query(mods, monkeypatch, capsys):
    out, calls = run_context(
        mods,
        monkeypatch,
        capsys,
        {
            "hook_event_name": "SessionStart",
            "source": "startup",
            "cwd": "/work/web app",
        },
        facts=[fact("uses pnpm")],
    )
    assert "uses pnpm" in out
    assert calls[0][1]["group_ids"] == ["web_app"]  # sanitised group id
    assert "web_app" in calls[0][1]["query"]


def test_session_start_other_source_is_ignored(mods, monkeypatch, capsys):
    out, calls = run_context(
        mods,
        monkeypatch,
        capsys,
        {"hook_event_name": "SessionStart", "source": "clear", "cwd": "/w/x"},
        facts=[fact("x")],
    )
    assert out == "" and calls == []


def test_hermes_pre_llm_call_prints_context_json(mods, monkeypatch, capsys):
    out, calls = run_context(
        mods,
        monkeypatch,
        capsys,
        {
            "hook_event_name": "pre_llm_call",
            "cwd": "/w/svc",
            "extra": {"user_message": "what database do we use?"},
        },
        facts=[fact("svc uses Postgres")],
    )
    data = json.loads(out)
    assert "svc uses Postgres" in data["context"]
    assert calls[0][1]["query"] == "what database do we use?"


@pytest.mark.parametrize("prompt", ["/help", "hi", ""])
def test_short_or_slash_prompts_skip_search(mods, monkeypatch, capsys, prompt):
    out, calls = run_context(
        mods,
        monkeypatch,
        capsys,
        {"hook_event_name": "UserPromptSubmit", "prompt": prompt, "cwd": "/w/x"},
        facts=[fact("x")],
    )
    assert out == "" and calls == []


def test_injected_blocks_are_stripped_from_query(mods, monkeypatch, capsys):
    prompt = (
        "<system-reminder>ignore me please</system-reminder>\nwhich linter do we use?"
    )
    _, calls = run_context(
        mods,
        monkeypatch,
        capsys,
        {"hook_event_name": "UserPromptSubmit", "prompt": prompt, "cwd": "/w/x"},
        facts=[fact("ruff")],
    )
    assert calls[0][1]["query"] == "which linter do we use?"


# ---- filtering and cap --------------------------------------------------------------------


def test_invalidated_facts_are_filtered(mods, monkeypatch, capsys):
    out, _ = run_context(
        mods,
        monkeypatch,
        capsys,
        {
            "hook_event_name": "UserPromptSubmit",
            "prompt": "which test runner do we use?",
            "cwd": "/w/api",
        },
        facts=[
            fact("api uses Jest", invalid="2026-09-30T00:00:00Z"),
            fact("api uses Vitest"),
        ],
    )
    assert "Vitest" in out and "Jest" not in out


def test_all_facts_invalid_prints_nothing(mods, monkeypatch, capsys):
    out, _ = run_context(
        mods,
        monkeypatch,
        capsys,
        {
            "hook_event_name": "UserPromptSubmit",
            "prompt": "which test runner do we use?",
            "cwd": "/w/api",
        },
        facts=[fact("old", invalid="2026-01-01T00:00:00Z")],
    )
    assert out == ""


def test_fact_cap_is_eight(mods, monkeypatch, capsys):
    many = [fact(f"fact number {i}") for i in range(20)]
    out, calls = run_context(
        mods,
        monkeypatch,
        capsys,
        {
            "hook_event_name": "UserPromptSubmit",
            "prompt": "tell me everything you know",
            "cwd": "/w/api",
        },
        facts=many,
    )
    assert out.count("\n- ") == 8
    assert "fact number 7" in out and "fact number 8" not in out
    assert calls[0][1]["max_facts"] == 24


def test_cap_cannot_be_raised_by_caller(mods):
    common, _, _ = mods
    common.call_tool = lambda *a, **k: {"facts": [fact(f"f{i}") for i in range(50)]}
    assert len(common.current_facts("query text here", "g", limit=100)) == 8


# ---- silent failure when the service is down ----------------------------------------------


def test_service_down_is_silent_and_skips_search(mods, monkeypatch, capsys):
    out, calls = run_context(
        mods,
        monkeypatch,
        capsys,
        {
            "hook_event_name": "UserPromptSubmit",
            "prompt": "which test runner do we use?",
            "cwd": "/w/api",
        },
        facts=[fact("x")],
        up=False,
    )
    assert out == "" and calls == []


def test_tool_error_is_silent(mods, monkeypatch, capsys):
    common, context, _ = mods
    monkeypatch.setattr(common, "healthy", lambda timeout=1.0: True)

    def boom(*a, **k):
        raise urllib.error.URLError("refused")

    monkeypatch.setattr(common, "call_tool", boom)
    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO(
            json.dumps(
                {
                    "hook_event_name": "UserPromptSubmit",
                    "prompt": "which test runner do we use?",
                    "cwd": "/w/api",
                }
            )
        ),
    )
    assert context.main() == 0
    assert capsys.readouterr().out == ""


def test_bad_stdin_is_silent(mods, monkeypatch, capsys):
    _, context, _ = mods
    monkeypatch.setattr(sys, "stdin", io.StringIO("not json"))
    assert context.main() == 0
    assert capsys.readouterr().out == ""


def test_real_script_exits_zero_fast_when_port_closed(tmp_path):
    """Run the actual script as a subprocess against a closed local port (connection refused)."""
    env = {
        "PATH": "/usr/bin:/bin",
        "HOME": str(tmp_path),
        "GRAPHITI_URL": "http://127.0.0.1:1",
        "GRAPHITI_HOOK_STATE": str(tmp_path / "s"),
    }
    payload = json.dumps(
        {
            "hook_event_name": "UserPromptSubmit",
            "prompt": "which test runner do we use?",
            "cwd": "/w/api",
        }
    )
    res = subprocess.run(
        [sys.executable, str(SCRIPTS / "graphiti_context.py")],
        input=payload,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert (res.returncode, res.stdout, res.stderr) == (0, "", "")


# ---- endpoint resolution ------------------------------------------------------------------


def test_endpoint_from_port_env(monkeypatch, mods):
    monkeypatch.setenv("GRAPHITI_MCP_PORT", "49123")
    common = importlib.reload(mods[0])
    assert common.BASE_URL == "http://127.0.0.1:49123" and common.MCP_URL.endswith(
        "/mcp"
    )


def test_endpoint_from_config_file(monkeypatch, tmp_path, mods):
    cfg = tmp_path / "c.json"
    cfg.write_text(json.dumps({"url": "http://127.0.0.1:40001/"}))
    monkeypatch.setenv("GRAPHITI_HOOK_CONFIG", str(cfg))
    common = importlib.reload(mods[0])
    assert common.BASE_URL == "http://127.0.0.1:40001"


# ---- secret redaction ---------------------------------------------------------------------

SECRETS = [
    FAKE_KEY,
    "ghp_" + "a" * 36,
    "AKIA" + "ABCDEFGHIJKLMNOP",
    "Authorization: Bearer abcdefghijklmnop1234567890",
    "password=hunter2hunter2",
    "postgres://admin:s3cretpw@db.internal:5432/app",
    "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----",
]


@pytest.mark.parametrize("secret", SECRETS)
def test_redact_removes_secret(mods, secret):
    common, _, _ = mods
    out = common.redact(f"before {secret} after")
    assert "[REDACTED]" in out
    for needle in (
        "A1b2C3d4",
        "hunter2",
        "s3cretpw",
        "abcdefghijklmnop1234567890",
        "ghp_aaaa",
        "AKIAABCD",
    ):
        assert needle not in out


def test_redact_keeps_plain_text(mods):
    common, _, _ = mods
    assert (
        common.redact("we use Vitest for the api package")
        == "we use Vitest for the api package"
    )


# ---- ingest: transcript shapes, body building, detach, hermes buffering ------------------


def write_jsonl(path, rows):
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")


LONG = (
    "We decided to switch the api package from Jest to Vitest because of ESM support. "
    * 3
)


def test_parse_claude_transcript(mods, tmp_path):
    _, _, ingest = mods
    p = tmp_path / "t.jsonl"
    write_jsonl(
        p,
        [
            {"type": "user", "message": {"content": "hello there"}},
            {
                "type": "assistant",
                "message": {
                    "content": [{"type": "text", "text": "hi"}, {"type": "tool_use"}]
                },
            },
            {"type": "user", "isMeta": True, "message": {"content": "meta"}},
            {"type": "assistant", "isSidechain": True, "message": {"content": "side"}},
        ],
    )
    msgs, total = ingest.parse_transcript(str(p), 0)
    assert msgs == [("user", "hello there"), ("assistant", "hi")] and total == 4
    assert ingest.parse_transcript(str(p), 3)[0] == []  # cursor skips processed lines


def test_parse_codex_transcript(mods, tmp_path):
    _, _, ingest = mods
    p = tmp_path / "rollout.jsonl"
    write_jsonl(
        p,
        [
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "question"}],
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "answer"}],
                },
            },
            {"type": "response_item", "payload": {"type": "function_call"}},
        ],
    )
    assert ingest.parse_transcript(str(p), 0)[0] == [
        ("user", "question"),
        ("assistant", "answer"),
    ]


def test_build_body_redacts_and_requires_both_roles(mods):
    common, _, ingest = mods
    body = ingest.build_body(
        common, [("user", LONG + f" key {FAKE_KEY}"), ("assistant", LONG)]
    )
    assert body and "A1b2C3d4" not in body and "[REDACTED]" in body
    assert ingest.build_body(common, [("user", LONG)]) is None  # no assistant turn
    assert (
        ingest.build_body(common, [("user", "hi"), ("assistant", "yo")]) is None
    )  # under minimum size


def test_hermes_turns_buffer_then_flush(mods, monkeypatch):
    common, _, ingest = mods
    started = []
    monkeypatch.setattr(
        ingest.subprocess, "Popen", lambda *a, **k: started.append((a, k))
    )
    turn = {
        "hook_event_name": "post_llm_call",
        "session_id": "s1",
        "cwd": "/w/svc",
        "extra": {"user_message": LONG + FAKE_KEY, "assistant_response": LONG},
    }
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(turn)))
    assert ingest.main() == 0
    buf = common.STATE_DIR / "hermes-s1.jsonl"
    assert (
        buf.exists() and "A1b2C3d4" not in buf.read_text()
    )  # redacted before it touches disk
    assert started == []  # buffering never spawns or uses the network

    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO(
            json.dumps(
                {
                    "hook_event_name": "on_session_finalize",
                    "session_id": "s1",
                    "cwd": "/w/svc",
                }
            )
        ),
    )
    assert ingest.main() == 0
    assert len(started) == 1 and started[0][1]["start_new_session"] is True

    sent = []
    monkeypatch.setattr(common, "healthy", lambda timeout=1.0: True)
    monkeypatch.setattr(
        common,
        "call_tool",
        lambda name, args, timeout=4.0: (
            sent.append((name, args)) or {"message": "queued"}
        ),
    )
    payload = Path(started[0][0][0][-1])
    assert ingest.worker(str(payload)) == 0
    assert sent and sent[0][0] == "add_memory" and sent[0][1]["group_id"] == "svc"
    assert not buf.exists()


def test_session_end_detaches_and_advances_cursor(mods, monkeypatch, tmp_path):
    common, _, ingest = mods
    tr = tmp_path / "t.jsonl"
    write_jsonl(
        tr,
        [
            {"type": "user", "message": {"content": LONG}},
            {"type": "assistant", "message": {"content": LONG}},
        ],
    )
    started = []
    monkeypatch.setattr(
        ingest.subprocess, "Popen", lambda *a, **k: started.append((a, k))
    )
    payload = {
        "hook_event_name": "SessionEnd",
        "session_id": "abc12345",
        "cwd": "/w/api",
        "transcript_path": str(tr),
    }
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    assert ingest.main() == 0
    kwargs = started[0][1]
    assert (
        kwargs["start_new_session"] is True and kwargs["stdout"] == subprocess.DEVNULL
    )

    sent = []
    monkeypatch.setattr(common, "healthy", lambda timeout=1.0: True)
    monkeypatch.setattr(
        common,
        "call_tool",
        lambda name, args, timeout=4.0: sent.append(args) or {"message": "ok"},
    )
    assert ingest.worker(started[0][0][0][-1]) == 0
    assert len(sent) == 1 and sent[0]["group_id"] == "api"
    assert json.loads((common.STATE_DIR / "cursors.json").read_text())["abc12345"] == 2


def test_ingest_without_transcript_does_nothing(mods, monkeypatch):
    _, _, ingest = mods
    started = []
    monkeypatch.setattr(ingest.subprocess, "Popen", lambda *a, **k: started.append(1))
    monkeypatch.setattr(
        sys, "stdin", io.StringIO(json.dumps({"hook_event_name": "SessionEnd"}))
    )
    assert ingest.main() == 0 and started == []


def test_worker_skips_when_service_down(mods, monkeypatch, tmp_path):
    common, _, ingest = mods
    tr = tmp_path / "t.jsonl"
    write_jsonl(
        tr,
        [
            {"type": "user", "message": {"content": LONG}},
            {"type": "assistant", "message": {"content": LONG}},
        ],
    )
    p = tmp_path / "payload.json"
    p.write_text(
        json.dumps({"session_id": "s", "cwd": "/w/api", "transcript_path": str(tr)})
    )
    monkeypatch.setattr(common, "healthy", lambda timeout=1.0: False)
    monkeypatch.setattr(
        common, "call_tool", lambda *a, **k: pytest.fail("must not call the server")
    )
    assert ingest.worker(str(p)) == 0


# ---- render / wire scripts and hygiene ----------------------------------------------------


def test_render_service_binds_loopback_and_has_targets(tmp_path):
    out = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "render_service.py"),
            "--dir",
            str(tmp_path / "svc"),
            "--llm",
            "openai",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert out.returncode == 0, out.stderr
    compose = (tmp_path / "svc/docker-compose.yml").read_text()
    ports = re.findall(r'^\s+- "([^"]+)"', compose, re.MULTILINE)
    assert ports and all(p.startswith("127.0.0.1:") for p in ports)
    assert not re.search(
        r"\b(3000|5000|8000|8080):\d", " ".join(p.split(":", 1)[1] for p in ports)
    )
    make = (tmp_path / "svc/Makefile").read_text()
    for target in ("up:", "down:", "restart:", "status:", "logs:"):
        assert target in make
    assert oct((tmp_path / "svc/.env").stat().st_mode & 0o777) == "0o600"
    assert ".env" in (tmp_path / "svc/.gitignore").read_text()
    assert "@" not in re.sub(
        r"\S+@\S+", "", (tmp_path / "svc/config/config.yaml").read_text()
    ).replace("@PATCH", "")


def test_wire_agents_remove_keeps_foreign_hooks(tmp_path):
    sys.path.insert(0, str(SCRIPTS))
    wire = importlib.import_module("wire_agents")
    settings = tmp_path / "settings.json"
    settings.write_text(
        json.dumps(
            {
                "hooks": {
                    "Stop": [{"hooks": [{"type": "command", "command": "keep-me"}]}]
                }
            }
        )
    )
    wire.merge_json_hooks(settings, Path("/h"), False, False)
    wire.merge_json_hooks(settings, Path("/h"), False, False)  # idempotent
    data = json.loads(settings.read_text())
    assert len(data["hooks"]["UserPromptSubmit"]) == 1
    assert (tmp_path / "settings.json.bak-graphiti").exists()
    wire.merge_json_hooks(settings, Path("/h"), False, True)
    assert json.loads(settings.read_text()) == {
        "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "keep-me"}]}]}
    }


def test_no_user_specific_values_in_skill_files():
    banned = ["zeno", "dev_personal", "/Users/scott", "citadelgrad", "scott@"]
    offenders = []
    for path in SKILL.rglob("*"):
        if path.is_file() and path.suffix in {
            ".py",
            ".md",
            ".tmpl",
            ".patched",
            ".json",
            ".yaml",
            ".yml",
        }:
            text = path.read_text(errors="replace")
            offenders += [f"{path.name}:{b}" for b in banned if b in text]
    assert offenders == []
