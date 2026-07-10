# CAST and SPAWN

The first two stages of the panel loop. CAST decides who's on the panel; SPAWN runs them.

---

## CAST

**Goal:** produce a concrete list of reviewer seats to dispatch, each seat mapped to the specific
skill it casts (per `reviewers/persona-catalog.md`) and a model tier, before any subagent is
spawned.

### Step 1 — Read the catalog

Read `reviewers/persona-catalog.md` in full (it is short enough to read whole; do not skim). It
defines:
- **Core seats** (Correctness/Adversarial, Simplicity, Structural, Security-conditional,
  Domain-Intent, Fresh-Eyes) — cast on every run per their individual cast-when criteria.
- **Risk-triggered seats** (Change-Trajectory, Design-Alternatives Check) — cast only when diff
  content signals relevance.
- A **fail-closed rule**: when it's ambiguous whether a risk-triggered seat's cast-when criteria
  are met, INCLUDE it. This is not a suggestion — apply it every time ambiguity arises, per-seat,
  independently. Panel size is a consequence of applying the criteria, never a target to trim to.
- **Model tiers** per seat (top-tier: Correctness/Adversarial, Security, Fresh-Eyes; mid-tier:
  everything else unless a seat's own catalog entry says otherwise).

### Step 2 — Judgment-match against diff CONTENT, not paths

For each seat in the catalog, decide cast/skip by actually reading what the diff changed, not by
pattern-matching file extensions or directory names. Concretely:

- Read the packaged diff (from the Setup step in SKILL.md) in full before making any casting
  decision — casting is a judgment call informed by what the change actually does, not a
  keyword/regex sweep over file paths.
- **Domain-Intent example done right:** a diff that touches `types.ts` is not automatically cast
  for Domain-Intent — read whether it actually defines or modifies a type/interface/schema/entity,
  a validation/parsing boundary, or a multi-step workflow. A diff to `types.ts` that only fixes a
  typo in a comment does not meet the cast-when bar; a diff to a file named `helpers.ts` that
  introduces a new tagged-union state machine does.
- **Change-Trajectory example done right:** don't cast just because the diff "modifies a file
  that already exists" as a path-level fact — confirm the diff actually contains non-trivial
  changed/removed lines against pre-existing logic (per its cast-when criteria), not e.g. a
  new file added alongside an unrelated one-line touch to an existing file's import list.
- **Security example done right:** the trigger list (auth, crypto, secrets handling, input
  validation at a trust boundary, deserialization, dependency/supply-chain changes) is a content
  question — read whether the diff's logic actually crosses one of those boundaries, not whether
  a file path contains the word "auth."
- When a diff is large enough that reading it in full before casting is impractical, read the
  full stat summary (file list + line counts from the packaged diff) plus the actual diff hunks
  for every file whose stat suggests non-trivial logic change (exclude only clearly-mechanical
  hunks: lockfiles, generated code, pure formatting). Note in the coverage-honesty statement if
  any file's diff was assessed by stat summary alone rather than full hunk content.

### Step 3 — Apply the fail-closed rule

For every risk-triggered seat where Step 2 leaves genuine ambiguity (not "I didn't bother
checking," but "I read the diff and a reasonable reviewer could argue either way"), cast the
seat. Document the ambiguity in one sentence in the panel's internal casting log so MERGE/CONVERGE
can see why a seat with a marginal signal was included.

### Step 4 — Live-scan secondary enrichment

After Step 3 produces the primary cast list from the catalog, run a secondary enrichment pass:

1. Enumerate skills visible in the current session beyond what's vendored in this plugin —
   `~/.claude/skills` (user-level personal skills) and any installed plugin's skills, notably
   `compound-engineering` (per plan decision Q8, it stays installed and its ~15 review personas
   are cast at runtime, never vendored into this plugin). **Concretely, `compound-engineering`'s
   review personas are not exposed as `skills/*/SKILL.md` files — they live under `agents/review/`
   (e.g. `architecture-strategist.md`, `security-sentinel.md`, `code-simplicity-reviewer.md`) and
   are surfaced to the orchestrator as dispatchable agent types named
   `compound-engineering:review:<persona>` (visible in the session's available Task/Agent-tool
   agent-type list, not by directory-listing a `skills/` folder).** So this enumeration step must
   cover two distinct sources, not one: (a) skill directories under `~/.claude/skills` and any
   plugin's `skills/` tree, matched by reading each `SKILL.md`'s description; and (b) agent types
   available via the `Task`/Agent tool whose name is namespaced `<plugin>:review:*` or otherwise
   self-describes as a review persona, matched by reading their one-line description the same way.
   A live-scan that only walks `skills/` directories will silently miss (b) and undercount
   compound-engineering's actual review-persona roster.
2. For each skill found that is NOT already represented by a catalog seat (check the catalog's
   "Excluded from Individual Casting" section too — those clairvoyance lenses are intentionally
   subsumed by `design-review` and must not be double-cast even if live-scan finds them
   installed standalone), judge whether its stated purpose applies to this diff using the same
   content-based judgment as Step 2.
3. Add matching skills (or matching agent types, per item 1's two-source enumeration) as
   supplementary seats. Common finds: a security-specific skill (resolves the catalog's Security
   seat when none is vendored — see catalog "Missing skill handling"), a language-specific
   linter/reviewer skill, a framework-specific reviewer, or one of compound-engineering's
   `agents/review/*` personas offering a review angle no catalog seat covers (e.g.
   `architecture-strategist` for structural review of a new architectural pattern, or
   `security-sentinel` for the Security seat). A supplementary seat's Step 6 "target skill path"
   is either a skill file path or, for an agent-type find, the dispatchable agent-type name itself
   (e.g. `compound-engineering:review:security-sentinel`) — SPAWN dispatches it via `Task` using
   that name directly, the same as any other seat.
4. Live-scan results are strictly additive — they never remove or override a catalog-cast seat,
   per the catalog's discovery-source-order rule (catalog is primary and durable; live-scan is
   secondary enrichment that can vanish if the user uninstalls something next session).
5. If live-scan finds nothing beyond the catalog roster, that's a normal, expected outcome — don't
   manufacture a supplementary seat to look thorough.

**Verified (scc-ns8.11, manual check, 2026-07-10):** confirmed by direct filesystem inspection
that `compound-engineering` was installed on the machine this plugin was authored on (present
under `~/.claude/plugins/marketplaces/every-marketplace/plugins/compound-engineering/`, with a
matching entry in `~/.claude/plugins/cache/every-marketplace/compound-engineering/`). Its ~15
review personas — `agent-native-reviewer`, `architecture-strategist`, `code-simplicity-reviewer`,
`data-integrity-guardian`, `data-migration-expert`, `deployment-verification-agent`,
`dhh-rails-reviewer`, `julik-frontend-races-reviewer`, `kieran-python-reviewer`,
`kieran-rails-reviewer`, `kieran-typescript-reviewer`, `pattern-recognition-specialist`,
`performance-oracle`, `schema-drift-detector`, `security-sentinel` — live under that plugin's
`agents/review/*.md`, **not** under its `skills/` tree, and are surfaced to the host session as
dispatchable `compound-engineering:review:<persona>` agent types (independently confirmed: this
exact session's own available-agent-types list included all of the above under that naming
scheme). The originally-drafted item 1 said "enumerate skills," which — read literally — would
have walked `skills/` directories only and silently missed all ~15 of these, since
compound-engineering's `skills/` tree holds unrelated skills (e.g. `document-review`,
`agent-native-architecture`) rather than the review personas themselves. Item 1 and item 3 above
were amended (this task, scc-ns8.11) to explicitly enumerate agent types as a second source
alongside skill directories, closing that gap. With the amendment applied, the live-scan procedure
as now written **does** concretely surface compound-engineering's personas: e.g.
`security-sentinel` would be judged against the catalog's Security seat (resolving "Missing skill
handling" when the diff trips a security signal), and `architecture-strategist` would be judged as
a supplementary seat for diffs with structural/architectural content the catalog's Structural seat
description doesn't already fully cover. This was a manual, one-time verification on the
machine/session available at authoring time, not an automated test — a live-scan on a different
machine without compound-engineering installed will correctly find nothing from that source (see
item 5).

### Step 5 — Missing-skill handling

If a catalog seat's target skill is not actually installed in this session (a broken/partial
install, not merely "no live-scan match" — see Step 4, which is about finding *extra* skills, not
verifying core ones exist):
- **Core seats** (they ship with this plugin, so this should be rare): report the gap in the
  coverage-honesty statement rather than silently dropping the seat.
- **Security seat**: if no security skill is found via live-scan AND the diff trips a
  security-relevant signal (per the catalog's Security cast-when list), state explicitly in the
  report that no dedicated security seat was cast, and that baseline coverage falls to
  `adversarial-reviewer`'s Scope item 2 only — do not present that as equivalent full coverage.

### Step 6 — Emit the cast list

Produce a concrete list: `{seat name, target skill path, model tier, one-line cast rationale}`
for every seat that will be dispatched. This list is SPAWN's input and MERGE's provenance record
(which seat produced which finding).

---

## SPAWN

**Goal:** dispatch every cast seat concurrently against the ONE shared packaged diff, bounded by a
concrete concurrency cap, with read-only tool access.

### Shared diff, not per-seat re-derivation

Every seat's dispatch prompt includes the SAME packaged diff artifact (the file `review-package`
wrote in Setup, or the in-conversation fallback diff) — pass its content or path directly. Do not
let any seat run its own `git diff` against possibly-different refs; that would let seats silently
review different code and break MERGE's ability to correlate findings by file:line against one
ground truth.

### Bounded-parallel, not unbounded

Dispatch seats via the `Task` tool in batches of **at most 5 concurrent subagents per batch**.
Justification: this plugin has no runtime control over the host session's actual subagent
concurrency ceiling (it varies by Claude Code version/configuration), and unbounded fan-out risks
silent throttling or dropped dispatches that would corrupt the panel's provenance (a seat that
never ran but isn't reported as skipped). 5 is a conservative bound comfortably under typical
observed concurrent-subagent limits, while still getting real wall-clock benefit over serial
dispatch — a typical panel (6 core + 0-2 risk-triggered + 0-1 live-scan supplementary seats) fits
in one or two batches. If a specific runtime is known to support higher bounded concurrency
reliably, that's an acceptable deviation; document the chosen bound and why in the coverage-honesty
statement if it differs from 5.

Within a batch, all seats run concurrently. Across batches, run sequentially (batch 2 does not
start until batch 1's dispatches have returned or been confirmed failed).

### Read-only tool access

Every seat subagent gets read-only tools only: `Read`, `Grep`, `Glob`, and — for seats whose own
SKILL.md specifies it (e.g. `adversarial-reviewer`'s internal `clean-room-alternative` dispatch,
`design-it-twice`'s alternative-design generation) — `Task`, so a seat can itself dispatch a
nested clean-room subagent for its own independence needs. No seat gets `Edit`, `Write`, or `Bash`
with mutation capability during SPAWN — findings are gathered here, fixes happen later in FIX,
under a single fixer with full context, not scattered across N seats each making uncoordinated
edits.

### Fresh-Eyes seat specifics

The Fresh-Eyes seat (`agents/clean-room-alternative.md`, adapted here as a first-read seat rather
than an attack-existing-findings seat) must be dispatched via `Task` with ONLY the packaged diff
and read access to the codebase — no PR description rationale, no other seats' findings, no
design-doc reasoning in its prompt. If this session's runtime has no `Task`/subagent support,
Fresh-Eyes cannot be cast in isolation; report it as skipped in the coverage-honesty statement
rather than faking independence by running it in shared context with other seats (this mirrors
`adversarial-reviewer`'s own documented fallback for the same constraint).

### Pipeline-not-barrier applies here too

SPAWN does not wait for every seat to finish before MERGE can begin working on the seats that
have already returned. See
[references/converge-and-pipeline.md](converge-and-pipeline.md) for the full pipeline-not-barrier
mechanism — the short version: a seat that returns "no findings" should be marked done and free
MERGE to start consuming other seats' results immediately, not held until the slowest seat in the
batch also returns.

### Collect raw output

Each seat returns its findings in the shared `contracts/reviewer-output.md` structure (Strengths /
Issues: Critical, Important, Minor with file:line / Recommendations / Assessment). Collect all
seats' raw output, tagged with which seat produced it, as MERGE's input. A seat that errors out
(subagent failure, tool denial, timeout) is recorded as a coverage gap, not silently dropped.
