# Investigation: scc-f9k (Phase 2a — DATA-MODEL.md format)

## Task
Create `plugins/review-panel/formats/DATA-MODEL-FORMAT.md`, sibling of the existing
`CONTEXT-FORMAT.md`, defining the shared contract format that three downstream tasks
depend on: `grill-the-schema` (2b, elicits it), `data-steward` seat (2c, enforces it),
and the data-layer guard hook (2d, mechanically gates edits based on its change log).
Spec source: `docs/plans/2026-07-16-two-system-architecture/two-system-spec.md:118-129`
(section "2a. `DATA-MODEL.md` format (shared contract)").

## Files to modify/create
- **New:** `plugins/review-panel/formats/DATA-MODEL-FORMAT.md` — the primary artifact
  this task creates.
- **Edit:** `plugins/review-panel/formats/CONTEXT-FORMAT.md` — add a small
  cross-link/contrast note pointing at the new file, so the relationship is discoverable
  from both directions (spec: "Cross-link both files' formats to each other").

No other files need touching. `persona-catalog.md`, the `grill-the-schema` skill, and
the guard hook are explicitly out of scope — they belong to 2b/2c/2d, which are blocked
on this task and not yet started (confirmed via `rg`: no `data-steward`/`sovereignty`/
`DATA-MODEL` references exist anywhere in `persona-catalog.md` or the rest of the repo
yet — this is a pure addition with zero conflict risk).

## Current behavior / precedent to follow
`plugins/review-panel/formats/` holds two sibling format specs today, both single
canonical markdown files with no frontmatter, referenced by relative link from skills
that consume them:

- **`CONTEXT-FORMAT.md`** (81 lines): opens with an HTML comment declaring itself the
  canonical/single-source-of-truth copy ("do not fork or duplicate this file elsewhere
  in the plugin; reference it instead"). Structure: `## Structure` (a fenced `md`
  example of a full populated file), `## Rules` (bullet list of authoring principles),
  `## Single vs multi-context repos` (lazy-creation + multi-file `CONTEXT-MAP.md` case).
- **`ADR-FORMAT.md`** (48 lines): opens by stating where the artifact lives and its
  numbering scheme, then `## Template` (minimal fenced example), `## Optional sections`,
  `## Numbering`, `## When to offer an ADR` (a 3-part gate: hard to reverse, surprising,
  real trade-off — reused verbatim by `grill-with-docs` for its own ADR offers).

Both are referenced from `grill-with-docs/SKILL.md` and `improve-codebase-architecture/
SKILL.md` via relative links, e.g. `[CONTEXT-FORMAT.md](../../formats/CONTEXT-FORMAT.md)`.
`DATA-MODEL-FORMAT.md` should follow the same relative-link convention once 2b's skill
consumes it — wiring that link into `grill-with-docs` or a new `grill-the-schema` skill
is 2b's job, not this task's.

The `order-fulfillment` fixture's `CONTEXT.md` (`plugins/review-panel/tests/fixtures/
order-fulfillment/CONTEXT.md`) shows what a populated instance looks like: `# Context:
{Name}` title, short scope-disclaimer paragraph, `## Glossary` with bold term +
definition, `## Decision log` with dated entries. No equivalent `DATA-MODEL.md` fixture
exists yet — 2b creates one, tied to its own acceptance criteria (grilling session
against an orders-schema fixture repo).

## Required content (task description + spec:118-129)

**Required sections**, in order, matching the task's exact phrasing (headings are
load-bearing — see Risks below):
1. **Entities & relationships** — with storage mapping (which table/collection an
   entity maps to; this is the "implementation detail" CONTEXT.md forbids).
2. **Invariants** — what must never be violated (consumed directly by 2c's data-steward
   seat, which checks diffs against this section).
3. **Ownership & routing** — which system writes what (System 1 vs System 2, per the
   PRD's two-system vocabulary, `two-system-prd.md:19-27`).
4. **Agent boundary** — decisions agents may not revisit without escalation. This is
   the section 2c's "sovereignty escalation" mechanism checks crossings against
   (`two-system-spec.md:157-160`: a finding gets marked `sovereignty: human-required`
   when a diff "crosses the Agent boundary section of DATA-MODEL.md").
5. **Change log** — dated, human-initialed. This is what 2d's guard hook checks for
   (presence of a current-work entry) before allowing an Edit/Write to a data-layer path
   (`two-system-spec.md:189-191`).

**Two explicit requirements beyond the section list**, both must be spelled out in prose
in the format file itself (not just implied by section names):

- **Contrast with CONTEXT.md.** CONTEXT.md is a glossary of *what things are called*
  and explicitly forbids implementation detail (its own Rules say "Define what it IS,
  not what it does"). DATA-MODEL.md is the inverse — it *is* the implementation-detail
  record: storage mapping, schema/migration-level invariants, etc. Must cross-link to
  `CONTEXT-FORMAT.md` and vice versa, stating this distinction so a reader landing on
  either file understands which one they need.
- **Cross-system contract declaration.** Must state explicitly that DATA-MODEL.md binds
  System 2 fixes (a migration inside a library upgrade, an IaC data-store change) to the
  identical rules as System 1 changes — not a separate, looser standard. Directly serves
  `two-system-prd.md:75`: "shared contract honored by both systems."

## How downstream tasks will read this file (context only, not this task's job to build)
- **2b (`grill-the-schema`)** interviews the human about entities, invariants,
  lifecycle, volume/access patterns, boundaries — populates sections 1, 2, 4 (and
  touches 3/5) through elicitation, modeled on `grill-with-docs`.
- **2c (`data-steward` seat)** reads Invariants + Agent boundary to evaluate diffs, and
  writes the `sovereignty: human-required` marker when a diff crosses an Agent-boundary
  entry, or when DATA-MODEL.md is absent entirely while the diff changes schema
  semantics (a boundary case the spec already resolves at the 2c/2d level — this format
  file doesn't need to define fallback behavior itself, just be unambiguous about what
  "Agent boundary" contains).
- **2d (guard hook)** looks for the Change log section specifically — checks for a dated
  entry for current work before allowing edits to data-layer paths.

Section *names* and their semantics are load-bearing — 2b/2c/2d will read/parse against
these heading strings, so the format file must state the five section headings plainly
(as `##` headings in a fenced template example, matching CONTEXT-FORMAT.md's
convention) rather than only describing them in prose.

## Risks / things to get right
- **Don't over-specify.** Per repo convention (ADR-FORMAT.md's minimalism, CLAUDE.md's
  "don't design for hypothetical future requirements"), define the five required
  sections and the two explicit requirements, then stop — no need to invent a
  storage-mapping sub-schema or an Agent-boundary entry schema beyond what 2c's spec
  text already implies (a per-decision item flaggable with a marker). 2b/2c/2d can
  refine consumption details when they land; this task only establishes the contract
  shape.
- **Heading-name stability matters more than for CONTEXT.md.** Because 2c/2d parse
  against "Invariants," "Agent boundary," and "Change log" specifically (per spec
  wording), the template headings must exactly match the section names the task
  description uses, not paraphrases.
- **Lazy creation.** CONTEXT-FORMAT.md documents lazy creation of CONTEXT.md ("create
  the file lazily when the first term is resolved"). The spec says 2b "creates
  DATA-MODEL.md lazily on first resolved decision" — worth stating the same lazy-creation
  norm in this format file for consistency, even though actual creation happens in 2b.
- **Scope discipline.** Do not touch `persona-catalog.md`, `grill-with-docs/SKILL.md`,
  or create any `grill-the-schema` skill — all belong to the three blocked downstream
  tasks (2b/2c/2d), which is exactly why this task exists first (`bd show scc-f9k`
  confirms it blocks all three).

## Acceptance criteria mapping
Task's stated AC ("Grilling session on a fixture repo... produces a DATA-MODEL.md
containing at least entities, one invariant, and an Agent boundary section... verified
indirectly via task 2b's grilling flow, but the format itself must define and require
these sections") means this task's own testable surface is: does
`DATA-MODEL-FORMAT.md` exist and does it *define and require* (not just optionally
mention) the five sections, especially Entities & relationships, Invariants, and Agent
boundary? The actual grilling-session behavior is 2b's test, not this task's — this
task is format-definition only, no runtime/skill behavior to exercise.
