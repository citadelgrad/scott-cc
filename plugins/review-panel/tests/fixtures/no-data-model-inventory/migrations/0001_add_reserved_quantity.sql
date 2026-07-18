-- Fixture: no-data-model-inventory migration under review (scc-bqp AC5)
-- Used only by plugins/review-panel/tests/PRESSURE-TEST.md. Not part of any real application.
--
-- Adds reserved_quantity to warehouse_items so in-flight order reservations can be tracked
-- separately from on_hand_quantity -- a new schema-semantics concept (what counts as
-- "available" stock now depends on two columns, not one) with no DATA-MODEL.md in this repo to
-- record that decision against.

ALTER TABLE warehouse_items ADD COLUMN reserved_quantity INTEGER NOT NULL DEFAULT 0;
