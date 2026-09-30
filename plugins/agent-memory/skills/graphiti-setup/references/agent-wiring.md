# Per-agent wiring (manual fallback)

`scripts/wire_agents.py` does all of this. Use this file when the script cannot edit a file, or to check its result. Replace `$URL` with the base URL (for example `http://127.0.0.1:48100`) and `$HOOKS` with `~/.local/share/graphiti-hooks`.

Rules for every file: back it up once as `<file>.bak-graphiti`, merge (never overwrite), keep existing hooks and servers, validate after the edit.

## Memory pointer (all agents)

Append this block to the always-loaded file. The markers let `--remove` find it.

```
<!-- graphiti-memory:start -->
## Memory
Project facts live in Graphiti (MCP server `graphiti`, group_id = repo name).
Current facts for each prompt arrive in <graphiti-facts>. They win over older notes.
Before you change tooling, dependencies or conventions, call search_memory_facts.
When the user corrects you, call add_memory.
Do not save project facts in MEMORY.md.
<!-- graphiti-memory:end -->
```

Always-loaded file per agent:

| Agent | File | Why |
|-------|------|-----|
| Claude Code | `~/.claude/CLAUDE.md` | User memory file, loaded in every session |
| Codex CLI | `~/.codex/AGENTS.md` | Global instructions, loaded in every session |
| Hermes Agent | `~/.hermes/SOUL.md` | Hermes puts this file in every system prompt. Other Hermes notes files are loaded on demand, so a pointer there can be skipped. |

## Claude Code

MCP server (user scope):

```bash
claude mcp add --scope user --transport http graphiti $URL/mcp
claude mcp list          # graphiti must show Connected
```

Hooks in `~/.claude/settings.json`. Merge these entries into the existing `hooks` object. Keep other entries.

```json
{
  "hooks": {
    "UserPromptSubmit": [{"hooks": [{"type": "command", "command": "uv run --script $HOOKS/graphiti_context.py", "timeout": 10}]}],
    "SessionStart": [{"matcher": "startup|resume|compact", "hooks": [{"type": "command", "command": "uv run --script $HOOKS/graphiti_context.py", "timeout": 10}]}],
    "SessionEnd": [{"hooks": [{"type": "command", "command": "uv run --script $HOOKS/graphiti_ingest.py", "timeout": 5}]}]
  }
}
```

Write the real expanded path for `$HOOKS` (no tilde or variable). Validate: `jq empty ~/.claude/settings.json`. Plain stdout from the two context hooks is added to the model context.

## Codex CLI

MCP server. This writes `[mcp_servers.graphiti]` with `url = "$URL/mcp"` in `~/.codex/config.toml`:

```bash
codex mcp add graphiti --url $URL/mcp
codex mcp get graphiti
```

Hooks in `~/.codex/hooks.json`. Same three entries and same JSON shape as Claude Code. Validate: `jq empty ~/.codex/hooks.json`. If `config.toml` was edited by hand, validate it: `python3 -c "import tomllib,sys; tomllib.load(open(sys.argv[1],'rb'))" ~/.codex/config.toml`. Check that your Codex version enables hooks (see `codex --help` or its docs). The session transcript is in Codex `rollout-*.jsonl` (`response_item` lines), and the ingest hook reads that shape.

## Hermes Agent

`hermes mcp add` asks interactive questions, so edit `~/.hermes/config.yaml` directly. Merge these blocks into the existing top-level keys:

```yaml
mcp_servers:
  graphiti:
    url: $URL/mcp
    enabled: true
hooks:
  pre_llm_call:
    - command: uv run --script $HOOKS/graphiti_context.py
      timeout: 10
  post_llm_call:
    - command: uv run --script $HOOKS/graphiti_ingest.py
      timeout: 5
  on_session_finalize:
    - command: uv run --script $HOOKS/graphiti_ingest.py
      timeout: 5
```

`pre_llm_call` output must be JSON `{"context": "..."}`. The context hook does this when it sees the Hermes payload. `post_llm_call` only buffers one turn on disk (no network). `on_session_finalize` sends the buffer to Graphiti in a detached process.

Approve the hooks once: `hermes --accept-hooks -z "ping"`, or set `hooks_auto_accept: true`. Check: `hermes hooks doctor` and `hermes mcp test graphiti`.

If `mcp_servers:` or `hooks:` already contains the same key, merge by hand. The script stops and tells you in that case.

## Hook input shapes (reference)

| Agent | Event | Fields used |
|-------|-------|-------------|
| Claude Code, Codex | UserPromptSubmit | `prompt`, `cwd` |
| Claude Code, Codex | SessionStart | `source` (startup, resume, compact), `cwd` |
| Claude Code, Codex | SessionEnd | `transcript_path`, `session_id`, `cwd` |
| Hermes | pre_llm_call | `extra.user_message`, `cwd` |
| Hermes | post_llm_call | `extra.user_message`, `extra.assistant_response`, `session_id` |
| Hermes | on_session_finalize | `session_id`, `cwd` |

The Graphiti `group_id` is the basename of `cwd`, with any character outside `A-Za-z0-9_-` replaced by `_`.
