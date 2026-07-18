---
name: data-steward
description: Reviews diffs touching migrations, ORM/model definitions, schema files, or serialization formats against DATA-MODEL.md's Invariants and Agent boundary sections, plus a 7-item migration-safety checklist (reversibility, expand-migrate-contract sequencing, backfill strategy, lock behavior, index-creation strategy, nullable-then-tighten, dual-write windows). Use when a diff touches migration files, ORM/model definitions, schema files (*.sql, schema.*, prisma/, alembic/, migrations/), serialization formats, or any file DATA-MODEL.md maps an entity to. Findings may carry a sovereignty: human-required marker when the diff crosses a DATA-MODEL.md Agent boundary entry, or when DATA-MODEL.md is absent while the diff changes schema semantics — that marker is a contract extension FIX must never auto-resolve. Not for reviewing application-level domain types unrelated to persistence (use domain-modeling), and not a substitute for the data-layer guard hook (out of scope here — see references/data-steward-hook.md if installed).
argument-hint: "[diff, file, or directory to review]"
allowed-tools: Read, Grep
---

# Data Steward

Read-only review seat for the data layer, following the same structural shape as
`domain-modeling/SKILL.md` (frontmatter, When to Apply, How to Review, Output Contract). Not
derived from any vendored source — authored for this plugin as Phase 2c of the Two-System
Architecture. It checks a diff against a project's `DATA-MODEL.md`
([formats/DATA-MODEL-FORMAT.md](../../formats/DATA-MODEL-FORMAT.md)) and against a fixed
migration-safety checklist, and it is the sole mechanism for unattended sovereignty enforcement
(the data-layer guard hook is a separate, interactive-only mechanism that no-ops unattended).

This skill is **read-only** and reviews existing diffs; it does not write or refactor code, and it
does not edit `DATA-MODEL.md` itself — that file is human-owned (see its format doc's rules).

## When to Apply

Cast (fail-closed, per `reviewers/persona-catalog.md`'s global casting rule) when the diff touches
any of:

- Migration files (any directory/naming convention a project uses for versioned schema changes —
  `migrations/`, `alembic/`, `db/migrate/`, etc.)
- ORM/model definitions (e.g. SQLAlchemy/Django/ActiveRecord/Prisma model classes, TypeORM
  entities)
- Schema files: `*.sql`, `schema.*`, `prisma/schema.prisma`, `alembic/` version files, or any
  other file whose primary content is a data-store schema definition
- Serialization formats (protobuf `.proto`, Avro/JSON Schema definitions, wire-format structs)
  where a field addition/removal/type-change affects on-disk or on-wire compatibility
- Any file `DATA-MODEL.md`'s "Entities & relationships" or "Ownership & routing" sections map an
  entity or path to, even if the file extension isn't one of the above (e.g. a hand-written
  repository/DAO module `DATA-MODEL.md` names as an entity's owner)

**Not** for application-level domain types with no persistence surface (use `domain-modeling`),
and **not** the data-layer guard hook — that's a separate pre-write mechanism (Phase 2d, scoped
out of this skill; see `references/data-steward-hook.md` if that plugin component is installed).

## How to Review

When invoked with `$ARGUMENTS`, scope the review to the diff, file, or directory given. Read the
target diff first (do not review from memory or from other seats' summaries).

1. **Check for `DATA-MODEL.md`** at the repo root (per `formats/DATA-MODEL-FORMAT.md`'s "lives at
   the repo root" convention).
   - **If present:** read its Invariants and Agent boundary sections. For each changed entity or
     path in the diff, check whether the change violates a stated invariant (e.g. a migration that
     allows `amount_cents` to go negative when an invariant says it's always positive) or crosses
     an Agent-boundary rule (e.g. adding an `UPDATE` path to a field marked append-only, or adding
     a new enum state to a "fixed, do not add without human sign-off" transition list).
   - **If absent:** the seat still casts (the file-pattern triggers above don't depend on
     `DATA-MODEL.md` existing) — proceed straight to the migration-safety checklist, and see
     "Missing DATA-MODEL.md" below for the required finding.
2. **Check against the migration-safety checklist.** For every migration/schema change in the
   diff, evaluate each of the following 7 items explicitly. A Critical finding must name the
   specific item violated (not just "unsafe migration") so the finding is directly actionable:
   - **Reversibility / down-path** — does the migration have a working `down`/rollback, or is it a
     one-way destructive change (e.g. `DROP COLUMN` on a column holding live data, `DROP TABLE`)
     with no path back?
   - **Expand→migrate→contract sequencing** — for a breaking schema change, is it split into an
     expand step (add the new shape alongside the old), a migrate step (backfill/dual-write), and
     a contract step (remove the old shape) across separate deploys, rather than one diff that
     changes and removes in the same step?
   - **Backfill strategy and volume** — if the change requires backfilling existing rows, is the
     strategy stated (batched vs. single transaction) and does it account for table size (a
     single-transaction backfill on a large table risks long locks or timeouts)?
   - **Lock behavior** — does the migration take a lock that blocks reads/writes for longer than
     acceptable (e.g. an unguarded `ALTER TABLE ... ADD COLUMN NOT NULL` with a default on a large
     table, in engines where that rewrites the table)?
   - **Index-creation strategy** — is a new index created concurrently/without blocking writes
     (e.g. `CREATE INDEX CONCURRENTLY` in Postgres) where the target table is expected to have
     production traffic, rather than a blocking index build?
   - **Nullable-then-tighten** — when adding a new required column to a table with existing rows,
     is it added nullable first, backfilled, and only tightened to `NOT NULL` in a later step —
     rather than added as `NOT NULL` in one step against a table that already has rows?
   - **Dual-write windows** — for a change that moves data from one location/shape to another, is
     there a stated dual-write period where both the old and new paths are kept in sync before
     cutover, or does the diff cut over in one step with a window where reads/writes could be lost?

## Output Contract

Findings use the same Critical/Important/Minor shape as
[`contracts/reviewer-output.md`](../../contracts/reviewer-output.md)'s Issue shape (file:line,
what's wrong, why it matters, how to fix), so this seat's output merges cleanly through
`references/merge-and-validate.md`'s fingerprinting/confidence-scoring pipeline with zero
special-casing — documented locally here rather than by editing that shared contract file, the
same pattern `domain-modeling/SKILL.md` uses for its own CLEAR/TRIGGERED/N/A vocabulary.

- **Location** — file:line
- **Principle violated** — name the specific `DATA-MODEL.md` invariant/Agent-boundary entry, or
  the specific migration-safety checklist item, that's violated
- **Severity** — `Critical` | `Important` | `Minor`, by the same blast-radius judgment
  `domain-modeling`'s Output Contract uses:
  - **Critical** — a destructive, irreversible, or data-loss-risking change ships as-is (e.g. a
    `DROP COLUMN` on a column with live data and no down-path; a migration that violates a stated
    invariant directly)
  - **Important** — a real migration-safety gap that won't lose data today but creates outage or
    correctness risk under production load (e.g. a blocking index build, a missing dual-write
    window)
  - **Minor** — a genuine hardening opportunity with no current bug behind it

### Sovereignty extension

In addition to the standard shape, a finding may carry an optional marker:

```
sovereignty: human-required
```

Set this marker when either is true:

1. **The diff crosses a `DATA-MODEL.md` Agent boundary entry** — the change does exactly what an
   Agent-boundary rule says an agent must not do unilaterally (e.g. adds an enum state to a fixed
   transition list, introduces an `UPDATE` path on an append-only entity).
2. **`DATA-MODEL.md` is absent while the diff changes schema semantics** — there is no file to
   check invariants/boundaries against, but the diff is doing exactly the kind of schema-semantics
   change `DATA-MODEL.md` exists to govern. Emit this as its own finding (severity Important unless
   the change is also independently Critical on migration-safety-checklist grounds), and recommend
   the user run `grill-the-schema` to create `DATA-MODEL.md` — phrased as a documentation pointer,
   not a mechanism invocation, since that skill (`skills/grill-the-schema/SKILL.md`, tracked
   separately as Phase 2b) may not be installed in this session. If it isn't, say so explicitly
   rather than silently assuming it ran (coverage honesty, per `persona-catalog.md`'s missing-skill
   handling and the `grill-with-docs` precedent for referencing a sibling capability that may be
   absent).

A `sovereignty`-marked finding is otherwise a normal finding: it still carries Critical/Important/
Minor severity, still needs file:line and a stated principle, and still goes through MERGE/VALIDATE
like any other finding. The marker only changes what the orchestrator is allowed to do with it
downstream (see `references/fix-and-rereview.md`'s "Sovereignty guard" and
`references/converge-and-pipeline.md`'s `escalated` status) — this skill's only job is to set the
marker correctly, not to enforce what happens next.

Example line:
`Critical — migrations/0042_drop_legacy_status.sql:12 — migration-safety: reversibility/down-path (DROP COLUMN status on a table with live data, no down migration provided) — sovereignty: human-required — this also crosses DATA-MODEL.md's Agent boundary entry for orders.status ("fixed, do not remove without human sign-off")`

If everything is clear, say so plainly — do not force findings where none exist.
