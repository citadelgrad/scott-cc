# Test Results: scc-f9k — Phase 2a (DATA-MODEL.md format, shared contract)

## 0. What this covers

This is the "Run Tests" step for `scc-f9k`, which adds
`plugins/review-panel/formats/DATA-MODEL-FORMAT.md` (new) and a small
reciprocal cross-link edit to `plugins/review-panel/formats/CONTEXT-FORMAT.md`.

Per `.pas/investigation.md`, this task is **format-definition only** — no
skill or runtime behavior ships in this task (that's 2b/`grill-the-schema`,
2c/`data-steward`, 2d/guard hook, all blocked on this one). The task's stated
acceptance criterion is explicit that the actual "grilling session" behavior
is verified indirectly by 2b later; this task's own testable surface is
whether the format file **defines and requires** the five sections, not
whether a working skill exists yet.

Given that, and following the same live-dispatch methodology as prior tasks
in this epic (`scc-g12`'s `test-results.md`), I ran two independent checks:
1. A structural/content check of the format file itself.
2. A **live** `Agent` dispatch (not simulated) that used *only* the new format
   document as guidance to hand-derive a `DATA-MODEL.md` from a freshly seeded
   fixture — a stronger bar than the task's own stated AC, because it tests
   whether the format is actually sufficient to drive correct output, not just
   whether the right headings exist.

**Verdict: PASS.** Details below.

## 1. Structural check (does the format define and require the 5 sections?)

Confirmed via direct read + `rg -n "^## " plugins/review-panel/formats/DATA-MODEL-FORMAT.md`:

```
11:## Structure
18:## Entities & relationships
30:## Invariants
36:## Ownership & routing
44:## Agent boundary
50:## Change log
56:## Rules
75:## Relationship to CONTEXT.md
92:## Cross-system contract
100:## Lazy creation
```

- All five required headings present **verbatim** as the task's exact phrasing
  ("Entities & relationships", "Invariants", "Ownership & routing", "Agent
  boundary", "Change log") — both inside the fenced `## Structure` template
  (load-bearing for 2b/2c/2d parsing) and reinforced by name in `## Rules`.
- **Contrast with CONTEXT.md**: present as its own `## Relationship to
  CONTEXT.md` section, stating the glossary-vs-implementation-detail
  distinction explicitly, plus a reciprocal link.
- **Cross-system contract declaration**: present as its own `## Cross-system
  contract` section, stating System 2 fixes (migrations, IaC data-store
  changes) are bound identically to System 1 diffs — matches
  `two-system-prd.md:75`'s "shared contract honored by both systems."
- **Cross-link is bidirectional**: `CONTEXT-FORMAT.md`'s opening paragraph
  (before its own `## Structure`) now links to `DATA-MODEL-FORMAT.md` with the
  same glossary/implementation-detail contrast stated from the other
  direction. Confirmed both relative links resolve (siblings in the same
  `formats/` directory).
- **Lazy creation** norm carried over from `CONTEXT-FORMAT.md` for
  consistency, as flagged in the investigation.

PASS — the file exists and requires (not just optionally mentions) all five
sections, satisfying the task's literal AC text.

## 2. Live dispatch: is the format sufficient to drive a correct instance?

### Fixture created
`plugins/review-panel/tests/fixtures/orders-schema/`:
- `schema.sql` — a Postgres schema for `orders` / `line_items` / `shipments`
  (enum state column, two `CHECK` constraints, FKs) — a different shape than
  the format doc's own worked example (Order/Invoice/Customer), so an agent
  can't pass by copying the template.
- `README.md` — two business rules that exist **only** as team knowledge, not
  as SQL constraints: (1) line items become immutable once an order is
  `placed`; (2) an order's row becomes read-only to the order service once any
  shipment is delivered (corrections go through a separate returns service).
  These exist specifically to test whether a "grilling session" against the
  format would surface facts a schema-only reader couldn't get right.

### Dispatch
Live `Agent` dispatch (task id `a1fa535847af08754`, general-purpose,
~35s, 6 tool uses), instructed to read **only**
`DATA-MODEL-FORMAT.md` as its guidance (no other skill/format file), read the
fixture, and produce `plugins/review-panel/tests/fixtures/orders-schema/DATA-MODEL.md`
without copying the format doc's own Order/Invoice example content.

### Result — PASS
Output file (`.../orders-schema/DATA-MODEL.md`, 80 lines) contains all five
required sections with exact heading strings, genuinely derived from the
fixture (Order/Line Item/Shipment, not Order/Invoice/Customer):
- **Entities & relationships**: 3 entities, each with Storage/Key
  fields/Relationships, matching `schema.sql`.
- **Invariants**: 5 entries — 3 map to actual `CHECK` constraints, and both
  README-only business rules were surfaced as invariants #4 and #5, each
  explicitly flagged "enforced only by convention today; the schema has no
  constraint preventing an `UPDATE`" — meaning the dispatch not only
  transcribed the rules but correctly distinguished schema-enforced vs.
  convention-only, unprompted.
- **Ownership & routing**: table with System 1/System 2 column populated for
  every entity, including splitting `orders` into pre-/post-delivery rows to
  reflect the returns-service handoff.
- **Agent boundary**: 4 entries, phrased as escalation triggers — both
  README rules appear here too (line-item immutability, post-delivery
  order lock), plus the enum-transition and check-constraint-integrity
  entries mirrored from the format's own Rules guidance.
- **Change log**: 2 dated, initialed entries.

Self-report from the dispatch (verbatim, abridged): *"All five sections
produced, no ambiguity blocking completion. The format document alone ...
was sufficient to derive a valid instance ... without needing to consult any
other file."* Both non-SQL business rules were confirmed captured in both
Invariants and Agent boundary.

### Friction points flagged by the dispatch (advisory, not blocking)
Recorded here for 2b (`grill-the-schema`) to consider, **not** acted on in
this task — per the investigation's explicit risk note ("don't over-specify,"
"2b/2c/2d can refine consumption details when they land; this task only
establishes the contract shape"):
1. No guidance on split/footnote convention for state-conditional ownership
   rows (e.g. a table written by different services depending on lifecycle
   phase).
2. No explicit call-out in Rules for phrasing a constraint-backed invariant
   differently from a convention-only (team-knowledge) invariant — the
   dispatch handled it well on its own, but a future skill author may want
   this made explicit.
3. No stated cross-section consistency checklist (e.g. "every entity in
   Entities & relationships must also appear in Ownership & routing") —
   inferred correctly from the worked example, not stated as a rule.

None of these caused a section to be missing, ambiguous, or malformed — they
are minor completeness suggestions for whoever builds 2b, not defects in this
task's deliverable.

## 3. Linting / secrets

No JS/TS files touched (markdown + one `.sql` fixture + one fixture
`README.md`); no markdown linter or CI workflow configured in this repo
(confirmed: no `.markdownlint*` config, no `.github/workflows/` present).
`gitleaks detect --no-git` run independently against all three
new/modified files (`DATA-MODEL-FORMAT.md`, `CONTEXT-FORMAT.md`,
`tests/fixtures/orders-schema/`) — no leaks found in any.

## 4. Scope check

Files touched by this Run Tests step, all additive test artifacts:
- `plugins/review-panel/tests/fixtures/orders-schema/schema.sql` (new)
- `plugins/review-panel/tests/fixtures/orders-schema/README.md` (new)
- `plugins/review-panel/tests/fixtures/orders-schema/DATA-MODEL.md` (new,
  produced by the live dispatch — kept as a concrete fixture instance for 2b
  to reference, matching the repo convention of populated fixture files like
  `order-fulfillment/CONTEXT.md`)
- `.pas/test-results.md` (this file)

No changes made to `persona-catalog.md`, `grill-with-docs/SKILL.md`, or any
`grill-the-schema` skill — confirmed still out of scope for 2b/2c/2d, matching
the investigation's scope discipline note.

## Summary

| Check | Result |
|---|---|
| Format file exists, defines & requires all 5 sections | PASS |
| Contrast with CONTEXT.md documented + bidirectional cross-link | PASS |
| Cross-system contract declaration present | PASS |
| Live dispatch: format alone drives a correct, non-copied instance | PASS |
| Live dispatch: both non-SQL business rules surfaced correctly | PASS |
| Gitleaks | PASS (no leaks) |
| Scope discipline | PASS (no 2b/2c/2d files touched) |

**All acceptance criteria met.** No fixes required before Close Task.
