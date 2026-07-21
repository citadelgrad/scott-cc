# Data Model: Customers (fixture)

Minimal `DATA-MODEL.md` fixture used only by
`plugins/review-panel/tests/TIER-VERIFICATION.md`. Not part of any real application — do not wire
it into build tooling.

## Tables

### customers

| Column | Type | Notes |
|---|---|---|
| id | uuid | primary key |
| email | text | unique, not null |
| display_name | text | |
| created_at | timestamptz | not null, default now() |
| tax_id | text | added by `db/migrations/0012_add_customer_tax_id.sql`; government-issued taxpayer ID, nullable until backfilled |
