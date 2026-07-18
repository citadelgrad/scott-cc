# Investigation: scc-cnx (Phase 3a — TASTE.md format)

## Task

Create `plugins/review-panel/formats/TASTE-FORMAT.md`, the format specification for a
new human-owned artifact, `TASTE.md`. This is a pure documentation deliverable (like
Phase 2a's `DATA-MODEL-FORMAT.md`) — no code, no hooks, no skill logic. It only defines
the shape that Phase 3b (`grill-my-taste`), 3c (feedback loop / `--distill`), and 3d
(taste review seat) will read and write.

## Files to create

- `plugins/review-panel/formats/TASTE-FORMAT.md` — new file, the only deliverable.

No existing files need to change. `TASTE.md` itself is not created by this task — per
Invariant 5 and the pattern already established for `DATA-MODEL.md`, the artifact is
only ever produced through a human grilling session (Phase 3b), never scaffolded by an
agent ahead of time.

## Current behavior / precedent

`plugins/review-panel/formats/` currently has three format specs, all following the
same shape: short intro paragraph(s), a fenced `## Structure` template block, a
`## Rules` section explaining *why* each field/section exists, and closing sections for
cross-references and lazy-creation guidance.

- **`DATA-MODEL-FORMAT.md`** (Phase 2a) is the closest precedent — same "human-owned
  artifact fed by a grilling session" pattern that 3a/3b will mirror for taste. Notable
  conventions worth reusing:
  - Opening HTML comment marking the file as the canonical/single source of truth (not
    forked elsewhere).
  - `## Structure` gives one concrete worked example in a fenced `md` block, not an
    abstract schema.
  - `## Rules` restates each required field as an imperative, tied to *why* it matters
    and *which downstream consumer* reads it (e.g. "the data-layer guard hook checks for
    a current-work entry").
  - A `## Relationship to CONTEXT.md` section exists specifically to disambiguate two
    documents with overlapping subject matter but different scope — directly analogous
    to what's needed here for TASTE.md vs. Ousterhout-lens/Karpathy-guidelines universal
    quality.
  - Closing `## Lazy creation` section: don't scaffold the file until there's a real
    decision to record.
- **`ADR-FORMAT.md`** shows the "when to invoke this vs. not" three-part-gate pattern —
  useful precedent for how TASTE-FORMAT.md should gate what counts as a "preference"
  worth recording vs. noise.
- **`plugins/review-panel/skills/grill-the-schema/SKILL.md`** (Phase 2b, the skill that
  *consumes* DATA-MODEL-FORMAT.md) confirms the downstream contract: it links to the
  format file, updates the artifact inline as decisions crystallize, includes a dated
  Change-log-style entry per resolved decision, and explicitly states the artifact is
  human-owned and FIX never auto-modifies it. Phase 3b (`grill-my-taste`, not yet built)
  will do the equivalent for TASTE.md — this task must produce a format spec that
  supports that same inline-update, human-owned workflow.

No existing `TASTE.md` file or `TASTE-FORMAT.md` reference exists anywhere in the repo
yet (confirmed via grep) — this is a clean creation, not a migration or rewrite.

## Required changes (from task file + two-system-spec.md §3a, lines 231-241)

The spec and `.pas/current_task.md` agree exactly on required content.
`TASTE-FORMAT.md` must define:

1. **Preferences** — each entry needs four fields:
   - `rule` — the actual preference statement
   - `rationale` — why
   - `strength` — enum: `weak | strong | absolute`
   - `provenance` — which choice or override produced it (traceable back to a
     grill-my-taste forced-choice session or a captured override, per 3b/3c)
2. **Weightings** — personal calibrations of *universal* principles, not new
   principles. Spec's own example: "locality beats DRY." These are relative-priority
   statements between two things that are each independently legitimate elsewhere, not
   a preference in the Preferences-list sense.
3. **Anti-preferences** — patterns to flag even when individually defensible (i.e.,
   things that are locally fine per Ousterhout/Karpathy but that this particular human
   still wants flagged).
4. **Candidate rules** — a staging area for overrides captured by the Phase 3c feedback
   loop, awaiting a `--distill` pass (3c) to promote/merge/reject each one. This section
   must be structurally distinct from the confirmed Preferences list so 3c's acceptance
   criterion ("ends with zero remaining candidates") is checkable — i.e. "Candidate
   rules empty" must be a well-defined, greppable state.
5. **Scope note** (required *in the format itself*, not just in this investigation):
   universal quality does NOT belong in TASTE.md — that's the Ousterhout lens set (the
   local skills grounded in *A Philosophy of Software Design*: `deep-modules`,
   `complexity-recognition`, `naming-obviousness`, `general-vs-special`,
   `strategic-mindset`, `code-evolution`, `comments-docs`, etc. — confirmed via grep,
   all cite Ousterhout directly) and `skills/karpathy-guidelines/SKILL.md`. Only
   *personal, contested* preference belongs here.

## Downstream consumers (why the field set is load-bearing, not decorative)

- **3b (`grill-my-taste`)** must be able to write a conforming entry after each forced
  choice — the AC requires ≥5 forced choices → TASTE.md where *every* preference has all
  four fields. The format's field names/order need to be unambiguous enough that a skill
  description (not custom code) can reliably produce them.
- **3c (feedback loop / `--distill`)** reads Candidate rules and needs a clear
  promote/merge/reject action model — the format should make each candidate entry
  self-contained enough to evaluate independently (own rationale/provenance, not just a
  bare rule string), since `--distill` "walks Candidate rules, promotes/merges/rejects
  each."
- **3d (taste seat)** cites "the specific TASTE.md clause" and maps strength → severity
  (`absolute → Important+, strong → Important, weak → Minor`). This means `strength`
  must be exactly one of the three named values — no synonyms — and each Preference
  needs to be independently citable (discrete entries, not prose paragraphs).
- **Phase 4 (variant-explorer)** scores shortlists against TASTE.md and must degrade
  gracefully (omit the taste axis, say so) when the file doesn't exist — reinforces that
  the file's existence/absence must be a clean binary, with no partial/ambiguous state
  where the file exists but is unusable. Phase 3's own AC #5 covers this directly:
  malformed TASTE.md (missing `strength`) must be reported as unusable in Coverage
  Honesty rather than guessed at — worth stating explicitly in the format spec's Rules
  section so 3d's implementer has textual grounding for that behavior.

## Risks / dependencies

- **Scope discipline is the main risk.** Because "taste" and "quality" overlap
  linguistically, the format doc needs an explicit, hard-to-miss boundary (mirroring how
  `DATA-MODEL-FORMAT.md` has a dedicated "Relationship to CONTEXT.md" section) rather
  than a single throwaway sentence — otherwise 3d's taste seat risks duplicating
  Ousterhout-lens/Karpathy findings, which the spec's severity mapping ("taste findings
  are never Critical") implies is meant to be a distinct, deliberately-lower-stakes
  category.
- **Field-name stability matters for 3b/3c/3d correctness** since none of those skills
  exist yet — whatever field names/enum values are chosen here become the de facto
  contract those three tasks build against. Must match the task file's exact wording
  (`rule`, `rationale`, `strength` with `weak/strong/absolute`, `provenance`) rather than
  inventing synonyms.
- **No code/hook risk** — this task touches only a new markdown file under
  `plugins/review-panel/formats/`, so there's no lint/test/runtime surface to break.
  Verification is necessarily deferred to 3b's actual grilling-session flow, exactly as
  the task's own Acceptance Criteria note states ("verified via task 3b's flow, but the
  format itself must define and require these fields").
- **Human-owned-artifact framing must be explicit in this file too** — should include a
  sentence-level echo of Invariant 5 (agents may propose edits, FIX never auto-modifies)
  so a reader who lands on TASTE-FORMAT.md without having read the epic still gets the
  constraint, matching how `DATA-MODEL-FORMAT.md`'s prose ("which decisions require a
  human before an agent touches them") and `grill-the-schema/SKILL.md`'s explicit
  "FIX never auto-modifies" sentence both restate it locally.
- **Weightings vs. Preferences boundary** is worth calling out precisely in the Rules
  section (a Weighting is a *relative priority between two legitimate options*, e.g.
  "locality beats DRY," not a standalone rule) so 3b's elicitation logic can route a
  forced-choice answer to the right section instead of dumping everything into
  Preferences.
