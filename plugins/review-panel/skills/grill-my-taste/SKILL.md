---
name: grill-my-taste
description: Grilling session that elicits personal taste via forced choices between realistic alternatives — not introspective questions — distilling each pick into a Preference, Weighting, or Anti-preference and writing it to TASTE.md inline. Includes an evidence-mining mode that mines repo/PR history for places you rewrote agent or contributor output, and houses the --distill entry point for promoting Candidate rules. Use when the user wants to build or extend TASTE.md.
---

<what-to-do>

Elicit taste through forced choices, not introspection. Do not ask "what's your invariant here?" or "how do you like to structure X?" — those questions ask the user to theorize about their own preferences, and people are unreliable narrators of their own taste. Instead, present two concrete, realistic alternatives and make them pick.

For each forced choice:

1. Present two realistic alternatives — two API shapes, two error-message styles, two module layouts, two naming schemes. Prefer alternatives generated from the user's actual codebase where you can find a real contrast; fall back to a representative synthetic pair only when the codebase doesn't offer one, and say so.
2. Let the user pick.
3. Ask why.
4. Distill the answer into a candidate rule (rule, rationale, strength, provenance).
5. Confirm the wording with the user before writing anything.
6. Write the confirmed entry to `TASTE.md` inline, in the correct section.

Ask one forced choice at a time, waiting for the pick and the why before moving to the next. Run at least 5 forced choices per session before treating the session as complete.

If invoked with `--mine-evidence` (or the user asks to mine repo/PR history), run evidence-mining mode instead of generating live pairs (see below).

If invoked with `--distill`, run the distill pass over Candidate rules instead of eliciting new choices (see below).

</what-to-do>

<supporting-info>

## Domain awareness

Look for an existing `TASTE.md` at the repo root, alongside `DATA-MODEL.md` and `CONTEXT.md`. Read it first so forced choices don't re-litigate settled Preferences — probe topics that aren't covered yet, or that the user flags as having changed.

Create `TASTE.md` lazily — only on the first real session, when the first choice is confirmed. Do not pre-scaffold it.

## During the session

### Sourcing forced-choice pairs

Explore the codebase for genuine contrasts before inventing synthetic ones: two error-handling styles in different modules, two naming conventions across files, two ways collections are exposed. A real pair carries more weight because the user can react to their own code.

When the codebase doesn't have enough signal on a topic, use a realistic synthetic pair instead — but say plainly that it's synthetic. Never write a provenance line that implies a choice came from the user's codebase when it didn't; that would misrepresent Coverage Honesty.

### Distilling the choice

After the user picks and explains why, decide which TASTE.md section the confirmed choice belongs in, per [TASTE-FORMAT.md](../../formats/TASTE-FORMAT.md):

- **Preference** — the choice is between two independently-legitimate options, and the user's answer states a standalone rule ("always do X, not Y").
- **Weighting** — the user's answer names two legitimate things and picks a relative priority between them ("locality beats DRY"), rather than ruling one out entirely.
- **Anti-preference** — the user rejects a pattern even though it's individually defensible on its own terms — they want it flagged whenever it shows up, not just in this instance.

If the choice doesn't resolve cleanly into one of the three — wording is unresolved, or the "why" is thin — do not force it into a section. Hold it back rather than writing a partial entry.

### Confirm before writing

Read the drafted rule, rationale, strength, and provenance back to the user in the words you intend to write. Only write once they confirm. Never write a Preference missing any of the four required fields — per TASTE-FORMAT.md, a partial entry is not a valid entry, and the taste review seat (Phase 3d) has no way to guess at what's missing.

### Number forced choices within the session

Track a running count of forced choices in the session (`forced choice #1`, `#2`, ...) so each `Provenance` line can cite it directly, matching TASTE-FORMAT.md's worked example (`grill-my-taste session {date}, forced choice #{n} ({short description})`).

### Write TASTE.md inline

When a choice is confirmed, update `TASTE.md` right there — don't batch entries up for the end of the session. Use the structure in [TASTE-FORMAT.md](../../formats/TASTE-FORMAT.md) exactly, including the dated session/forced-choice provenance string.

This skill proposes and drafts `TASTE.md` content through the conversation, but the resulting file is a human-owned artifact (Invariant 5) — produced through the grilling session the user is actively steering, never silently generated. FIX never auto-modifies `TASTE.md`.

## Evidence-mining mode

When pointed at a repo's commit or PR history (or the user asks to mine evidence instead of generating live pairs), look for diffs where the human rewrote agent-generated or contributor-submitted code — commits that follow shortly after an AI-attributed commit or a PR, touching the same lines, where the rewrite isn't a bug fix or feature change but a stylistic one.

For each rewrite found, turn it into a forced-choice question: presented as "before" (the original agent/contributor version) and "after" (the human's rewrite), exactly as if the pair had been generated live. Ask why the rewrite happened, then follow the same distill → confirm → write-inline steps as mode 1 above — evidence mining changes where the pair comes from, not what happens after the user picks.

If no qualifying rewrites are found in the available history, say so explicitly and offer to fall back to live-generated pairs, rather than silently producing nothing.

## `--distill` mode

`--distill` is a mode of this same skill, not a separate skill — it walks the `Candidate rules` section of `TASTE.md` and, for each entry, promotes it into a full Preference (assigning the `strength` it doesn't yet have), merges it into an existing Preference, or rejects it. Its full promote/merge/reject logic belongs to Phase 3c (`scc-da0`); this file only establishes that `--distill` is invoked through `grill-my-taste`, not a distinct tool.

</supporting-info>
