# Investigation: scc-g12 — Phase 1b Plan-security pass

## Task
Add `plugins/security-suite/skills/plan-security-review/SKILL.md`, a planning-stage
threat-model checkpoint (not a diff/code review — that's the Phase 1a Security seat in
review-panel, already shipped in commit eb5ee33). Wire it into
`plugins/review-panel/skills/grill-with-docs/SKILL.md` as a closing-step offer. Spec
source: `docs/plans/2026-07-16-two-system-architecture/two-system-spec.md:81-113`
(section "1b. Plan-security pass").

## Current state

### security-suite plugin layout
- `plugins/security-suite/.claude-plugin/plugin.json` — name/version/author only, no
  `skills` field to register (Claude Code plugin skills auto-discover from
  `skills/*/SKILL.md`, same as review-panel — no plugin.json edit needed).
- `plugins/security-suite/agents/security-advisor.md` — has the OWASP topic table this
  task must reuse: "Available Topics by Category" (lines 28-63), organized as
  Authentication & Sessions, Injection Prevention, Web Application Security, API & Web
  Services, Infrastructure & DevOps, Data Protection & Cryptography, AI/LLM Security,
  Secure Development. Each topic maps to a fetchable URL:
  `https://cheatsheetseries.owasp.org/cheatsheets/{Topic}_Cheat_Sheet.html`.
- `plugins/security-suite/agents/security-engineer.md` — diff/code-review agent (Phase
  1a's cast target), not this task's concern.
- **No `skills/` directory exists yet in security-suite** — this is the plugin's first
  skill. Precedent for skill frontmatter/structure comes from review-panel's skills
  (see below), not from security-suite itself.
- `plugins/security-suite/README.md` lines 59-68 has a ready-made "Security Checklist"
  (no hardcoded secrets, input validation, SQL injection, XSS, CSRF, authn/authz, data
  encryption at rest/in transit) — a reasonable seed for the offline/degraded built-in
  checklist fallback (AC3), since no other air-gapped checklist precedent exists
  anywhere in the repo.

### CLEAR/TRIGGERED/N/A vocabulary precedent
`plugins/review-panel/skills/domain-modeling/SKILL.md` (lines 30, 33-47) is the
canonical source of this vocabulary:
- Screen every check as `CLEAR` / `TRIGGERED` / `N/A` (not applicable to this artifact's
  shape).
- Only `TRIGGERED` lines are reportable findings; `CLEAR`/`N/A` carry no severity and
  aren't forced.
- Report format per triggered line: `TRIGGERED — <location> — <principle> — <severity> —
  <note>`.
- Explicit instruction: "If everything is CLEAR, say so plainly — do not force findings
  where none exist." This directly satisfies AC2 (pure UI-copy plan → all CLEAR/N/A, zero
  TRIGGERED, explicit "no security-relevant surface" statement).

`plugins/review-panel/skills/red-flags/SKILL.md` is a second, lighter-weight precedent
for the same vocabulary applied to a checklist-of-checks structure (Review Process step
2: "For each: CLEAR, TRIGGERED, or N/A").

### grill-with-docs (wire-in target)
`plugins/review-panel/skills/grill-with-docs/SKILL.md` (89 lines) is a single-file skill,
no `SKILL.md` frontmatter fields beyond `name`/`description` (no `allowed-tools` — it's a
conversational interview skill, not a scanner). Structure: `<what-to-do>` block (top),
`<supporting-info>` block (bottom) with subsections (Domain awareness, During the
session: Challenge against the glossary / Sharpen fuzzy language / Discuss concrete
scenarios / Cross-reference with code / Update CONTEXT.md inline / Offer ADRs sparingly).
The session currently has **no closing step at all** — it just ends when decisions are
resolved. This task adds one: a closing offer of the plan-security pass "when the
grilling session ends with a build-ready plan," documentation-only (no new mechanism,
just a step that tells the assistant to offer/invoke the skill).

### Foundry section / docs/foundry-recipes.md
- `docs/foundry-recipes.md` **does not exist yet** (confirmed: no matches for
  `foundry-recipes` under `docs/`). Per spec lines 330-371 (Phase 5 — Triage spine),
  creating this file with its full schedule-wiring content
  (`docs/foundry-recipes.md          # schedule wiring for Foundry`, spec line 342) is
  explicitly **Phase 5's job** (task `scc-tsa`, currently blocked and not started — this
  task, scc-g12, is one of its two blockers per `bd show scc-g12`).
- Spec line 102 / current_task.md line 22 both describe this task's obligation as: "This
  spec's Foundry section (Phase 5) lists it as a schedulable pre-build gate in
  docs/foundry-recipes.md" — worded as a **forward reference**, not an instruction for
  this task to create the file itself. Spec lines 368-371 confirm Phase 5 is what
  actually writes `docs/foundry-recipes.md` and explicitly says it "lists Phase 1b's
  plan-security pass ... as a schedulable entry" — i.e., Phase 5 does the listing, using
  Phase 1b's skill as an input.
- **Judgment call (flagging for Plan step):** scc-g12 should NOT create
  `docs/foundry-recipes.md` — that would be doing Phase 5's work early, out of this
  task's file scope, and duplicating effort once scc-tsa actually builds it. Instead,
  the new `plan-security-review/SKILL.md` should include a short "Foundry" note stating
  it is designed to be schedulable as a pre-build gate (so Phase 5 has something concrete
  to wire in), without touching `docs/foundry-recipes.md` itself. This mirrors the
  Task's own file list wording — "docs/foundry-recipes.md (Phase 5 section reference)" —
  which reads as "referenced by," not "created by," this task.

### Air-gapped / offline constraint precedent
- `two-system-prd.md` decision D7: security-suite is "Reference; no vendoring — revisit
  only if an air-gapped deploy actually materializes" — i.e., WebFetch-to-OWASP-online is
  the default/expected path today; air-gapped is the exception path this task must still
  handle gracefully (AC3), not the default.
- `plugins/review-panel/skills/review-panel/references/design-lineage.md:41-43` documents
  the plugin's general "air-gapped constraint" as a known hard constraint from the plan's
  §2, already used to justify why VALIDATE uses same-model Task dispatch instead of
  cross-model integration. This is the closest existing "graceful offline degradation"
  precedent in the repo, though it's about model diversity, not WebFetch — no reusable
  code/logic, just confirms the constraint is a recognized first-class concern.
- No skill in the repo currently implements a live WebFetch-with-fallback pattern to
  copy structurally. This task's SKILL.md must originate that pattern itself, using
  security-advisor.md's topic table as the "always available" (non-network) baseline
  data, and WebFetch as an enrichment step when reachable.

## Required changes

1. **New file: `plugins/security-suite/skills/plan-security-review/SKILL.md`**
   - Frontmatter: `name`, `description` (with explicit "Use when..." trigger language
     and a "Not for..." boundary line, matching domain-modeling's/red-flags'
     description style), no `allowed-tools` restriction needed since it only reads a
     plan doc + optionally WebFetches (or `Read, Grep, Glob, WebFetch` if being
     explicit/read-only, following domain-modeling's `allowed-tools: Read, Grep`
     precedent extended with WebFetch).
   - Input: a plan/PRD/spec document, either a path argument or already in
     conversation context.
   - Procedure:
     a. Extract security-relevant deltas from the plan (new endpoints, new data flows,
        authn/authz surface changes, secrets/credentials introduced, third-party deps
        added, trust boundaries crossed).
     b. Map each delta to OWASP cheatsheet topics, reusing security-advisor.md's topic
        table (link to it, don't duplicate the whole table — keep single-sourced)
     c. Online: WebFetch the relevant cheatsheet(s) for citation-quality detail.
        Offline/WebFetch unavailable: fall back to a **built-in checklist** derived from
        security-suite/README.md's Security Checklist (secrets, input validation, SQLi,
        XSS, CSRF, authn/authz, encryption at rest/in transit) plus the topic *names*
        from security-advisor.md's table (topic names alone are enough for AC1's "cite
        topic names" requirement even without live fetch content).
     d. Emit findings as `CLEAR` / `TRIGGERED` / `N/A` lines per topic area, each
        `TRIGGERED` line citing the OWASP topic name (AC1). Follow domain-modeling's
        format convention: `TRIGGERED — <plan section/feature> — <OWASP topic> —
        <one-line rationale>`.
     e. If the pass ran in degraded (no-WebFetch) mode, state that explicitly in the
        output (AC3) — e.g. a leading "Degraded mode: WebFetch unavailable, built-in
        checklist used" line.
     f. Close with a one-paragraph go/no-go recommendation.
   - Explicit boundary statement (verbatim requirement from spec/task): "Not for
     reviewing code diffs — that is the panel's security seat" (i.e. review-panel's
     Phase-1a Security seat, `persona-catalog.md`'s `### Security` entry).
   - AC2 handling: when no delta maps to any topic, all lines are `CLEAR`/`N/A` and the
     skill states plainly "no security-relevant surface" (mirrors domain-modeling's "If
     everything is CLEAR, say so plainly" instruction) — zero forced TRIGGERED lines.
   - Include a short "Foundry" note (see judgment call above) that this pass is designed
     to be schedulable as a pre-build gate, without creating `docs/foundry-recipes.md`.

2. **Edit: `plugins/review-panel/skills/grill-with-docs/SKILL.md`**
   - Add a closing step (new subsection under `<supporting-info>`, e.g. after "Offer
     ADRs sparingly") offering the plan-security pass when the session concludes with a
     build-ready plan. Documentation-only — point at
     `security-suite`'s `plan-security-review` skill by name, note the missing-plugin
     degrade (if `security-suite` isn't installed, say so rather than silently skipping
     — consistent with Invariant 3, Coverage honesty, and the Phase 1a missing-plugin
     fallback pattern already established in `persona-catalog.md`).

3. **`docs/foundry-recipes.md`** — do not create in this task (see judgment call above).
   Flag this deviation from the literal task file list explicitly in the Plan step for
   confirmation before implementation.

## Testing approach (for later Run Tests step)
Mirrors scc-4xa's approach (hand-worked/live-dispatched scenarios, no unit test
framework in this repo for skills):
- AC1: construct a small plan snippet adding a login endpoint, run the skill's
  procedure against it (live Task dispatch or manual walkthrough), confirm TRIGGERED
  lines cite authn/session-family OWASP topic names.
- AC2: construct a pure UI-copy-change plan snippet, confirm all-CLEAR/N/A output with
  the explicit "no security-relevant surface" statement.
- AC3: simulate WebFetch unavailability (or just don't invoke it) and confirm the skill
  still completes using topic names / built-in checklist, with an explicit degraded-mode
  note.

## Risks / open questions
- **docs/foundry-recipes.md scope** (flagged above) — recommend NOT creating it now;
  confirm with Plan step.
- No existing skill in either plugin implements WebFetch-with-graceful-fallback; this
  task originates the pattern, so keep it simple and self-contained rather than
  over-engineering a "network detection" mechanism — the skill should just attempt
  WebFetch and treat failure/unavailability as the trigger for degraded mode, per how
  Claude Code tools already fail (tool call error/absence), no bespoke connectivity
  check needed.
- Keep the new skill decoupled from `review-panel` internals (Invariant 2: dependency
  direction) — it must not import/reference review-panel's MERGE/VALIDATE machinery;
  the only review-panel touchpoint is the one-line documentation offer added to
  `grill-with-docs/SKILL.md`.
