# Subtraction Lens Catalog

Step 3 of the review says which lenses apply to each target type. For each lens you walk, write a concrete candidate or mark it `n/a` with a one-line reason. Each lens has a prompt, the additive reflex it counters, and an engineering example.

| ID | Lens | Code | Plan | Process |
|---|---|:-:|:-:|:-:|
| L1 | Remove the cause | ✓ | ✓ | ✓ |
| L2 | Remove the special case | ✓ | | |
| L3 | Remove a layer | ✓ | ✓ | |
| L4 | Remove state | ✓ | ✓ | |
| L5 | Remove a duplicate source of truth | ✓ | ✓ | |
| L6 | Remove a dependency | ✓ | ✓ | |
| L7 | Remove configuration surface | ✓ | new options | |
| L8 | Remove dead and dormant code | ✓ | | |
| L9 | Revert | ✓ | | |
| L10 | Remove the requirement | | ✓ | ✓ |
| L11 | Remove the feature | | ✓ | |
| L12 | Remove a constraint | | ✓ | ✓ |
| L13 | Remove a step | | | ✓ |
| L14 | Remove a handoff | | | ✓ |
| L15 | Remove documentation that lies | | | ✓ |
| L16 | Remove the second implementation | ✓ | ✓ | |
| L17 | Validate once, at the boundary | ✓ | | |

## Code and design

### L1. Remove the cause, not the symptom

- **Prompt:** What existing thing makes this addition necessary? What if it were gone?
- **Additive reflex:** add a guard, retry, null check, or cleanup job around the symptom.
- **Example:** A PR adds a deduplication pass because a webhook handler double-inserts rows. The subtractive fix removes the second code path that also inserts on the same event.
- **For bug fixes:** ask whether the code path that made the bug possible can be deleted, instead of hardening it.

### L2. Remove the special case

- **Prompt:** Can the general path handle this input so no branch is needed?
- **Additive reflex:** `if edge_case: ...`
- **Example:** An empty-list branch returns early with a hand-built result. Removing it lets the normal loop produce the same result for zero items.

### L3. Remove a layer

- **Prompt:** Which wrapper, adapter, manager, or interface could be deleted so callers use the real thing directly?
- **Additive reflex:** add a new wrapper to fix the old wrapper's leaky behavior.
- **Example:** A bug comes from a caching wrapper that hides the client's own timeout setting. Delete the wrapper; set the timeout on the client.

### L4. Remove state

- **Prompt:** Can this stored value be derived when needed? Can this flag, setting, or mode disappear?
- **Additive reflex:** add a sync job or invalidation logic to keep stored state correct.
- **Example:** A `total` column drifts from the sum of line items. Drop the column and compute the sum.

### L5. Remove a duplicate source of truth

- **Prompt:** Are two things that must agree both writable? Which one can go?
- **Additive reflex:** add a reconciliation script or a consistency check.
- **Example:** Version numbers live in three manifests. Keep one and generate or read the others from it.

### L6. Remove a dependency

- **Prompt:** Can stdlib, the platform, or code already in the repo replace this package or service?
- **Additive reflex:** add a package to fix a gap, or add a shim around a package's bug.
- **Example:** A date library is added for one ISO-8601 parse that the stdlib already does.

### L7. Remove configuration surface

- **Prompt:** Does anyone set this option to a non-default value? Can the default become the only behavior?
- **Additive reflex:** add a flag so both behaviors stay available.
- **Example:** A new `--strict` flag is proposed. Usage shows nobody needs the lax mode. Make strict the only mode.

### L8. Remove dead and dormant code

- **Prompt:** Which flags are fully rolled out, which paths have no callers, which fallbacks never fire?
- **Additive reflex:** add the new path beside the old one "for safety" and never come back.
- **Example:** A feature flag at 100% for six months still guards two code paths. Remove the flag and the losing path.

### L9. Revert

- **Prompt:** Did a recent change introduce this problem? Is reverting it the full fix?
- **Additive reflex:** add a forward fix on top of the change that caused the bug.
- **Example:** A performance regression follows a new middleware. Revert the middleware instead of adding a cache to compensate.

### L16. Remove the second implementation

- **Prompt:** Does the change add a near-copy of a function, guard, helper, fixture, or path that already exists? Can one of them go?
- **Additive reflex:** add a new sibling with the small difference you need, and leave the old one in place.
- **Example:** A PR adds `guarded_release` beside `released_guard`. The only caller of the old one moves to the new one. Delete the old one, or extend it and skip the new one. L5 covers duplicated *data*; this lens covers duplicated *code*.

### L17. Validate once, at the boundary

- **Prompt:** Is the same input checked in several places inside the system? Can one check at the trust boundary replace them?
- **Additive reflex:** add another defensive check in each function that touches the value.
- **Example:** Three internal functions each re-validate a run pointer. Parse it once into a validated type where it enters the system; delete the inner checks.
- **Guard:** the boundary check must exist and be tested before the inner checks go. This is net removal, not moving complexity.

## Requirements and scope

### L10. Remove the requirement

- **Prompt:** Who owns this requirement? Is it still true? What happens if it is dropped or narrowed?
- **Additive reflex:** build the feature as specified.
- **Example:** A spec asks for export in five formats. Only CSV has any recorded use. Ship CSV.

### L11. Remove the feature

- **Prompt:** Is the thing being fixed or extended actually used?
- **Additive reflex:** keep improving a feature nobody uses.
- **Example:** A bug report against a legacy report page with no visits in a year. Delete the page.

### L12. Remove a constraint

- **Prompt:** Which self-imposed rule forces this addition? Is the rule still earning its cost?
- **Additive reflex:** work around the constraint with more code.
- **Example:** A rule that every module must have an interface forces a new interface with one implementation. Drop the rule for single-implementation modules.

## Process and operations

### L13. Remove a step

- **Prompt:** Which step in this workflow produces nothing anyone reads or acts on?
- **Additive reflex:** add a checklist item, approval, or meeting after each incident.
- **Example:** A release needs a manual sign-off that has never blocked a release. Remove it; keep the automated gate.

### L14. Remove a handoff

- **Prompt:** Can one owner do this end to end so the handoff and its tracking disappear?
- **Additive reflex:** add a ticket type or status to track the handoff.

### L15. Remove documentation that lies

- **Prompt:** Which docs, comments, or runbooks are stale? Is deleting them better than adding a correction note?
- **Additive reflex:** add a "NOTE: this is outdated" banner.

## How to record a lens result

```text
L1 remove-cause: SUB-1 — delete second insert path in webhook.py:88; dedup pass not needed
L2 special-case: n/a — no new branches in the diff
L7 config-surface: SUB-2 (hypothesis) — --strict flag; check usage before deciding
```
