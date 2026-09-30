# Providers and secrets

## Provider table

| Provider | `render_service.py --llm` | Key variable | Status on image graphiti-core 0.29.1 |
|----------|---------------------------|--------------|--------------------------------------|
| OpenAI | `openai` (default) | `OPENAI_API_KEY` | Upstream default. Works with no patch. |
| Google Gemini | `gemini` | `GOOGLE_API_KEY` | Works. Small model default 404s, so the conditional patch may be needed. |
| Anthropic | edit `config.yaml` by hand | `ANTHROPIC_API_KEY` | Fails: the anthropic SDK in the image rejects the `temperature` argument. Needs a separate embedder too. |
| Groq | edit `config.yaml` by hand | `GROQ_API_KEY` | Not tested. Needs a separate embedder. |
| Azure OpenAI | edit `config.yaml` by hand | see upstream README | Not tested. |
| Voyage (embedder only) | edit `config.yaml` by hand | `VOYAGE_API_KEY` | Not tested. |

"Not tested" means the provider exists in the upstream config. This skill has no proof that it works. Test with `smoke_test.py`.

The embedder dimension must match the embedder model. Changing it after data exists breaks search. Run `clear_graph` (or use a new group) first.

## Conditional patch (Gemini, image 0.29.1)

Files: `assets/gemini_client.py.patched`, `assets/gemini_reranker_client.py.patched`.

| Item | Value |
|------|-------|
| Applies to | `zepai/knowledge-graph-mcp`, graphiti-core 0.29.1, image built 2026-09-01 |
| Problem | Built-in small model `gemini-2.5-flash-lite` returns 404 for new users |
| Change | The two default model constants become `gemini-3.5-flash-lite` (lines marked `PATCHED`) |
| Mount | Read-only, over the two files under `graphiti_core/` in the image venv (`python3.13` path in the compose template) |

Check again before you use it:

1. Start the service without the patch. Run `smoke_test.py`. Read `make logs`.
2. No 404 for `gemini-2.5-flash-lite`? Do not patch.
3. 404 and the image is still 0.29.1? Run `render_service.py ... --patch-gemini`, then `make restart`.
4. 404 and the image is newer? `docker compose exec graphiti pip show graphiti-core` (or read the venv). Diff the `.patched` files against the new upstream files. If the model constant is the only difference, apply the same one-line change to the new file. Do not mount the old file.

A cleaner fix, if the upstream config accepts a small-model setting in your version: set it in `config.yaml` and skip the patch.

## Secret sources

The compose file reads `${OPENAI_API_KEY:-}` (and the other key variables) from the environment of `docker compose`. The Makefile runs compose through a `SECRETS` prefix. Nothing secret is written to compose, Makefile or config.

| `--secrets` | How the key reaches compose | User does |
|-------------|-----------------------------|-----------|
| `env-file` (default) | Compose reads `<dir>/.env` automatically. File is mode 600 and git-ignored. | Puts `KEY=value` in `.env` |
| `doppler` | `doppler run --project P --config C -- docker compose ...` | Has the key in that Doppler config |
| `op` | `op run --env-file=F -- docker compose ...`. `F` holds `KEY=op://vault/item/field`. | Creates `F` (no real values inside) |
| `direnv` | `direnv exec . docker compose ...`. `.envrc` in the service dir exports the key. | Writes `.envrc`, runs `direnv allow` |

For every source:
- Check presence only: `grep -c '^OPENAI_API_KEY=.' .env`, `doppler secrets get KEY --plain | wc -c`, and so on. Never print the value.
- If the key is set in the shell that runs `make up`, compose also picks it up from there.
- `.gitignore` in the service dir lists `.env`, `.envrc` and backups. If the service dir is inside a git repo, check that `git check-ignore .env` prints the path.
- After a key change, run `make restart`. The container reads the key only at start.
