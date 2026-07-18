# Investigation: scc-b56 (Phase 2b — grill-the-schema skill)

## Task
Create `plugins/review-panel/skills/grill-the-schema/SKILL.md`, a new planning-stage skill
modeled on `grill-with-docs`, that interviews the human to build `DATA-MODEL.md` (instead of
`CONTEXT.md`).

## Files to create
- `plugins/review-panel/skills/grill-the-schema/SKILL.md` — new skill file. No other file is
  named in the task's "Files to Create" list, and none needs to change (see "Cross-file check"
  below).

## Current behavior (what exists today)

### The model to mirror: `grill-with-docs/SKILL.md`
`plugins/review-panel/skills/grill-with-docs/SKILL.md` (102 lines) has this shape:
- Frontmatter: `name`, `description` (no `argument-hint`/`allowed-tools` — this is a
  conversational skill, not a review seat like `data-steward`).
- `<what-to-do>`: interview relentlessly, one question at a time with a recommended answer,
  wait for feedback before continuing, prefer exploring the codebase over asking.
- `<supporting-info>`, with sections:
  - **Domain awareness** — file structure (single `CONTEXT.md` vs. multi-context
    `CONTEXT-MAP.md`), lazy file creation.
  - **During the session** — challenge against the glossary, sharpen fuzzy language, discuss
    concrete scenarios, cross-reference with code, update `CONTEXT.md` inline (linking to
    `../../formats/CONTEXT-FORMAT.md`), offer ADRs sparingly (3-part gate, linking to
    `../../formats/ADR-FORMAT.md`).
  - **Offer the plan-security pass when build-ready** — a documentation-pointer offer to a
    sibling skill (`security-suite`'s `plan-security-review`) that may not be installed;
    explicit "say so, don't silently skip" instruction.

### The target format: `formats/DATA-MODEL-FORMAT.md`
Canonical, already built in Phase 2a (scc-f9k). Key structure the interview must populate:
`# Data Model: {Project Name}` intro, `## Entities & relationships` (storage, key fields,
relationships per entity), `## Invariants`, `## Ownership & routing` (table: entity/path →
writer → System 1 or System 2), `## Agent boundary` (escalation-trigger rules), `## Change log`
(dated, human-initialed entries). Rules worth carrying into the interview: record
implementation detail not vocabulary; invariants must be testable, not aspirational; every
entity/path needs both an owner and a System 1/System 2 designation; Agent boundary entries are
escalation triggers, not design notes; change-log entries are dated/initialed; lazy creation
(only when the first entity/invariant/boundary is resolved); repos with no persistent data layer
don't get one.

### Consumers already depending on this skill existing
- `plugins/review-panel/skills/data-steward/SKILL.md` (Phase 2c, already built) references
  `grill-the-schema` twice: once as a recommendation when `DATA-MODEL.md` is absent, phrased
  defensively — "since that skill (`skills/grill-the-schema/SKILL.md`, tracked separately as
  Phase 2b) may not be installed in this session. If it isn't, say so explicitly." This phrasing
  is about session/plugin availability, not file existence, so it stays correct after this task
  lands — **no edit needed there**.
- `plugins/review-panel/reviewers/persona-catalog.md` (Data Steward entry, "Missing-`DATA-MODEL.md`
  fallback" note) also points at the same recommend-grill-the-schema behavior — same reasoning,
  no edit needed.

### Fixture already in place
`plugins/review-panel/tests/fixtures/orders-schema/` (`schema.sql` + `README.md`) already
exists, built during scc-f9k specifically to exercise a grilling-session-style pass against the
format doc *before* this skill existed. Its README states two business rules that exist only as
team knowledge, not SQL constraints (the exact kind of thing a grilling session should surface
as Invariants/Agent-boundary entries):
- Once a `shipments` row has `delivered_at` set, its order is never written again by the order
  service (corrections go through a separate returns service).
- `line_items` are immutable once `orders.state` reaches `placed`.

This fixture is reusable as-is for this task's Run Tests step — no new fixture files are needed
to satisfy the acceptance criterion.

## Required changes, mapped to the acceptance criterion

**AC1**: A grilling session on the `orders-schema` fixture must produce a `DATA-MODEL.md` with
at least an Entities section, one invariant, and an Agent boundary section.

To make that possible, `grill-the-schema/SKILL.md` must:
1. Carry the same interview mechanics as `grill-with-docs` (one question at a time,
   recommended answer, prefer codebase exploration, wait for feedback).
2. Target `DATA-MODEL.md` instead of `CONTEXT.md`, linking to
   `../../formats/DATA-MODEL-FORMAT.md` (same relative path depth as `grill-with-docs` uses for
   `CONTEXT-FORMAT.md`/`ADR-FORMAT.md`, since both skills live at `skills/<name>/SKILL.md`).
3. Interview topics called out explicitly in the task description: entities, invariants,
   lifecycle (soft-delete? audit? retention?), volume/access patterns, and boundaries — these
   map onto `DATA-MODEL-FORMAT.md`'s Entities & relationships, Invariants, and Agent boundary
   sections (lifecycle/volume/access are the *questions that surface* invariants and boundaries,
   not a separate doc section).
4. Stress-test with concrete scenarios (mirrors `grill-with-docs`' "Discuss concrete scenarios"),
   applied to data lifecycle instead of domain relationships — e.g. "if a shipment is marked
   delivered and then a customer disputes the charge, who writes the correction?"
5. Cross-reference actual schema/migration files for contradictions (mirrors "Cross-reference
   with code"), adapted to schema files/migrations instead of domain code.
6. Create `DATA-MODEL.md` lazily on first resolved decision (mirrors `grill-with-docs`' lazy
   `CONTEXT.md` creation).
7. Offer ADRs under the same unmodified 3-part gate (hard to reverse / surprising / real
   trade-off), noting schema decisions frequently clear it — reuse `../../formats/ADR-FORMAT.md`.
8. State Invariant 5 compliance explicitly in the skill text: this skill proposes/drafts
   `DATA-MODEL.md` content through the conversation, but the resulting file is human-owned;
   FIX never auto-modifies it (parallels how `data-steward/SKILL.md` states it is read-only and
   does not edit `DATA-MODEL.md`).
9. Should NOT carry over "Challenge against the glossary"/"Sharpen fuzzy language" verbatim —
   those are CONTEXT.md-specific vocabulary-sharpening behaviors, and `DATA-MODEL-FORMAT.md`'s
   own "Relationship to CONTEXT.md" section says vocabulary belongs in CONTEXT.md, not here.
   The analogous DATA-MODEL session behaviors instead are: (a) checking each entity/path has
   both a named writer and a System 1/System 2 designation (Ownership & routing), and
   (b) phrasing Agent-boundary entries as things an agent must not cross unilaterally, not as
   design notes — both pulled directly from `DATA-MODEL-FORMAT.md`'s Rules.

No frontmatter `allowed-tools`/`argument-hint` needed — `grill-with-docs` has neither, since it's
an interactive conversational skill invoked directly by a human, not a review seat dispatched by
CAST with `$ARGUMENTS`.

## Risks / dependencies
- **Scope discipline**: only the one new SKILL.md file is required. Do not touch
  `data-steward/SKILL.md` or `persona-catalog.md` — their existing forward-references to
  `grill-the-schema` are already correctly hedged for "may not be installed this session" and
  need no update now that the file exists.
- **Don't duplicate the DATA-MODEL-FORMAT.md structure inline** — link to the canonical format
  doc (`../../formats/DATA-MODEL-FORMAT.md`) rather than re-describing its structure, matching
  the "single source of truth" comment at the top of that file and `grill-with-docs`' own
  practice of linking rather than inlining `CONTEXT-FORMAT.md`.
- **Invariant 5** is the main correctness risk: phrasing must make clear the skill drafts/
  proposes, and a human resolves each decision through the conversation — it must not read as
  "the agent writes DATA-MODEL.md for you."
- **Testing**: the Run Tests step will need a live grilling-session dispatch against the
  existing `orders-schema` fixture (playing the human role using the fixture's README's stated
  business rules as answers) to produce an actual `DATA-MODEL.md` and check it against AC1's
  three required sections — no new fixture files anticipated, but the produced `DATA-MODEL.md`
  itself will be a new artifact under the fixture directory (or a scratch location) that should
  be reviewed for section completeness, then handled per the test-results convention used in
  prior phases (scc-bqp's Run Tests step, `.pas/test-results.md`).
