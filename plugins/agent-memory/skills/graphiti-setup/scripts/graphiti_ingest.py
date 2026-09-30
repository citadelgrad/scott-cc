#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
# ruff: noqa: BLE001, S110, S112  (hooks must never raise: blind excepts are the fail-silent contract)
"""Send the NEW conversation text of a session to Graphiti (add_memory), in the background.

Hook input (stdin JSON):
  Claude Code  SessionEnd  {session_id, transcript_path, cwd}
  Codex        SessionEnd  {session_id, transcript_path, cwd}
  Hermes       post_llm_call       {session_id, cwd, extra:{user_message, assistant_response}}
                 -> only buffers text to a local file (no network)
               on_session_finalize {session_id, cwd}
                 -> flushes the buffer

The hook process returns at once. A detached worker (new session) does the slow part.
Only user/assistant text is sent (no tool calls or tool output). Secrets are redacted.
Fails silent (exit 0) in every error case.
"""

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

MAX_MSG = 2000
MAX_BODY = 16000
MIN_BODY = 200


def _log(g, msg: str) -> None:
    try:
        g.STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(g.STATE_DIR / "ingest.log", "a") as fh:
            fh.write(f"{datetime.now(timezone.utc).isoformat()} {msg}\n")
    except Exception:
        pass


def _content_text(content, kinds=("text", "input_text", "output_text")) -> str:
    if isinstance(content, str):
        return content
    parts = []
    if isinstance(content, list):
        for p in content:
            if (
                isinstance(p, dict)
                and p.get("type") in kinds
                and isinstance(p.get("text"), str)
            ):
                parts.append(p["text"])
    return "\n".join(parts)


def parse_transcript(path: str, start: int):
    """Return (messages, total_lines). Handles Claude Code and Codex JSONL."""
    msgs = []
    total = 0
    with open(path, "r", errors="replace") as fh:
        for i, line in enumerate(fh):
            total = i + 1
            if i < start:
                continue
            try:
                o = json.loads(line)
            except Exception:
                continue
            t = o.get("type")
            if t in ("user", "assistant") and isinstance(
                o.get("message"), dict
            ):  # Claude Code
                if o.get("isMeta") or o.get("isSidechain"):
                    continue
                msgs.append((t, _content_text(o["message"].get("content"), ("text",))))
            elif t == "response_item" and isinstance(o.get("payload"), dict):  # Codex
                p = o["payload"]
                if p.get("type") == "message" and p.get("role") in (
                    "user",
                    "assistant",
                ):
                    msgs.append((p["role"], _content_text(p.get("content"))))
    return msgs, total


def build_body(g, msgs):
    lines = []
    n_user = n_asst = 0
    for role, text in msgs:
        text = g.redact(g.strip_injected(text or ""))
        if not text or text.startswith(("<command-", "<local-command", "Caveat:")):
            continue
        if len(text) > MAX_MSG:
            text = text[:MAX_MSG] + " ...[truncated]"
        who = "User" if role == "user" else "Assistant"
        n_user += role == "user"
        n_asst += role != "user"
        lines.append(f"{who}: {text}")
    body = "\n".join(lines)
    if n_user == 0 or n_asst == 0 or len(body) < MIN_BODY:
        return None
    if len(body) > MAX_BODY:
        body = body[-MAX_BODY:]  # keep the most recent part
    return body


def send(g, repo: str, session_id: str, body: str, source_desc: str) -> None:
    if not g.healthy(2.0):
        _log(g, f"skip {repo}/{session_id[:8]}: service down")
        return
    name = (
        f"{repo} session {session_id[:8]} {datetime.now(timezone.utc):%Y-%m-%dT%H:%MZ}"
    )
    res = g.call_tool(
        "add_memory",
        {
            "name": name,
            "episode_body": body,
            "group_id": repo,
            "source": "message",
            "source_description": source_desc,
            "reference_time": datetime.now(timezone.utc).isoformat(),
        },
        timeout=60.0,
    )
    _log(
        g,
        f"sent {repo}/{session_id[:8]} chars={len(body)} result={json.dumps(res)[:120]}",
    )


def _cursors(g):
    try:
        return json.loads((g.STATE_DIR / "cursors.json").read_text())
    except Exception:
        return {}


def _save_cursors(g, c):
    g.STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = g.STATE_DIR / "cursors.json.tmp"
    tmp.write_text(json.dumps(c))
    tmp.replace(g.STATE_DIR / "cursors.json")


def worker(payload_file: str) -> int:
    import graphiti_common as g  # ty: ignore[unresolved-import]

    try:
        data = json.loads(Path(payload_file).read_text())
    finally:
        try:
            os.unlink(payload_file)
        except OSError:
            pass
    repo = g.repo_name(data.get("cwd"))
    sid = str(data.get("session_id") or "unknown")
    if data.get("mode") == "hermes":
        buf = g.STATE_DIR / f"hermes-{sid}.jsonl"
        if not buf.exists():
            return 0
        msgs = []
        for line in buf.read_text().splitlines():
            try:
                o = json.loads(line)
                msgs += [("user", o["u"]), ("assistant", o["a"])]
            except Exception:
                pass
        body = build_body(g, msgs)
        buf.unlink(missing_ok=True)
        if body:
            send(g, repo, sid, body, "Hermes Agent session")
        return 0
    path = data.get("transcript_path")
    if not path or not os.path.exists(path):
        return 0
    cur = _cursors(g)
    start = int(cur.get(sid, 0))
    msgs, total = parse_transcript(path, start)
    body = build_body(g, msgs)
    if body:
        send(
            g, repo, sid, body, data.get("source_description") or "coding agent session"
        )
    cur[sid] = total
    _save_cursors(g, cur)
    return 0


def main() -> int:
    if len(sys.argv) > 2 and sys.argv[1] == "--worker":
        try:
            return worker(sys.argv[2])
        except Exception:
            return 0
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    try:
        import graphiti_common as g  # ty: ignore[unresolved-import]

        event = data.get("hook_event_name", "")
        if event == "post_llm_call":  # Hermes: buffer one turn, no network
            extra = data.get("extra") or {}
            u, a = extra.get("user_message"), extra.get("assistant_response")
            if isinstance(u, str) and isinstance(a, str):
                g.STATE_DIR.mkdir(parents=True, exist_ok=True)
                sid = str(data.get("session_id") or "unknown")
                with open(g.STATE_DIR / f"hermes-{sid}.jsonl", "a") as fh:
                    fh.write(json.dumps({"u": g.redact(u), "a": g.redact(a)}) + "\n")
            return 0
        if event == "on_session_finalize":
            data["mode"] = "hermes"
        elif not data.get("transcript_path"):
            return 0
        fd, tmp = tempfile.mkstemp(prefix="graphiti-ingest-", suffix=".json")
        with os.fdopen(fd, "w") as fh:
            json.dump(data, fh)
        subprocess.Popen(
            [sys.executable, os.path.abspath(__file__), "--worker", tmp],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            close_fds=True,
        )
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
