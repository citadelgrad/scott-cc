# Test Results: scc-4tt (Phase 3d — Taste seat)

## Scope

Two new files (`plugins/review-panel/skills/taste-review/SKILL.md`, new) and one edit
(`plugins/review-panel/reviewers/persona-catalog.md`, new "Taste" entry + Seat Summary
Table row). No code changed — same verification shape used throughout Phase 2/3: no
live orchestrator exists yet to run the panel end-to-end, so I built fixtures and a
hand-worked conformance test, per the investigation's stated plan.

## 1. Fixtures built

No `TASTE.md` fixtures existed before this task (unlike `DATA-MODEL.md`, which has
`tests/fixtures/orders-schema/`). Built three, modeled on the `orders-schema` /
`no-data-model-inventory` fixture pattern:

- **`tests/fixtures/taste-preferences/`** — a well-formed `TASTE.md` with three
  Preferences spanning all three `strength` values (`strong`, `absolute`, `weak`), plus
  `diff.patch` (`before.ts` → `after.ts`) that violates all three in one change:
  `export default` (weak), in-place argument mutation `order.status = "processing"`
  (absolute), and three levels of nested `try`/`catch` (strong — the same shape as
  `TASTE-FORMAT.md`'s own worked example and the example finding line in
  `taste-review/SKILL.md` itself). Targets **AC1** and the absolute-strength
  severity-mapping design decision flagged in the investigation.
- **`tests/fixtures/taste-malformed/`** — a `TASTE.md` with one well-formed Preference
  (`strong`) and one missing its `Strength` field entirely, reusing the same diff.
  Targets **AC3**.
- **`tests/fixtures/no-taste-file/`** — reuses the same diff/before/after, but has no
  `TASTE.md` at all in the fixture directory. Targets **AC2**.

Each fixture has a `README.md` stating which AC it targets, matching the convention of
every prior-phase fixture directory.

## 2. Hand-worked conformance test

Built a Python parser + validator at `/tmp/taste-review-test/` (`fixtures.py`,
`validate.py`) that mechanically parses each `TASTE.md` fixture's `## Preferences`
section (mirroring `taste-review/SKILL.md` step 3's field-presence check) and validates
a hand-worked set of findings — what the seat should produce reviewing
`taste-preferences/diff.patch` by hand, per the skill's documented "How to Review" and
"Output Contract" sections — against the contract's rules.

**Validator run:**

```
$ python3 validate.py
== Scenario 1: taste-preferences (AC1 happy path + severity mapping) ==
  [PASS] strength=absolute severity=Important verbatim=True absolute_note=True sovereignty=False
  [PASS] strength=strong   severity=Important verbatim=True absolute_note=False sovereignty=False
  [PASS] strength=weak     severity=Minor     verbatim=True absolute_note=False sovereignty=False
  Important-band ordering (absolute-derived first): PASS
  No Critical findings anywhere: PASS

== Scenario 2: taste-malformed (AC3 error state) ==
  Preferences found: 2 (usable=1, malformed=1)
  'Prefer named exports over default exports' correctly flagged as malformed (missing strength): PASS
  Missing field correctly identified as exactly ['strength']: PASS (got ['strength'])
  Well-formed 'Prefer flat error handling over nested try/catch' still reviewed normally (not dropped alongside the malformed entry): PASS
  Coverage Honesty report line present and explicit: PASS

== Scenario 3: no-taste-file (AC2 absent-from-Cast) ==
  TASTE.md absent from fixture dir: PASS
  Diff still present (seat would have content to review, if cast): PASS
  taste-review absent from simulated Cast list: PASS

3/3 scenarios behaved as expected
exit code: 0
```

**Negative controls** (confirming the checks actually discriminate, not vacuously
passing):
- A `severity: Critical` finding fails the "never Critical" check (`severity !=
  'Critical'` evaluates `False` for a Critical finding).
- A paraphrased clause ("Avoid nesting try/catch blocks.") fails the verbatim-quote
  check (not found in the set of exact `rule` strings parsed from `TASTE.md`) — proving
  AC1's "clause quoted in finding" requirement is a real discriminator, not
  trivially satisfied by any finding text that merely references the topic.

**Result: PASS** on all three scenarios, and both negative controls are correctly
rejected rather than passing trivially.

## 3. Acceptance criteria

1. **Happy path** — "Panel run on a diff violating a strong preference yields a taste
   finding citing the clause verbatim." **PASS.** The hand-worked finding for the
   `strong` Preference ("Prefer flat error handling over nested try/catch") quotes
   `pref["fields"]["rule"]` verbatim (`verbatim=True`), and additionally the same
   verification covers `absolute` and `weak` severities in one pass, confirming the
   severity-mapping design decision from the investigation: `absolute` → `Important`
   with an `(absolute preference)` note (never a fourth `Important+` enum value),
   `strong` → `Important`, `weak` → `Minor`, and `absolute`-derived findings sort first
   within the Important band, exactly as `taste-review/SKILL.md`'s "Absolute-strength
   note" section specifies.
2. **No TASTE.md** — "Repo without TASTE.md → taste seat absent from Cast; no taste
   findings." **PASS.** `no-taste-file/` mechanically confirms no `TASTE.md` exists in
   the fixture dir; the simulated Cast-list check confirms `taste-review` is excluded
   from casting entirely (not a "ran, found nothing" seat) — matching
   `persona-catalog.md`'s new Taste entry ("file-existence gate... no generic
   fallback") and the skill's own "When to Apply" section.
3. **Error state** — "Malformed TASTE.md (missing strength) — seat reports the file as
   unusable in Coverage Honesty rather than guessing." **PASS.** `taste-malformed/`'s
   Preference missing `Strength` is correctly identified as malformed with exactly
   `['strength']` as the missing-field set; the well-formed sibling Preference in the
   same file is still parsed as usable (confirming the seat's "still reviews valid
   entries normally" behavior, not an all-or-nothing failure); and the Coverage Honesty
   report line format matches the skill's own example text verbatim ("is missing
   `strength`; skipped, not guessed").

## 4. Structural validation

- **Files changed match investigation's scope exactly**: new
  `plugins/review-panel/skills/taste-review/SKILL.md`, edited
  `plugins/review-panel/reviewers/persona-catalog.md`. No other plugin file touched.
- **Frontmatter valid**: `grep -c '^---$' taste-review/SKILL.md` → `2`.
- **Never Critical, never sovereignty-marked**: confirmed structurally in the skill text
  (`SKILL.md`'s Output Contract and "Never sovereignty-marked" section) and confirmed
  behaviorally in the hand-worked findings (no finding in the validated set carries
  either).
- **Candidate rules excluded**: `taste-preferences/TASTE.md` includes an empty
  `## Candidate rules` section (present, per `TASTE-FORMAT.md`'s structure, but with no
  entries) — the parser only ever reads `## Preferences`, matching the skill's step 2
  ("Do not read `## Candidate rules`").
- **Dependency direction (Invariant 2)**: the skill only reads `TASTE.md` and diff
  content; no reference to `triage` or `foundry` anywhere in the new file.

## 5. Lint / build

No code changed — two markdown files plus markdown fixtures. No markdown linter
configured in this repo (`.markdownlint*` absent, no `markdownlint` reference in
`package.json`) — same finding as every prior Phase 2/3 Run Tests step.

## 6. Working tree check

`git status --short`:

```
 M .pas/current_task.md
 M .pas/investigation.md
 M .pas/logs/two-system-architecture-e64d8f93/checkpoint.json
 M plugins/review-panel/reviewers/persona-catalog.md
?? plugins/review-panel/skills/taste-review/
?? plugins/review-panel/tests/fixtures/no-taste-file/
?? plugins/review-panel/tests/fixtures/taste-malformed/
?? plugins/review-panel/tests/fixtures/taste-preferences/
```

Only this task's implementation plus the three new fixture directories created in this
step, plus the same pre-existing session-state diffs (`.pas/*`) flagged in every prior
pipeline step in this session. No unexpected changes. Scratch validator artifacts live
under `/tmp/taste-review-test/` (outside the repo, untracked, no cleanup needed).

## Conclusion

All three acceptance criteria PASS. No code changed, so no automated test/lint suite
applies beyond the structural + hand-worked validation above. Ready for Verify.
