-- Fixture: orders-schema
-- A small orders system, used to exercise a DATA-MODEL.md grilling session
-- against plugins/review-panel/formats/DATA-MODEL-FORMAT.md.

CREATE TYPE order_state AS ENUM ('draft', 'placed', 'picking', 'shipped', 'cancelled');

CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id),
    state order_state NOT NULL DEFAULT 'draft',
    placed_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,
    CONSTRAINT cancelled_after_placed CHECK (
        cancelled_at IS NULL OR placed_at IS NOT NULL
    )
);

CREATE TABLE line_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id),
    sku TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price_cents INTEGER NOT NULL CHECK (unit_price_cents >= 0)
);

CREATE TABLE shipments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id),
    carrier TEXT NOT NULL,
    tracking_number TEXT,
    dispatched_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    CONSTRAINT delivered_after_dispatched CHECK (
        delivered_at IS NULL OR dispatched_at IS NOT NULL
    )
);
