# Test Results: scc-b56 (Phase 2b — grill-the-schema skill)

## Scope

Task added one file: `plugins/review-panel/skills/grill-the-schema/SKILL.md`. No code, no
test harness, no `package.json`/`pyproject.toml`/lint config exists anywhere under
`plugins/review-panel/` (confirmed via directory listing) — this is a markdown skill
definition consumed by a human/agent conversation, not executable code. The project's
established validation convention for this plugin is live sub-agent dispatch against a
fixture (`plugins/review-panel/tests/PRESSURE-TEST.md`, and precedent from scc-bqp's
`.pas/test-results.md`), not an automated test suite.

## AC1 — Grilling session produces complete DATA-MODEL.md

**Fixture note:** `plugins/review-panel/tests/fixtures/orders-schema/` already contains a
`DATA-MODEL.md`, but it predates this skill — it was produced during scc-f9k's (Phase 2a) Run
Tests step to prove the *format doc alone* was sufficient, before `grill-the-schema` existed
(the fixture's own `README.md` says so explicitly: "no skill yet exists — that's task 2b").
Reusing that file would not test the skill under review. Instead, this test ran a live dispatch
against a clean scratch copy of the fixture (`schema.sql` + `README.md` only, no
`DATA-MODEL.md`, copied to `/tmp/grill-the-schema-test/orders-schema/` — outside the repo, not
committed) so the produced artifact is actually attributable to the skill's instructions. The
committed fixture's pre-existing `DATA-MODEL.md` was left untouched.

**Method:** Live dispatch (general-purpose sub-agent) given the actual `SKILL.md` content and
`DATA-MODEL-FORMAT.md`, instructed to play both interviewer and human-answering roles (using
the fixture README's two team-knowledge business rules as the "human's" ground-truth answers,
since no live human is available in an automated test), and to produce
`/tmp/grill-the-schema-test/orders-schema/DATA-MODEL.md`.

**Transcript evidence the skill's actual mechanics were exercised** (not just file production):
- Explored `schema.sql` before asking, per "if a question can be answered by exploring the
  codebase, explore the codebase instead" — derived the three entities and translated the two
  SQL `CHECK` constraints into testable invariants directly, without prompting the human for
  facts already visible in the schema.
- Cross-referenced the README's stated business rules against `schema.sql` and explicitly
  flagged the contradiction/gap: no trigger or constraint enforces "no writes to `orders` after
  `delivered_at`" — surfaced as the exact SQL-invisible team-knowledge invariant the skill
  exists to catch.
- Ran two concrete-scenario stress tests ("shipment delivered, then customer disputes the
  charge — who writes the correction?"; "customer wants to add a unit to an already-placed
  order — is that an UPDATE?"), each forcing a precise ownership/boundary answer rather than a
  vague one.
- Asked about volume/access patterns, got no signal from the fixture, and explicitly noted it
  out of scope rather than fabricating an answer.
- Converted every surfaced invariant into Agent-boundary language phrased as an escalation
  trigger ("do not add an UPDATE path... without escalation"), not a design note.

**Resulting `DATA-MODEL.md` — section-by-section check against AC1's three required sections
(plus the format's other required sections, which the skill also produced):**

| Required section | Present | Detail |
|---|---|---|
| Entities & relationships | ✅ | Order, Line Item, Shipment — each with Storage/Key fields/Relationships |
| Invariants (≥1) | ✅ | 4 entries: 2 derived from SQL `CHECK` constraints, 2 derived from README team-knowledge rules, explicitly marked "Not enforced in SQL" |
| Agent boundary | ✅ | 3 escalation-trigger rules, phrased as "do not... without escalation/sign-off" |
| Ownership & routing (format requirement, not AC1-listed but produced) | ✅ | 5 rows, every row has both a writer and a System 1/System 2 designation |
| Change log (format requirement) | ✅ | 3 dated, initialed (SN) entries |

**AC1: PASS** — file exists with all three AC1-required sections (Entities, ≥1 Invariant, Agent
boundary), plus the format's other required sections (Ownership & routing, Change log), all
correctly structured per `DATA-MODEL-FORMAT.md`.

## Skill-clarity findings (informational, not blocking)

The dispatch flagged two points worth a human's attention, neither of which is an AC1 defect:

1. The skill's "one question at a time, wait for feedback" and "update inline, don't batch"
   instructions assume a live interactive session; they don't define a fallback for
   non-interactive/scripted validation. This is correct behavior for the skill's real use case
   (a human-driven grilling session) — the ambiguity only surfaced because this test dispatch
   had to simulate both sides of a conversation that normally has two participants.
2. `plugins/review-panel/tests/fixtures/orders-schema/README.md` is now stale: it says "no
   skill yet exists — that's task 2b," which was true when written (during scc-f9k) but is no
   longer true now that `grill-the-schema/SKILL.md` exists. Not part of this task's Files to
   Create list and not required by AC1 — flagged here for a human to decide whether to update it
   in a future pass, per this task's scope-discipline note in `.pas/investigation.md` (only the
   one new SKILL.md file is in scope).

## Security scan

`gitleaks detect --no-git` run against the scratch dispatch output
(`/tmp/grill-the-schema-test/`, ~5.4 KB): **no leaks found**. This scratch directory is outside
the repo and was not committed; it was deleted after this write-up was authored.

## Fixture/artifact summary

- No new fixture files added to the repo — the existing `orders-schema` fixture
  (`schema.sql` + `README.md`) was reused as-is, per `.pas/investigation.md`'s assessment.
  Confirmed via `git status --porcelain` on the fixture directory: no changes.
- One scratch artifact produced and reviewed outside the repo
  (`/tmp/grill-the-schema-test/orders-schema/DATA-MODEL.md`), then discarded — not committed,
  matching the task's Invariant-5-adjacent scope discipline (this Run Tests step should not add
  a second `DATA-MODEL.md` to the committed fixture).
