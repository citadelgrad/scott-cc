#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Render the Graphiti service directory from the templates in ../assets.

Usage:
  render_service.py --dir ~/services/graphiti --llm openai
  render_service.py --dir ~/services/graphiti --llm gemini --secrets doppler \
      --doppler-project P --doppler-config C --patch-gemini

Writes docker-compose.yml, Makefile, config/config.yaml, .gitignore and (for
--secrets env-file) an EMPTY .env template with mode 600. It never reads or
prints a secret value. Existing files are backed up as <file>.bak-graphiti
before they are replaced.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"

PRESETS: dict[str, dict[str, str]] = {
    "openai": {
        "llm_provider": "openai",
        "llm_model": "gpt-5.5",
        "embedder_provider": "openai",
        "embedder_model": "text-embedding-3-small",
        "dims": "1536",
        "key_var": "OPENAI_API_KEY",
    },
    "gemini": {
        "llm_provider": "gemini",
        "llm_model": "gemini-2.5-flash",
        "embedder_provider": "gemini",
        "embedder_model": "gemini-embedding-001",
        "dims": "768",
        "key_var": "GOOGLE_API_KEY",
    },
}

PATCH_VOLUMES = (
    "      # CONDITIONAL patch, see SKILL.md: upstream default small model is retired (404).\n"
    "      - ./config/gemini_client.py:/app/mcp/.venv/lib/python3.13/site-packages/graphiti_core/llm_client/gemini_client.py:ro\n"
    "      - ./config/gemini_reranker_client.py:/app/mcp/.venv/lib/python3.13/site-packages/graphiti_core/cross_encoder/gemini_reranker_client.py:ro\n"
)


def secrets_wrapper(args: argparse.Namespace, key_var: str) -> tuple[str, str]:
    """Return (makefile wrapper prefix, human note). Compose reads .env itself."""
    if args.secrets == "doppler":
        parts = ["doppler run"]
        if args.doppler_project:
            parts.append(f"--project {args.doppler_project}")
        if args.doppler_config:
            parts.append(f"--config {args.doppler_config}")
        return " ".join(
            parts + ["--"]
        ), f"{key_var} is injected by doppler run at `make up`."
    if args.secrets == "op":
        if not args.op_env_file:
            sys.exit("--secrets op needs --op-env-file (a file of op:// references)")
        return (
            f"op run --env-file={args.op_env_file} --",
            f"{key_var} is resolved by 1Password `op run`.",
        )
    if args.secrets == "direnv":
        return (
            "direnv exec .",
            f"{key_var} comes from this directory's .envrc via direnv.",
        )
    return (
        "",
        f"{key_var} is read from the git-ignored .env in this directory (mode 600).",
    )


def render(text: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        text = text.replace(f"@{key}@", value)
    if "@" in text and any(f"@{k}@" in text for k in values):
        raise ValueError("unrendered placeholder left in template")
    return text


def write(
    path: Path, content: str, mode: int | None = None, force: bool = False
) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text() == content:
            return f"unchanged {path}"
        backup = path.with_name(path.name + ".bak-graphiti")
        if not backup.exists():
            shutil.copy2(path, backup)
    path.write_text(content)
    if mode is not None:
        os.chmod(path, mode)
    return f"wrote {path}"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--dir", default="~/services/graphiti")
    p.add_argument("--llm", choices=sorted(PRESETS), default="openai")
    p.add_argument("--llm-model")
    p.add_argument("--embedder-model")
    p.add_argument("--embedder-dims", type=int)
    p.add_argument("--mcp-port", type=int, default=48100)
    p.add_argument("--db-port", type=int, default=48101)
    p.add_argument("--ui-port", type=int, default=48102)
    p.add_argument(
        "--secrets", choices=["env-file", "doppler", "op", "direnv"], default="env-file"
    )
    p.add_argument("--doppler-project")
    p.add_argument("--doppler-config")
    p.add_argument("--op-env-file")
    p.add_argument(
        "--patch-gemini",
        action="store_true",
        help="CONDITIONAL: mount the patched gemini files. Use only if the image still needs it.",
    )
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    preset = PRESETS[args.llm]
    target = Path(args.dir).expanduser()
    wrapper, note = secrets_wrapper(args, preset["key_var"])
    values: dict[str, str] = {
        "LLM_PROVIDER": preset["llm_provider"],
        "LLM_MODEL": args.llm_model or preset["llm_model"],
        "EMBEDDER_PROVIDER": preset["embedder_provider"],
        "EMBEDDER_MODEL": args.embedder_model or preset["embedder_model"],
        "EMBEDDER_DIMS": str(args.embedder_dims or preset["dims"]),
        "MCP_PORT": str(args.mcp_port),
        "DB_PORT": str(args.db_port),
        "UI_PORT": str(args.ui_port),
        "SECRETS_WRAPPER": wrapper,
        "SECRETS_NOTE": note,
        "PATCH_VOLUMES": PATCH_VOLUMES if args.patch_gemini else "",
    }
    plan = {
        target / "docker-compose.yml": render(
            (ASSETS / "docker-compose.yml.tmpl").read_text(), values
        ),
        target / "Makefile": render((ASSETS / "Makefile.tmpl").read_text(), values),
        target / "config" / "config.yaml": render(
            (ASSETS / "config.yaml.tmpl").read_text(), values
        ),
        target / ".gitignore": ".env\n.envrc\n*.bak-graphiti\n",
    }
    if args.secrets == "env-file":
        plan[target / ".env"] = (
            f"# Fill in the value, keep this file mode 600 and out of git.\n{preset['key_var']}=\n"
        )
    if args.dry_run:
        for path in plan:
            print(f"would write {path}")
        return 0
    for path, content in plan.items():
        if path.name == ".env" and path.exists():
            print(f"kept {path} (never overwritten)")
            continue
        print(write(path, content, mode=0o600 if path.name == ".env" else None))
    if args.patch_gemini:
        for name in ("gemini_client.py", "gemini_reranker_client.py"):
            print(
                write(
                    target / "config" / name, (ASSETS / f"{name}.patched").read_text()
                )
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
