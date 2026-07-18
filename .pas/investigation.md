# Investigation: scc-4tt (Phase 3d — Taste seat)

## Task

New risk-triggered, read-only, mid-tier review seat (`taste-review`) that applies `TASTE.md` as
a review lens: cites the specific clause, maps severity from the preference's declared
`strength`, never casts without `TASTE.md`, never emits Critical or `sovereignty`-marked
findings.

## Files to modify/create

1. **New file:** `plugins/review-panel/skills/taste-review/SKILL.md` — the seat itself.
2. **Edit:** `plugins/review-panel/reviewers/persona-catalog.md` — add a new entry under
   "Risk-Triggered Seats" (after the existing "Data Steward" entry, before the "Excluded from
   Individual Casting" section), plus a row in the "Seat Summary Table" at the bottom.

No other files are in scope. `TASTE-FORMAT.md` already defines everything this seat reads
(Phase 3a, complete) and explicitly reserves the "malformed/missing" contract this seat must
honor. `grill-my-taste/SKILL.md` (3b/3c, complete) already forward-references "the taste review
seat (Phase 3d)" at line 55 — this task is what fulfills that reference, not a file to edit.

## Pattern to follow: `data-steward/SKILL.md`

`data-steward` is the closest existing seat — same shape (risk-triggered, read-only, reads a
human-owned format file, cites specific clauses, maps severity, has a "missing file" fallback
governed by Coverage Honesty). Its structure is the template:

- Frontmatter: `name`, `description` (dense, single-paragraph, states cast-when + what it does +
  what it explicitly excludes), `argument-hint`, `allowed-tools: Read, Grep`.
- Body: intro paragraph (what it is, what format doc it reads, what it's not), then `## When to
  Apply`, `## How to Review`, `## Output Contract` sections — mirroring `domain-modeling/SKILL.md`'s
  shape, which `data-steward` itself cites as its structural precedent.
- `allowed-tools: Read, Grep` matches `cast-and-spawn.md`'s "Read-only tool access" rule (no
  `Edit`/`Write`/`Bash` for any SPAWN-dispatched seat) — `taste-review` needs no `Glob`/`Task`
  since, unlike `adversarial-reviewer` or `design-it-twice`, it never dispatches a nested
  subagent.

## Required content, derived from TASTE-FORMAT.md + the task's Design Details

### When to Apply
- **Cast-when:** `TASTE.md` exists at the repo root. This is a **file-existence gate, not a
  diff-content-pattern gate** — unlike every other risk-triggered seat in the catalog (which
  trigger on diff signal: touches auth, touches migrations, etc.), this seat's trigger is purely
  "does the artifact exist." If it doesn't, the seat is absent from Cast — no generic fallback,
  no partial casting. This must be stated explicitly since it's a different casting shape from
  every sibling entry in `persona-catalog.md`.
- Read-only: reviews the diff/file/directory given, never edits `TASTE.md` or the code (matches
  Invariant 5 — "Human artifacts are human-owned"; `TASTE.md` is edited only via `grill-my-taste`
  grilling sessions).

### How to Review
1. Check for `TASTE.md` at repo root. If absent → seat does not cast at all (this is a
   pre-condition checked by the orchestrator via Cast, not a per-review "no findings" state —
   worth being explicit that an absent-TASTE.md run of this skill directly is a no-op that says
   so, since a human or `--mode=agent` harness could still invoke the skill file directly outside
   the panel's Cast step).
2. Parse `## Preferences`, `## Weightings`, and `## Anti-preferences` sections (per
   TASTE-FORMAT.md's Structure). **`## Candidate rules` entries are explicitly out of scope** —
   TASTE-FORMAT.md is explicit that Candidates have no `strength` yet (assigned only at
   `--distill`-time promotion) and aren't confirmed preferences; citing an unconfirmed candidate
   as a review finding would misrepresent it as settled taste.
3. For each Preference: validate all four required fields are present (`rule`, `rationale`,
   `strength`, `provenance`). A Preference missing any field (most commonly `strength`) is
   **unusable** — do not guess the missing field; report it in Coverage Honesty (AC #3, this is
   the seat's explicit malformed-file contract straight from TASTE-FORMAT.md's own "Malformed or
   missing TASTE.md" section).
4. Check the diff against each valid Preference's `rule`, each Weighting's stated priority, and
   each Anti-preference's flagged pattern. Where the diff violates one, produce a finding that
   quotes the clause verbatim (AC #1 requires the clause text appear in the finding, not just a
   paraphrase/reference).

### Output Contract — severity mapping (the interesting design decision)

Task says: `absolute → Important+`, `strong → Important`, `weak → Minor`, never Critical, never
sovereignty-marked.

**Constraint found during investigation:** the panel's actual severity enum is a **closed
three-value set**, enforced in two places:
- `dual-mode-contract.md`'s JSON contract: `"severity": "Critical | Important | Minor"` (line
  105) — a `mode:agent` consumer parses exactly these three strings.
- `merge-and-validate.md` line 101: dedup/fingerprinting explicitly reasons over
  "Critical/Important/Minor, taking the highest severity."

There is no fourth `Important+` value anywhere else in this plugin. Introducing a literal
`"Important+"` severity string would break the closed enum every downstream stage (MERGE,
VALIDATE, the JSON contract, a `foundry` gate's `jq` parsing) depends on — this is exactly the
kind of contract-breaking special-case Invariant 2 (review-panel never special-cases a
subordinate concern) warns against.

**Resolution to write into the skill:** treat `Important+` as "the top of the Important band,"
not a fourth severity value — same pattern `data-steward` already uses for `sovereignty:
human-required` (an additional documented field/convention layered on the closed
Critical/Important/Minor enum, not a new enum value). Concretely:
- Emit `severity: Important` for `absolute`-strength findings (keeps the closed enum intact).
- Additionally note `(absolute preference)` inline in the finding text/rationale so a human or
  downstream consumer can distinguish it from a `strong`-derived Important finding, and sort
  `absolute`-derived findings first within the Important bucket in any locally-rendered listing.
- This must be spelled out as a deliberate design note in the SKILL.md's Output Contract (mirrors
  how `data-steward`'s "Sovereignty extension" subsection documents its own contract extension
  locally rather than editing the shared `contracts/reviewer-output.md`).

Severity floor/ceiling, explicit:
- `absolute` → `Important` (top of band, noted as absolute)
- `strong` → `Important`
- `weak` → `Minor`
- **Never `Critical`**, regardless of strength — this is an explicit task/format-doc invariant,
  not a judgment call the seat makes per-finding.
- **Never `sovereignty: human-required`** — this seat must not set that field under any
  circumstance (it's a `data-steward`-only contract extension per TASTE-FORMAT.md's own framing
  of taste vs. quality/sovereignty concerns).

### Missing / malformed TASTE.md (AC #2, #3)

- **No `TASTE.md` at all:** seat does not cast (Cast-level exclusion, handled in "When to
  Apply"/persona-catalog entry) — not a "ran and found nothing" state.
- **`TASTE.md` exists, well-formed, no violations found:** say so plainly (matches
  `data-steward`'s "If everything is clear, say so plainly" closing line).
- **`TASTE.md` exists but has a malformed entry** (e.g. missing `strength`): the seat still casts
  (file exists) and still reviews valid entries normally, but reports the malformed entry as
  unusable under Coverage Honesty, explicitly, rather than guessing at severity — this is the
  literal text of TASTE-FORMAT.md's own "Malformed or missing TASTE.md" rule, and Invariant 3
  (coverage honesty) directly governs it.

## persona-catalog.md changes

Add a new "Taste" entry under `## Risk-Triggered Seats`, following the same field structure as
every existing entry (Casts / Cast-when / Model tier / Notes):

- **Casts:** `skills/taste-review/SKILL.md`
- **Cast-when:** `TASTE.md` exists at the repo root — **not** a diff-content-pattern trigger
  (unlike every sibling risk-triggered entry); must be called out as this catalog's only
  file-existence-gated seat rather than diff-signal-gated. No fail-closed ambiguity applies here
  since it's a mechanical file check, not a judgment call.
- **Model tier:** Mid-tier, matching the task's explicit rationale ("applying a written
  preference file is procedural") — this is the same mid-tier default the catalog uses generally,
  contrasted explicitly against `data-steward`'s top-tier deviation (blast-radius asymmetry
  doesn't apply here; a missed taste nit is not a data-loss risk).
- **Notes:** severity-mapping summary (absolute/strong/weak → Important(absolute-noted)/
  Important/Minor, never Critical, never sovereignty-marked); explicit no-`TASTE.md`-means-absent
  rule (cross-reference to "Missing skill handling" section's coverage-honesty pattern, though
  this is a "missing artifact" case rather than a "missing skill" case — worth distinguishing in
  the note since the catalog's existing "Missing skill handling" section is about the skill file
  itself being uninstalled, a different failure mode than the target repo simply having no
  `TASTE.md`); note that Phase 4 (variant-explorer, `scc-5hy`, currently blocked on this task)
  will consume this same severity mapping for its scoring function, per the epic's stated
  dependency ("Phase 4 blocked on Phase 3 (taste is the scoring function)").

Also add a row to the "Seat Summary Table" at the bottom, consistent with the other 10 rows:

| Seat | Casts | Cast-when | Model tier |
|---|---|---|---|
| Taste | `taste-review` | `TASTE.md` exists at repo root | Mid-tier |

## Risks / dependencies

- **Must not introduce a 4th severity value.** This is the main design trap in the task's own
  wording ("Important+") — confirmed no such value exists anywhere in the merge/validate/JSON
  pipeline. Handling this as a documented sub-band of Important (as `data-steward` handles
  `sovereignty` as an additional field, not a new severity) keeps the seat's output mergeable
  through `merge-and-validate.md` and valid against `dual-mode-contract.md`'s JSON schema with
  zero special-casing anywhere else in the pipeline — satisfies Invariant 2.
- **Must not read `## Candidate rules`.** Candidates are unconfirmed and have no `strength` by
  design (TASTE-FORMAT.md) — citing one as a finding would be citing an entry the format doc
  itself says isn't ready to be treated as settled taste.
- **No test fixtures currently exist for TASTE.md** (unlike `DATA-MODEL.md`, which has a fixture
  at `tests/fixtures/orders-schema/DATA-MODEL.md`). The Run Tests step will likely need to build
  fixtures by hand (a `TASTE.md` with a strong-strength Preference + a diff violating it, a
  malformed entry missing `strength`, and a no-TASTE.md case) — consistent with the hand-worked
  conformance-test approach used throughout Phase 3 (no live orchestrator exists yet to execute
  the panel end-to-end).
- **Dependency direction check (Invariant 2):** this seat only reads `TASTE.md` and diff content;
  it does not import from or special-case `triage` or `foundry` — consistent with the invariant.
- **Blocks Phase 4** (`scc-5hy`): the epic notes taste is Phase 4's scoring function, so getting
  the severity-mapping contract right here (not just "it compiles") matters for that consumer,
  even though wiring the two together is explicitly out of this task's scope.
