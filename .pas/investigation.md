# Investigation: scc-4xa — Security seat in the review panel

## Task
Rewrite the Security seat entry in `plugins/review-panel/reviewers/persona-catalog.md` to cast
`security-suite`'s existing `security-engineer` agent directly, closing the documented gap
("no security-specific skill is vendored... conditional on live-scan") since that agent already
exists in this repo.

## Files to modify

1. **`plugins/review-panel/reviewers/persona-catalog.md`** — primary target. Three separate spots
   currently describe the "no security skill exists, conditional on live-scan" state and must all
   be rewritten consistently (leaving any one stale reproduces the exact bug this task fixes):
   - The `### Security (conditional)` entry (lines 132–149)
   - The "Security seat" bullet under `## Missing skill handling` (lines 61–66) — duplicates/
     restates the same now-stale claim ("no security-specific skill is vendored... conditional on
     live-scan enrichment finding a security skill installed")
   - The Seat Summary Table's Security row (line 286)
2. **`plugins/security-suite/agents/security-engineer.md`** — investigated, **no edit needed** (see
   "Output conformance" below for reasoning).
3. **New test fixture** under `plugins/review-panel/tests/fixtures/` — needed to satisfy AC4 (a
   seeded vulnerable-diff fixture producing a validated MERGE finding), following the
   `tests/PRESSURE-TEST.md` pattern. None exists yet; `tests/fixtures/order-fulfillment/` is the
   only fixture in the repo today and doesn't touch security-relevant surface.

## Current behavior

`persona-catalog.md`'s Security entry says no security skill is vendored (true, still) and makes
casting **conditional on the live-scan secondary-enrichment layer** finding *some* security skill
installed at runtime — i.e., if a user happens to have a security skill installed, live-scan
surfaces it; otherwise the seat silently reduces to `adversarial-reviewer`'s Scope item 2 plus a
required coverage-gap note. This is stale: `plugins/security-suite/agents/security-engineer.md`
already ships in this repo, is diff-shaped (OWASP/CWE vulnerability assessment, threat modeling,
compliance), and doesn't need live-scan discovery — it can be a **primary catalog cast**, the same
tier as Fresh-Eyes casting `agents/clean-room-alternative.md`.

**Key precedent confirmed:** review-panel's own Fresh-Eyes seat already casts an *agent* (not a
skill) — `agents/clean-room-alternative.md` — via `Task`. In this very session's available
agent-type list it's exposed as `review-panel:clean-room-alternative` (flat `<plugin>:<agent-name>`
namespacing, no subdirectory segment, since the file lives directly under `agents/`, unlike
compound-engineering's `agents/review/*.md` which namespaces as `<plugin>:review:<persona>`).
`security-suite/agents/security-engineer.md` lives directly under `agents/` the same way, so by the
identical convention it is dispatchable as **`security-suite:security-engineer`**. This is the
concrete "target" value the rewritten catalog entry should name.

`security-engineer.md` itself (frontmatter: `name`, `description`, `category` — no `tools:` or
`model:` field) has **no declared tool restriction**, unlike `clean-room-alternative.md` (which
declares `tools: Read, Grep, Glob`, `model: opus`). This means:
- Its tool grant is whatever the runtime defaults an undeclared agent to, which may be broader than
  read-only. Per `cast-and-spawn.md`'s existing SPAWN rule ("Read-only tool access" section, ~line
  240), the orchestrator cannot force read-only from the outside for an externally-defined
  agent-type dispatch — it must check the actual grant and note any `Edit`/`Write`/mutating `Bash`
  deviation in the coverage-honesty statement, exactly as already documented for
  `compound-engineering:review:<persona>` finds. This applies unchanged to `security-suite:
  security-engineer` and is already covered by existing cast-and-spawn.md text — no new rule
  needed, just something the catalog entry's Notes should point at rather than silently assume away.
- No `model:` field means the catalog's "top-tier" designation is a *request* the SPAWN dispatch
  should honor if the `Task` call can pin a model for a named agent-type; if it can't, that's a
  coverage-honesty-worthy deviation too. Worth one sentence in the catalog entry's Notes; not a
  blocker.

## Required changes to `persona-catalog.md`

### 1. Rewrite the `### Security` entry (currently `### Security (conditional)`)

Replace with something structurally parallel to the Fresh-Eyes entry:

- **Casts:** `security-suite`'s `agents/security-engineer.md`, dispatched via `Task` as agent type
  `security-suite:security-engineer` — the same cross-plugin agent-dispatch pattern this catalog
  already uses for its own Fresh-Eyes seat (`agents/clean-room-alternative.md`, exposed as
  `review-panel:clean-room-alternative`). No vendoring: this is a live cross-plugin reference, not
  a copy, since `security-suite` ships alongside `review-panel` in this same repo/marketplace.
- **Cast-when (risk-triggered, fail-closed):** diff touches auth, crypto, secrets handling, input
  validation at a trust boundary, deserialization, dependency manifests/lockfiles, IaC, or CI
  config. Ambiguity → cast, per the catalog's global fail-closed rule. (Note: this list is a
  superset of the old cast-when trigger list — it adds IaC/CI config explicitly per the task's
  design notes.)
- **Model tier:** Top-tier (unchanged).
- **Missing-plugin fallback:** if `security-suite` is not installed in this session, keep the
  current fallback behavior verbatim — apply baseline security attention via
  `adversarial-reviewer`'s Scope item 2, and state explicitly in the report (Coverage Honesty
  section / `coverage` JSON object) that no dedicated security seat was cast and why. This is a
  plugin-installed check now, not a live-scan-miss check — different failure condition, same
  fallback text and same "never silently drop" rule.
- **Notes:** (a) tool-grant caveat above (check actual grant; note deviation if not read-only); (b)
  output-shape caveat (see below); (c) `adversarial-reviewer` Scope item 2 still provides baseline
  coverage on every run regardless — don't conflate that with this specialist seat.

### 2. Rewrite the "Security seat" bullet under `## Missing skill handling`

Currently says the seat "is conditional on live-scan enrichment finding a security skill
installed." Must be updated to match the new primary-cast behavior: cast directly when
`security-suite` is installed and cast-when criteria are met; the *only* remaining fallback
condition is `security-suite` itself being absent, not "live-scan found nothing." Leaving this
bullet as-is after rewriting the main entry would reintroduce exactly the kind of
already-fixed-but-still-documented-as-broken inconsistency this task exists to close, just in a
second location in the same file.

### 3. Update the Seat Summary Table row

Current: `| Security | *(none vendored — live-scan conditional)* | Diff touches auth/crypto/
secrets/input-validation/deserialization/deps, AND live-scan finds a security skill | Top-tier |`

New `Casts` column: `security-suite:security-engineer`. New `Cast-when` column: drop the "AND
live-scan finds a security skill" clause (no longer applicable — it's a primary cast now); keep
the trigger list, add IaC/CI config.

### 4. Docs-only diff (AC3)

No catalog change needed for this — it already works correctly once cast-when is content-based:
a docs-only diff trips none of the trigger conditions, so CAST (per `cast-and-spawn.md` Step 2)
correctly skips it. Confirmed by re-reading Step 2's existing judgment-match logic; nothing
security-specific needs to change there.

## Output conformance — why `security-engineer.md` likely does NOT need editing

`security-engineer.md`'s own `## Outputs` section (Security Audit Reports, Threat Models,
Compliance Reports, Vulnerability Assessments, Security Guidelines) does not natively use the
Critical/Important/Minor + verdict shape. However, `cast-and-spawn.md`'s SPAWN "Collect raw output"
step already states generically, for *every* seat regardless of source: "Each seat returns its
findings in the shared `contracts/reviewer-output.md` structure... Collect all seats' raw output."
This is necessarily true today for every live-scan-found foreign agent-type seat too (e.g. a
hypothetical `compound-engineering:review:security-sentinel` cast) — none of those foreign files are
owned/editable by this plugin either, yet the mechanism is presumed to already work by imposing the
output-shape instruction **in the SPAWN dispatch prompt**, not by requiring the target file itself
to natively emit that shape. So: the correct fix is a one-line Note in the catalog's Security entry
telling SPAWN's dispatch prompt to explicitly instruct this seat to render its findings in
`contracts/reviewer-output.md`'s shape (since, unlike `adversarial-reviewer`/`domain-modeling`,
this agent's own file doesn't self-declare that contract) — not an edit to `security-engineer.md`
itself. Editing a foreign plugin's file to reference review-panel's contract would also create
needless two-way coupling between plugins that are supposed to combine only via the documented
cross-plugin-reference/live-scan mechanisms, not by each plugin knowing about the other's internal
formats.

**Risk / open judgment call:** if whoever reviews this disagrees and wants belt-and-suspenders
robustness, a minimal alternative is a single added sentence in `security-engineer.md`'s Outputs
section noting it may be asked to conform to a caller-specified output contract — this is a small,
defensible addition but not strictly required. Flagging rather than deciding unilaterally, since
the task file explicitly says "Possibly" for this file.

## AC4 — fixture requirement (new work, not just doc edits)

AC4 requires "at least one seeded vulnerable-diff fixture produces a validated security finding in
MERGE, with fingerprints and confidence anchors." No security fixture exists yet. Following
`tests/PRESSURE-TEST.md`'s exact methodology (live `Task` dispatch of the cast seat against a
seeded-bug fixture, then hand-worked MERGE table with fingerprint + confidence anchor, explicitly
labeling live vs. worked-by-hand sections), this task needs:
1. A new fixture directory (e.g. `tests/fixtures/<name>/`) with a `before`/`after`/`diff.patch` set
   seeding a real vulnerability that trips the Security cast-when list — a dependency lockfile bump
   pulling a known-vulnerable version, or an auth/crypto code change (e.g. a removed signature
   check, a hardcoded secret, an unparameterized query) is the cleanest choice matching AC1's own
   "dependency lockfile diff" scenario.
2. A live `Task` dispatch of `security-suite:security-engineer` against that fixture (mirroring
   PRESSURE-TEST.md's Section 3 live dispatch), demonstrating it produces a Critical/Important
   finding.
3. A hand-worked MERGE table (fingerprint match, confidence anchor) per
   `references/merge-and-validate.md`'s existing methodology, appended either to
   `tests/PRESSURE-TEST.md` or a new companion doc.
4. Optionally, a walked-through AC1/AC2 scenario pair (with vs. without `security-suite` installed)
   in the same style as PRESSURE-TEST.md Section 5's coverage-honesty walkthrough, since AC1/AC2 are
   about the Cast/Coverage-Honesty *sections* of the report, not just the finding itself.

## Risks / dependencies

- **Cross-plugin dispatch mechanics are unverified beyond the compound-engineering precedent.**
  Everything above assumes `security-suite:security-engineer` dispatches identically to how
  `review-panel:clean-room-alternative` and `compound-engineering:review:<persona>` already do in
  this session (confirmed via the live agent-type list). This should hold, but the AC4 fixture work
  is exactly what empirically confirms it rather than assuming it.
- **This is a hard blocker for Phase 5** (scc-tsa) per the epic's build order — triage feeds
  dependency/IaC diffs into review-panel, and those are precisely the diff shapes this Security
  seat's cast-when list targets. Getting the cast-when list right (deps/lockfiles/IaC/CI, not just
  auth/crypto/secrets) matters more here than it would in isolation.
- **Scope boundary respected:** no changes needed to `cast-and-spawn.md`, `dual-mode-contract.md`,
  or `merge-and-validate.md` — their existing generic mechanisms (agent-type dispatch, tool-grant
  checking, output-shape collection) already cover this seat without modification. Confirmed by
  reading all three; flagging here so implementation doesn't over-scope into editing them.
