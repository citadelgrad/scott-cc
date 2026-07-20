# Fixture: taste-preferences

A well-formed `TASTE.md` with three Preferences spanning all three `strength` values
(`strong`, `absolute`, `weak`), plus `diff.patch` (`before.ts` → `after.ts`) that
violates all three in one change:

- `export default function processOrder` — violates the **weak** "Prefer named exports
  over default exports" Preference.
- `order.status = "processing";` (mutates the `order` argument in place) — violates the
  **absolute** "Never mutate function arguments in place" Preference.
- Three levels of nested `try`/`catch` — violates the **strong** "Prefer flat error
  handling over nested try/catch" Preference.

Used by `scc-4tt`'s Run Tests step to validate AC1 (happy path: a strong-preference
violation yields a finding that quotes the clause verbatim) and the absolute-strength
severity-mapping design decision (`Important` + `(absolute preference)` note, sorted
first — not a fourth severity value).
