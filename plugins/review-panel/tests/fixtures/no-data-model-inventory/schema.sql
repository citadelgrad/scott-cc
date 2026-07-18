-- Fixture: no-data-model-inventory (scc-bqp AC5 — missing DATA-MODEL.md test)
-- A small warehouse-inventory schema. Deliberately has NO DATA-MODEL.md anywhere in this
-- fixture directory. Used only by plugins/review-panel/tests/PRESSURE-TEST.md.

CREATE TABLE warehouse_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku TEXT NOT NULL UNIQUE,
    on_hand_quantity INTEGER NOT NULL DEFAULT 0,
    reorder_threshold INTEGER NOT NULL DEFAULT 10
);
