# Troubleshooting

First commands: `cd <service dir> && make status`, then `make logs` (streams with `-f`; stop it with Ctrl-C, or use `docker compose logs --tail=50 graphiti` for a fixed read).

| Symptom or error text | Cause | Fix |
|-----------------------|-------|-----|
| HTTP 307 on `/mcp/` | The server redirects the trailing-slash path, and some clients do not follow the redirect on POST | Use `http://127.0.0.1:<port>/mcp` with no slash, in every agent config and in `GRAPHITI_URL` (the base URL has no `/mcp`) |
| `add_memory` answers "queued" but search finds nothing | Ingest is asynchronous (several LLM calls per episode) | Wait up to 2 minutes. If still empty, read the log |
| `404 ... models/gemini-2.5-flash-lite is not found` | Retired default small model (image graphiti-core 0.29.1) | Conditional patch in `references/providers-and-secrets.md` |
| `temperature` is not supported / unexpected keyword (anthropic) | anthropic SDK 1.3 in the image | Use openai or gemini |
| `401`, `API key not valid`, `Incorrect API key` | Key empty or wrong inside the container | Check the secret source. `make restart` after a change |
| `429` or quota errors | Provider rate limit | Lower `SEMAPHORE_LIMIT` (Makefile, default 5), retry later |
| Search returns facts, dimension error in log | Embedder dimension changed after data was stored | `clear_graph` for the group, or use a new group |
| `Bind for 127.0.0.1:<port> failed: port is already allocated` | Port in use | `lsof -nP -iTCP:<port> -sTCP:LISTEN`, choose another port, re-run `render_service.py`, `make restart`, re-run `wire_agents.py --url` |
| `Cannot connect to the Docker daemon` | Docker Desktop or OrbStack not running | Ask the user to start it |
| `make: *** No rule to make target` | Wrong directory | `cd` to the service dir |
| Container restarts in a loop | Bad `config.yaml` or missing key | `docker compose logs --tail=50 graphiti` |
| Hook prints nothing | Server down, prompt shorter than 8 characters, prompt starts with `/`, or no current facts | `make status`, then the pipe tests in `references/verification.md` |
| Hook works in a shell but not in the agent | Wrong path in agent config, or `uv` not on the agent's PATH | Use the expanded hooks path. Check `which uv`. Use the full path to `uv` in the hook command if needed |
| Hermes hook never runs | Hooks not approved | `hermes --accept-hooks -z "ping"`, `hermes hooks doctor` |
| Hermes: `hooks.pre_llm_call already exists` (script message) | A hook of that name is already set | Merge the entry by hand (`references/agent-wiring.md`) |
| Claude or Codex does not load the MCP server | Added in the wrong scope, or agent not restarted | `claude mcp list`, restart the agent |
| `jq: parse error` after an edit | A manual edit broke JSON | Restore `<file>.bak-graphiti`, run `wire_agents.py` again |
| Facts from a different project appear | Two repos share the same folder name (group id is the basename) | Rename the folder, or set a unique name; data is per group |
| Old fact still shown | Fact is not yet invalidated | Hooks hide facts that have `invalid_at`. Add the correction with `add_memory` and wait for ingest |

## Known image-specific facts (verify again on a new image)

- Image `zepai/knowledge-graph-mcp` contains the MCP server and FalkorDB in one container. The container exposes MCP on 8000, FalkorDB on 6379 and the browser UI on 3000 (the compose template maps them to loopback ports).
- Config values use `${VAR:default}` expansion.
- Each `group_id` has its own graph.
- The server has no authentication. Keep the ports on 127.0.0.1.

Check the image before you rely on these: `docker image inspect zepai/knowledge-graph-mcp:latest --format '{{.Created}} {{.Id}}'`.
