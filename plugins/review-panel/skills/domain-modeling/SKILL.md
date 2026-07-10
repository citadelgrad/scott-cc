---
name: domain-modeling
description: Reviews a domain model against 8 type-driven functional-modeling techniques (algebraic data types, illegal-states-unrepresentable, exhaustive matching, parse-don't-validate, smart constructors, errors-as-values, custom error types, workflows-as-functions) and produces a CLEAR/TRIGGERED/N/A findings report. Use when reviewing a type/interface/schema definition, an entity or aggregate with boolean/optional-field clusters, a validation layer, or a multi-step business workflow, or when the user asks for a "domain modeling review" or "type-driven review". Not for OOP entity/repository/aggregate-pattern reviews (this skill is FP-only and does not evaluate class hierarchies), not for general code-quality review (use red-flags or design-review), and not for glossary/terminology work in isolation (use grill-with-docs).
argument-hint: "[file, directory, or domain to review]"
allowed-tools: Read, Grep
---

# Domain Modeling (Type-Driven, Functional)

Authored from scratch for this plugin — grounded in Scott Wlaschin's *Domain Modeling Made Functional*, Alexis King's "Parse, Don't Validate", and Marvin Minsky's illegal-states essay. Not derived from mattpocock's `domain-modeling` skill (confirmed OOP-only, no type-driven content) or any other vendored source. See [CREDITS.md](../../CREDITS.md) for cannibalized-snippet attribution.

This skill is **read-only** and reviews existing code; it does not write or refactor code itself.

## When to Apply

- Reviewing a type, interface, schema, or entity definition for representability of illegal states
- Reviewing a validation layer, parsing boundary, or "checked at the API edge" code path
- Reviewing a multi-step business workflow (order processing, checkout, approval chains, state machines)
- The user asks for a "domain modeling review", "type-driven review", or to check a model against illegal states / ADTs / parse-don't-validate
- **Not** for OOP entity/aggregate/repository review — this skill has no opinion on class design beyond "avoid it except for error types"
- **Not** for general code smells unrelated to domain types (use `red-flags`)
- **Not** for glossary/terminology-only sessions with no code involved (use `grill-with-docs`)

## How to Review

When invoked with `$ARGUMENTS`, scope the review to the specified file, directory, or domain concept. Read the target code first (do not skim from memory).

1. Read [TECHNIQUES.md](./TECHNIQUES.md) for the 8 techniques in teaching/dependency order — each with TS, Python, and Rust reference examples. Techniques build on each other: ADTs (1) are the vocabulary that makes illegal-states-unrepresentable (2) possible; exhaustive matching (3) is the compiler guardrail that keeps (2) true as the model grows; parse-don't-validate (4) is where runtime checks turn into type proofs, made concrete by smart constructors (5); errors-as-values (6) is what a failed parse/step returns instead of throwing, with custom error types (7) giving that channel its own shape; workflows-as-functions (8) composes all seven into a pipeline.
2. Read [WORKED-EXAMPLE.md](./WORKED-EXAMPLE.md) if you need a concrete before/after reference for how a real domain (order → payment → fulfillment) transforms under these techniques.
3. Run the target against every check in [RED-FLAGS.md](./RED-FLAGS.md). Mark each as `CLEAR`, `TRIGGERED`, or `N/A` (not applicable to this code's shape/language).
4. If terminology in the target domain is ambiguous or undocumented, consult [CONTEXT-AND-ADR.md](./CONTEXT-AND-ADR.md) for how to record it in `CONTEXT.md` — but do not write code changes yourself; this skill reports findings only.

## Output Contract

Output is **markdown**, not JSON, so results merge cleanly with other review-panel skills (`red-flags`, `design-review`) that use the same CLEAR/TRIGGERED/N/A vocabulary. For every `TRIGGERED` flag, report:

- **Location** — file:line or type/function name
- **Principle violated** — which of the 8 techniques or red flags
- **Candidate fix** — one or two sentences, not a full rewrite

Example line: `TRIGGERED — src/order.ts:14 — boolean-pair/flag-cluster (illegal states unrepresentable) — replace isPaid/isShipped/isRefunded booleans with a status-tagged union; see WORKED-EXAMPLE.md`

If everything is `CLEAR`, say so plainly — do not force findings where none exist.
