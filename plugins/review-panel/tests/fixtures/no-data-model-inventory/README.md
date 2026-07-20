# Fixture: no-data-model-inventory

A minimal warehouse-inventory schema (`schema.sql`) plus one migration under review
(`migrations/0001_add_reserved_quantity.sql`). Deliberately has **no `DATA-MODEL.md`** anywhere
in this fixture directory.

Used by `scc-bqp`'s (Phase 2c, data-steward seat) Run Tests step to validate AC5: a repo with no
`DATA-MODEL.md` at all still gets the data-steward seat cast on schema/migration diffs (the
seat's file-pattern triggers don't depend on `DATA-MODEL.md` existing), and the seat emits a
`sovereignty: human-required` finding recommending the user run `grill-the-schema`
(`skills/grill-the-schema/SKILL.md`, tracked separately as Phase 2b, not yet installed).
