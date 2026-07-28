---
name: data-steward
description: Use when a diff touches migration files, ORM/model definitions, schema
  files, serialization formats, or any file DATA-MODEL.md maps an entity to. Reviews
  against DATA-MODEL.md's Invariants and Agent boundary sections plus a 7-item migration-safety
  checklist. Not for application-level domain types (use domain-modeling). touching
  migrations, ORM/model definitions, schema files, or serialization formats against
  DATA-MODEL.md's Invariants and Agent boundary sections, plus a 7-item migration-safety
  checklist (reversibility, expand-migrate-contract sequencing, backfill strategy,
  lock behavior, index-creation strategy, nullable-then-tighten, dual-write windows)
argument-hint: '[diff, file, or directory to review]'
allowed-tools: Read, Grep
metadata:
  category: discipline
  triggers:
  - data-quality
  - schema-review
  - data-validation
---
