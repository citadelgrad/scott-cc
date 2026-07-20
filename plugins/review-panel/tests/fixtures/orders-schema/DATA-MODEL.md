# Data Model: orders-schema

Tracks orders and their line items through fulfillment, and the shipments that
deliver them.

## Entities & relationships

### Order
- **Storage:** `orders` table (Postgres)
- **Key fields:** `id` (uuid, pk), `customer_id` (fk → `customers.id`), `state`
  (`order_state` enum: `draft`, `placed`, `picking`, `shipped`, `cancelled`),
  `placed_at`, `cancelled_at`
- **Relationships:** has many **Line Items**; has many **Shipments**; belongs
  to one **Customer**

### Line Item
- **Storage:** `line_items` table (Postgres)
- **Key fields:** `id` (uuid, pk), `order_id` (fk → `orders.id`), `sku`,
  `quantity`, `unit_price_cents`
- **Relationships:** belongs to one **Order**

### Shipment
- **Storage:** `shipments` table (Postgres)
- **Key fields:** `id` (uuid, pk), `order_id` (fk → `orders.id`), `carrier`,
  `tracking_number`, `dispatched_at`, `delivered_at`
- **Relationships:** belongs to one **Order**

## Invariants

- An **Order**'s `cancelled_at` is never set unless `placed_at` is already
  set (`cancelled_after_placed` check constraint) — an order must be placed
  before it can be cancelled.
- A **Shipment**'s `delivered_at` is never set unless `dispatched_at` is
  already set (`delivered_after_dispatched` check constraint).
- **Line Item** `quantity` is always a positive integer; `unit_price_cents`
  is always a non-negative integer (check constraints).
- Once an **Order**'s `state` reaches `placed`, its **Line Items** are
  immutable — quantity/price corrections happen by cancelling and
  re-placing the order, never by an in-place `UPDATE` of a `line_items`
  row. This is enforced only by convention today; the schema has no
  constraint preventing an `UPDATE`.
- Once any **Shipment** for an **Order** has `delivered_at` set, that
  **Order**'s row is never written again by the order service —
  post-delivery corrections go through a separate returns service, not an
  `UPDATE` to `orders`. This is enforced only by convention today; the
  schema has no constraint preventing an `UPDATE`.

## Ownership & routing

| Entity / path | Written by | System |
|---|---|---|
| `orders` (pre-delivery) | Order service | System 1 (feature code) |
| `orders` (post-delivery corrections) | Returns service | System 1 (feature code) |
| `line_items` | Order service (only while parent `orders.state` is `draft`) | System 1 (feature code) |
| `shipments` | Fulfillment service | System 1 (feature code) |
| `migrations/` | Reviewed migration files | System 2 (ops fixes, library/IaC upgrades) |

## Agent boundary

- Do not add an `UPDATE` path to `line_items` for orders whose parent
  `orders.state` is `placed` or later — line items are immutable once
  placed; corrections require cancel-and-re-place, not escalation-free
  in-place edits.
- Do not add or permit an `UPDATE` to an `orders` row once any of its
  `shipments` rows has `delivered_at` set — post-delivery writes belong to
  the returns service; the order service must not touch that row again
  without human sign-off.
- `orders.state` enum values and transitions are fixed — do not add,
  remove, or reorder states without human sign-off.
- Do not weaken or remove the `cancelled_after_placed` or
  `delivered_after_dispatched` check constraints without escalation.

## Change log

- 2026-07-17 SN: Initial schema recorded (Order, Line Item, Shipment
  entities) from grilling session against `orders-schema` fixture.
- 2026-07-17 SN: Added invariants and agent-boundary entries for the two
  team-knowledge rules not encoded in SQL — line items immutable once
  placed, and orders read-only to the order service after delivery.
