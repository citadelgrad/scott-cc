# CLI Tool Preferences

Prefer these modern CLI tools when available:

| Task | Preferred Tool | Fallback | Notes |
|------|---------------|----------|-------|
| File search by content | `rg` (ripgrep) | `grep` | Use `-C 3` for context when showing matches |
| File search by name | `fd` | `find` | Respects .gitignore, faster than find |
| Directory listing | `lsd -la` | `ls -la` | Shows git status, better formatting |
| Display file contents | `bat --style=plain` | `cat` | Use for showing code to user |
| Follow file changes | `uu-tail -f` | `tail -f` | uutils uses kqueue (efficient, no polling) |
| View file start | `uu-head` | `head` | Rust-based from uutils-coreutils |

**Important:** These tools are installed at `/opt/homebrew/bin/` and should be preferred for their speed and better output formatting.

**uutils note:** The `uu-*` tools are from `uutils-coreutils` (Rust rewrite of GNU coreutils). They use modern system APIs like kqueue on macOS instead of polling, making them more resource-efficient for operations like `tail -f`.

## Environment Variables: direnv (.envrc)

**Always use `.envrc` files with [direnv](https://direnv.net/) for managing environment variables and secrets.** direnv automatically loads/unloads environment variables when entering/leaving a directory.

- Store secrets and environment-specific config in `.envrc` files (never hardcode in source)
- `.envrc` files should be in `.gitignore` — never commit secrets to git
- When a project needs env vars (API keys, database URLs, etc.), create or update the `.envrc` file
- Use `dotenv` or `source_env` directives in `.envrc` to load from `.env` files when needed
- If a project is missing a `.envrc`, suggest creating one for any required environment variables

## Service Management: Makefiles

**Always use a Makefile as the primary interface for starting, stopping, and managing services.** Every project with services should have a Makefile with standard targets.

- Services must run in the background (detached mode) — never block the terminal
- Standard targets: `make up`, `make down`, `make restart`, `make status`, `make logs`
- For Docker Compose services, use `docker compose up -d` (detached) in Make targets
- If a project is missing a Makefile, create one with the standard targets
- All service lifecycle commands should go through Make — avoid raw `docker compose` or direct process management in normal workflows

## Port Selection: Avoid Defaults

**Never use default ports (3000, 5000, 8000, 8080, etc.) when setting up new services.** Multiple projects run simultaneously on this machine and default ports cause conflicts.

- Choose a unique, non-standard port for each new service (e.g., 3847, 9142, 7631)
- Check what's already in use before picking a port: `lsof -i -P | grep LISTEN`
- Document chosen ports in the project's Makefile or README
- When configuring Docker Compose, web servers, or dev servers, always set an explicit custom port
- If a framework defaults to a common port, override it in configuration

## Python Dependencies: uv Only

**uv is the only allowed Python package manager — globally, in projects, and inside containers.** Never use pip, pip-tools, poetry, pipenv, or conda.

- Use `uv add <package>` to add dependencies (not `pip install`)
- Use `uv sync` to install from lock file (not `pip install -r`)
- Use `uv run <command>` to run tools in the project environment
- **Inside Dockerfiles and containers:** install uv and use it there too — no `pip install` even in Docker
- Dockerfile pattern:
  ```dockerfile
  COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
  RUN uv sync --frozen --no-dev
  ```
- If you see `pip install` in an existing Dockerfile or script, flag it for migration to uv

## Architecture Diagrams

When creating architecture or system diagrams:

- **Always use C4 model** (Context, Container, Component levels) to structure diagrams
- **Use standard Mermaid `flowchart`** syntax, NOT the `C4Context`/`C4Container`/`C4Component` Mermaid plugin (it has broken layout with overlapping labels)
- Apply C4 conventions via styling: color-code nodes by type (person, system, container, external), use subgraphs for system boundaries
- **Keep node labels short** (max ~5 words). Put details in a separate legend table below the diagram, not inside node text
- **Use `flowchart TB`** (top-to-bottom) for hierarchy diagrams, `flowchart LR` (left-to-right) for sequence-like flows
- Include a **sequence diagram** (`sequenceDiagram`) alongside C4 levels when showing runtime behavior
- Save diagrams as `.md` files in `docs/`
- When creating Graphviz charts in markdown use `graphviz` as the language identifier

## Code Analysis: TLDR MCP

When analyzing code, prefer using TLDR tools (via the `tldr` MCP server) for:

- **Function context**: use `tldr_context` instead of reading entire files
- **Call graphs**: use `tldr_impact` to see who calls a function
- **Semantic search**: use `tldr_semantic` for natural language code search
- **Code structure**: use `tldr_structure` to list functions/classes without reading raw files
- **Dead code**: use `tldr_dead` to find unreachable code
- **Program slicing**: use `tldr_slice` to trace what affects a specific line
