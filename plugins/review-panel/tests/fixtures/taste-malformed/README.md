# Fixture: taste-malformed

A `TASTE.md` with two Preferences: one well-formed (`strong`, all four fields present),
one malformed — "Prefer named exports over default exports" is missing its `Strength`
field entirely. Reuses `taste-preferences/before.ts` and `after.ts`
(`diff.patch` violates both the well-formed strong Preference and the pattern the
malformed entry would have flagged, had it been usable).

Used by `scc-4tt`'s Run Tests step to validate AC3: the seat still casts (the file
exists), still reviews the well-formed entry normally, but reports the malformed entry
as unusable in Coverage Honesty rather than guessing a `strength` for it.
