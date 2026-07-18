# Investigation: scc-da0 (Phase 3c — Taste feedback loop)

## Task

Close the loop between human overrides/rejections during review and `TASTE.md`'s
`Candidate rules` section, plus flesh out the `--distill` mode of `grill-my-taste` that
periodically promotes/merges/rejects candidates with the human.

Two deliverables per the task design and spec §3c:

1. **Capture** — convention + `bd remember`: whenever a human overrides a panel finding
   or rejects agent output with a reason, record it as a taste candidate. "Documented in
   the skill; no new tooling required in v1."
2. **Distillation** — a full `--distill` mode implementation (currently stubbed) that
   walks `Candidate rules`, promotes/merges/rejects each, and prunes stale preferences.
   Foundry-schedulable as a *prompt* only; the session itself stays interactive
   (Invariant 5).

AC (verbatim from `bd show scc-da0` / spec.md line 284-286): `--distill` on a `TASTE.md`
with ≥3 candidate rules ends with zero remaining candidates (each promoted, merged, or
rejected with the human). PASS/FAIL: Candidate section empty after session.

## File to modify

**`plugins/review-panel/skills/grill-my-taste/SKILL.md`** — the sole file. This is a
docs-only skill, same as Phase 3a/3b; no new files, no new tooling (per the task's own
design note). Two edits to this one file:

1. Add a new "Capturing overrides as Candidate rules" section (currently absent).
2. Replace the `--distill` stub (current lines 75-78) with the full promote/merge/reject
   procedure.

No other file needs to change:
- `formats/TASTE-FORMAT.md` (Phase 3a) already defines the `Candidate rules` section
  shape and its four sub-fields (`Candidate`, `Rationale (tentative)`, `Provenance`,
  `Status`) — this task consumes that contract, doesn't extend it.
- `review-panel/references/dual-mode-contract.md`'s "Interactive apply loop" (lines
  64-78) is where a human currently rejects/directs a manual edit that diverges from a
  panel finding — the exact "override a panel finding" moment the capture convention
  hooks into conceptually. Per the task's explicit scope ("documented in the skill; no
  new tooling required"), this task does **not** edit that file — capture stays a
  documented convention inside `grill-my-taste`, not a special-cased wire-in to
  review-panel's core substrate. This mirrors how Phase 3d (not yet built) will be the
  thing that actually casts during review runs, not a hook into the core loop.
- `docs/foundry-recipes.md` (referenced in spec.md line 342, 368-371 as consolidating
  "what Foundry runs," explicitly listing "Phase 3c's distillation prompt") does not
  exist yet — confirmed via `fd -H "foundry-recipes"` (no hits). That file is Phase 5
  territory (scc-tsa, still open). This task only needs to *note*, inside
  `grill-my-taste/SKILL.md`, that `--distill` is Foundry-schedulable as a reminder
  prompt — not author the recipes doc itself.

## Current state of the stub (what exists today)

`grill-my-taste/SKILL.md` lines 75-78:

```
## `--distill` mode

`--distill` is a mode of this same skill, not a separate skill — it walks the `Candidate
rules` section of `TASTE.md` and, for each entry, promotes it into a full Preference
(assigning the `strength` it doesn't yet have), merges it into an existing Preference, or
rejects it. Its full promote/merge/reject logic belongs to Phase 3c (`scc-da0`); this file
only establishes that `--distill` is invoked through `grill-my-taste`, not a distinct tool.
```

This explicitly defers its own logic to this task. Nothing else in the skill references
`--distill` except the one-line dispatch note in `<what-to-do>` ("If invoked with
`--distill`, run the distill pass over Candidate rules instead of eliciting new choices").

There is currently **no** "capture" section anywhere in the skill — the only mention of
overrides is inside `TASTE-FORMAT.md`'s worked example (`Candidate rules` sample entry,
provenance: "Override captured 2026-07-19 — human rewrote agent output... no reason given
yet") and in `TASTE-FORMAT.md`'s Rules section ("`provenance` ... the grill-my-taste
session/forced-choice, **or captured-override**, that produced it").

## Required changes, in detail

### 1. Capture section (new)

Document, as a convention (not new tooling), that whenever a human overrides a
review-panel finding or rejects agent-produced output and states (or doesn't state) a
reason, the agent should:

- Call `bd remember` to durably persist the raw observation (what was proposed, what the
  human did instead, any stated reason) — this survives past the current session even
  before anything lands in `TASTE.md`, and is a "no new tooling" fit since `bd remember`
  already exists as this project's cross-session memory primitive (see root `CLAUDE.md`:
  "Use `bd remember` for persistent knowledge").
- Propose — never silently write — a `Candidate rules` entry in `TASTE.md`, using
  `TASTE-FORMAT.md`'s exact shape (`Candidate` / `Rationale (tentative)` / `Provenance` /
  `Status: awaiting --distill pass`). This must stay a lightweight one-line confirmation
  ("capture this as a taste candidate?"), not a full grilling session — but it still
  requires the human's go-ahead before the write happens, because Invariant 5 draws no
  exception for Candidates: `TASTE.md` is proposed-by-agent/confirmed-by-human, never
  auto-modified, at every tier including this low-friction one.
  - Note the tension to resolve explicitly in the write-up: Invariant 5 says "written via
    human grilling sessions" — a captured-override confirmation is not a grilling
    session, but it's still human-confirmed-before-write, which is the load-bearing part
    of the invariant ("FIX never auto-modifies them"). The confirmation step is what
    keeps this consistent.
- If no reason was given, capture anyway with "no reason given yet" (matches
  `TASTE-FORMAT.md`'s own worked example verbatim) rather than skipping the capture —
  asking "why" in the moment interrupts flow; that follow-up is `--distill`'s job later,
  not capture's.
- Applies whether or not `TASTE.md` exists yet — a confirmed capture can be the file's
  lazy-creation trigger, consistent with `TASTE-FORMAT.md`'s "Lazy creation" rule.

### 2. `--distill` mode (replace stub)

Full procedure to add, mirroring the level of detail the main forced-choice mode already
has:

1. Read `TASTE.md`. If missing, or `Candidate rules` is absent/empty, say so explicitly
   and stop — nothing to distill (Coverage Honesty; matches the "malformed or missing"
   handling `TASTE-FORMAT.md` already defines).
2. Walk `Candidate rules` entries **one at a time**, not batched (same discipline as the
   main mode's "one forced choice at a time"). For each:
   - Present the candidate (its tentative rule, rationale, provenance) to the human.
   - Ask for one of three outcomes:
     - **Promote** — turn it into a full Preference/Weighting/Anti-preference. Reuse the
       existing "Distilling the choice" section-routing rules (already in the skill,
       lines 45-49) to pick the section. Since Candidates never carry `strength`, this is
       exactly where it must be assigned (per the existing stub's own note). Confirm
       wording before writing — same "Confirm before writing" discipline already
       documented for the main mode (lines 53-55) applies identically here.
     - **Merge** — fold into an existing Preference/Weighting/Anti-preference; locate the
       target entry and update its rationale/provenance to note the merge (e.g. "...
       reinforced by override captured {date}").
     - **Reject** — remove the candidate; no residue needs to survive in `TASTE.md` since
       the raw observation already durably lives in `bd remember` from capture-time.
   - Remove the Candidate entry from `TASTE.md` the moment its outcome is written —
     the section only reaches empty once every entry has been individually resolved,
     which is exactly what the AC checks.
3. **Prune stale preferences** — after all Candidates are resolved, ask the human
   (once, lightweight) whether any existing Preferences/Weightings/Anti-preferences no
   longer apply. This is explicitly in the task's design line ("...and prunes stale
   preferences") but is not part of the AC's pass/fail check — scope it as a bounded
   final question, not a full re-litigation of the file (the main mode already says not
   to re-litigate settled Preferences; the same restraint applies here for anything the
   human doesn't flag).
4. **Foundry-schedulable note** — state plainly that `--distill` can be nudged via a
   scheduled Foundry profile (per this repo's `foundry.yaml` convention) as a periodic
   *prompt* only (e.g., monthly reminder: "N candidate rules pending, run `grill-my-taste
   --distill`") — the distillation conversation itself must never run unattended
   (Invariant 5). Do not author a `foundry.yaml` stanza or `docs/foundry-recipes.md`
   entry here — that belongs to Phase 5 (scc-tsa), which explicitly lists "Phase 3c's
   distillation prompt" as something it will wire in.
5. **End state** — session is complete once `Candidate rules` is empty. If the human
   stops early with candidates still pending, say so explicitly in the session summary
   (Coverage Honesty) rather than implying completion.

## Risks / things to get right

- **Don't violate Invariant 5.** Every write path here — capture-time proposal and
  distill-time promote/merge/reject — must stay confirm-before-write. This is the
  primary risk: "convention + bd remember, no new tooling" could be misread as license
  for a silent auto-append. It is not; `bd remember` is the durable side-channel, the
  `TASTE.md` write itself always needs a human nod.
- **Don't scope-creep into review-panel's core files.** The design explicitly limits
  this to "documented in the skill" — resist the temptation to also wire a hook into
  `dual-mode-contract.md`'s interactive apply loop; that would be new tooling, not
  convention, and isn't what the task asks for.
- **Reuse existing section-routing logic rather than re-deriving it.** The
  Preference/Weighting/Anti-preference distinction is already spelled out once in the
  skill (lines 45-49) for the main mode — `--distill`'s promote path should reference it,
  not restate a divergent version.
- **Match `TASTE-FORMAT.md`'s Candidate shape exactly** (`Candidate` /
  `Rationale (tentative)` / `Provenance` / `Status`) since that format file is the single
  source of truth and is out of scope to edit here.
- **AC is mechanically checkable** ("Candidate section empty after session") — make sure
  the procedure has an unambiguous loop-until-empty structure, not just a general
  "process the candidates" instruction, so a hand-worked test (same style as Phase
  3a/3b's `.pas/test-results.md`) can simulate ≥3 candidates and verify zero remain.

## Testing approach (for later Run Tests step)

No live orchestrator exists yet (same situation as 3a/3b). Verification will again be a
hand-worked conformance test: simulate a `TASTE.md` with ≥3 Candidate rules, walk the
documented `--distill` procedure by hand (one promoted, one merged, one rejected), and
confirm the resulting file has an empty `Candidate rules` section and that the promoted/
merged entries retain full required fields per `TASTE-FORMAT.md`'s Rules section.
