# Makefile Templates

Auto-generated Makefile templates based on project type detection.

## Python Project Template

Use when `pyproject.toml` is detected:

```makefile
.PHONY: up down restart status logs test lint

up:
	docker compose up -d

down:
	docker compose down

restart: down up

status:
	docker compose ps

logs:
	docker compose logs -f

test:
	uv run pytest

lint:
	uv run ruff check .
```

## Node/TypeScript Project Template

Use when `package.json` or `tsconfig.json` is detected:

```makefile
.PHONY: up down restart status logs test lint

up:
	docker compose up -d

down:
	docker compose down

restart: down up

status:
	docker compose ps

logs:
	docker compose logs -f

test:
	npm test

lint:
	npx biome check .
```

## Unknown Project Type Template

Use when none of the above project markers are detected:

```makefile
.PHONY: up down restart status logs

up:
	docker compose up -d

down:
	docker compose down

restart: down up

status:
	docker compose ps

logs:
	docker compose logs -f
```

## Notes

- **Indentation:** Use tabs for recipe lines, not spaces (Makefile requirement).
- **logs target:** Intentionally streams with `-f`. Do not chain it from other targets.
- **Never overwrite:** If `Makefile` already exists in the project, skip entirely. Do not ask.
