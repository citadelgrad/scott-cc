---
name: grill-my-taste
description: Use when the user wants to build or extend TASTE.md. Grilling session
  that elicits personal taste via forced choices between realistic alternatives, distilling
  each pick into a Preference, Weighting, or Anti-preference. Includes evidence-mining
  mode and --distill entry point for promoting Candidate rules.
metadata:
  category: technique
  triggers:
  - taste-review
  - subjective-quality
  - code-review
---

## When to Use
- Building or extending a TASTE.md file for a project
- Eliciting personal taste via forced choices between realistic alternatives
- Distilling taste picks into Preferences, Weightings, and Anti-preferences
- Running a grilling session to surface implicit design preferences

<what-to-do>

Elicit taste through forced choices, not introspection. Do not ask "what's your invariant here?" or "how do you like to structure X?" — those questions ask the user to theorize about their own preferences, and people are unreliable narrators of their own taste. Instead, present two concrete, realistic alternatives and make them pick.

For each forced choice:

1. Present two realistic alternatives — two API shapes, two error-message styles, two module layouts, two naming schemes. Prefer alternatives generated from the user's actual codebase where you can find a real contrast; fall back to a representative synthetic pair only when the codebase doesn't offer one, and say so.
2. Let the user pick.
3. Ask why.
4. Distill the answer into a candidate rule (rule, rationale, strength, provenance).
5. Confirm the wording with the user before writing anything.
6. Write the confirmed entry to `TASTE.md` inline, in the correct section.

Ask one forced choice at a time, waiting for the pick and the why before moving to the next. Run at
least 5 and at most 8 forced choices per session before treating the session as complete.

If invoked with `--mine-evidence` (or the user asks to mine repo/PR history), run evidence-mining mode instead of generating live pairs (see below).

If invoked with `--distill`, run the distill pass over Candidate rules instead of eliciting new choices (see below).

</what-to-do>

## Context architecture contract

- **Scope contract:** Live mode covers one TASTE.md and **5–8 forced choices**. Evidence-mining mode
  scans at most **100 commits / 20 qualifying diffs** after metadata preflight; reject larger
  history with `SCOPE_TOO_LARGE` and a commit-range partition.
- **Fan-out contract:** Ask at most **8 human questions per session**, one at a time, with no
  concurrent choice or mining workers. Distill mode resolves at most **8 candidates** per session.
- **Artifact contract:** Confirmed rules stay in the human-owned TASTE.md. A continuation manifest
  is at most **2 KiB** and contains at most **8 choice/candidate IDs**, provenance, paths, and
  SHA-256 values; never embed full alternatives, diffs, or conversation history.
- **Failure contract:** Missing human confirmation, scope metadata, writable TASTE.md, or valid
  manifest stops before writing. Never continue past question 8, auto-confirm wording, or silently
  discard pending candidates.
- **Continuation contract:** At question 8 or an earlier pause, write
  `grill-my-taste-checkpoint.json` bound to the TASTE.md and source-history SHA-256 values. Resume
  only in a fresh session after hash verification, starting with unresolved IDs.
- **Mechanical-test contract:** `scripts/tests/test_second_wave_context_budget.py` asserts the
  choice, commit, diff, question, candidate, manifest, hash, and fresh-session bounds for this skill.

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

## Capturing overrides as Candidate rules

Outside of a live grilling session, taste signal also shows up in the moment: a human overrides a review-panel finding, or rejects agent-produced output and says (or doesn't say) why. Capture that moment rather than letting it evaporate:

1. Call `bd remember` with the raw observation — what was proposed, what the human did instead, and any stated reason. This is the durable side-channel; it survives independently of whatever happens to `TASTE.md`, and needs no new tooling since `bd remember` is already this project's cross-session memory primitive.
2. Propose a `Candidate rules` entry in `TASTE.md`, using the exact shape from [TASTE-FORMAT.md](../../formats/TASTE-FORMAT.md) (`Candidate` / `Rationale (tentative)` / `Provenance` / `Status: awaiting --distill pass`). Ask a single lightweight yes/no — "capture this as a taste candidate?" — before writing. This is not a grilling session, but Invariant 5 draws no exception for Candidates: propose, don't auto-write, even for this low-friction path.
3. If no reason was given, capture anyway with "no reason given yet" rather than skipping the capture or interrupting flow to ask why — following up on a thin reason is `--distill`'s job later, not capture's.
4. This applies whether or not `TASTE.md` exists yet. A confirmed capture can be the file's lazy-creation trigger, same as a confirmed forced choice.

## `--distill` mode

`--distill` is a mode of this same skill, not a separate skill. It walks the `Candidate rules` section of `TASTE.md` and resolves each entry into a full Preference, Weighting, or Anti-preference, a merge into an existing one, or a rejection — ending with the section empty.

1. Read `TASTE.md`. If it's missing, or `Candidate rules` is absent or already empty, say so explicitly and stop — there is nothing to distill (Coverage Honesty).
2. Walk the `Candidate rules` entries one at a time, not batched — same discipline as the main mode's one-forced-choice-at-a-time pacing. For each entry, present its tentative rule, rationale, and provenance to the human and ask for one outcome:
   - **Promote** — turn it into a full Preference, Weighting, or Anti-preference. Use the same section-routing rules already defined above under "Distilling the choice" to pick the section. A Candidate never carries `strength`, so promotion is where it must be assigned. Confirm the wording before writing, per "Confirm before writing" above — that discipline applies identically here.
   - **Merge** — fold it into an existing Preference, Weighting, or Anti-preference. Locate the target entry and update its rationale or provenance to note the merge (for example, "... reinforced by override captured {date}").
   - **Reject** — remove the candidate outright. No residue needs to survive in `TASTE.md`, since the raw observation already lives durably in `bd remember` from capture time.
   Remove the Candidate entry from `TASTE.md` the moment its outcome is written, before moving to the next one — the section only reaches empty once every entry has been individually resolved.
3. Once every Candidate is resolved, ask the human once, lightly, whether any existing Preferences, Weightings, or Anti-preferences no longer apply, and prune the ones they flag. This is a bounded final question, not a re-litigation of the whole file — leave anything the human doesn't flag alone.
4. `--distill` can be nudged via a scheduled Foundry profile (per this repo's `foundry.yaml` convention) as a periodic reminder prompt only — e.g., a monthly nudge like "N candidate rules pending, run `grill-my-taste --distill`." The distillation conversation itself must never run unattended (Invariant 5); Foundry may only schedule the prompt to start the session, never the session.
5. The session is complete once `Candidate rules` is empty. If the human stops early with candidates still pending, say so explicitly in the session summary rather than implying completion.

</supporting-info>

## Limitations
- Use this skill only when the task clearly matches the scope described above.
- Taste preferences are subjective — they document personal style, not universal quality.
- Effectiveness depends on the user engaging honestly with forced choices.
- Does not replace universal-quality lenses (design-review, ponytail-review).
- Stop and ask for clarification if the domain, scope of taste elicitation, or TASTE.md format is unclear.
