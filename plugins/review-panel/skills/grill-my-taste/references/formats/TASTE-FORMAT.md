<!-- Canonical copy. This is the single source of truth for the TASTE.md format —
     do not fork or duplicate this file elsewhere in the plugin; reference it instead. -->

# TASTE.md Format

`TASTE.md` lives at the repo root. It is the record of one human's personal, contested
preferences for how code should look and be organized — the opinions that remain after
universal quality is already satisfied. It is built and maintained through forced-choice
grilling sessions (`grill-my-taste`, Phase 3b), not written up front.

## Scope note: taste is not quality

`TASTE.md` and universal quality are deliberately different categories, and confusing
them breaks the taste review seat's severity model (taste findings are never Critical —
see "Rules" below).

- **Universal quality** — properties that hold regardless of who's reading the code:
  deep modules, complexity recognition, obvious naming, general-vs-special-case
  discipline, and the rest of the Ousterhout lens set
  (`plugins/review-panel/skills/deep-modules/`,
  `plugins/review-panel/skills/complexity-recognition/`,
  `plugins/review-panel/skills/naming-obviousness/`,
  `plugins/review-panel/skills/general-vs-special/`,
  `plugins/review-panel/skills/strategic-mindset/`,
  `plugins/review-panel/skills/code-evolution/`,
  `plugins/review-panel/skills/comments-docs/`, all grounded in Ousterhout's *A
  Philosophy of Software Design*), plus `skills/karpathy-guidelines/SKILL.md`. These are
  defensible on their own terms to any reader, not just this one.
- **Taste** — this human's personal, contested calibration on top of that baseline:
  which of two independently-legitimate options they prefer, and which locally-defensible
  patterns they still want flagged. A taste entry that just restates an Ousterhout or
  Karpathy finding is out of scope — it belongs in those skills, not here.

If a finding would hold for any competent reviewer, it is quality and does not belong in
`TASTE.md`. If it only holds because this specific human prefers it, it belongs here.

## Structure

```md
# Taste: {Human Name}

{One or two sentence description — what this file calibrates and for whom.}

## Preferences

### Prefer flat error handling over nested try/catch
- **Rule:** Return errors as values (Result-style) instead of throwing and catching
  across multiple nesting levels.
- **Rationale:** Nested try/catch obscures which call in a chain actually failed; flat
  error values keep the failure point local to the call that produced it.
- **Strength:** strong
- **Provenance:** grill-my-taste session 2026-07-18, forced choice #2 (nested try/catch
  vs. Result-returning helpers).

### Prefer named exports over default exports
- **Rule:** Use named exports for all module boundaries; avoid `export default`.
- **Rationale:** Named exports keep import statements grep-able and rename-safe across
  the codebase.
- **Strength:** weak
- **Provenance:** grill-my-taste session 2026-07-18, forced choice #4.

## Weightings

- **Locality beats DRY.** When a shared abstraction would need to travel more than one
  module boundary to be reused, prefer duplicating the logic locally over introducing a
  shared dependency.
- **Readability beats brevity.** Given two equally correct expressions, prefer the one
  that reads clearly over the one with fewer characters.

## Anti-preferences

- **Flag deeply chained optional access** (`a?.b?.c?.d`) even when each link is
  individually defensible — it's still hard to scan.
- **Flag boolean parameters in function signatures** even when named clearly — prefer an
  options object or two named functions.

## Candidate rules

- **Candidate:** Prefer early returns over wrapping a function body in an `if` block.
  - **Rationale (tentative):** Reduces nesting depth in the common case.
  - **Provenance:** Override captured 2026-07-19 — human rewrote agent output from
    wrapped-if to early-return, no reason given yet.
  - **Status:** awaiting `--distill` pass (Phase 3c).
```

## Rules

- **Every Preference needs all four fields.** `rule`, `rationale`, `strength`
  (`weak` | `strong` | `absolute` — exactly one of these three words, no synonyms), and
  `provenance` (the grill-my-taste session/forced-choice, or captured-override, that
  produced it). A Preference missing any field is not a valid entry — `grill-my-taste`
  (3b) must not write one, and the taste review seat (3d) must treat one as unusable
  rather than guess at the missing field.
- **`strength` drives severity — get it right at write time.** The taste review seat maps
  `absolute → Important+`, `strong → Important`, `weak → Minor`. Taste findings are never
  Critical and never sovereignty-marked, regardless of strength.
- **A Weighting is a relative priority, not a standalone rule.** It names two
  independently legitimate things and states which wins for this human (e.g. "locality
  beats DRY"). If an entry doesn't have two legitimate sides, it's a Preference, not a
  Weighting.
- **Anti-preferences flag locally-defensible patterns anyway.** These are not violations
  of universal quality — the Ousterhout/Karpathy lenses would pass them. They're flagged
  purely because this human doesn't want to see them.
- **Candidate rules are a distinct, greppable staging area.** Entries here are not yet
  confirmed Preferences — each still needs its own rationale and provenance so it can be
  evaluated independently, but it has no `strength` yet (strength is assigned on
  promotion). The Phase 3c `--distill` pass walks this section and promotes each entry
  into Preferences, merges it into an existing one, or rejects it. "Candidate rules
  empty" is the section having no entries — a clean, checkable state, not a judgment
  call.
- **Discrete entries, not prose paragraphs.** Each Preference, Weighting, Anti-preference,
  and Candidate rule is its own citable item (the taste review seat cites "the specific
  TASTE.md clause" in its findings) — don't collapse multiple preferences into one
  paragraph.
- **Human-owned — agents propose, never auto-modify.** Per Invariant 5, `TASTE.md` is
  edited only through a human grilling session (`grill-my-taste`, Phase 3b/3c). An agent
  may propose a candidate entry or a wording suggestion, but FIX never writes to this
  file directly.

## Malformed or missing TASTE.md

A missing `TASTE.md` and a malformed one are both a clean "no taste axis available," not
a guess:

- **No `TASTE.md` file:** the taste review seat never casts (no generic fallback), and
  Phase 4 variant scoring omits the taste axis. Both report the gap explicitly per
  Coverage Honesty rather than silently skipping.
- **`TASTE.md` exists but a Preference is missing a required field** (most commonly
  `strength`): that entry is unusable and must be reported as such in Coverage Honesty,
  not guessed at or silently dropped.

## Lazy creation

Create `TASTE.md` lazily — the first time a human runs a `grill-my-taste` session, not
scaffolded ahead of time by an agent.
