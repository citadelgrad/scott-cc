# Verification

Run every check. Report the real output, not a summary. `$SK` is the skill directory. Use a group name that is not a real project for test data.

## 1. Service

```bash
cd ~/services/graphiti && make status
curl -s --max-time 3 http://127.0.0.1:48100/health
```

Expect: container `healthy`, and a health reply (HTTP 200). Use your MCP port if it is not 48100.

MCP redirect check (must not be 307):

```bash
curl -s -o /dev/null -w '%{http_code}\n' -X POST http://127.0.0.1:48100/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"ping"}'
```

Any code except 307 is fine here (the test shows the path is served). `/mcp/` with a trailing slash returns 307.

## 2. Smoke test (episode, search, invalidation, cleanup)

```bash
uv run --script $SK/scripts/smoke_test.py
```

What it does: `clear_graph` on group `graphiti-smoke-test`, `add_memory` with "api package uses Vitest, replaced Jest", poll `search_memory_facts` for up to 180 s, print each fact with `invalid_at`, `clear_graph` again. PASS means a current Vitest fact exists. A Jest fact with `invalid_at` set is the proof of invalidation, but the model may not return it, so it is reported and not required.

FAIL: read `make logs` (troubleshooting table).

## 3. Hook pipe tests

The hooks read JSON on stdin. Use a repo name that has facts (group id = basename of `cwd`). Check the hooks dir path first: `ls ~/.local/share/graphiti-hooks`.

Claude Code or Codex prompt shape (prints plain text):

```bash
echo '{"hook_event_name":"UserPromptSubmit","prompt":"which test runner do we use?","cwd":"/path/to/REPO"}' \
  | uv run --script ~/.local/share/graphiti-hooks/graphiti_context.py
```

Session start shape:

```bash
echo '{"hook_event_name":"SessionStart","source":"startup","cwd":"/path/to/REPO"}' \
  | uv run --script ~/.local/share/graphiti-hooks/graphiti_context.py
```

Hermes shape (prints one JSON line with `context`):

```bash
echo '{"hook_event_name":"pre_llm_call","cwd":"/path/to/REPO","extra":{"user_message":"which test runner do we use?"}}' \
  | uv run --script ~/.local/share/graphiti-hooks/graphiti_context.py
```

Expect `<graphiti-facts repo="REPO">` with at most 8 lines. Empty output is correct if the repo has no facts.

Service down test: `make down`, run the same commands. Expect no output, exit code 0 (`echo $?`), and a fast return (under 2 s). Then `make up`.

Ingest buffer test (Hermes shape, no network): pipe a `post_llm_call` payload, then check that `~/.local/state/graphiti-hooks/hermes-<session_id>.jsonl` exists and holds no secret text.

Ingest log: `tail ~/.local/state/graphiti-hooks/ingest.log` shows `sent` or `skip ... service down`.

## 4. Agent registration

```bash
claude mcp list                 # graphiti: Connected
codex mcp get graphiti          # shows url .../mcp
hermes mcp test graphiti        # lists the tools
hermes hooks doctor             # hooks approved and runnable
```

Expected tools: `add_memory`, `search_memory_facts`, `search_nodes`, `get_episodes`, `delete_episode`, `delete_entity_edge`, `clear_graph`, `get_status` (names can differ by version).

## 5. Tests in this repository

```bash
uv run --no-project --with pytest pytest scripts/tests/test_graphiti_hooks.py -q
```

Offline. It needs no running server.

## 6. Cleanup of test data

`smoke_test.py` clears its own group. To remove a leftover group by hand, call the `clear_graph` tool with `group_ids: ["graphiti-smoke-test"]` from any connected agent. Do not clear a real project group unless the user asks.
