# Uninstall and rollback

Choose the level. Go in this order. Stop at the level the user asked for.

## Level 1: stop using memory, keep data

```bash
uv run --script $SK/scripts/wire_agents.py --agents auto --remove
```

Removes only what the script added:
- the `graphiti` MCP server (Claude via `claude mcp remove`, Codex via `codex mcp remove`, Hermes from `config.yaml`)
- our three hook entries (other hooks stay)
- the Memory pointer block between the `graphiti-memory` markers

Not removed: `~/.local/share/graphiti-hooks/`, `~/.config/graphiti-hooks/config.json`, `~/.local/state/graphiti-hooks/` (buffers, cursors, log), the `.bak-graphiti` files. Delete them by hand if the user wants.

## Level 2: exact restore from backups

Use when the user wants each file back byte for byte:

```bash
cp ~/.claude/settings.json.bak-graphiti ~/.claude/settings.json
cp ~/.claude/CLAUDE.md.bak-graphiti ~/.claude/CLAUDE.md
cp ~/.claude.json.bak-graphiti ~/.claude.json
cp ~/.codex/hooks.json.bak-graphiti ~/.codex/hooks.json
cp ~/.codex/config.toml.bak-graphiti ~/.codex/config.toml
cp ~/.codex/AGENTS.md.bak-graphiti ~/.codex/AGENTS.md
cp ~/.hermes/config.yaml.bak-graphiti ~/.hermes/config.yaml
cp ~/.hermes/SOUL.md.bak-graphiti ~/.hermes/SOUL.md
```

Only restore files that have a backup. A backup is made once, before the first edit. Changes the user made to these files after the install are lost when you restore, so check with `diff <file> <file>.bak-graphiti` first. Validate after a restore (`jq empty`, TOML parse).

## Level 3: stop the service, keep data

```bash
cd ~/services/graphiti && make down
```

Data stays in the Docker volumes `falkordb_data` and `mcp_logs`. `make up` brings it back.

## Level 4: delete the data

Only if the user asks. This cannot be undone.

```bash
cd ~/services/graphiti && docker compose down -v
```

Then delete the service directory, if the user wants: check its content first (`.env` may hold the only copy of a key).

## Check after rollback

- `claude mcp list` and `codex mcp list` do not show `graphiti`.
- `grep -c graphiti ~/.claude/settings.json ~/.codex/hooks.json ~/.hermes/config.yaml` prints 0 for each.
- A new agent session starts with no hook error.
