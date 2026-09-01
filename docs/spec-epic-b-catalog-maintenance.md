# Technical Specification: Epic B — Persona Catalog Maintenance Workflow

**Status:** Approved
**Author:** Claude (epic-planner agent)
**Created:** 2026-08-31
**PRD:** `docs/prd-epic-b-catalog-maintenance.md`
**Beads Epic:** `scc-6lj`

---

## Architecture Overview

```
                     ┌─────────────────────────────┐
                     │ persona-catalog.md           │
                     │ (human-owned, curated)        │
                     └───────────────┬───────────────┘
                                      │ read-only
                                      ▼
   ┌──────────────────────────────────────────────────────────┐
   │ scripts/catalog_seat_audit.py  (deterministic, stdlib)     │
   │  - parse Seat Summary Table + Excluded section              │
   │  - cross-check plugins/review-panel/skills/*/SKILL.md dirs  │
   │  - cross-check design-review/SKILL.md's lens list           │
   │  - emit report.md (+ embedded JSON block)                   │
   │  - exit 0 = clean, exit 1 = findings present                │
   └───────────────────────────┬──────────────────────────────┘
                                │ report artifact (bounded, single file)
                                ▼
   ┌──────────────────────────────────────────────────────────┐
   │ catalog-steward skill                                       │
   │ plugins/review-panel/skills/catalog-steward/                │
   │                                                              │
   │  Procedure A: hole-finding                                  │
   │   reads report.md → drafts proposed catalog diff            │
   │                                                              │
   │  Procedure B: new-skill evaluation                          │
   │   reads 1 candidate skill's frontmatter/purpose              │
   │   compares against catalog conventions                       │
   │   → one of: new seat / new trigger / exclude+reason / reject │
   └───────────────────────────┬──────────────────────────────┘
                                │ output: proposed-diff.md (advisory only)
                                ▼
                     human reviews and applies to
                     persona-catalog.md manually

   ┌──────────────────────────────────────────────────────────┐
   │ foundry.yaml — catalog-audit profile (scheduled, monthly)   │
   │  gate: uv run python scripts/catalog_seat_audit.py ...      │
   │  on failure (findings present): integrations.beads           │
   │  on_needs_human: true → auto-files a beads issue             │
   └──────────────────────────────────────────────────────────┘
```

Both procedures are single-shot, non-checkpointed, and bounded to a small,
fixed corpus (one catalog file, ~33 skill directories' frontmatter, one
candidate skill per Procedure B run). No fan-out, no resumability, per the
PRD's explicit non-goals.

## Deterministic Script: `scripts/catalog_seat_audit.py`

### Inputs
- `--catalog PATH` (default `plugins/review-panel/reviewers/persona-catalog.md`)
- `--skills-dir PATH` (default `plugins/review-panel/skills/`)
- `--design-review PATH` (default `plugins/review-panel/skills/design-review/SKILL.md`)
- `--out PATH` (report output path; required)

### Parsing approach (stdlib only, mirrors `hooks/data_layer_guard.py`'s style)

```python
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CatalogFinding:
    kind: str          # "undocumented" | "missing_target" | "lens_drift_added"
                        # | "lens_drift_removed"
    subject: str        # skill dir name or lens name
    detail: str


@dataclass
class AuditReport:
    findings: list[CatalogFinding] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not self.findings


SEAT_ROW_RE = re.compile(r"^\|\s*`([a-z0-9\-]+)`\s*\|")           # Seat Summary Table rows
EXCLUDED_ENTRY_RE = re.compile(r"^-\s*`([a-z0-9\-]+)`")           # Excluded section bullet entries
LENS_BULLET_RE = re.compile(r"`([a-z0-9\-]+)`")                    # lens names inside prose bullets


def parse_catalogued_seats(catalog_text: str) -> set[str]:
    """Extract skill names from the Seat Summary Table."""
    ...


def parse_excluded_skills(catalog_text: str) -> dict[str, str]:
    """Extract skill name -> stated reason from the Excluded section."""
    ...


def parse_design_review_lenses(catalog_text: str) -> set[str]:
    """Extract the lens names the Excluded section claims are subsumed
    by design-review's funnel."""
    ...


def real_skill_dirs(skills_dir: Path) -> set[str]:
    return {p.name for p in skills_dir.iterdir() if p.is_dir() and (p / "SKILL.md").exists()}


def actual_design_review_lenses(design_review_text: str) -> set[str]:
    """Extract the lens names design-review/SKILL.md actually references
    in its funnel."""
    ...


def audit(catalog_text: str, skills_dir: Path, design_review_text: str) -> AuditReport:
    report = AuditReport()

    catalogued = parse_catalogued_seats(catalog_text)
    excluded = parse_excluded_skills(catalog_text)
    real_dirs = real_skill_dirs(skills_dir)

    accounted_for = catalogued | excluded.keys()
    for name in sorted(real_dirs - accounted_for):
        report.findings.append(CatalogFinding(
            kind="undocumented",
            subject=name,
            detail=f"'{name}' exists under skills/ but is neither a "
                    f"catalogued seat nor a formally excluded entry.",
        ))

    for seat in sorted(catalogued):
        if seat not in real_dirs:
            report.findings.append(CatalogFinding(
                kind="missing_target",
                subject=seat,
                detail=f"Seat '{seat}' is catalogued but no matching "
                        f"skill directory exists (renamed or removed?).",
            ))

    claimed_lenses = parse_design_review_lenses(catalog_text)
    real_lenses = actual_design_review_lenses(design_review_text)
    for lens in sorted(real_lenses - claimed_lenses):
        report.findings.append(CatalogFinding(
            kind="lens_drift_added",
            subject=lens,
            detail=f"design-review's funnel now includes '{lens}', not "
                    f"listed in persona-catalog.md's Excluded section.",
        ))
    for lens in sorted(claimed_lenses - real_lenses):
        report.findings.append(CatalogFinding(
            kind="lens_drift_removed",
            subject=lens,
            detail=f"persona-catalog.md lists '{lens}' as subsumed by "
                    f"design-review, but it's no longer in design-review's funnel.",
        ))

    return report


def render_report(report: AuditReport) -> str:
    """Render markdown with an embedded ```json block for machine consumption."""
    ...


def main() -> int:
    ...
    report = audit(catalog_text, skills_dir, design_review_text)
    out_path.write_text(render_report(report))
    return 0 if report.clean else 1
```

### Output format (`report.md`)

```markdown
# Catalog Seat Audit Report

Generated: <ISO timestamp>
Status: <CLEAN | FINDINGS PRESENT>

## Findings

### Undocumented skills
- `adr-skill` — exists under skills/ but is neither a catalogued seat
  nor a formally excluded entry.
- `grill-my-taste` — ...
- `grill-the-schema` — ...

### Missing seat targets
(none)

### design-review lens drift
(none)

​```json
{"findings": [{"kind": "undocumented", "subject": "adr-skill", "detail": "..."}, ...]}
​```
```

## Skill: `catalog-steward`

### Location
`plugins/review-panel/skills/catalog-steward/SKILL.md`

### Frontmatter (following existing catalog conventions, e.g. `data-steward`)

```yaml
---
name: catalog-steward
description: Maintains plugins/review-panel/reviewers/persona-catalog.md over time — finds coverage holes and evaluates candidate skills for catalog inclusion. Advisory only; never auto-edits the catalog. Not a per-diff review lens; do not cast this as a review-panel seat.
---
```

### Procedure A: Hole-finding

1. Run `uv run python scripts/catalog_seat_audit.py --out <tmp>/report.md`.
2. Read `<tmp>/report.md` (single bounded artifact, not the raw catalog or
   skill directory contents).
3. For each finding, draft a concrete proposed catalog edit:
   - `undocumented` → propose either a new Seat Summary Table row (if the
     skill looks like a diff-scoped review lens) or a new Excluded-section
     bullet with reasoning (if it looks like a construction/build tool, per
     the existing `grill-with-docs`/`improve-codebase-architecture` pattern).
   - `missing_target` → propose either updating the seat's path (if the
     skill was renamed — search `plugins/review-panel/skills/` for a
     plausible rename target) or removing the seat entry (if truly gone).
   - `lens_drift_added` / `lens_drift_removed` → propose updating the
     Excluded section's lens list to match design-review's actual funnel.
4. Write the proposed diff to an output artifact (e.g.
   `catalog-steward-proposal-<date>.md`), formatted as a unified diff or a
   clearly labeled before/after snippet per finding.
5. Never write to `persona-catalog.md` directly.

### Procedure B: New-skill evaluation

1. Input: exactly one skill path or name.
2. Read that skill's `SKILL.md` frontmatter (`name`, `description`) only —
   not its full body, keeping the read bounded.
3. Compare against:
   - Existing seats' `cast-when` criteria (does this overlap an existing
     seat's trigger?).
   - The Excluded section's stated reasons (does this look like a
     construction/build tool rather than a diff-scoped lens, matching an
     existing excluded pattern?).
   - design-review's funnel (is this already subsumed there?).
4. Produce exactly one of:
   - **New seat** — proposed Seat Summary Table row + cast-when criteria +
     model tier recommendation.
   - **New trigger** — proposed addition to an existing seat's cast-when
     list.
   - **Exclude with reason** — proposed Excluded-section bullet.
   - **Reject** — stated reasoning (e.g., duplicate of an existing seat,
     out of scope for review-panel entirely).
5. Write the recommendation to an output artifact with stated reasoning.
   Never edits `persona-catalog.md` directly.

## Configuration

`foundry.yaml` (repo root) gains a `catalog-audit` profile:

```yaml
profiles:
  catalog-audit:
    gates:
      - id: catalog-seat-audit
        run: uv run python scripts/catalog_seat_audit.py --out .foundry/catalog-audit-report.md
        timeout: 5m
        allow_failure: true
        decision_on_failure: warn

schedules:
  catalog-audit-monthly:
    profile: catalog-audit
    cron: '0 6 1 * *'   # 06:00 UTC on the 1st of each month

integrations:
  beads:
    on_needs_human: true
```

`allow_failure: true` + `decision_on_failure: warn` because a finding is a
maintenance signal, not a build-breaking failure; `on_needs_human` still
files a beads issue so it is tracked, without blocking unrelated CI.

## Implementation Phases

- [ ] Phase 1 — Deterministic script: `scripts/catalog_seat_audit.py` +
      `scripts/tests/test_catalog_seat_audit.py`.
- [ ] Phase 2 — `catalog-steward` skill: SKILL.md + Procedure A
      (hole-finding).
- [ ] Phase 3 — `catalog-steward` skill: Procedure B (new-skill
      evaluation).
- [ ] Phase 4 — `foundry.yaml` `catalog-audit` profile + monthly schedule.
- [ ] Phase 5 — First real run of Procedure A against the live catalog;
      apply the resulting proposed diff to close the 3 known gaps
      (`adr-skill`, `grill-my-taste`, `grill-the-schema`).
