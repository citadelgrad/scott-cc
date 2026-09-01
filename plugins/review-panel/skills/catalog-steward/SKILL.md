---
name: catalog-steward
description: Maintains plugins/review-panel/reviewers/persona-catalog.md over time — finds coverage holes and evaluates candidate skills for catalog inclusion. Advisory only; never auto-edits the catalog. Not a per-diff review lens; do not cast this as a review-panel seat.
---

# Catalog Steward

Periodic maintenance skill for `plugins/review-panel/reviewers/persona-catalog.md`, invoked by the
`catalog-audit` foundry schedule or manually — not a per-diff reviewer, and never cast as a
review-panel seat. `persona-catalog.md` is human-owned, the same posture `data-steward` takes
toward `DATA-MODEL.md` and `taste-review` takes toward `TASTE.md`: this skill drafts proposed
edits and a human applies them.

This SKILL.md documents two procedures: **Procedure A (hole-finding)**, a whole-catalog sweep
backed by `scripts/catalog_seat_audit.py`, and **Procedure B (new-skill evaluation)**, a
single-candidate comparison against the already-known catalog text.

## Procedure A: Hole-finding

1. Run `uv run python scripts/catalog_seat_audit.py --out <tmp>/report.md`.
2. Check whether the report was actually written before proceeding — see "Script failure" below.
   If it was, read `<tmp>/report.md` as the sole input. Do not separately re-read the raw catalog
   or skill directory contents to re-derive facts the script already computed mechanically.
3. For each finding in the report, translate it into a concrete proposed edit:
   - **`undocumented`** → propose either a new Seat Summary Table row (if the skill looks like a
     diff-scoped review lens) or a new Excluded-section bullet with reasoning (if it looks like a
     construction/build tool, matching the existing `grill-with-docs`/`improve-codebase-architecture`
     pattern).
   - **`missing_target`** → propose either updating the seat's path (search
     `plugins/review-panel/skills/` for a plausible rename target) or removing the seat entry if
     the skill is genuinely gone.
   - **`lens_drift_added` / `lens_drift_removed`** → propose an update to the Excluded section's
     lens list to match `design-review`'s actual funnel.
4. Write the proposed edits to a new output artifact, e.g. `catalog-steward-proposal-<date>.md`
   (a unified diff or a clearly labeled before/after snippet per finding).
5. **Never write to `persona-catalog.md` directly.** This procedure is advisory only — a human
   reviews the proposal artifact and applies whichever edits they accept.

### Zero findings

If the report shows no findings (script exits 0, prints `OK: catalog is clean`, and every report
section renders `(none)`), still produce a proposal artifact — one that states plainly no changes
are needed. Do not skip writing an artifact and do not leave it empty or missing.

### Script failure

`scripts/catalog_seat_audit.py` exits 1 both when findings are present *and* on a hard failure
(e.g. a missing `--catalog`/`--design-review` file or a missing `--skills-dir` directory) — exit
code alone cannot distinguish the two. Detect a hard failure by checking whether `--out` was
actually written (a hard failure calls `fail()` and exits before the report is written) or whether
stdout starts with `FAIL:`. If the report file is absent, **stop and surface the script's `FAIL:`
message** rather than treating it as "0 findings" or writing an empty/fabricated proposal.

### Output Contract (Procedure A)

The proposal artifact has one entry per finding: the finding's kind and subject, a concrete
before/after snippet or unified diff for the proposed edit, and a short rationale. If there are no
findings, the artifact says so explicitly instead of being empty.

## Procedure B: New-skill evaluation

1. **Input**: exactly one candidate skill, given as a path or a name. If a request names more than
   one candidate, **refuse the request** and ask the caller to re-invoke once per candidate. This
   refusal is a distinct "cannot proceed" outcome, separate from the four recommendation types in
   step 4 below — do not treat "too many candidates" as a form of "Reject" (Reject is a judgment
   about a *candidate*, not about the *request's shape*).
2. **Read frontmatter only**: read only the candidate's `SKILL.md` YAML frontmatter (`name`,
   `description`) — not its full body. Bounded-read discipline, the same posture as Procedure A's
   "read the report once, don't re-derive facts."
   - **Missing description**: if the candidate's frontmatter has no `description` field, stop and
     report insufficient information rather than guessing one of the four recommendation types.
3. **Compare against the existing catalog** (`persona-catalog.md`'s already-known content — no
   script invocation needed here, unlike Procedure A):
   - Existing seats' `cast-when` criteria (Seat Summary Table) — does the candidate overlap an
     existing seat's trigger?
   - The Excluded section's stated reasons — does the candidate look like a construction/build/
     conversational tool rather than a diff-scoped lens, matching an already-documented pattern
     (e.g. `grill-with-docs`, `improve-codebase-architecture`)?
   - `design-review`'s funnel — is the candidate's function already subsumed by one of
     design-review's five phases?
4. **Produce exactly one of four recommendation types**, each with stated reasoning:
   - **New seat** — proposed Seat Summary Table row (Seat / Casts / Cast-when / Model tier) +
     cast-when criteria + a model tier recommendation (Top-tier for adversarial,
     correctness-critical, or independence-requiring judgment; Mid-tier for well-defined,
     mechanical-ish checklist application — per the catalog's own "Model tiers" section).
   - **New trigger** — proposed addition to an existing seat's `cast-when` list.
   - **Exclude with reason** — proposed Excluded-section bullet.
   - **Reject** — stated reasoning (e.g. duplicate of an existing seat — name the specific seat —
     or out of scope for review-panel entirely).
   - **Duplicate boundary case**: if the candidate duplicates an existing seat's stated purpose,
     the recommendation must be "Reject" naming that seat, not "New trigger" and not silence.
5. **Output**: write the recommendation, with its stated reasoning, to a new output artifact, e.g.
   `catalog-steward-eval-<candidate-name>-<date>.md`. **Never write to `persona-catalog.md`
   directly** — same advisory-only contract as Procedure A; a human reviews the artifact and
   applies whichever recommendation they accept.

### Output Contract (Procedure B)

The evaluation artifact names the candidate, states which one of the four recommendation types
(or the "refuse: multiple candidates" / "insufficient information: no description" boundary
outcomes) applies, and gives the reasoning behind it. For "New seat" it includes the proposed
table row and model tier; for "New trigger" or "Exclude with reason" it includes the proposed
text to add.

## Sub-agent dispatch

Neither procedure dispatches sub-agents. Procedure A's corpus is one bounded report file, read
once; Procedure B's corpus is one candidate's frontmatter (a few lines) plus catalog content
already in context — also read once, single-shot. This is a deliberate design choice — small,
bounded, no checkpoint/resume machinery — not an oversight, per the PRD's explicit non-goal of
over-building this skill into a full orchestrator. Per SPEC FR-10,
`scripts/verify_orchestration_contracts.py`'s `COMPONENTS` registration is conditional on
sub-agent dispatch at the `catalog-steward` component level, so no registration is required for
either procedure.

## Limitations
- Use this skill only for periodic catalog maintenance, not as a per-diff review lens.
- Never writes to `persona-catalog.md` directly; a human must review and apply the proposal.
- Procedure A: stop and ask for clarification if a finding's proposed edit type (new seat row vs.
  Excluded-section bullet, path update vs. removal) is ambiguous rather than guessing.
- Procedure B: bounded to exactly one candidate per invocation (refuse multi-candidate requests);
  reads frontmatter only, never the candidate's full body; stops and reports insufficient
  information rather than guessing when `description` is missing.
