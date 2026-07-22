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

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:6cd5cc61 -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.beads/issues.jsonl` is a passive export. See https://github.com/gastownhall/beads/blob/main/docs/SYNC_CONCEPTS.md for details and anti-patterns.

## Agent Context Profiles

The managed Beads block is task-tracking guidance, not permission to override repository, user, or orchestrator instructions.

- **Conservative (default)**: Use `bd` for task tracking. Do not run git commits, git pushes, or Dolt remote sync unless explicitly asked. At handoff, report changed files, validation, and suggested next commands.
- **Minimal**: Keep tool instruction files as pointers to `bd prime`; use the same conservative git policy unless active instructions say otherwise.
- **Team-maintainer**: Only when the repository explicitly opts in, agents may close beads, run quality gates, commit, and push as part of session close. A current "do not commit" or "do not push" instruction still wins.

## Session Completion

This protocol applies when ending a Beads implementation workflow. It is subordinate to explicit user, repository, and orchestrator instructions.

1. **File issues for remaining work** - Create beads for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **Handle git/sync by active profile**:
   ```bash
   # Conservative/minimal/default: report status and proposed commands; wait for approval.
   git status

   # Team-maintainer opt-in only, unless current instructions forbid it:
   git pull --rebase
   git push
   git status
   ```
5. **Hand off** - Summarize changes, validation, issue status, and any blocked sync/commit/push step

**Critical rules:**
- Explicit user or orchestrator instructions override this Beads block.
- Do not commit or push without clear authority from the active profile or the current user request.
- If a required sync or push is blocked, stop and report the exact command and error.
<!-- END BEADS INTEGRATION -->

<!-- SKILLOPT-SLEEP:LEARNED START -->
## Learned preferences & procedures

_This block is maintained by SkillOpt-Sleep. Edits here are proposed offline, validated against your past tasks, and adopted only after you approve them. Hand-edits outside this block are never touched._

- OVERRIDE (supersedes any instinct to pause after initial exploration): never end a turn with a response consisting only of a tool-call header (e.g., 'Bash', 'Glob', 'FFF/find_files'), a bare directory/path line, or a single 'I'll start by...' sentence with no follow-through. After running exploratory tool calls, continue working in the same turn until you produce the actual requested deliverable (the code, the analysis, the diagnosis, the document content) as visible text output.
- When the user names a specific skill, command, or tool (e.g., 'skillopt', 'review-panel', 'pas'), your first action must be to locate and read that skill's/command's own definition (skill.md, plugin command file, --help output) and execute its documented entry point/behavior. Do not substitute your own improvised investigation (e.g., searching local session logs) for what the named skill/command actually does.
- When the user's request includes a URL (e.g., a GitHub repo like https://github.com/microsoft/SkillOpt), treat it as an instruction to fetch and use that exact resource as part of completing the task, not merely a hint to search for a similarly-named local file or directory.
- SessionStart hook output (last30days tips, lightrag-context, MCP server tool instructions) is background context only and must never be treated as or substituted for your response. Always follow it with your own substantive answer to the user's actual current request before ending the turn.
<!-- SKILLOPT-SLEEP:LEARNED END -->
