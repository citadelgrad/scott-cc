# Agent Instructions

## Project Conventions

- **Services**: Use `make up/down/restart/status/logs` — never raw docker compose commands
- **Ports**: Never use defaults (3000, 5000, 8080). Pick unique ports, document in Makefile
- **Environment**: Use `.envrc` with direnv for all env vars and secrets — never hardcode
- **Python deps**: `uv` only — `uv add`, `uv sync`, `uv run`. Never pip/poetry/pipenv
- **TypeScript**: biome for lint + format. No eslint/prettier

## Code Style

- Functional over OOP — avoid classes except for custom error types
- No speculative abstractions — solve the actual problem, not hypothetical future ones
- No comments explaining what the code does — good names do that
- Only comment the non-obvious WHY (workarounds, invariants, subtle constraints)

## Git Workflow

Work is not done until pushed:
1. `git add <specific files>`
2. `git commit -m "..."`
3. `git push`

## Task Tracking

This project uses beads (`bd`) for issue tracking:
- `bd ready` — find available work
- `bd show <id>` — view issue details
- `bd close <id>` — mark complete
