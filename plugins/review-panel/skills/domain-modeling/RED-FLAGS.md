# Domain Modeling Red Flags

Scan checklist for [SKILL.md](./SKILL.md). Styled after the clairvoyance `red-flags` skill's verdict vocabulary so results merge into the same review-panel report with zero translation. For each flag below, mark the target `CLEAR`, `TRIGGERED`, or `N/A` (the flag doesn't apply to this code's language/shape — e.g. exception-based flags are `N/A` for a codebase that has no exception mechanism at all).

Each flag names the [TECHNIQUES.md](./TECHNIQUES.md) principle it violates and the fix pattern. See [WORKED-EXAMPLE.md](./WORKED-EXAMPLE.md) for a fully worked before/after.

## 1. Boolean-Pair / Flag-Cluster Fields

**Check:** Does a type have 2+ boolean fields whose combinations aren't all valid (`isPaid`, `isShipped`, `isCancelled`, `isRefunded` on one struct)?

- **Principle violated:** illegal states unrepresentable (technique 2)
- **TRIGGERED signal:** any pair of booleans on the same type where some combination is a domain impossibility
- **Fix:** collapse the flags into a status-tagged union (sum type, technique 1) — one variant per legal combination

## 2. Stringly-Typed Domain Values

**Check:** Are domain-meaningful values (customer ID, email, currency code, order status) passed around as bare `string`/`str`?

- **Principle violated:** smart constructors / branded primitives (technique 5)
- **TRIGGERED signal:** a function signature with 2+ same-typed string/number parameters representing different domain concepts (see flag 5), or a status/kind value compared via `=== "shipped"` string literals scattered across the codebase instead of a closed union
- **Fix:** brand/newtype the primitive; parse into it once at the boundary (technique 4)

## 3. Validation Scattered Past the Boundary

**Check:** Does the same validation logic (email format, non-negative amount, valid status transition) get re-checked in multiple places downstream of where the data first entered the system?

- **Principle violated:** parse, don't validate (technique 4)
- **TRIGGERED signal:** grep for the same regex/condition appearing in 2+ non-adjacent call sites; a comment like "just in case" or "defensive check" guarding against a state that should be unrepresentable
- **Fix:** move the check to a single parse function at the boundary that returns a precise type; delete the redundant downstream checks

## 4. Non-Exhaustive Switch/Match

**Check:** Does a `switch`/`match`/`if-elif` chain over a sum type have a `default`/wildcard/catch-all branch instead of one arm per variant?

- **Principle violated:** exhaustive matching (technique 3)
- **TRIGGERED signal:** a `default:` branch that does anything other than call `assertNever`/`assert_never` (or is genuinely `N/A` because the language enforces exhaustiveness natively, e.g. Rust `match`); a runtime `else` fallback that silently does nothing or returns a generic error for "any other case"
- **Fix:** remove the catch-all; enumerate every variant explicitly; use `assertNever`/`assert_never` (or trust the compiler in Rust) so adding a variant is a build failure until handled everywhere

## 5. Primitive Obsession (3+ Same-Typed Parameters)

**Check:** Does a function/constructor take 3 or more parameters of the same primitive type (e.g. three `string` params: `customerId`, `orderId`, `productId`)?

- **Principle violated:** smart constructors / branded primitives (technique 5)
- **TRIGGERED signal:** any function signature where two adjacent same-typed parameters could be silently swapped by a caller and still compile
- **Fix:** brand each ID type distinctly (technique 5) so swapping arguments becomes a type error

## 6. Optional Fields That Should Be a Variant

**Check:** Does a type have an `optional`/`Option`/`nullable` field that is only ever populated when some *other* field has a specific value (i.e., the optionality is really a state dependency, not independent absence)?

- **Principle violated:** illegal states unrepresentable (technique 2)
- **TRIGGERED signal:** `field?: T` (or `Optional[T]`) where a code comment, name, or nearby check implies "only set when status is X"
- **Fix:** move `T` onto the specific sum-type variant where it's actually valid (technique 2), instead of making it optional on the shared type

## 7. Exceptions for Expected Domain Failures

**Check:** Does the code `throw`/`raise`/`panic!` for failure modes that are a normal, anticipated part of the domain (payment declined, item out of stock, email already registered) rather than truly exceptional/unrecoverable conditions?

- **Principle violated:** errors as values (technique 6), custom error types (technique 7)
- **TRIGGERED signal:** a `try/catch` (or `try/except`) wrapping a domain operation where the caught case is a normal business outcome, not a bug; a function whose real failure modes aren't visible in its signature
- **Fix:** return `Result<T, E>`/`Either` (technique 6) with a custom error sum type (technique 7) instead of throwing; reserve exceptions/panics for truly unrecoverable conditions (out of memory, invariant violation, programmer error)

## 8. Lifecycle-via-Nullable-Fields Instead of a Tagged Union

**Check:** Is an entity's lifecycle/workflow progress (draft → submitted → approved → archived, or similar) represented by a growing set of nullable timestamp/ID fields (`submittedAt?`, `approvedAt?`, `approvedBy?`, `archivedAt?`) on one flat type, rather than by explicit state variants?

- **Principle violated:** workflows as functions / state machines over booleans (technique 8), which itself depends on illegal states unrepresentable (technique 2)
- **TRIGGERED signal:** 3+ nullable "when did X happen" fields on a single type where the domain rule is "these become non-null in a fixed order"; a workflow function that takes the whole flat entity and internally branches on which nullable fields are set to figure out "what state am I actually in"
- **Fix:** model each lifecycle stage as its own tagged-union variant (technique 2) carrying only the timestamp/actor fields valid at that stage; make each transition a `PrevState -> Result<NextState, StepError>` function (technique 8)

## Reporting Format

For every `TRIGGERED` flag, report location + principle + candidate fix, per [SKILL.md](./SKILL.md)'s output contract:

```
TRIGGERED — <file>:<line> — <flag name> (<technique principle>) — <one-line candidate fix>
```

If a flag is `N/A`, say why in one clause (e.g. "N/A — Rust `match` enforces exhaustiveness natively, no catch-all possible"). Do not mark a flag `CLEAR` without having actually looked for it — `CLEAR` means checked and found nothing, not skipped.
