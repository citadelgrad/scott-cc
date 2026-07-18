# Taste: Test Fixture Human

Calibrates personal, contested preferences on top of universal quality for this fixture's
owner. Used only by `scc-4tt`'s Run Tests step to exercise the `taste-review` seat.

## Preferences

### Prefer flat error handling over nested try/catch
- **Rule:** Return errors as values (Result-style) instead of throwing and catching
  across multiple nesting levels.
- **Rationale:** Nested try/catch obscures which call in a chain actually failed; flat
  error values keep the failure point local to the call that produced it.
- **Strength:** strong
- **Provenance:** grill-my-taste session 2026-07-18, forced choice #2 (nested try/catch
  vs. Result-returning helpers).

### Never mutate function arguments in place
- **Rule:** Function parameters must be treated as read-only; never reassign or mutate
  an argument object inside the function body.
- **Rationale:** Argument mutation creates action-at-a-distance bugs when a caller still
  holds a reference to the same object.
- **Strength:** absolute
- **Provenance:** grill-my-taste session 2026-07-18, forced choice #7 (mutate-in-place
  vs. return-a-new-object).

### Prefer named exports over default exports
- **Rule:** Use named exports for all module boundaries; avoid `export default`.
- **Rationale:** Named exports keep import statements grep-able and rename-safe across
  the codebase.
- **Strength:** weak
- **Provenance:** grill-my-taste session 2026-07-18, forced choice #4.

## Weightings

- **Locality beats DRY.** When a shared abstraction would need to travel more than one
  module boundary to be reused, prefer duplicating the logic locally over introducing a
  shared dependency.

## Anti-preferences

- **Flag boolean parameters in function signatures** even when named clearly — prefer an
  options object or two named functions.

## Candidate rules
