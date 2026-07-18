# Taste: Test Fixture Human

Calibrates personal, contested preferences on top of universal quality for this fixture's
owner. Used only by `scc-4tt`'s Run Tests step to exercise the `taste-review` seat's
malformed-entry handling.

## Preferences

### Prefer flat error handling over nested try/catch
- **Rule:** Return errors as values (Result-style) instead of throwing and catching
  across multiple nesting levels.
- **Rationale:** Nested try/catch obscures which call in a chain actually failed; flat
  error values keep the failure point local to the call that produced it.
- **Strength:** strong
- **Provenance:** grill-my-taste session 2026-07-18, forced choice #2 (nested try/catch
  vs. Result-returning helpers).

### Prefer named exports over default exports
- **Rule:** Use named exports for all module boundaries; avoid `export default`.
- **Rationale:** Named exports keep import statements grep-able and rename-safe across
  the codebase.
- **Provenance:** grill-my-taste session 2026-07-18, forced choice #4.

## Weightings

## Anti-preferences

## Candidate rules
