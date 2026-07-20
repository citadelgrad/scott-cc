<!-- Canonical copy. This is the single source of truth for the DATA-MODEL.md format —
     do not fork or duplicate this file elsewhere in the plugin; reference it instead. -->

# DATA-MODEL.md Format

`DATA-MODEL.md` lives at the repo root, alongside `CONTEXT.md`. It is the
implementation-detail record for a project's data layer: what's stored, what must never
break, who's allowed to write it, and which decisions require a human before an agent
touches them.

## Structure

```md
# Data Model: {Project Name}

{One or two sentence description of what this data model covers.}

## Entities & relationships

### Order
- **Storage:** `orders` table (Postgres, `commerce` schema)
- **Key fields:** `id` (uuid, pk), `customer_id` (fk → `customers.id`), `status`, `placed_at`
- **Relationships:** has many **Invoices**; belongs to one **Customer**

### Invoice
- **Storage:** `invoices` table (Postgres, `commerce` schema)
- **Key fields:** `id` (uuid, pk), `order_id` (fk → `orders.id`), `amount_cents`, `issued_at`
- **Relationships:** belongs to one **Order**

## Invariants

- An **Invoice** is never created before its **Order**'s `status` reaches `fulfilled`.
- `amount_cents` is always a positive integer; refunds create a new negative-amount
  **Invoice** — an existing invoice is never mutated.

## Ownership & routing

| Entity / path | Written by | System |
|---|---|---|
| `orders` | Checkout service | System 1 (feature code) |
| `invoices` | Billing worker | System 1 (feature code) |
| `migrations/` | Reviewed migration files | System 2 (ops fixes, library/IaC upgrades) |

## Agent boundary

- `orders.status` enum values and transitions are fixed — do not add, remove, or
  reorder states without human sign-off.
- `invoices` are append-only — do not introduce an `UPDATE` path without escalation.

## Change log

- 2026-07-16 SN: Initial schema recorded (Order, Invoice, Customer entities).
- 2026-07-17 SN: Added invariant — invoices are append-only.
```

## Rules

- **Record implementation detail, not vocabulary.** Storage mapping — table/collection,
  schema, key fields, foreign keys — belongs here. This is exactly the detail
  `CONTEXT.md` forbids (see "Relationship to CONTEXT.md" below).
- **State invariants as testable rules, not aspirations.** Each invariant should be
  specific enough that a diff can be checked against it directly (the data-steward seat
  and the data-layer guard hook both read this section).
- **Every entity and every data-layer path needs an owner and a system.** Ownership &
  routing must name a writer and say whether it's System 1 (feature code) or System 2
  (ops fixes: library upgrades, IaC data-store changes) for every row — not just a team
  name.
- **Agent boundary entries are escalation triggers, not design notes.** Phrase each as a
  rule an agent must not cross unilaterally. A diff that crosses one gets escalated for
  human review rather than approved automatically.
- **Change log entries are dated and human-initialed.** An agent proposing a change but
  not producing a dated, initialed entry is a gap, not a green light — the data-layer
  guard hook checks for a current-work entry before allowing edits to data-layer paths.

## Relationship to CONTEXT.md

`CONTEXT.md` and `DATA-MODEL.md` are deliberately different documents, and each links to
the other's format so a reader lands on the right one:

- **[CONTEXT.md](./CONTEXT-FORMAT.md)** is a glossary. It defines what things are called
  and explicitly forbids implementation detail — its Rules say "Define what it IS, not
  what it does."
- **DATA-MODEL.md** is the inverse. It *is* the implementation-detail record for data:
  storage mapping, schema/migration-level invariants, ownership, and agent boundaries.
  Where `CONTEXT.md` says "an **Order** produces one or more **Invoices**,"
  `DATA-MODEL.md` says which table, which foreign key, and which invariant enforces it.

If a term needs a definition, it belongs in `CONTEXT.md`. If it needs a storage mapping,
an invariant, or an ownership rule, it belongs in `DATA-MODEL.md`. A repo may have both;
they cross-reference by entity name rather than duplicating content.

## Cross-system contract

`DATA-MODEL.md` binds **both systems identically**. A migration inside a System 2
library upgrade or an IaC data-store change is held to the same Invariants and Agent
boundary as a System 1 feature diff — there is no separate, looser standard for ops
fixes. The data-steward seat and the data-layer guard hook enforce this file the same
way regardless of which system produced the diff.

## Lazy creation

Create `DATA-MODEL.md` lazily — when the first entity, invariant, or boundary decision
is resolved, not up front, and not for repos with no persistent data layer.
