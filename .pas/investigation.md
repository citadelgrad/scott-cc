# Investigation: scc-3x5 (Phase 3b — grill-my-taste skill)

## Task

Create `plugins/review-panel/skills/grill-my-taste/SKILL.md` — a new grill-family skill
that elicits taste via **forced choices** between realistic alternatives (not
introspective questions), distills each choice into a candidate rule, and writes it to
`TASTE.md` inline. Includes an **evidence-mining mode** that mines repo/PR history for
places the human rewrote agent/contributor output, turning each rewrite into a
before/after forced-choice question.

Per the task notes, the `--distill` mode used by Phase 3c (`scc-da0`) is a **mode of this
same skill**, not a separate skill — so this SKILL.md needs to at least stub/describe that
mode's existence even though its full behavior is 3c's job to flesh out. (Checked: 3c is
not yet implemented — `scc-da0` is still open, blocked on this task.)

## Files to create

- `plugins/review-panel/skills/grill-my-taste/SKILL.md` (only file — matches the
  single-file pattern used by `grill-the-schema` and `grill-with-docs`, no `references/`
  subdirectory needed since there's no long reference material to externalize).

No other files need to change. `TASTE-FORMAT.md` (3a) already exists and is the
target format this skill writes to — nothing there needs modification.

## Precedent: two existing grill-family skills

Both are single-file `SKILL.md`s with the same two-part shape: a short imperative
`<what-to-do>` block, then a `<supporting-info>` block with domain awareness + session
mechanics. I'll follow this shape exactly for consistency:

1. **`plugins/review-panel/skills/grill-the-schema/SKILL.md`** (Phase 2b, closest
   precedent — same author, same target pattern of "interview → write structured file
   inline → cite the format spec"). Sections: Domain awareness (where to look, lazy
   creation), During the session (interview topics, concrete scenarios, cross-reference
   with code, update file inline, offer ADRs sparingly).
2. **`plugins/review-panel/skills/grill-with-docs/SKILL.md`** (glossary/CONTEXT.md
   version, also ends with an "offer the plan-security pass" cross-plugin pointer —
   relevant precedent for how to write a "point at another skill/plugin without coupling
   to it" note, per Invariant 4).

**Key difference this skill must diverge on:** both precedents are *introspective*
interviews ("what's the invariant here?", "which term do you mean?"). `grill-my-taste`
is explicitly **choice-based, not introspective** per the spec — present two concrete
alternatives, user picks, agent asks why. This is a different interaction pattern from
the precedents and needs its own `<what-to-do>` framing rather than copying
grill-the-schema's "interview me relentlessly" opener verbatim.

## Target format: TASTE-FORMAT.md (already exists, Phase 3a — verified complete)

`plugins/review-panel/formats/TASTE-FORMAT.md` defines what this skill must produce:

- **Preferences**: rule, rationale, strength (`weak|strong|absolute`, exact word, no
  synonyms), provenance. Format's own worked example shows provenance written as
  `"grill-my-taste session {date}, forced choice #{n} ({short description})"` — this
  skill must number its forced choices within a session so provenance can cite them.
- **Weightings**: relative priority between two independently-legitimate things (e.g.
  "locality beats DRY") — distinct from a Preference, which needs two legitimate sides.
- **Anti-preferences**: patterns to flag even when individually defensible.
- **Candidate rules**: staging area, no `strength` yet, populated by captured overrides
  (3c's job) and awaiting `--distill`. This skill's mechanics don't need to fully
  implement `--distill`'s distillation logic (that's 3c/scc-da0), but must house the
  `--distill` mode entry point since the task explicitly says it's "a mode of this same
  skill, not a separate skill."
- **Human-owned artifact rule** (Invariant 5): "FIX never writes to this file directly" —
  same rule `grill-the-schema` states for `DATA-MODEL.md`. This skill is the *human
  grilling session* that legitimately writes the file — that's the mechanism Invariant 5
  carves out.
- **Lazy creation**: `TASTE.md` created only on first real `grill-my-taste` session, not
  pre-scaffolded.
- **Malformed/missing file section**: not this skill's concern directly (that's the 3d
  taste-review seat's read path), but worth a one-line acknowledgment that a session
  always produces well-formed entries (all four fields) so 3d never encounters a partial
  Preference this skill wrote.

## Required mechanics (from task description + spec §3b, both in exact agreement)

1. **Forced-choice elicitation loop:**
   - Present pairs of realistic alternatives — two API shapes, two error-message styles,
     two module layouts — **generated from the user's actual codebase where available**
     (i.e., don't always use generic canned examples; pull real patterns via codebase
     exploration when possible, falling back to representative synthetic examples when
     the codebase doesn't have enough signal).
   - User picks one.
   - Agent asks why.
   - Agent distills a candidate rule (rule + rationale + strength + provenance).
   - Agent confirms wording with the user.
   - Writes to `TASTE.md` inline (not batched — same "update inline" convention as
     `grill-the-schema`).

2. **Evidence-mining mode:**
   - Given a repo/PR history, find diffs where the human rewrote agent or contributor
     output.
   - Turn each rewrite into a forced-choice question: "before" (original/agent output)
     vs "after" (human's rewrite) — same choice mechanics as mode 1, just sourced from
     history instead of live-generated pairs.
   - This is a *mode* of eliciting the forced choices, not a different output format —
     still funnels into the same distill-rule → confirm → write-inline pipeline.

3. **`--distill` mode (housed here, fleshed out by 3c/scc-da0):**
   - Since 3c is not yet built, describe this as an existing mode/entry point of the
     skill (so the file structurally supports it and 3c's task doesn't need to
     restructure this file, only extend its logic) without inventing 3c's full
     promote/merge/reject mechanics prematurely. A short pointer paragraph, not a full
     spec, avoids scope creep into scc-da0's job while satisfying "not a separate skill."

4. **Session must support ≥5 forced choices** producing full 4-field entries — this is
   the Phase 3 acceptance criterion (`scc-3x5`'s own AC): "A grill-my-taste session of
   ≥5 forced choices produces a TASTE.md where every preference has rule + rationale +
   strength + provenance." The skill's mechanics section should make clear that each
   completed choice becomes one fully-formed Preference (or Weighting/Anti-preference
   where the choice reveals a relative-priority or flag-anyway pattern instead of a
   straightforward rule) — never a partial entry.

## Cross-plugin / dependency-direction considerations

- This skill lives entirely inside `plugins/review-panel/` — no new plugin, no
  cross-plugin imports. Consistent with Invariant 2 (dependency direction) since
  review-panel doesn't reference triage or variant-explorer.
- `plugins/variant-explorer` (Phase 4, scc-5hy) is *blocked on* this task per `bd show`,
  because Phase 4's scoring function needs `TASTE.md` to exist — but this skill itself
  doesn't need to reference variant-explorer at all. No forward-reference needed (Phase 4
  doesn't exist yet).
- Taste-review seat (Phase 3d, scc-4tt) reads `TASTE.md` this skill produces — again no
  direct coupling needed in this file; the format contract (TASTE-FORMAT.md) is the
  interface.

## Risks / things to get right

1. **Don't accidentally make this introspective.** The single biggest divergence from the
   grill-the-schema/grill-with-docs precedent is the choice-based mechanic. Must resist
   copying "ask them what their invariants are" style questions.
2. **Don't let this skill silently write partial entries.** Per TASTE-FORMAT.md's own
   rule ("A Preference missing any field is not a valid entry — grill-my-taste must not
   write one"), the skill's inline-write step must always have all four fields before
   writing, or defer the item to Candidate rules if strength/wording isn't resolved yet.
3. **Distinguish Preference vs. Weighting vs. Anti-preference at write time.** A forced
   choice might reveal any of the three depending on how the user answers "why" — the
   skill needs a decision rule for which section a given confirmed choice lands in,
   mirroring TASTE-FORMAT.md's own "Rules" section distinctions.
4. **Codebase-sourced alternatives require exploration, with a fallback.** Should state
   what to do when the codebase doesn't have enough real examples for a topic (fall back
   to realistic synthetic pairs) — Coverage Honesty spirit (don't fake "found in your
   codebase" provenance for synthetic examples).
5. **Session-level forced-choice numbering** needed so provenance strings
   ("...forced choice #4") are meaningful and citable, matching the TASTE-FORMAT.md
   worked example exactly.
6. **`--distill` scope discipline** — must not pre-implement scc-da0's full logic; only
   establish that it's a mode of this skill per task constraint, leaving depth to 3c.

## No test/lint surface

Pure markdown skill file, same as Phase 3a. No code changes, no automated test suite
applies. Verification will be a hand-worked simulated session (as was done for 3a),
checked against TASTE-FORMAT.md's own rules — consistent with how 3a's Run Tests step
was conducted, since no live orchestrator exists yet to run a real session against.
