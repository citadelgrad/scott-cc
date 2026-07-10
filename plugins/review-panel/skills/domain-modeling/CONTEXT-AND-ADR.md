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
