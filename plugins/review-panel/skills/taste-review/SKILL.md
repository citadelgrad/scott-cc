---
name: taste-review
description: Reviews diffs against TASTE.md's Preferences, Weightings, and Anti-preferences, citing the specific clause violated and mapping severity from the preference's declared strength (absolute/strong -> Important, weak -> Minor; never Critical). Use only when TASTE.md exists at the repo root — this seat never casts on its absence, and has no generic fallback. Ignores TASTE.md's Candidate rules section (unconfirmed, no strength assigned yet). A Preference missing a required field (most commonly strength) is reported as unusable in Coverage Honesty rather than guessed at. Findings never carry a sovereignty: human-required marker — that is a data-steward-only contract extension. Not a substitute for the Ousterhout/Karpathy universal-quality lenses (design-review, ponytail-review, etc.) — TASTE.md is explicitly scoped to this human's contested calibration on top of that baseline, not a restatement of it.
argument-hint: "[diff, file, or directory to review]"
allowed-tools: Read, Grep
---

# Taste Review

Read-only review seat for personal taste, following the same structural shape as
`data-steward/SKILL.md` and `domain-modeling/SKILL.md` (frontmatter, When to Apply, How to
Review, Output Contract). Not derived from any vendored source — authored for this plugin as
Phase 3d of the Two-System Architecture. It checks a diff against a project's `TASTE.md`
([formats/TASTE-FORMAT.md](../../formats/TASTE-FORMAT.md)) and cites the specific clause a
finding is grounded in.

This skill is **read-only** and reviews existing diffs; it does not write or refactor code, and
it does not edit `TASTE.md` itself — that file is human-owned, built and maintained only through
`grill-my-taste` grilling sessions (Invariant 5: human artifacts are human-owned).

## When to Apply

**Cast-when:** `TASTE.md` exists at the repo root. This is a **file-existence gate, not a
diff-content-pattern gate** — unlike every other risk-triggered seat in this catalog (which
trigger on diff signal: touches auth, touches migrations, etc.), this seat's trigger is purely
"does the artifact exist."

If `TASTE.md` is absent, this seat does **not** cast — there is no generic fallback, and no
partial casting. This is a pre-condition checked by the orchestrator via Cast (see
`persona-catalog.md`'s Taste entry), not a per-review "no findings" state. A human or
`--mode=agent` harness invoking this skill file directly, outside the panel's Cast step, against
a repo with no `TASTE.md` must still say so explicitly and stop — not silently produce an empty
report that could be mistaken for "reviewed, found nothing."

Read-only: reviews the diff/file/directory given, never edits `TASTE.md` or the code under
review.

## How to Review

When invoked with `$ARGUMENTS`, scope the review to the diff, file, or directory given. Read the
target diff first (do not review from memory or from other seats' summaries).

1. **Check for `TASTE.md`** at the repo root. If absent, stop and report that this seat has no
   taste axis to apply (see "When to Apply" above) — do not proceed to steps 2-4.
2. **Read `## Preferences`, `## Weightings`, and `## Anti-preferences`** (per
   `formats/TASTE-FORMAT.md`'s Structure). **Do not read `## Candidate rules`** — entries there
   are unconfirmed, have no `strength` assigned yet (strength is only assigned at `--distill`-time
   promotion), and citing one as a finding would misrepresent an unconfirmed candidate as settled
   taste.
3. **Validate each Preference** carries all four required fields: `rule`, `rationale`, `strength`,
   `provenance`. A Preference missing any field (most commonly `strength`) is **unusable** — do
   not guess the missing field or infer a severity. Report it as unusable in Coverage Honesty and
   skip it; continue reviewing the remaining valid entries normally.
4. **Check the diff against each valid entry:**
   - Each Preference's `rule`
   - Each Weighting's stated priority (which of two legitimate options wins)
   - Each Anti-preference's flagged pattern
   Where the diff violates one, produce a finding that quotes the clause verbatim — a paraphrase
   or reference alone is not sufficient; the finding must contain the clause text itself.

If everything is clear, say so plainly — do not force findings where none exist.

## Output Contract

Findings use the same Critical/Important/Minor shape as
[`contracts/reviewer-output.md`](../../contracts/reviewer-output.md)'s Issue shape (file:line,
what's wrong, why it matters, how to fix), so this seat's output merges cleanly through
`references/merge-and-validate.md`'s fingerprinting/confidence-scoring pipeline with zero
special-casing — documented locally here rather than by editing that shared contract file, the
same pattern `data-steward/SKILL.md` uses for its own sovereignty extension.

- **Location** — file:line
- **Principle violated** — quote the specific `TASTE.md` clause verbatim (the Preference's `rule`
  text, the Weighting's stated priority, or the Anti-preference's flagged pattern)
- **Severity** — mapped from the entry's declared `strength`, per `formats/TASTE-FORMAT.md`'s
  Rules section:
  - `strong` or `absolute` strength -> `Important`
  - `weak` strength -> `Minor`
  - **Never `Critical`**, regardless of strength — this is a fixed invariant of the taste axis
    (see `formats/TASTE-FORMAT.md`'s "Scope note: taste is not quality"), not a per-finding
    judgment call.

### Absolute-strength note (not a fourth severity value)

The panel's severity enum is closed to exactly `Critical | Important | Minor` — enforced by
`dual-mode-contract.md`'s JSON contract and `merge-and-validate.md`'s fingerprinting/dedup logic,
both of which reason over exactly these three strings. This seat does not introduce a literal
`Important+` value, which would break every downstream consumer of that closed enum.

Instead, an `absolute`-strength finding is emitted with `severity: Important` and an additional
inline note — `(absolute preference)` — appended to the finding's rationale, so a human or
downstream consumer can distinguish it from a `strong`-derived Important finding. Where multiple
Important-severity taste findings are rendered together in this seat's own local output, list the
`absolute`-derived ones first within the Important group. This is the same pattern
`data-steward/SKILL.md` uses for its `sovereignty: human-required` marker: a documented
convention layered on top of the closed severity enum, not a new enum value.

### Never sovereignty-marked

This seat must never set `sovereignty: human-required` on any finding, under any circumstance.
That marker is a `data-steward`-only contract extension (see `data-steward/SKILL.md`'s
"Sovereignty extension"), scoped to `DATA-MODEL.md` Agent-boundary crossings and missing-schema
cases — a different concern from personal taste, and `formats/TASTE-FORMAT.md` itself draws this
line explicitly (taste vs. quality/sovereignty).

### Malformed entries (Coverage Honesty)

A Preference missing a required field (most commonly `strength`) is reported once, plainly, as
unusable — e.g. "TASTE.md's Preference 'Prefer X over Y' is missing `strength`; skipped, not
guessed." This is `formats/TASTE-FORMAT.md`'s own "Malformed or missing TASTE.md" rule, and
Invariant 3 (coverage honesty) governs it: report the gap explicitly, never silently drop the
entry or invent a value for it.

Example finding line:
`Important — src/errors.ts:42 — taste: "Return errors as values (Result-style) instead of throwing and catching across multiple nesting levels." (strength: strong) — this diff introduces a nested try/catch three levels deep`
