#!/usr/bin/env python3
"""Deterministic, read-only cross-check of the review-panel persona catalog.

Parses `plugins/review-panel/reviewers/persona-catalog.md`'s Seat Summary
Table and Excluded section against the real skill directories under
`plugins/review-panel/skills/` and against `design-review/SKILL.md`'s
actual lens list, and emits a findings report. Mirrors
`hooks/data_layer_guard.py`'s canonical-source-plus-sync-test pattern: two
real sources (the filesystem and design-review's text) are diffed against
what the catalog claims, never the other way around.

This script never writes to `--catalog`, `--skills-dir`, or
`--design-review` — it only reads them and writes `--out`.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import NoReturn

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_CATALOG = "plugins/review-panel/reviewers/persona-catalog.md"
DEFAULT_SKILLS_DIR = "plugins/review-panel/skills/"
DEFAULT_DESIGN_REVIEW = "plugins/review-panel/skills/design-review/SKILL.md"

BACKTICK_NAME_RE = re.compile(r"`([a-z0-9\-]+)`")
BOLD_NAME_RE = re.compile(r"\*\*([a-z0-9\-]+)\*\*")
EXCLUDED_BULLET_RE = re.compile(r"^-\s*\*\*(.+?)\*\*(.*)$", re.DOTALL)


@dataclass
class CatalogFinding:
    kind: str  # "undocumented" | "missing_target" | "lens_drift_added" | "lens_drift_removed"
    subject: str
    detail: str


@dataclass
class AuditReport:
    findings: list[CatalogFinding] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not self.findings


def fail(message: str) -> NoReturn:
    print(f"FAIL: {message}")
    sys.exit(1)


def extract_section(text: str, heading_prefix: str) -> str:
    """Slice out the section whose `## ` heading starts with heading_prefix,
    up to (but not including) the next `## ` heading or EOF."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith("## ") and line[3:].startswith(heading_prefix):
            start = i + 1
            break
    if start is None:
        return ""
    end = len(lines)
    for i in range(start, len(lines)):
        if lines[i].startswith("## "):
            end = i
            break
    return "\n".join(lines[start:end])


def parse_catalogued_seats(catalog_text: str) -> set[str]:
    """Extract skill names from the Seat Summary Table's Casts column."""
    section = extract_section(catalog_text, "Seat Summary Table")
    names: set[str] = set()
    for line in section.splitlines():
        line = line.strip()
        if not (line.startswith("|") and line.endswith("|")):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not cells:
            continue
        if cells[0].lower() == "seat":
            continue
        if all(set(cell) <= {"-", ":", ""} for cell in cells):
            continue
        if len(cells) < 2:
            continue
        names.update(BACKTICK_NAME_RE.findall(cells[1]))
    return names


def _iter_excluded_bullets(section: str) -> list[str]:
    """Group the Excluded section's lines into one string per bullet.

    A new bullet starts at a line matching `^-\\s`; continuation lines
    (indented, not prefixed with `-`) accumulate into the current bullet.
    A blank line closes the current bullet, which also excludes the
    trailing prose paragraph after the list.
    """
    bullets: list[str] = []
    current: list[str] | None = None
    for line in section.splitlines():
        if not line.strip():
            if current is not None:
                bullets.append("\n".join(current))
            current = None
            continue
        if line.startswith("- "):
            if current is not None:
                bullets.append("\n".join(current))
            current = [line]
        elif current is not None:
            current.append(line)
    if current is not None:
        bullets.append("\n".join(current))
    return bullets


def parse_excluded_skills(catalog_text: str) -> dict[str, str]:
    """Extract skill name -> stated reason from the Excluded section."""
    section = extract_section(catalog_text, "Excluded from Individual Casting")
    excluded: dict[str, str] = {}
    for bullet in _iter_excluded_bullets(section):
        match = EXCLUDED_BULLET_RE.match(bullet)
        if not match:
            continue
        name_list, reason = match.group(1), match.group(2)
        for name in BACKTICK_NAME_RE.findall(name_list):
            excluded[name] = reason.strip()
    return excluded


def parse_design_review_lenses(catalog_text: str) -> set[str]:
    """Extract the lens names the Excluded section claims are subsumed
    by design-review's funnel (the bullet whose reason mentions
    design-review)."""
    section = extract_section(catalog_text, "Excluded from Individual Casting")
    for bullet in _iter_excluded_bullets(section):
        match = EXCLUDED_BULLET_RE.match(bullet)
        if not match:
            continue
        name_list, reason = match.group(1), match.group(2)
        if "design-review" in reason:
            return set(BACKTICK_NAME_RE.findall(name_list))
    return set()


def real_skill_dirs(skills_dir: Path) -> set[str]:
    """List skill directory names containing a SKILL.md.

    Excludes the plugin's own orchestrator entry point (a directory named
    after the plugin itself, e.g. `skills/review-panel/`) — a structural
    convention, not a reviewer seat: a plugin named X ships
    `skills/X/SKILL.md` as its own entry point, which is neither
    catalogued nor excluded and should not be flagged as undocumented.
    """
    plugin_name = skills_dir.resolve().parent.name
    return {
        p.name
        for p in skills_dir.iterdir()
        if p.is_dir() and (p / "SKILL.md").exists() and p.name != plugin_name
    }


def real_agent_stems(skills_dir: Path) -> set[str]:
    """List `*.md` file stems under the sibling `agents/` directory.

    A catalogued seat may cast an `agents/*.md` file (a cross-plugin or
    blind-subagent target) instead of a `skills/` directory — see the
    Fresh-Eyes seat's `agents/clean-room-alternative.md` cast target.
    """
    agents_dir = skills_dir.resolve().parent / "agents"
    if not agents_dir.is_dir():
        return set()
    return {p.stem for p in agents_dir.glob("*.md")}


def actual_design_review_lenses(design_review_text: str) -> set[str]:
    """Extract the lens names design-review/SKILL.md actually references
    in its funnel (every `**lowercase-hyphenated**` bold span)."""
    return set(BOLD_NAME_RE.findall(design_review_text))


def audit(catalog_text: str, skills_dir: Path, design_review_text: str) -> AuditReport:
    report = AuditReport()

    catalogued = parse_catalogued_seats(catalog_text)
    excluded = parse_excluded_skills(catalog_text)
    real_dirs = real_skill_dirs(skills_dir)
    real_agents = real_agent_stems(skills_dir)

    accounted_for = catalogued | excluded.keys()
    for name in sorted(real_dirs - accounted_for):
        report.findings.append(
            CatalogFinding(
                kind="undocumented",
                subject=name,
                detail=(
                    f"'{name}' exists under skills/ but is neither a "
                    "catalogued seat nor a formally excluded entry."
                ),
            )
        )

    for seat in sorted(catalogued):
        if seat not in real_dirs and seat not in real_agents:
            report.findings.append(
                CatalogFinding(
                    kind="missing_target",
                    subject=seat,
                    detail=(
                        f"Seat '{seat}' is catalogued but no matching skill "
                        "directory or agents/*.md file exists (renamed or "
                        "removed?)."
                    ),
                )
            )

    claimed_lenses = parse_design_review_lenses(catalog_text)
    real_lenses = actual_design_review_lenses(design_review_text)
    for lens in sorted(real_lenses - claimed_lenses):
        report.findings.append(
            CatalogFinding(
                kind="lens_drift_added",
                subject=lens,
                detail=(
                    f"design-review's funnel now includes '{lens}', not "
                    "listed in persona-catalog.md's Excluded section."
                ),
            )
        )
    for lens in sorted(claimed_lenses - real_lenses):
        report.findings.append(
            CatalogFinding(
                kind="lens_drift_removed",
                subject=lens,
                detail=(
                    f"persona-catalog.md lists '{lens}' as subsumed by "
                    "design-review, but it's no longer in design-review's "
                    "funnel."
                ),
            )
        )

    return report


def _render_findings(findings: list[CatalogFinding]) -> str:
    if not findings:
        return "(none)"
    return "\n".join(f"- `{f.subject}` — {f.detail}" for f in findings)


def render_report(report: AuditReport) -> str:
    """Render markdown with an embedded ```json block for machine consumption."""
    timestamp = datetime.datetime.now(datetime.UTC).isoformat()
    status = "CLEAN" if report.clean else "FINDINGS PRESENT"

    undocumented = [f for f in report.findings if f.kind == "undocumented"]
    missing_target = [f for f in report.findings if f.kind == "missing_target"]
    lens_drift = [
        f
        for f in report.findings
        if f.kind in ("lens_drift_added", "lens_drift_removed")
    ]

    findings_json = json.dumps(
        {
            "findings": [
                {"kind": f.kind, "subject": f.subject, "detail": f.detail}
                for f in report.findings
            ]
        },
        indent=2,
    )

    return f"""# Catalog Seat Audit Report

Generated: {timestamp}
Status: {status}

## Findings

### Undocumented skills
{_render_findings(undocumented)}

### Missing seat targets
{_render_findings(missing_target)}

### design-review lens drift
{_render_findings(lens_drift)}

```json
{findings_json}
```
"""


def read_text(path: Path) -> str:
    try:
        return path.read_text()
    except FileNotFoundError:
        fail(f"no such file: {path}")
    except OSError as exc:
        fail(f"could not read {path}: {exc}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=ROOT / DEFAULT_CATALOG)
    parser.add_argument("--skills-dir", type=Path, default=ROOT / DEFAULT_SKILLS_DIR)
    parser.add_argument(
        "--design-review", type=Path, default=ROOT / DEFAULT_DESIGN_REVIEW
    )
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    catalog_text = read_text(args.catalog)
    design_review_text = read_text(args.design_review)
    if not args.skills_dir.is_dir():
        fail(f"no such directory: {args.skills_dir}")

    report = audit(catalog_text, args.skills_dir, design_review_text)
    args.out.write_text(render_report(report))

    if report.clean:
        print(f"OK: catalog is clean; report written to {args.out}")
    else:
        print(
            f"FINDINGS: {len(report.findings)} finding(s); report written to {args.out}"
        )

    return 0 if report.clean else 1


if __name__ == "__main__":
    raise SystemExit(main())
