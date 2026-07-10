# CONTEXT.md and ADR Wiring

This skill does **not** invent a new documentation schema. It reuses the vendored mattpocock schema verbatim, exactly as defined in [../../formats/CONTEXT-FORMAT.md](../../formats/CONTEXT-FORMAT.md) and [../../formats/ADR-FORMAT.md](../../formats/ADR-FORMAT.md) — read those two files for the authoritative format. This file only documents *when* this skill writes to them and what stays out.

## CONTEXT.md: Glossary Only

`CONTEXT.md` is a pure domain glossary — term, one-or-two-sentence definition, `_Avoid_` synonyms. It contains **no code, no Result/Either mechanics, no branding/newtype mechanics, no mention of ADTs, exhaustive matching, or any of the 8 techniques in [TECHNIQUES.md](./TECHNIQUES.md)**. Those are implementation-pattern concerns; `CONTEXT.md` is about what a domain *term* means, not how it's typed.

Example of what belongs vs. what doesn't, using the [WORKED-EXAMPLE.md](./WORKED-EXAMPLE.md) domain:

- **Belongs in CONTEXT.md:** `**Fulfillment**: The act of shipping a paid order to the customer. _Avoid_: Shipping (ambiguous with the carrier step alone), Delivery (implies customer receipt, which this term does not).`
- **Does NOT belong in CONTEXT.md:** "Fulfillment is modeled as the `FulfilledOrder` variant of the `Order` sum type, constructed only from a `PaidOrder` via the `fulfill: PaidOrder -> Result<FulfilledOrder, OrderError>` function." — this is a type-design decision, not a glossary entry. It may belong in code comments or (if it clears the ADR gate below) an ADR.

**Written lazily, inline, as terms resolve** — same rule as `grill-with-docs`: don't batch glossary updates. When this skill's review surfaces a domain term that's ambiguous, contested, or undocumented (e.g. reviewer and codebase disagree on what "cancelled" means, or two sibling types use different words for the same concept), resolve it in the moment and write the entry immediately, following the exact structure in [../../formats/CONTEXT-FORMAT.md](../../formats/CONTEXT-FORMAT.md) (single `CONTEXT.md` at repo root, or `CONTEXT-MAP.md` + per-context files for multi-context repos — same detection rule: check for `CONTEXT-MAP.md` first, then root `CONTEXT.md`, then create lazily on first resolved term).

## ADR: The 3-Part Gate

Use the gate exactly as defined in [../../formats/ADR-FORMAT.md](../../formats/ADR-FORMAT.md) — do not loosen or add criteria. All three must be true before offering an ADR:

1. **Hard to reverse** — meaningful cost to changing your mind later
2. **Surprising without context** — a future reader would wonder "why did they do it this way?"
3. **The result of a real trade-off** — genuine alternatives existed and one was picked for specific reasons

### Applying the gate to domain-modeling decisions

**Clears the gate — write an ADR:**
- Choosing an entity's state-machine shape (e.g. "Order lifecycle is a 6-variant tagged union: cart, placed, paid, fulfilled, cancelled, refunded — cancellation and refund are mutually exclusive terminal states, not flags"). This is hard to reverse (every call site depends on the shape), surprising to a reader used to boolean-flag entities, and the result of a real trade-off (a flatter/simpler shape was possible and rejected for specific reasons).
- Adopting Result/errors-as-values **project-wide** as the standing convention for how this codebase's domain layer signals failure. This is an architectural/technology-lock-in-shaped decision per the ADR-FORMAT "what qualifies" list — it constrains every future function signature in the domain layer.

**Does NOT clear the gate — skip the ADR, this is style:**
- Picking `Result` over exceptions for **one function**. Trivially reversible (change one function), not surprising once the project-wide convention (if any) is known, and not really a trade-off if the convention was already decided elsewhere.
- Naming one branded type `CustomerId` vs `CustomerID`. Not hard to reverse, not surprising, not a meaningful trade-off.
- Using a `switch` vs an `if`-chain for one exhaustive match. Implementation detail, not an architectural decision.

The distinguishing question this skill applies: **is this a one-off application of a technique, or the adoption/rejection of the technique as a project-wide convention (or a specific shape decision that many other types will depend on)?** One-offs are style. Convention adoptions and load-bearing shape decisions are ADR-worthy.

### Numbering and location

Follow [../../formats/ADR-FORMAT.md](../../formats/ADR-FORMAT.md) exactly: `docs/adr/NNNN-slug.md`, sequential numbering, directory created lazily on first ADR, template is 1-3 sentences (context, decision, why) with optional Status/Considered-Options/Consequences sections only when they add genuine value. This skill does not add any domain-modeling-specific ADR template — it uses the same one every other reviewer in this plugin uses.

## Invoking adr-skill

`domain-modeling` does not draft ADRs itself and does not duplicate `adr-skill`'s workflow. When the 3-part gate above clears for a finding, **invoke the `adr-skill` skill directly** — see [../adr-skill/SKILL.md](../adr-skill/SKILL.md) — rather than writing the ADR file by hand from this skill's own logic.

Concretely:

1. State the gate result to the human/agent driving the review: which finding cleared the gate and why (cite the specific criterion — hard-to-reverse / surprising / real-trade-off — that each of the three checks satisfied).
2. Invoke `adr-skill` and let it run its own **"Creating an ADR: Four-Phase Workflow"** (Phase 0: Scan the Codebase → Phase 1: Capture Intent (Socratic) → Phase 2: Draft the ADR → Phase 3: Review Against Checklist), as documented in [../adr-skill/SKILL.md](../adr-skill/SKILL.md#creating-an-adr-four-phase-workflow). `domain-modeling` supplies the *trigger and the title material* (the decision that cleared the gate); `adr-skill` owns everything from Socratic questioning through the final reviewed file — do not shortcut its phases just because `domain-modeling` already did the gate-check.
3. `adr-skill` will pick the ADR directory (`docs/adr/` per this skill's numbering convention above, since [../../formats/ADR-FORMAT.md](../../formats/ADR-FORMAT.md) already specifies it — Phase 0 of `adr-skill`'s workflow will find it if it already exists, or create it lazily on first ADR if not) and generate the file, preferably via `scripts/new_adr.js` (see [../adr-skill/SKILL.md](../adr-skill/SKILL.md), "Phase 2: Draft the ADR", step 7).
4. `domain-modeling`'s own output (the CLEAR/TRIGGERED/N/A report) should note that an ADR was proposed/created and link to the resulting file — it does not need to restate the ADR's content.

## No-Node Fallback

`adr-skill`'s directory-detection, drafting, and status-update steps are normally automated by its `scripts/*.js` helpers (`new_adr.js`, `set_adr_status.js`, `bootstrap_adr.js`), which require Node.js. If Node.js is unavailable in the environment where `domain-modeling`'s review is running, **do not skip the ADR just because the script can't run** — `adr-skill` documents a manual fallback for exactly this case in [../adr-skill/ADR-TEMPLATE.md](../adr-skill/ADR-TEMPLATE.md) ("Manual ADR Fallback (No-Node Environments)"). That file reproduces, by hand, the same directory-detection order, filename convention, and field-by-field template the scripts would otherwise generate, so an ADR authored this way is equivalent in content to one produced by `scripts/new_adr.js`.

Use it when: `adr-skill` is invoked per the section above but its `.js` scripts cannot execute (no Node.js on `PATH`, sandboxed environment, etc.). Otherwise the workflow is identical — Phases 0-3 still apply, only the mechanical "generate the file" step in Phase 2 changes from "run `scripts/new_adr.js`" to "copy the template body from `ADR-TEMPLATE.md` and fill it by hand."

## Worked Test Case

This walkthrough grounds both branches of the gate in the order/payment/fulfillment domain from [WORKED-EXAMPLE.md](./WORKED-EXAMPLE.md). It is a demonstration embedded in this documentation — no `docs/adr/` directory or `CONTEXT.md` file is actually created by this walkthrough itself.

### Case A — clears the gate: Order lifecycle state-machine shape

A `domain-modeling` review of the "before" `Order` interface in WORKED-EXAMPLE.md (booleans `isPaid`/`isShipped`/`isCancelled`/`isRefunded` plus optional `paymentId`/`trackingNumber`) flags `TRIGGERED — boolean-pair/flag-cluster (illegal states unrepresentable)` and recommends the "after" shape: a 6-variant tagged union (`CartOrder | PlacedOrder | PaidOrder | FulfilledOrder | CancelledOrder | RefundedOrder`).

Running this recommendation through the 3-part gate:

1. **Hard to reverse?** Yes — every call site (`pay`, `fulfill`, and any future transition function) is written against the shape of the union. Reverting to booleans later means rewriting every consumer's control flow, not a local edit.
2. **Surprising without context?** Yes — a reader used to boolean-flag entities (the "before" shape, which "compiles fine while allowing nonsense" per WORKED-EXAMPLE.md) would wonder why cancellation and refund are separate terminal variants instead of two more booleans.
3. **Real trade-off?** Yes — a flatter shape (keep the booleans, add runtime validation) was a genuine alternative and was rejected specifically because it cannot make `shipped=true, isPaid=false` or `isCancelled=true, isRefunded=true` unrepresentable at the type level; only the tagged union does.

All three clear, so `domain-modeling` invokes `adr-skill` per "Invoking adr-skill" above. `adr-skill` runs its four phases (Phase 0 finds no existing `docs/adr/`, so Phase 2 creates it lazily; Phase 1's Socratic questioning surfaces the same 3 criteria as the trigger, the alternative considered, and the affected files) but **fills the [../../formats/ADR-FORMAT.md](../../formats/ADR-FORMAT.md) template** — the authoritative one for this plugin, per this file's "Numbering and location" section above — not `adr-skill`'s own default MADR/simple templates in `assets/templates/`. That means: title + 1-3 sentences as the required core, with Status/Considered-Options/Consequences added only because they add genuine value here (the rejected alternative and downstream effect are both non-obvious). The resulting `docs/adr/0001-order-lifecycle-state-machine.md` would read like this:

```markdown
---
status: accepted
---

# Model Order lifecycle as a 6-variant tagged union, not boolean flags

`Order` was modeled with independent boolean flags (`isPaid`, `isShipped`,
`isCancelled`, `isRefunded`) plus optional `paymentId`/`trackingNumber`
fields, which compiled while allowing nonsensical states (shipped without
payment, cancelled and refunded at once). We replaced it with a 6-variant
tagged union (`CartOrder | PlacedOrder | PaidOrder | FulfilledOrder |
CancelledOrder | RefundedOrder`) where each variant carries only the
fields valid for that state, because this is the only shape that makes
those illegal combinations a compile error rather than a runtime bug —
the alternative (keep the flags, add a `validateOrder` runtime check) was
rejected since it only catches violations that remember to call it.

## Considered Options

* Keep boolean flags, add a `validateOrder` runtime-check function called
  before every mutation — rejected: same failure mode as the bug we're
  fixing (a forgotten check), just moved one level up.
* 6-variant tagged union with per-variant fields — chosen: makes the
  illegal states unrepresentable at the type level; every transition
  function's signature (`PrevState -> Result<NextState, OrderError>`)
  documents its own precondition.

## Consequences

Every existing call site that reads/writes `Order` via the boolean fields
must migrate to match on the `status` discriminant instead.
```

This is deliberately shorter than `adr-skill`'s own default templates (`assets/templates/adr-simple.md` / `adr-madr.md`, which add Implementation Plan and checkbox Verification sections) — this plugin's wiring asks `adr-skill` to defer to [../../formats/ADR-FORMAT.md](../../formats/ADR-FORMAT.md) instead of its own default output shape, exactly as "Numbering and location" above specifies.

### Case B — does NOT clear the gate: Result vs. exceptions for one function

The same review, examining the `pay` function in isolation, might note that `pay` returns `Result<PaidOrder, OrderError>` rather than throwing. Suppose a reviewer asks whether this one function's choice of `Result` over throwing an exception should be captured as an ADR.

Running it through the gate:

1. **Hard to reverse?** No — changing `pay` alone from `Result` back to a thrown exception is a local, single-function edit with no fan-out beyond its direct callers.
2. **Surprising without context?** No — *if* the project has already adopted errors-as-values project-wide (per this file's "Clears the gate" example: "Adopting Result/errors-as-values project-wide..."), then `pay` using `Result` is simply following the established convention, not something a reader would question. And if no project-wide convention exists yet, that absence is the real gap — not this one function's choice.
3. **Real trade-off?** No — there's nothing to weigh here that wasn't already weighed (and, per criterion 2, likely already decided) at the project-wide level. A single function's error-handling style is not an independent trade-off.

The gate fails on all three criteria (WORKED-EXAMPLE.md's own text calls the project-wide Result convention the ADR-worthy decision, and a single function following it is explicitly listed as a non-example in this file's "Does NOT clear the gate" list above). Nothing gets written as an ADR — `adr-skill` is not invoked.

Instead, this is where the CONTEXT.md lazy-write trigger fires: if, during this same review, "fulfillment" is used inconsistently (e.g. one reviewer comment says "fulfillment" and another says "shipping" for the same `fulfill` step), that's an undocumented/contested domain term — the actual trigger condition from this file's "CONTEXT.md: Glossary Only" section. `domain-modeling` resolves it in the moment and writes the entry immediately (no batching), reusing [../../formats/CONTEXT-FORMAT.md](../../formats/CONTEXT-FORMAT.md)'s schema exactly:

```markdown
## Fulfillment

**Fulfillment**: The act of shipping a paid order to the customer.
_Avoid_: Shipping (ambiguous with the carrier step alone), Delivery
(implies customer receipt, which this term does not).
```

So the outcome of Case B is: no ADR (gate failed on all three criteria), but a `CONTEXT.md` glossary entry for "Fulfillment" written lazily and inline, at the moment the term's ambiguity surfaced — not batched to the end of the review.
