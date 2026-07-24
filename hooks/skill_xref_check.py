#!/usr/bin/env python3
"""
Pre-commit check: verify prose cross-references between review-panel skills
still resolve.

plugins/review-panel/skills/*/SKILL.md files disambiguate overlapping skills
with prose like:

    Not for evaluating module depth (use deep-modules) or checking for
    information leakage (use information-hiding).

Each `(use <skill>[, <skill> | or <skill>]*)` parenthetical names one or more
sibling skill directories by name. Nothing enforced that those directories
still exist, so a rename or removal silently breaks the cross-reference.
This script parses every such parenthetical out of every SKILL.md under
plugins/review-panel/skills/ and confirms the named directory is present.

Pure-function core (`find_broken_references`) plus a thin CLI wrapper, same
shape as hooks/data_layer_guard.py. Fails open (exit 0) on unexpected
errors — this is a lint, not a build-breaker for infrastructure problems.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

# Matches one or more skill-name references inside a "(use X)" / "(use X or Y)"
# / "(use X, Y or Z)" parenthetical. Skill names are lowercase kebab-case
# identifiers, optionally wrapped in backticks (e.g. "(use `red-flags`)").
USE_GROUP_RE = re.compile(r"\(use ([^)]*)\)")
SKILL_NAME_RE = re.compile(r"`?([a-z][a-z0-9]*(?:-[a-z0-9]+)+)`?")


@dataclass(frozen=True)
class BrokenReference:
    source_file: Path
    line_number: int
    target: str
    context: str


def extract_referenced_skills(use_group_text: str) -> list[str]:
    """Pull skill-name-shaped tokens out of a '(use ...)' group's inner text.

    Handles comma- and "or"-separated lists ("use X, Y or Z") and backtick-
    wrapped names ("use `red-flags`"). Non-skill-shaped prose like "use that
    skill directly" yields no matches, which is intentional: there's nothing
    concrete to verify there.
    """
    return SKILL_NAME_RE.findall(use_group_text)


def find_broken_references(skills_root: Path) -> list[BrokenReference]:
    """Scan every SKILL.md under skills_root for '(use X)' cross-references
    and return the ones whose target skill directory doesn't exist.

    skills_root is expected to be a .../skills directory whose immediate
    children are skill directories (each containing a SKILL.md).
    """
    broken: list[BrokenReference] = []
    if not skills_root.is_dir():
        return broken

    valid_skill_names = {
        child.name for child in skills_root.iterdir() if child.is_dir()
    }

    for skill_md in sorted(skills_root.glob("*/SKILL.md")):
        source_skill = skill_md.parent.name
        text = skill_md.read_text(encoding="utf-8", errors="replace")

        for line_number, line in enumerate(text.splitlines(), start=1):
            for use_group in USE_GROUP_RE.finditer(line):
                for target in extract_referenced_skills(use_group.group(1)):
                    if target == source_skill:
                        continue  # self-reference, not a cross-skill link
                    if target not in valid_skill_names:
                        broken.append(
                            BrokenReference(
                                source_file=skill_md,
                                line_number=line_number,
                                target=target,
                                context=line.strip(),
                            )
                        )

    return broken


def format_report(broken: list[BrokenReference], skills_root: Path) -> str:
    lines = [
        f"Found {len(broken)} broken skill cross-reference"
        f"{'s' if len(broken) != 1 else ''}:",
        "",
    ]
    for ref in broken:
        try:
            rel = ref.source_file.relative_to(Path.cwd())
        except ValueError:
            rel = ref.source_file
        lines.append(f"  {rel}:{ref.line_number}: references missing skill "
                      f"'{ref.target}'")
        lines.append(f"    {ref.context}")
    lines.append("")
    lines.append(
        "Fix: rename/restore the target skill directory under "
        f"{skills_root}, or update the cross-reference to point at the "
        "skill's new name."
    )
    return "\n".join(lines)


def default_skills_root(start: str = ".") -> Path | None:
    path = Path(start).resolve()
    for candidate in (path, *path.parents):
        candidate_skills = candidate / "plugins" / "review-panel" / "skills"
        if candidate_skills.is_dir():
            return candidate_skills
        if (candidate / ".git").exists():
            # Reached repo root without finding it there either.
            return candidate_skills if candidate_skills.is_dir() else None
    return None


def main(argv: list[str]) -> int:
    skills_root = Path(argv[1]).resolve() if len(argv) > 1 else default_skills_root()

    if skills_root is None or not skills_root.is_dir():
        print(
            "skill_xref_check: could not find plugins/review-panel/skills "
            "(pass a path explicitly to run standalone); skipping.",
            file=sys.stderr,
        )
        return 0

    broken = find_broken_references(skills_root)
    if not broken:
        print(f"skill_xref_check: OK — all cross-references resolve ({skills_root})")
        return 0

    print(format_report(broken, skills_root))
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as exc:  # fail-open: never block a commit on our own bug
        print(f"skill_xref_check: unexpected error, skipping ({exc})", file=sys.stderr)
        sys.exit(0)
