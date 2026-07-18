---
name: grill-the-schema
description: Grilling session that interviews you to build DATA-MODEL.md — entities and their storage, invariants, lifecycle (soft-delete? audit? retention?), volume/access patterns, ownership/routing, and Agent boundaries — cross-referencing actual schema/migration files and updating the file inline as decisions crystallise. Use when user wants to stress-test their data layer or has no DATA-MODEL.md yet.
---

<what-to-do>

Interview me relentlessly about the data layer until we reach a shared understanding. Walk down each branch — entities, invariants, lifecycle, volume/access patterns, ownership, boundaries — resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time, waiting for feedback on each question before continuing.

If a question can be answered by exploring the codebase, explore the codebase instead.

</what-to-do>

<supporting-info>

## Domain awareness

During codebase exploration, look for schema and migration files (`migrations/`, `alembic/`,
`db/migrate/`, `*.sql`, `schema.*`, `prisma/schema.prisma`, ORM model classes) and for an
existing `DATA-MODEL.md` at the repo root, alongside `CONTEXT.md`.

Create `DATA-MODEL.md` lazily — only when you have something to write. If it doesn't exist yet,
create it when the first entity, invariant, or boundary decision is resolved. Repos with no
persistent data layer don't get one — don't force the file into existence for its own sake.

## During the session

### Interview topics

Cover these in turn, letting codebase exploration answer what it can before asking:

- **Entities** — what's stored, where (table/collection, schema), key fields, relationships to
  other entities.
- **Invariants** — rules that must always hold. Push for testable statements, not aspirations:
  "amounts are always positive" is testable; "the system should be consistent" is not.
- **Lifecycle** — is this entity soft-deleted or hard-deleted? Is it audited? Does it have a
  retention policy? These questions are what surface invariants and boundaries, not a separate
  section of their own.
- **Volume/access patterns** — how much data, how it's read and written, whether that shapes an
  invariant (e.g. a table too large for a single-transaction backfill).
- **Ownership & routing** — for every entity and data-layer path, who writes it, and is that
  System 1 (feature code) or System 2 (ops fixes: library upgrades, IaC data-store changes)?
  Every row needs both — not just a team name.
- **Boundaries** — which changes to this entity require a human before an agent touches them?
  Phrase each as a rule an agent must not cross unilaterally (e.g. "do not add an `UPDATE` path
  without escalation"), not as a design note.

### Discuss concrete scenarios

Stress-test entities and lifecycle decisions with specific scenarios. Invent scenarios that probe
edge cases — "if a shipment is marked delivered and then a customer disputes the charge, who
writes the correction?" — and force the user to be precise about who owns what, and when.

### Cross-reference with schema/migration files

When the user states how the data layer works, check whether the actual schema/migration files
agree. If you find a contradiction, surface it: "Your migration makes `orders.status` a free-text
column, but you just said the states are fixed — which is right?"

### Update DATA-MODEL.md inline

When a decision is resolved, update `DATA-MODEL.md` right there. Don't batch these up — capture
them as they happen. Use the format in
[DATA-MODEL-FORMAT.md](../../formats/DATA-MODEL-FORMAT.md), including a dated, human-initialed
Change log entry for each resolved decision.

This skill proposes and drafts `DATA-MODEL.md` content through the conversation — but the
resulting file is a human-owned artifact, produced through the grilling session, not silently
generated. FIX never auto-modifies `DATA-MODEL.md` (the same rule `data-steward/SKILL.md` states
for its own read-only review of the file).

### Offer ADRs sparingly

Only offer to create an ADR when all three are true:

1. **Hard to reverse** — the cost of changing your mind later is meaningful
2. **Surprising without context** — a future reader will wonder "why did they do it this way?"
3. **The result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons

Schema decisions frequently clear this gate — a chosen soft-delete strategy, a denormalization,
an ownership split between two services are all common examples. If any of the three is missing,
skip the ADR. Use the format in [ADR-FORMAT.md](../../formats/ADR-FORMAT.md).

</supporting-info>
