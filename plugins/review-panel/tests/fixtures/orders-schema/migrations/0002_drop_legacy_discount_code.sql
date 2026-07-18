-- Fixture: orders-schema migration under review (scc-bqp AC1 — destructive migration test)
-- Used only by plugins/review-panel/tests/PRESSURE-TEST.md. Not part of any real application.
--
-- orders.legacy_discount_code predates this fixture's baseline schema.sql snapshot (added in an
-- earlier migration not included in this fixture) and has held historical discount-code values
-- for placed and cancelled orders since before the discount-codes-v2 rollout.

ALTER TABLE orders DROP COLUMN legacy_discount_code;
