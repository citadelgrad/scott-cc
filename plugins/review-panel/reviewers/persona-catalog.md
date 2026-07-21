# Reviewer Persona Catalog

This is the manifest the `review-panel` orchestrator skill (`skills/review-panel/SKILL.md`)
reads to decide which reviewer seats to cast for a given diff. It is authored from scratch for
this plugin — not vendored — informed by compound-engineering's `/ce:review` casting approach
(LLM judgment against actual diff content, a small always-on core plus risk-triggered additions,
fail-closed on ambiguity, model tiering). See [CREDITS.md](../CREDITS.md) for the inspiration
note; no compound-engineering text or code was copied, since that plugin was never vendored into
this repo.

## Discovery source order (resolves plan decision Q5)

This catalog is the **PRIMARY** casting source. It is a static, curated, version-controlled
manifest of seats this plugin ships and knows how to cast well. The orchestrator reads it first,
every time, regardless of what else is installed.

A **runtime live-scan** of currently-installed skills — `~/.claude/skills` plus any plugin
skills visible in the session (e.g. `compound-engineering`, `superpowers`, a user's personal
skill set) — is the **SECONDARY enrichment layer**. It runs after this catalog and can add extra
seats (e.g. a security-specific skill the user happens to have installed) but never removes or
overrides a seat this catalog says to cast.

This ordering is deliberate, not incidental: upstream skill sources this plugin vendors from
(clairvoyance, ponytail, superpowers) are third-party repos that get updated, renamed, or
uninstalled over time and cannot be relied upon to always be present in a given session. A
catalog entry that names a skill this plugin vendors and ships directly is durable. A live-scan
result is not — it reflects whatever happens to be installed *right now* and may vanish on the
next session. Casting decisions must not silently degrade just because an upstream skill was
uninstalled; the primary/secondary split is what keeps casting reproducible across sessions.

**Practical effect on the orchestrator:**
1. Read this catalog. Determine which seats it says to cast for the diff at hand (see cast-when
   criteria per seat below).
2. Separately, live-scan installed skills for anything not already represented by a seat above —
   e.g. a dedicated security-review skill, a language-specific linter skill, a framework-specific
   reviewer. Add these as supplementary seats.
3. If a catalog seat's target skill (the "Casts" column below) is not actually installed in this
   session, do not silently drop the seat — see "Missing skill handling" below.

## Fail-closed rule

**When casting judgment is ambiguous about whether a risk-triggered seat applies to a given
diff, the default behavior is to INCLUDE the seat, not exclude it.** This is an explicit rule,
not a suggestion or an example: ambiguity resolves to casting, every time. An extra reviewer
seat costs some time and tokens; a skipped seat that should have caught something costs a bug,
a security hole, or a design regression that ships. The cost asymmetry favors over-casting.

This rule applies per-seat, independently. It is never overridden by a desire to keep the panel
small — panel size is a consequence of applying the criteria below, not a target to hit.

## Missing skill handling

Every seat below names a specific skill it casts (the "Casts" column). If that skill is not
installed/available in the current session:

- **Core seats** (`adversarial-reviewer`, `ponytail-review`/`ponytail-audit`, `design-review`,
  `domain-modeling`, `clean-room-alternative`): these ship *with this plugin*, so under normal
  operation they are always available. If one is somehow missing (a broken install), report it
  as a coverage gap in the panel's final output rather than silently skipping — per the plan's
  "coverage honesty" rule (state what was skipped and why).
- **Security seat**: this plugin casts `security-suite`'s `agents/security-engineer.md` directly
  (see the Security row below) — a primary catalog cast, not a live-scan-conditional one. If
  `security-suite:security-engineer` is not present in the current session's available
  Task/Agent-tool agent-type list (the plugin is not installed/enabled this session), the
  orchestrator must still apply baseline security attention via `adversarial-reviewer`'s Scope
  item 2 (security holes) and say explicitly in the report that no dedicated security-specialist
  seat was cast and why — do not silently drop security coverage without comment.
- **Risk-triggered seats whose skill is missing**: same coverage-honesty rule — note the gap,
  don't fail silently.

## Model tiers

- **Top-tier**: seats whose job is adversarial/correctness-critical judgment, where a weaker
  model is more likely to miss a real bug, security hole, or fail to generate a genuinely
  independent perspective. Cast on the strongest available model.
- **Mid-tier**: seats whose job is applying a well-defined, mechanical-ish checklist or lens
  (structural heuristics, naming, simplicity patterns) where the review procedure itself does
  most of the cognitive work and a mid-tier model executing it faithfully is sufficient.

Per the plan's casting philosophy: top-tier for correctness/adversarial, security, and
fresh-eyes/clean-room-alternative seats specifically, because these three are the ones where
independence and adversarial rigor — not just procedure-following — are the point. Mid-tier for
the rest unless a specific seat's entry below explains a deviation.

---

## Core Seats (always cast)

These seats are cast on every panel run, regardless of diff content. They are cheap relative to
the risk of missing what they catch, and each covers a review angle none of the others provide.

### Correctness / Adversarial

- **Casts:** `skills/adversarial-reviewer/SKILL.md`
- **Cast-when:** Always cast. Core seat.
- **Model tier:** Top-tier. This seat's entire value is finding the bug, exploit, or hostile-input
  failure other reviewers miss, and (per its Scope item 4) attacking prior findings for false
  confidence — both require adversarial rigor a weaker model is less reliable at.
- **Notes:** Uses the `clean-room-alternative` blind-subagent isolation pattern internally when
  attacking existing findings, so it does not anchor to a prior reviewer's framing. See its own
  SKILL.md "Independence via clean-room-alternative" section.

### Simplicity

- **Casts:** `skills/ponytail-review/SKILL.md` (diff-scoped) — use `skills/ponytail-audit/SKILL.md`
  instead only when the panel is invoked in whole-repo audit mode rather than against a single
  diff/PR.
- **Cast-when:** Always cast (`ponytail-review`) for diff-scoped panel runs. `ponytail-audit`
  is cast instead of, not in addition to, `ponytail-review` when the target is an entire
  codebase rather than a diff.
- **Model tier:** Mid-tier. The over-engineering checklist (delete/stdlib/native/yagni/shrink
  tags) is a well-defined mechanical lens; it doesn't require adversarial judgment to execute
  well, just careful reading.
- **Notes:** Explicitly out of scope for bugs/security/performance (see its own Boundaries
  section) — this seat's findings are additive to, never a substitute for, the
  Correctness/Adversarial seat.

### Structural

- **Casts:** `skills/design-review/SKILL.md` (the clairvoyance diagnostic-funnel orchestrator)
- **Cast-when:** Always cast. Core seat.
- **Model tier:** Mid-tier. `design-review` is itself a five-phase funnel (complexity triage →
  structural → interface → surface → red-flags sweep) that sequences well-defined lenses; the
  procedure carries the weight, not raw model strength.
- **Notes:** This single seat internally covers `complexity-recognition`, `module-boundaries`,
  `deep-modules`, `abstraction-quality`, `information-hiding`, `general-vs-special`,
  `pull-complexity-down`, `error-design`, `naming-obviousness`, `comments-docs`, and the full
  `red-flags` 17-flag checklist. Casting it as one seat (rather than 11 separate lens seats)
  keeps the panel bounded-parallel per the plan's SPAWN step, while still getting funnel-level
  coverage. Do not additionally cast the individual lenses it subsumes as separate seats — that
  would duplicate work `design-review` already does internally.

### Security

- **Casts:** `security-suite`'s `agents/security-engineer.md`, dispatched via `Task` as agent type
  `security-suite:security-engineer` — the same cross-plugin agent-dispatch pattern this catalog
  already uses for its own Fresh-Eyes seat (`agents/clean-room-alternative.md`, exposed as
  `review-panel:clean-room-alternative`). This is a live cross-plugin reference, not a vendored
  copy: `security-suite` ships alongside `review-panel` in this repo, and no dedicated
  security-review skill is authored inside this plugin.
- **Cast-when (risk-triggered, fail-closed):** diff content touches auth, crypto, secrets
  handling, input validation at a trust boundary, deserialization, dependency manifests/lockfiles,
  IaC, or CI config. Ambiguity resolves to casting, per the catalog's global fail-closed rule
  above. This is decidable from CAST Steps 1-3 content/path matching alone — not a live-scan
  (Step 4)-conditional cast-when — so, like Data Steward below, this seat is forced into SPAWN
  dispatch in every tier, including `--lite`/`--medium` (see the Tier eligibility footnote below).
- **Model tier:** Top-tier. Security review has the same asymmetric-cost profile as adversarial
  review — a missed vulnerability is far more expensive than an extra review pass.
- **Missing-plugin fallback:** if `security-suite:security-engineer` is not present in the current
  session's available Task/Agent-tool agent-type list (i.e. `security-suite` is not
  installed/enabled this session — a concrete, mechanically checkable condition, since CAST's
  dispatch prompt already receives this list per `references/cast-and-spawn.md` Step 4 item 1(b)),
  the seat cannot be cast. The orchestrator must say so explicitly in its report (see "Missing
  skill handling" above) rather than silently treating `adversarial-reviewer`'s Scope item 2 as
  equivalent full coverage.
- **Notes:**
  - **Tool-grant caveat:** `security-engineer.md`'s frontmatter declares no `tools:` restriction
    (unlike `clean-room-alternative.md`'s explicit `Read, Grep, Glob`). Per
    `references/cast-and-spawn.md`'s SPAWN "Read-only tool access" section, the orchestrator
    cannot force this externally-defined agent-type dispatch to read-only from the outside — check
    its actual tool grant (visible in the Task/Agent-tool agent-type listing) and note any
    `Edit`/`Write`/mutating-`Bash` deviation in the coverage-honesty statement rather than
    silently assuming compliance.
  - **Model-pin caveat:** `security-engineer.md` also declares no `model:` field, so this entry's
    "top-tier" designation is a request the dispatching `Task` call should honor if it can pin a
    model for a named agent-type; if it can't, that's a coverage-honesty-worthy deviation too, not
    a blocker.
  - **Output-shape caveat:** `security-engineer.md`'s own `## Outputs` section (Security Audit
    Reports, Threat Models, Compliance Reports, Vulnerability Assessments, Security Guidelines)
    does not natively use this plugin's Critical/Important/Minor + verdict shape. SPAWN's dispatch
    prompt must explicitly instruct this seat to render its findings in
    `contracts/reviewer-output.md`'s structure — the same generic instruction SPAWN already gives
    every seat regardless of source (see "Collect raw output" in `references/cast-and-spawn.md`),
    not a change to `security-engineer.md` itself.
  - `adversarial-reviewer` Scope item 2 (security holes) provides baseline security attention on
    every run even when this seat isn't cast, but it is a general adversarial pass, not a
    specialist security review — don't conflate the two in reporting.
  - **Path-identifiable subset (for cheap, pre-CAST signals):** the auth / crypto / secrets-handling
    / dependency-supply-chain portion of the Cast-when categories above is also usable as a fast,
    path-only proxy — before any diff-content read — by callers that need a cheap sensitive-path
    check ahead of CAST itself (currently: `--auto`'s tier resolver, see
    [lite-mode.md](../skills/review-panel/references/lite-mode.md)'s "Auto resolution" section, which
    cites this list verbatim rather than defining its own copy). This is the single source of truth
    for that path list — do not redefine it elsewhere:
    - **Auth**: path contains `auth/`, `authn/`, `authz/`, `session/`, `oauth/`, `login`, or `jwt`.
    - **Crypto / secrets handling**: path contains `crypto/`, `cipher`, `secrets/`, `credentials/`,
      `.env` (or any `.env.*` variant), or matches `*.pem` / `*.key` / `*.p12` / `*.pfx`, or the
      filename itself contains `secret` or `credential`.
    - **Dependency / supply-chain**: path is a lockfile (`package-lock.json`, `yarn.lock`,
      `pnpm-lock.yaml`, `Cargo.lock`, `Gemfile.lock`, `poetry.lock`, `uv.lock`, `go.sum`,
      `composer.lock`, or any `*.lock`) or a dependency manifest (`package.json`, `Cargo.toml`,
      `pyproject.toml`, `Gemfile`, `go.mod`, `requirements*.txt`).
    - **Not included here** (content-only, not path-identifiable): input validation at a trust
      boundary, and deserialization — these two Cast-when categories require reading diff content,
      not just paths, so no caller should attempt to approximate them via a path list. A cheap
      pre-CAST resolver that omits them is a known, intentional narrowing of `--auto`'s *tier
      selection* signal only, not a coverage gap in the finished run — CAST's Steps 1-3
      content-based judgment still runs identically regardless of tier, and since this seat's
      cast-when is itself Steps-1-3-decidable (not Step-4/live-scan-gated), a diff that trips one
      of these content-only triggers still gets Security cast even in a narrowed tier whose
      `--auto` resolver missed it on the path-only signal — the resolver's blind spot narrows only
      which *tier* gets picked, never whether Security itself is cast once CAST actually runs.

### Domain-Intent

- **Casts:** `skills/domain-modeling/SKILL.md`
- **Cast-when:** Diff touches a type, interface, schema, or entity definition; a validation or
  parsing boundary; or a multi-step business workflow (state machines, approval chains,
  order/checkout-shaped processes). Also cast whenever a project `CONTEXT.md` exists (see
  `formats/CONTEXT-FORMAT.md`) and the diff touches code the CONTEXT.md documents domain
  decisions for — this is the RE-REVIEW step's "coherence-vs-intent" check from the panel loop.
- **Model tier:** Mid-tier. The 8-technique CLEAR/TRIGGERED/N/A checklist
  (`skills/domain-modeling/RED-FLAGS.md`) is procedural; applying it faithfully matters more than
  raw model strength.
- **Notes:** Explicitly FP-only (no opinion on OOP entity/aggregate/repository design) and
  read-only (reports findings, does not refactor). Do not cast for diffs with no type/schema/
  workflow surface — e.g. a pure config or docs change — since it would have nothing to evaluate.

### Fresh-Eyes

- **Casts:** `agents/clean-room-alternative.md` (blind-subagent pattern), dispatched via `Task`
  with the diff/target only — no PR description rationale, no other seats' findings, no design
  doc reasoning included in its prompt.
- **Cast-when:** Always cast. Core seat.
- **Model tier:** Top-tier. Independence is the entire point of this seat — a subagent given the
  same reasoning everyone else has seen just re-derives the same conclusions. This is one of the
  two seats (with Correctness/Adversarial) where the plan calls out top-tier explicitly, since a
  weaker model is more likely to under-explore and converge on an obvious-but-shallow read.
- **Notes:** This is the same isolation mechanism `adversarial-reviewer` reuses internally for
  attacking prior findings, but cast here as its own independent seat producing a first read of
  the diff, not an attack on others' conclusions. If the runtime has no `Task`/subagent support,
  this seat cannot be cast in isolation — report it as skipped per "coverage honesty," don't fake
  independence by running it in the same context as other seats.

---

## Risk-Triggered Seats (cast on diff signal)

These are cast only when diff content signals they're relevant — not on every run. Each entry
states the concrete diff signal that triggers casting. Per the fail-closed rule above, if it's
ambiguous whether the signal is present, cast the seat.

### Change-Trajectory

- **Casts:** `skills/code-evolution/SKILL.md`
- **Cast-when:** The diff modifies existing code (not a from-scratch new file/module) — i.e. any
  diff with non-trivial changed/removed lines against a file that existed before this change.
  This seat asks whether each individual change looks designed-in or bolted-on, which only
  makes sense against a pre-existing design to evolve.
- **Model tier:** Mid-tier. Applies a defined designed-in-vs-bolted-on heuristic per change.
- **Why included:** `design-review`'s funnel evaluates the *current* state of code; it does not
  specifically ask whether *this diff's edits* degraded trajectory relative to what was there
  before. That's a distinct question `code-evolution` is built to answer, and it's cheap to cast
  whenever there's a "before" to compare against.

### Design-Alternatives Check

- **Casts:** `skills/design-it-twice/SKILL.md`
- **Cast-when:** The diff introduces a new class, module, public API, or architectural approach
  from scratch (not a modification of existing structure), AND the PR/diff description or commit
  message gives no indication that alternatives were considered.
- **Model tier:** Mid-tier for the check itself; if it dispatches a `clean-room-alternative`
  subagent internally to generate a real second design, that inner dispatch should use top-tier
  per this catalog's Fresh-Eyes entry.
- **Why included:** Catches "first idea shipped" risk on genuinely new designs — a different
  failure mode than anything else in this catalog reviews for (everything else evaluates a
  design that already exists; this one asks whether the choice to build it *this way* was ever
  actually contested). Not cast for modifications to existing designs — there `code-evolution`
  and `design-review` already cover trajectory and current-state quality.

### Test-Design Quality

- **Casts:** `skills/tdd/SKILL.md`
- **Cast-when:** The diff adds or modifies test files. This seat evaluates the *test design*
  already present in the diff against the skill's Philosophy section (integration-style tests
  through public interfaces vs. implementation-coupled tests that mock internals or verify via
  side channels) — it is a read-only after-the-fact review lens on this axis, distinct from the
  skill's other, process-oriented content (the red-green-refactor workflow, Tracer Bullet step,
  per-cycle checklist), which is written for someone actively writing code test-first and does not
  translate into a post-hoc diff-review check. Only the test-quality judgment applies here.
- **Model tier:** Mid-tier. Applying the good-test/bad-test heuristics from the skill's Philosophy
  section is a well-defined judgment call, not adversarial-grade work.
- **Why included:** No other seat in this catalog specifically evaluates test *design* quality —
  `adversarial-reviewer` may flag a missing test, and `design-review`'s funnel evaluates
  production-code structure, but neither asks whether an added/changed test itself is
  well-designed (behavior-verifying, refactor-resistant) or a liability (coupled to internals,
  will false-positive-fail on the next refactor). Scoped narrowly to diffs that actually touch
  test files, since the seat has nothing to evaluate otherwise.

### Data Steward

- **Casts:** `skills/data-steward/SKILL.md`
- **Cast-when (fail-closed):** the diff touches migration files, ORM/model definitions, schema
  files (`*.sql`, `schema.*`, `prisma/`, `alembic/`, `migrations/`, etc.), serialization formats,
  or any file `DATA-MODEL.md` maps an entity to (see `formats/DATA-MODEL-FORMAT.md`'s "Entities &
  relationships" / "Ownership & routing" sections). Per the catalog's global fail-closed rule,
  ambiguity about whether a file is data-layer resolves to casting. This is decidable from CAST
  Steps 1-3 content/path matching alone, the same property that makes Security's cast-when above
  tier-independent — so this seat, too, is forced into SPAWN dispatch in every tier, including
  `--lite`/`--medium` (see the Tier eligibility footnote below).
- **Model tier:** Top-tier — a deviation from the "mid-tier unless a specific seat's entry explains
  a deviation" default. Justification: migration and schema mistakes are high-blast-radius and
  often irreversible (data loss/corruption, outage-causing locks), the same asymmetric-cost
  judgment that already justifies top-tier for Security/Correctness/Fresh-Eyes above — a weaker
  model is more likely to miss a destructive migration or a subtle Agent-boundary crossing than to
  miss a style nit.
- **Notes:**
  - Read-only, like `domain-modeling` — reports findings, does not edit `DATA-MODEL.md` or the
    diff itself. `DATA-MODEL.md` is a human-owned artifact (see its format doc); this seat may
    recommend edits but never makes them.
  - **Sovereignty marker:** findings may carry an optional `sovereignty: human-required` field (a
    contract extension beyond the standard Critical/Important/Minor shape, documented in
    `skills/data-steward/SKILL.md`'s Output Contract) when the diff crosses a `DATA-MODEL.md` Agent
    boundary entry, or when `DATA-MODEL.md` is absent while the diff changes schema semantics. The
    orchestrator's FIX stage must never auto-resolve a sovereignty-marked finding (see
    `references/fix-and-rereview.md`'s "Sovereignty guard"), and CONVERGE cannot report a clean
    round while one remains unresolved (see `references/converge-and-pipeline.md`'s `escalated`
    status).
  - **Missing-`DATA-MODEL.md` fallback:** the seat still casts on schema/migration diffs even when
    no `DATA-MODEL.md` exists in the repo — its file-pattern triggers don't depend on the file's
    presence. When absent, it emits a sovereignty-marked finding recommending the user run
    `grill-the-schema` to create one, phrased as a documentation pointer (mirroring the Security
    seat's missing-plugin fallback template above), and states explicitly that `grill-the-schema`
    (`skills/grill-the-schema/SKILL.md`) may not be installed in this session rather than silently
    assuming it ran — coverage honesty, same rule as every other seat in this catalog.
  - This seat is a hard prerequisite for Phase 5 (the Foundry-resident triage spine): triage-
    produced migrations must never ship with no data-steward seat and no sovereignty escalation
    path. It does not replace the data-layer guard hook (a separate, interactive-only pre-write
    mechanism, out of this seat's scope) — this seat is the sole mechanism for *unattended*
    sovereignty enforcement, since the hook no-ops in unattended runs.
  - **Path-identifiable subset (for cheap, pre-CAST signals):** the migration/schema portion of the
    Cast-when categories above is also usable as a fast, path-only proxy — before any diff-content
    read — by callers that need a cheap sensitive-path check ahead of CAST itself (currently:
    `--auto`'s tier resolver, see [lite-mode.md](../skills/review-panel/references/lite-mode.md)'s
    "Auto resolution" section, which cites this list verbatim alongside Security's path list above
    rather than defining its own copy). This is the single source of truth for that path list — do
    not redefine it elsewhere:
    - **Migrations/schema**: path is under a `migrations/` or `db/migrations/` directory, or
      matches `schema.sql`, `schema.prisma`, or `*.migration.*`, or is a file `DATA-MODEL.md` maps
      an entity to.
    - **Not included here** (content-only, not path-identifiable): ORM/model definitions and
      serialization-format changes that don't live under a recognizable migration/schema path or
      DATA-MODEL.md mapping — these require reading diff content, not just paths. As with
      Security's path-only proxy above, a cheap pre-CAST resolver that misses one of these narrows
      only `--auto`'s *tier selection* signal, never whether this seat gets cast once CAST's
      Steps 1-3 content matching actually runs.

### Taste

- **Casts:** `skills/taste-review/SKILL.md`
- **Cast-when:** `TASTE.md` exists at the repo root — this catalog's **only file-existence-gated
  seat**, as opposed to every sibling risk-triggered entry above, which triggers on diff-content
  signal (touches auth, touches migrations, adds tests, etc.). There is no diff-signal judgment
  call here and thus no fail-closed ambiguity to resolve: if `TASTE.md` is absent, the seat is
  absent from Cast, full stop — no generic fallback.
- **Model tier:** Mid-tier. Applying a written preference file against a diff is procedural, the
  same rationale the catalog's Mid-tier default already uses generally — contrast this
  explicitly with Data Steward's Top-tier deviation just above: a missed migration mistake risks
  data loss, but a missed taste nit does not carry that blast-radius asymmetry.
- **Notes:**
  - **Severity mapping:** findings are severity-mapped from each `TASTE.md` entry's declared
    `strength` — `absolute`/`strong` → `Important` (an `absolute`-strength finding additionally
    notes `(absolute preference)` inline and sorts first within the Important group, since the
    panel's severity enum is closed to `Critical`/`Important`/`Minor` and this seat does not
    introduce a fourth value), `weak` → `Minor`. Taste findings are **never** `Critical` and
    **never** carry the `sovereignty: human-required` marker — that marker is a `data-steward`-
    only contract extension (see the Data Steward entry above) for a different concern
    (`DATA-MODEL.md` Agent-boundary/schema-semantics risk), not personal taste.
  - **No-`TASTE.md`-means-absent is a missing-artifact case, not a missing-skill case:** this is
    distinct from this catalog's "Missing skill handling" section above, which covers the
    `taste-review` skill file itself being uninstalled (report as a coverage gap, per that
    section's rule). A target repo simply having no `TASTE.md` is a different, expected failure
    mode — the seat is absent from Cast by design, and both this seat and Phase 4's variant
    scoring must report that gap explicitly per Coverage Honesty rather than silently omitting
    the taste axis (see `formats/TASTE-FORMAT.md`'s "Malformed or missing TASTE.md").
  - **Malformed-entry handling:** a `TASTE.md` Preference missing a required field (most commonly
    `strength`) does not block the seat from casting or from reviewing its other, valid entries —
    the malformed entry is reported as unusable in Coverage Honesty rather than guessed at (see
    `skills/taste-review/SKILL.md`'s Output Contract).
  - **Read-only**, like `domain-modeling` and `data-steward` — reports findings, does not edit
    `TASTE.md` itself. `TASTE.md` is a human-owned artifact, built only through `grill-my-taste`
    grilling sessions (Invariant 5); this seat may cite it but never modifies it.
  - This seat's severity mapping is Phase 4's (`scc-5hy`, variant-explorer) scoring function per
    the epic's stated build order ("Phase 4 blocked on Phase 3 — taste is the scoring function");
    wiring the two together is out of this seat's own scope.

---

## Excluded from Individual Casting (left to `design-review` funnel or live-scan)

These clairvoyance lenses exist as vendored skills in this plugin but are **not** given their own
catalog entry, on the judgment that giving each one an independent seat would either duplicate
`design-review`'s funnel or doesn't fit the diff-triggered casting shape this catalog uses:

- **`complexity-recognition`, `module-boundaries`, `deep-modules`, `abstraction-quality`,
  `information-hiding`, `general-vs-special`, `pull-complexity-down`, `error-design`,
  `naming-obviousness`, `comments-docs`, `red-flags`** — all internally sequenced by
  `skills/design-review/SKILL.md`'s five-phase diagnostic funnel (see the Structural seat above).
  Casting them again as standalone seats would run the same checks twice under two different
  seats and inflate the panel without adding coverage.
- **`diagnose`** — a symptom-routing decision tree for a human who doesn't know which lens to
  reach for. It has no findings output of its own to contribute to a panel; it's a router, not a
  reviewer. Not seat-shaped.
- **`strategic-mindset`** — evaluates codebase-wide design investment trends (the 10-20%
  investment rule, tactical-tornado patterns) over time, not a single diff in isolation. This is
  better suited to a periodic whole-codebase audit (alongside `ponytail-audit`) than a per-PR
  panel seat, since a single diff rarely has enough signal to assess a *trend*. If the
  orchestrator later grows an audit mode, revisit adding this as an audit-mode seat.
- **`grill-with-docs`** — a Socratic, interactive dialogue tool: it walks a human through a
  design/onboarding conversation, asking clarifying questions and updating `CONTEXT.md`/ADRs live
  as the human answers. It has no diff-scoped findings-producing mode; its entire value is the
  back-and-forth with a person. Not seat-shaped for an autonomous panel run. `domain-modeling`'s
  `CONTEXT-AND-ADR.md` mechanism (see the Domain-Intent seat above) already gives the panel its own
  non-interactive path to the same `CONTEXT.md`/ADR artifacts this skill produces conversationally.
- **`improve-codebase-architecture`** — also fundamentally conversational: it identifies
  deepening/refactor *candidates* and then requires a human to pick one and "drop into a grilling
  conversation" before any side effect (a `CONTEXT.md` update or ADR) happens. Like
  `grill-with-docs`, it has no autonomous, diff-scoped findings output a panel seat could consume;
  the user's live selection between candidates is load-bearing to its design, not an implementation
  detail that could be stubbed out for an unattended panel run.

If any of these are separately installed and updated upstream (e.g. a user's live-scan finds a
newer or differently-scoped version), the live-scan secondary-enrichment layer may still surface
them — this catalog only governs the *primary* always-available seat roster, not what live-scan
is allowed to add.

---

## Seat Summary Table

| Seat | Casts | Cast-when | Model tier |
|---|---|---|---|
| Correctness/Adversarial | `adversarial-reviewer` | Always | Top-tier |
| Simplicity | `ponytail-review` (diff) / `ponytail-audit` (repo) | Always | Mid-tier |
| Structural | `design-review` | Always | Mid-tier |
| Security | `security-suite:security-engineer` | Diff touches auth/crypto/secrets/input-validation/deserialization/dependency-manifests/IaC/CI-config | Top-tier |
| Domain-Intent | `domain-modeling` | Diff touches types/schemas/validation/workflows or CONTEXT.md-documented domain code | Mid-tier |
| Fresh-Eyes | `clean-room-alternative` | Always | Top-tier |
| Change-Trajectory | `code-evolution` | Diff modifies pre-existing code | Mid-tier |
| Design-Alternatives | `design-it-twice` | New class/module/API/architecture with no alternatives-considered evidence | Mid-tier (top-tier for its internal fresh-design dispatch) |
| Test-Design Quality | `tdd` (Philosophy section only) | Diff adds or modifies test files | Mid-tier |
| Data Steward | `data-steward` | Diff touches migrations/ORM/schema/serialization files or a DATA-MODEL.md-mapped path | Top-tier |
| Taste | `taste-review` | `TASTE.md` exists at repo root | Mid-tier |

**Fail-closed reminder:** any ambiguity in the "Cast-when" column above resolves to casting the
seat, not skipping it.

**Tier eligibility** (which of the seats above `--lite`/`--medium` dispatch — see
[lite-mode.md](../skills/review-panel/references/lite-mode.md); this catalog's cast-when criteria
above are unmodified in every tier, only which of CAST's output seats SPAWN actually dispatches
narrows): Correctness/Adversarial — always, all tiers. Simplicity, Structural — medium and full
only. Any fail-closed-forced seat whose cast-when is decidable from CAST Steps 1-3 alone (content/
path judgment against a known, vendored or cross-plugin target skill, with no dependency on Step
4/live-scan) — fail-closed, all tiers, identically to full mode: a cast-when match forces the seat
in regardless of the active tier. **Security and Data Steward are both this kind of seat** — their
cast-when entries above are content/path matches CAST resolves in Steps 1-3, not a live-scan
(Step 4) discovery, so a cast-when match under `--lite`/`--medium` forces either in exactly as it
would in full mode; neither is skipped or downgraded to disclosure-only under a narrowed tier. All
other seats (Domain-Intent, Fresh-Eyes, Change-Trajectory, Design-Alternatives, Test-Design
Quality) — full-mode only.
