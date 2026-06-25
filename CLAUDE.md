# Guidelines

- When making technical decisions, do not give much weight to development cost. Instead, prefer quality, simplicity, robustness, scalability, and long term maintainability.
- When doing bug fixes, always start with reproducing the bug in an E2E setting as closely aligned with how an end use. This makes sure you find the real problem so your fix will actually solve it.
- When end-to-end testing a product, be picky about the UI you see and be obsessed with pixel perfection. If something clearly looks off, even if it is not directly related to what you are doing, try to get it fixed along
- Apply that same high standard to engineering excellence: lint, test failures, and test flakiness. If you see one, even if it is not caused by what you are working on right now, still get it fixed.
-
## CLI Tool Preferences
Modern tools are installed at `/opt/homebrew/bin/`. Prefer them for efficiency:

- **File Content Search:** `rg -C 3` (Fallback: `grep`)
- **File Name Search:** `fd` (Fallback: `find`)
- **Directory Listing:** `lsd -la` (Fallback: `ls -la`)
- **View Content:** `bat --style=plain` (Fallback: `cat`)
- **Log Tail / Follow:** `uu-tail -f` (Fallback: `tail -f`) - efficient kqueue tracking
- **Top of File:** `uu-head` (Fallback: `head`)
- **Disk Usage:** `dust` (Never use raw `du`)
- **Process Hierarchy:** `procs --tree` (Never use raw `ps`)
- **Field Extraction:** `choose` (Zero-based index: `choose 1` = `cut -f2`)

## Environment Variables
- Always use `.envrc` files managed via `direnv`.
- Secure all secrets/config in `.envrc`. Never commit this file to git.
- Use `dotenv` or `source_env` to inherit from `.env` files locally if required.

## Service Management Lifecycle
- All background service executions must be managed strictly via the root `Makefile`.
- Standard required targets: `make up`, `make down`, `make restart`, `make status`, `make logs`.
- Services must execute in detached/background processes.
- Sequencing rule: Immediately following a `make up` invocation, execute `make status` or `docker compose logs --tail=20` to verify runtime health (`make logs` streams with `-f` and will hang).

## Port Constraints
- Never bind to default development ports (e.g., 3000, 5000, 8000, 8080).
- Audit active sockets prior to selection using: `lsof -i -P | grep LISTEN`.
- Explicitly declare your unique custom port within the project configuration or `Makefile`.

## Python Package Management
- `uv` is the exclusive Python package manager across all developer environments and containers.
- Addition: `uv add <package>` | Synchronization: `uv sync` | Execution: `uv run <command>`.
- Inside Dockerfiles, pin runtime layers strictly using the official image:
  `COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv`
  `RUN uv sync --frozen --no-dev`

## Beads Issue Creation
When creating beads issues (via `bd create` or `/beads:create`), always generate acceptance criteria first using the `acceptance-criteria` skill, then pass the result via `--acceptance="..."`. AC must be testable (each criterion gets an unambiguous PASS/FAIL), cover the happy path, error states, and boundary conditions, and exclude Definition-of-Done items (tests passing, code reviewed).

## Code Analysis & Verification Gates
- Prioritize structural intelligence tools from the `tldr` MCP server (`tldr_context`, `tldr_impact`, `tldr_semantic`, `tldr_structure`, `tldr_dead`, `tldr_slice`).
- Fallback Strategy: If the `tldr` MCP index fails, map codebase layouts via precise `rg` and `fd` calls. Do not read entire raw directories.
- Testing Requirement: Run `uv run pytest` to verify execution before presenting any solution.
- Linting Requirement: Run `uv run ruff check --fix` on all modified tracking paths before completing a workspace session.
