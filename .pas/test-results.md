# Test Results: scc-cnx (Phase 3a — TASTE.md format)

## Nature of this deliverable

`plugins/review-panel/formats/TASTE-FORMAT.md` is a pure documentation deliverable — a
format specification with no code, hooks, or skill logic (consumer skills `grill-my-taste`
3b, `--distill` 3c, and `taste-review` 3d don't exist yet). There is no test suite or
lint surface to run against a markdown format spec. Per the task's own Acceptance
Criteria note, live behavioral verification (an actual `grill-my-taste` session producing
a conforming `TASTE.md`) is deferred to Phase 3b. This session instead did two things a
format spec *can* be checked for now: (1) structural/cross-reference validation of the
file itself, and (2) a hand-worked conformance test — simulating the Phase 3 acceptance
criteria against the format's own stated rules, to prove the format is capable of
satisfying them before 3b/3c/3d are built on top of it.

## 1. Structural validation of `TASTE-FORMAT.md`

- **Fenced code block balance:** 1 fenced block (2 backtick markers) — balanced, matches
  precedent (`DATA-MODEL-FORMAT.md` also has exactly one `## Structure` example block).
- **Header hierarchy:** no level-skips outside the fenced example (checked
  programmatically). Section order (`Scope note` → `Structure` → `Rules` →
  `Malformed or missing TASTE.md` → `Lazy creation`) mirrors the precedent files'
  intro → structure → rules → disambiguation → lazy-creation shape.
- **Cross-referenced paths all exist in the repo** (checked directly, not assumed):
  `plugins/review-panel/skills/{deep-modules,complexity-recognition,naming-obviousness,
  general-vs-special,strategic-mindset,code-evolution,comments-docs}`,
  `skills/karpathy-guidelines/SKILL.md`, `plugins/review-panel/formats/{DATA-MODEL-FORMAT,
  ADR-FORMAT}.md`, `plugins/review-panel/skills/grill-the-schema/SKILL.md`. All present.
- **Spec conformance:** compared section-by-section against
  `docs/plans/2026-07-16-two-system-architecture/two-system-spec.md` §3a (lines 233–241)
  and Phase 3 acceptance criteria (lines 275–288) — exact match on required sections,
  field names (`rule`, `rationale`, `strength`, `provenance`), and the `weak/strong/
  absolute` enum. No other file in the repo yet references `TASTE-FORMAT.md` or
  `TASTE.md` besides the PRD/SPEC/`.pas` docs — confirms the investigation's finding that
  no other files need to change in this phase.

## 2. Hand-worked conformance test (simulated Phase 3 ACs against the format's rules)

Since `grill-my-taste` doesn't exist yet, I hand-constructed three sample `TASTE.md`
files that a real session would plausibly produce, and wrote a small mechanical
validator (`/tmp/taste-format-test/validate.py`, scratch — not committed) that parses
`## Preferences` entries against exactly the rules stated in `TASTE-FORMAT.md`'s own
"Rules" and "Malformed or missing TASTE.md" sections: every Preference needs
`Rule`/`Rationale`/`Strength`/`Provenance`, and `Strength` must be one of
`weak|strong|absolute`.

| Scenario | File | Simulates | Result |
|---|---|---|---|
| ≥5 forced choices, all fields present | `valid_taste.md` | Phase 3 AC1 (grill-my-taste session ≥5 forced choices) | **PASS** — 5/5 Preferences parsed, all 4 fields present, all `Strength` values valid enum members, `Candidate rules` section empty |
| One Preference missing `Strength` | `malformed_taste.md` | Phase 3 AC5 (malformed TASTE.md, missing strength) | **PASS** — validator correctly flags the entry `UNUSABLE (missing: Strength)` rather than guessing a default, matching the format's "Malformed or missing TASTE.md" rule |
| Post-`--distill` state, one promoted entry, empty Candidate section | `distilled_taste.md` | Phase 3 AC4 (`--distill` ends with zero remaining candidates) | **PASS** — promoted entry has all 4 fields (provenance recorded as "Promoted via --distill"), `Candidate rules` section is empty and mechanically detected as such |

Full validator output:

```
=== valid_taste.md ===
Preferences found: 5
  - Prefer flat error handling over nested try/catch: OK
  - Prefer named exports over default exports: OK
  - Prefer composition over inheritance for shared behavior: OK
  - Prefer explicit null checks over optional chaining chains: OK
  - Prefer table-driven tests over repeated assertions: OK
Candidate rules section empty: True
Expected all-valid=True, got all-valid=True -> PASS

=== malformed_taste.md ===
Preferences found: 2
  - Prefer flat error handling over nested try/catch: OK
  - Prefer named exports over default exports: UNUSABLE (missing: Strength)
Candidate rules section empty: True
Expected all-valid=False, got all-valid=False -> PASS

=== distilled_taste.md ===
Preferences found: 1
  - Prefer early returns over wrapping a function body in an if block: OK
Candidate rules section empty: True
Expected all-valid=True, got all-valid=True -> PASS

OVERALL: PASS
```

## Acceptance criteria (scc-cnx)

> A grill-my-taste session of >=5 forced choices produces a TASTE.md where every
> preference has rule + rationale + strength + provenance.

**PASS** (format-level verification, as the task's own AC note anticipates — full
behavioral verification is 3b's responsibility): `TASTE-FORMAT.md` defines and requires
all four fields per Preference (`## Rules`, first bullet), constrains `strength` to
exactly `weak|strong|absolute` with no synonyms, and — demonstrated above — a
5-preference sample conforming to the format's `## Structure` template parses cleanly
with all fields present. The format also explicitly requires the "missing field →
unusable, not guessed" behavior needed by Phase 3's error-state AC, and defines
"Candidate rules empty" as a clean, greppable state needed by Phase 3's `--distill` AC —
both confirmed above.

## Scope check

No code changed, so no `ruff`/`ty`/test-suite run applies. Working tree for this task is
limited to the new `plugins/review-panel/formats/TASTE-FORMAT.md` file plus `.pas/`
tracking docs, consistent with the investigation and implementation summaries. Scratch
validation artifacts (`/tmp/taste-format-test/`) are outside the repo and were not
committed.
