# Fixture: orders-schema

A minimal orders/line-items/shipments schema (`schema.sql`) plus two business
rules that exist only as team knowledge, not as SQL constraints:

- Once a `shipments` row has `delivered_at` set, its `order_id`'s row in
  `orders` is never written again by the order service — corrections after
  delivery go through a separate returns service.
- `line_items` are immutable once the parent `orders.state` reaches
  `placed` — quantity/price corrections require cancelling and re-placing
  the order, never an in-place update.

Used by `scc-f9k`'s Run Tests step to validate that
`plugins/review-panel/formats/DATA-MODEL-FORMAT.md` alone (no skill yet
exists — that's task 2b) is sufficient to drive a grilling-session-style
pass producing a valid `DATA-MODEL.md`.
