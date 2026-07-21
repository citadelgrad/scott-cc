-- Fixture: sensitive-migration. Used only by
-- plugins/review-panel/tests/TIER-VERIFICATION.md. Not part of any real application.
--
-- Adds a nullable tax_id column to customers, backfilled out-of-band.
ALTER TABLE customers ADD COLUMN tax_id text;
