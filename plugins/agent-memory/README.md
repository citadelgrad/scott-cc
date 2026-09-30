# agent-memory

> Opt-in machine setup for shared, persistent agent memory

## What's Included

### Skills (1)
- **graphiti-setup** - macOS runbook that installs the Graphiti MCP server (Docker, FalkorDB) and wires Claude Code, Codex CLI and Hermes Agent to it, with bundled hooks that inject current facts into every prompt and save each session.

## Why this is a separate plugin

This skill changes the machine, not a project. It needs Docker and an LLM API key, and it edits the global config of up to three agents. Core scott-cc skills install for everyone, so this one is opt-in.

## Install

```bash
/plugin install agent-memory@scott-cc
```

Then ask your agent: "set up Graphiti memory on this Mac".

## Requirements

macOS, Docker Desktop or OrbStack (running), `uv`, `jq`, `git`, `curl`, and one LLM key (OpenAI or Google Gemini). At least one of `claude`, `codex`, `hermes` on PATH.

## Contents of the skill

| Path | Purpose |
|------|---------|
| `SKILL.md` | The runbook (preflight, provider, service, hooks, wiring, verify, rollback) |
| `scripts/preflight.py` | Reports tools, agents, ports and key presence (never key values) |
| `scripts/render_service.py` | Renders compose, Makefile and config from `assets/` |
| `scripts/wire_agents.py` | Merges MCP server, hooks and Memory pointer into each agent, with backups and `--remove` |
| `scripts/graphiti_*.py` | The hook scripts (fail silent, redact, detached ingest) |
| `scripts/smoke_test.py` | Episode, search and invalidation test with cleanup |
| `assets/` | Service templates and conditional Gemini patches |
| `references/` | Per-agent wiring, providers and secrets, verification, troubleshooting, rollback |

Tests: `scripts/tests/test_graphiti_hooks.py` (offline, no server needed).
