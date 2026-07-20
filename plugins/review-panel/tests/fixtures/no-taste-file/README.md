# Fixture: no-taste-file

Reuses `taste-preferences/before.ts`, `after.ts`, and `diff.patch` (a diff that would
trip all three severity bands if a `TASTE.md` existed), but deliberately has **no
`TASTE.md`** anywhere in this fixture directory — mirrors the
`no-data-model-inventory` fixture's shape for the data-steward seat's missing-artifact
case.

Used by `scc-4tt`'s Run Tests step to validate AC2: a repo with no `TASTE.md` never
casts the `taste-review` seat at all (file-existence gate, no generic fallback) — this
is a Cast-level exclusion, not a "ran and found nothing" state.
