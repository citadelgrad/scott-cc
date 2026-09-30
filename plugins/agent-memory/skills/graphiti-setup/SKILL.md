---
name: graphiti-setup
description: Use when the user wants shared persistent memory across Claude Code, Codex CLI and Hermes Agent on macOS, asks to install or repair Graphiti, a knowledge-graph MCP memory server, or sees Graphiti hook, /mcp 307 or add_memory errors.
metadata:
  category: technique
  triggers: graphiti, agent memory, shared memory, knowledge graph mcp, falkordb, add_memory, search_memory_facts, zepai/knowledge-graph-mcp
---

# Graphiti Setup (macOS)

Install Graphiti as one local memory service. Wire Claude Code, Codex CLI and Hermes Agent to it. Hooks push current facts into each prompt and save each session.

Work in this order. Do not skip preflight. Do not print secret values at any step.

## When to Use

- The user wants one memory shared by more than one coding agent.
- The user asks to install, repair, move or remove Graphiti.
- Errors: `307` on `/mcp/`, empty `<graphiti-facts>`, `add_memory` queued but nothing found, 404 on a Gemini model.

Not for: a Linux or Windows host (adapt by hand), a remote or multi-user server (the service has no authentication), or project-level notes (use the repo docs).

## Scripts in this skill

Run them with `uv run --script <path>`. `$SK` is this skill's directory.

| Script | Use |
|--------|-----|
| `$SK/scripts/preflight.py` | Step 1. JSON report. Exit 1 if not ready. |
| `$SK/scripts/render_service.py` | Step 3. Writes the service directory. |
| `$SK/scripts/wire_agents.py` | Steps 4 and 5. `--dry-run` first. `--remove` to undo. |
| `$SK/scripts/smoke_test.py` | Step 6. Needs a running server. |

## 1. Preflight

```bash
uv run --script $SK/scripts/preflight.py --ports 48100,48101,48102
```

Read the report. Fix these before you continue:
- `macos` true, `docker_running` true (the user must start Docker Desktop or OrbStack).
- `missing_required` empty (`docker uv jq git curl lsof`).
- `ports_free` true. If a port is in use, choose three other free ports in the 40000-49999 range and use them in every later step. Never use 3000, 5000, 8000 or 8080.
- `agents`: wire only the agents that are `true`.
- `keys_present`: at least one provider key must be set. If none is set, ask the user how they keep secrets (step 2). Do not ask them to paste a key into the chat.

## 2. Choose provider and secret source

| Choice | Models (defaults) | Notes |
|--------|------------------|-------|
| `openai` (default) | `gpt-5.5`, `text-embedding-3-small`, 1536 dims | Upstream default. Simplest. No patch needed. |
| `gemini` | `gemini-2.5-flash`, `gemini-embedding-001`, 768 dims | Needs the conditional patch check below. |
| others | anthropic, groq, azure_openai, voyage | See `references/providers-and-secrets.md`. Anthropic fails on image 0.29.1. |

Secret source (`--secrets`): `env-file` (default: git-ignored `.env`, mode 600), `doppler`, `op`, `direnv`. Details and exact flags: `references/providers-and-secrets.md`.

Embedding dimensions are fixed per graph. If you change provider later, run `clear_graph` or use a new group.

Conditional Gemini patch. The known problem applies to image `zepai/knowledge-graph-mcp` with graphiti-core 0.29.1 (built 2026-09-01): the built-in small model `gemini-2.5-flash-lite` returns 404. Check whether it still applies before you patch. Start the service without the patch, run step 6, and read `make logs`.

Patch only if the log shows a 404 for `gemini-2.5-flash-lite`. Then re-run step 3 with `--patch-gemini`. If the image has a newer graphiti-core, compare the two files in `assets/*.patched` with the new upstream first. Do not mount an old patch over a newer file without a diff.

## 3. Render the service directory

```bash
uv run --script $SK/scripts/render_service.py --dir ~/services/graphiti --llm openai \
  --mcp-port 48100 --db-port 48101 --ui-port 48102
```

Add `--secrets doppler --doppler-project P --doppler-config C`, `--secrets op --op-env-file F`, `--secrets direnv`, or `--patch-gemini` as needed. The script backs up changed files as `*.bak-graphiti` and never overwrites an existing `.env`.

If the user chose `env-file`: tell the user to put the key value in `<dir>/.env` themselves. Check only that the variable is non-empty (`grep -c '^OPENAI_API_KEY=.' .env`). Never print it.

Start and verify, always through the Makefile:

```bash
cd ~/services/graphiti && make up     # runs make status at the end
```

Status must show the container healthy and `/health` answering. Run `make status` again after 20 seconds if the first check is too early. Ports bind to 127.0.0.1 only. Do not change that.

## 4. Install hooks to a stable path

`wire_agents.py` copies the three hook scripts to `~/.local/share/graphiti-hooks/` and points every agent at that copy. It also writes `~/.config/graphiti-hooks/config.json` with the server URL, so the hooks find a non-default port.

Why a copy and not the plugin path: the plugin cache path contains the version number, so it breaks on every plugin update or removal. Codex and Hermes do not run from the plugin cache at all. A fixed path works for all three agents and survives plugin changes. The cost is that a newer plugin version does not update the hooks. Re-run `wire_agents.py` to refresh the copy.

The hooks read the server address from `GRAPHITI_URL`, or `GRAPHITI_MCP_PORT`, or the config file, in that order.

Hook behaviour (keep it when you edit): fail silent and fast (health check 1 s, search 4 s, exit 0 always), at most 8 current facts per prompt (invalidated facts removed), secrets redacted before any text is saved, ingest runs in a detached process.

## 5. Wire the agents

```bash
uv run --script $SK/scripts/wire_agents.py --agents auto --url http://127.0.0.1:48100 --dry-run
uv run --script $SK/scripts/wire_agents.py --agents auto --url http://127.0.0.1:48100
```

The script backs up each edited file as `<file>.bak-graphiti`, merges (it keeps all existing hooks and servers), validates JSON and TOML, and adds a marked Memory pointer. Per-agent details, exact snippets and the manual fallback are in `references/agent-wiring.md`.

| Agent | MCP server | Hooks | Pointer file (always loaded) |
|-------|-----------|-------|------------------------------|
| Claude Code | `claude mcp add --scope user --transport http graphiti <url>/mcp` | `~/.claude/settings.json` | `~/.claude/CLAUDE.md` |
| Codex CLI | `codex mcp add graphiti --url <url>/mcp` | `~/.codex/hooks.json` | `~/.codex/AGENTS.md` |
| Hermes Agent | `mcp_servers.graphiti` in `~/.hermes/config.yaml` | `hooks:` in the same file | `~/.hermes/SOUL.md` |

The MCP URL must end in `/mcp` with no trailing slash. `/mcp/` answers 307 and some clients fail on the redirect.

Hermes: SOUL.md is the file Hermes loads into every system prompt, so the pointer goes there. Hermes hooks need approval. Run `hermes --accept-hooks -z "ping"` once (or set `hooks_auto_accept: true`), then `hermes hooks doctor`.

## 6. Verify

1. `uv run --script $SK/scripts/smoke_test.py` adds an episode, waits for extraction, checks that the new fact is current, and clears the test group. Extraction takes 30 to 120 seconds.
2. Hook pipe test for each input shape. Commands are in `references/verification.md`. Each must print facts for a known repo, and must print nothing when the server is stopped.
3. `claude mcp list`, `codex mcp get graphiti`, `hermes mcp test graphiti`: each must show connected.
4. Start a new session in a repo that has facts. Ask a question that the facts answer.

Report pass or fail for each item with the real output. If a check fails, use the troubleshooting table, then retry. Do not claim success unless check 1 passes.

## 7. Uninstall and rollback

```bash
uv run --script $SK/scripts/wire_agents.py --agents auto --remove
cd ~/services/graphiti && make down
```

`--remove` strips only what the script added (MCP server, hook entries, Memory pointer). To restore files byte for byte, copy each `<file>.bak-graphiti` back. Data lives in Docker volumes `falkordb_data` and `mcp_logs`. `docker compose down -v` deletes the memory. Do that only if the user asks. Full steps: `references/uninstall-and-rollback.md`.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `307 Temporary Redirect` from MCP | URL ends in `/mcp/` | Use `/mcp` |
| `add_memory` returns queued, search is empty | Extraction is asynchronous, or an LLM call failed | Wait 2 minutes. `make logs`, look for 401, 404, 429 |
| 404 model not found (`gemini-2.5-flash-lite`) | Retired default small model in 0.29.1 | Conditional patch, step 2 |
| `temperature` error with anthropic | anthropic SDK 1.3 in the image rejects it | Use openai or gemini |
| 401 or `API key` error in logs | Key empty inside the container | Check `.env` or the wrapper, then `make restart` |
| Embedding dimension mismatch | Provider changed after data exists | `clear_graph` or new group |
| Hook prints nothing | Server down, prompt under 8 chars, slash command, or no facts | `make status`, then the pipe test |
| Hermes hook never runs | Not approved | `--accept-hooks`, `hermes hooks doctor` |
| Port already in use | Another service | Pick other free ports, re-render, re-wire |
| `make up` fails with docker error | Docker not running | Start Docker Desktop or OrbStack |

More errors and causes: `references/troubleshooting.md`.

## Rules

- Never print, log or commit a key value. Check presence only.
- Never bind to anything but 127.0.0.1. The server has no authentication.
- Manage the service only through the Makefile targets (`up down restart status logs`).
- Edit agent config only through merge plus `.bak-graphiti` backups.
- Do not add cron, launchd or background loops.
