# ruff: noqa: BLE001, S110  (hooks must never raise: blind excepts are the fail-silent contract)
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Shared helpers for the Graphiti memory hooks (Claude Code, Codex, Hermes).

Stdlib only. Talks to the Graphiti MCP server (streamable HTTP, /mcp).
Every function fails soft: callers treat None / exceptions as "service down".

Endpoint resolution order (first hit wins):
  1. env GRAPHITI_URL                  e.g. http://127.0.0.1:48100
  2. env GRAPHITI_MCP_PORT             -> http://127.0.0.1:<port>
  3. config file                       $GRAPHITI_HOOK_CONFIG or
                                       ~/.config/graphiti-hooks/config.json  {"url": "..."}
  4. default                           http://127.0.0.1:48100
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path

DEFAULT_URL = "http://127.0.0.1:48100"
MAX_FACTS = 8  # hard cap on facts injected per prompt


def _resolve_base_url() -> str:
    url = os.environ.get("GRAPHITI_URL")
    if url:
        return url.rstrip("/")
    port = os.environ.get("GRAPHITI_MCP_PORT")
    if port and port.isdigit():
        return f"http://127.0.0.1:{port}"
    cfg = Path(
        os.environ.get(
            "GRAPHITI_HOOK_CONFIG",
            str(Path.home() / ".config/graphiti-hooks/config.json"),
        )
    )
    try:
        value = json.loads(cfg.read_text()).get("url")
        if isinstance(value, str) and value:
            return value.rstrip("/")
    except Exception:
        pass
    return DEFAULT_URL


BASE_URL = _resolve_base_url()
MCP_URL = BASE_URL + "/mcp"  # the server 307-redirects /mcp/ to /mcp
STATE_DIR = Path(
    os.environ.get(
        "GRAPHITI_HOOK_STATE", str(Path.home() / ".local/state/graphiti-hooks")
    )
)

_SECRET_PATTERNS = [
    re.compile(
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?(-----END [A-Z ]*PRIVATE KEY-----|$)",
        re.DOTALL,
    ),
    re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_\-]{16,}"),
    re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr|github_pat)_[A-Za-z0-9_]{20,}"),
    re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_\-]{30,}"),
    re.compile(r"\bdp\.(?:st|ct|pt|sa|scim|audit)\.[A-Za-z0-9._\-]{10,}"),
    re.compile(r"\beyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=\-]{16,}"),
    re.compile(
        r"(?i)\b([A-Z0-9_]*(?:API[_-]?KEY|SECRET|TOKEN|PASSWORD|PASSWD|PRIVATE[_-]?KEY)[A-Z0-9_]*)\s*[=:]\s*['\"]?[^\s'\"]{6,}"
    ),
    re.compile(
        r"(?i)\b(postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp)://[^\s:@/]+:[^\s@/]+@"
    ),
    re.compile(r"\b[A-Fa-f0-9]{40,}\b"),
    re.compile(r"\b[A-Za-z0-9+/]{48,}={0,2}(?![A-Za-z0-9+/=])"),
]

_INJECTED = [
    re.compile(r"<graphiti-facts.*?</graphiti-facts>", re.DOTALL),
    re.compile(r"<system-reminder>.*?</system-reminder>", re.DOTALL),
    re.compile(r"<lightrag-context.*?</lightrag-context>", re.DOTALL),
    re.compile(r"<environment_context>.*?</environment_context>", re.DOTALL),
]


def redact(text: str) -> str:
    for pat in _SECRET_PATTERNS:
        text = pat.sub("[REDACTED]", text)
    return text


def strip_injected(text: str) -> str:
    for pat in _INJECTED:
        text = pat.sub("", text)
    return text.strip()


def repo_name(cwd: str | None) -> str:
    """group_id = basename of cwd, sanitised to Graphiti's allowed charset."""
    base = os.path.basename((cwd or os.getcwd()).rstrip("/")) or "main"
    return re.sub(r"[^A-Za-z0-9_\-]", "_", base)


def _post(body: dict, session: str | None, timeout: float):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": "2025-06-18",
    }
    if session:
        headers["Mcp-Session-Id"] = session
    req = urllib.request.Request(
        MCP_URL, data=json.dumps(body).encode(), headers=headers, method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        sid = resp.headers.get("Mcp-Session-Id") or resp.headers.get("mcp-session-id")
        raw = resp.read().decode("utf-8", "replace")
        ctype = resp.headers.get("Content-Type", "")
    if not raw.strip():
        return sid, None
    if "text/event-stream" in ctype:
        payload = None
        for line in raw.splitlines():
            if line.startswith("data:"):
                payload = line[5:].strip()
        return sid, json.loads(payload) if payload else None
    return sid, json.loads(raw)


def healthy(timeout: float = 1.0) -> bool:
    try:
        with urllib.request.urlopen(BASE_URL + "/health", timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def call_tool(name: str, arguments: dict, timeout: float = 4.0):
    """Call one MCP tool. Returns the decoded tool result (dict) or None."""
    sid, _ = _post(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "graphiti-hook", "version": "1"},
            },
        },
        None,
        timeout,
    )
    _post({"jsonrpc": "2.0", "method": "notifications/initialized"}, sid, timeout)
    _, resp = _post(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        },
        sid,
        timeout,
    )
    if not resp or "result" not in resp:
        return None
    result = resp["result"]
    if isinstance(result.get("structuredContent"), dict):
        sc = result["structuredContent"]
        return sc.get("result", sc) if set(sc) == {"result"} else sc
    for part in result.get("content", []):
        if part.get("type") == "text":
            try:
                return json.loads(part["text"])
            except Exception:
                return {"text": part["text"]}
    return None


def current_facts(
    query: str, group_id: str, limit: int = 8, timeout: float = 4.0
) -> list[dict]:
    """Facts whose invalid_at is None, at most min(limit, MAX_FACTS)."""
    limit = max(1, min(limit, MAX_FACTS))
    res = call_tool(
        "search_memory_facts",
        {"query": query[:500], "group_ids": [group_id], "max_facts": limit * 3},
        timeout=timeout,
    )
    if not isinstance(res, dict):
        return []
    facts = [
        f for f in res.get("facts", []) if f.get("invalid_at") is None and f.get("fact")
    ]
    return facts[:limit]


def format_facts(facts: list[dict], repo: str) -> str:
    if not facts:
        return ""
    lines = [f'<graphiti-facts repo="{repo}">']
    for f in facts:
        since = (f.get("valid_at") or "")[:10]
        lines.append(f"- {f['fact'].strip()}" + (f" (since {since})" if since else ""))
    lines.append("</graphiti-facts>")
    return "\n".join(lines)
