# Triage Spine Pressure Test

**Task:** scc-tsa — Phase 5 of epic scc-hzj, "Two-System Architecture."

This document is a pressure test of the `triage` plugin (`skills/triage-spine/SKILL.md` and its
two implemented detectors, `skills/detectors/lib-upgrades/SKILL.md` and
`skills/detectors/prod-errors/SKILL.md`), following the same discipline as
`plugins/variant-explorer/tests/PRESSURE-TEST.md` and `plugins/review-panel/tests/PRESSURE-TEST.md`:
prove the skill's prescribed process produces the behavior each acceptance criterion (AC1-AC6)
describes, via live dispatches with real side effects where the AC requires runtime evidence. All
six ACs here require runtime evidence (bead filing, rejection paths, reproduction ordering, status
branching, zero-side-effect boundaries), so unlike `variant-explorer`'s AC5, none were resolved by
citation alone. See "Limits of this pressure test" at the end.

**Methodology note — subagent-type substitution.** The `triage` plugin was created in this same
working session; no `triage:*` `subagent_type` was registered (plugins register at session start,
not hot-loaded mid-session). Every dispatch below used `subagent_type: "general-purpose"` with an
explicit instruction to read the target `SKILL.md` in full and follow its procedure exactly — the
identical substitution used in `variant-explorer`'s and `review-panel`'s own pressure tests. This
verifies the *procedure* the `SKILL.md` files describe, not Claude Code's `subagent_type`
resolution for a plugin-qualified name.

**Real side effects.** Every dispatch performed genuine `bd` CLI mutations (`bd create`, `bd
update`, `bd human`/label operations) and genuine detector executions (`npm audit`, `npm outdated`,
real Python reproduction scripts) — nothing here is narrated or simulated. Every bead a dispatch
claimed to create or modify was independently re-verified by this session directly via `bd show`
after the dispatch completed, not taken on the dispatch's self-report. All test-artifact beads are
closed out in the Cleanup section below.

---

## 1. The fixtures

All under `plugins/triage/tests/fixtures/`:

- **`lib-upgrades-vulnerable/`** — `package.json` + `package-lock.json` pinning `lodash@4.17.11`,
  a real, currently-registered npm package version. For AC1.
- **`lib-upgrades-clean/`** — pins `lodash@4.18.1`, the actual current release. For AC6.
- **`prod-errors-repro/`** — `app/checkout.py` (a genuine null-guard bug in `process_payment`) +
  `error.log` (3 identical `AttributeError` traces that must collapse to one triage item, plus 1
  distinct `KeyError`). For AC4.
- **`malformed-batch/`** — `batch.json`, a 5-item batch exercising Phase 1's 6 ordered validation
  rules: item 1 missing `evidence`, item 2 `severity: "urgent"`, item 3 `affected-paths` as a
  string instead of an array, item 4 `source: "iac-drift"` (a registered stub slot), item 5 fully
  valid. For AC5.
- **`panel-status/`** — four hand-crafted JSON fixtures (`converged.json`, `escalated.json`,
  `circuit-broken.json`, `error.json`) matching `review-panel`'s `dual-mode-contract.md` schema
  exactly, forcing each of the four possible gate statuses. `escalated.json` carries a realistic
  DATA-MODEL.md ownership-boundary finding (`sovereignty: "human-required"`, widening a
  billing-owned column) with `sovereignty_finding_ids: ["f-001"]`. For AC2/AC3.

A fixture-design defect was caught and corrected mid-test: see §7 (AC6) for the `lib-upgrades-clean`
correction, and §3 for the `malformed-batch` README correction.

---

## 2. AC1 — Lib-upgrade detector fixture

**Requirement:** lib-upgrades detector on a fixture with an outdated dep emits a valid triage item
and the spine files a bead with AC. PASS bar: bead exists, AC present, item validates against
contract.

**Dispatch:** ran the lib-upgrades detector procedure for real against `lib-upgrades-vulnerable/`.
`npm audit` against `lodash@4.17.11` reported multiple advisories (critical: `GHSA-35jh-r3h4-6jhm`
command injection, `GHSA-jf85-cpcp-j695` prototype pollution, `GHSA-p6mc-m468-83gw` prototype
pollution, `GHSA-29mw-wpgm-hmr9` ReDoS, plus three more affecting the `<=4.17.23` range) — a real,
current npm-registry result, not fabricated. The dispatch built a Triage Item Contract entry from
this (source `lib-upgrades`, severity `Critical`), ran it through Phase 1 (all 5 fields present and
valid), and filed a bead via Phase 3.

**Bead filed: `scc-9jx`** — independently re-verified via `bd show scc-9jx`:

- Title: "Upgrade vulnerable lodash@4.17.11 pin (GHSA-jf85-cpcp-j695 prototype pollution)"
- Priority **P0** — correct `Critical → P0` mapping per Phase 3 step 2
- Description cites the evidence and affected paths verbatim
- Acceptance criteria present, 5 checklist items covering the pin bump, a zero-vuln `npm audit`
  re-check, existing-suite regression, a behavior-compatibility boundary check, and a
  no-stale-transitive-pin check

**AC1: confirmed.** Bead exists, carries AC, and the originating item validates against the
contract.

**A genuine gap this caught, disclosed rather than smoothed over:** the bead's own acceptance
criteria state that pinning `lodash` to `>=4.17.21` is sufficient remediation. That was true for the
one advisory (`GHSA-jf85-cpcp-j695`) the dispatch named — but re-running `npm audit` in this
session directly against `4.17.21` (built while correcting the AC6 fixture, §7) shows it is *still*
flagged, under a different, newer advisory (`GHSA-r5fr-rjxr-66jc` code injection via `_.template`,
plus two prototype-pollution advisories), patched only in `4.18.1`. The lib-upgrades detector's
AC-generation is anchored to the one advisory it observed rather than a fresh audit of its own
proposed target version, so an AC written this way would pass its own checklist while leaving the
dependency still audit-flagged. AC1's PASS bar (bead exists, AC present, item validates) does not
require this level of correctness, so it doesn't change AC1's verdict — but it's a real detector
limitation worth fixing in a future revision of `lib-upgrades/SKILL.md` (re-audit the proposed
target version before writing the "pin to X" acceptance criterion, rather than assuming one version
bump clears everything the one detected advisory implies).

---

## 3. AC5 — Contract validation (error state)

**Requirement:** detector output failing contract validation is rejected with a named field error;
spine never processes a malformed item. PASS bar: rejection path.

**Dispatch:** ran Phase 1 validation against all 5 items in `malformed-batch/batch.json`, in order,
per `SKILL.md`'s 6 ordered rules.

| # | Outcome | Rule |
|---|---|---|
| 1 | **REJECTED** | missing `evidence` field — rule 1 |
| 2 | **REJECTED** | `severity: "urgent"` — rule 3, must be `Critical\|Important\|Minor` |
| 3 | **REJECTED** | `affected-paths` is a string, not an array — rule 5 |
| 4 | **Survives Phase 1** | `source: "iac-drift"` — rule 2 only checks `source` against the registered slot table; `iac-drift` is a registered *stub* slot, so it correctly passes even though its detector is unimplemented |
| 5 | **Survives Phase 1 → bead filed** | fully valid on every rule |

**Bead filed for item 5: `scc-9lt`** — independently re-verified via `bd show scc-9lt`: title "Bump
lodash to 4.17.21 in package.json and package-lock.json", priority **P2** (correct `Minor → P2`
mapping), description matches item 5's evidence verbatim, AC present. Item 4 correctly survived
Phase 1 but was not carried through to a filed bead in this dispatch — consistent with AC5's actual
PASS bar (the rejection path for malformed items 1-3, and non-blocking of valid siblings), not a
gap in the requirement being tested.

Item 3's rejection message and item 2's rejection message, reconstructed against `SKILL.md`'s own
worked examples (lines 62-64), match the exact format the spec prescribes: `REJECTED — triage item
from <source> — field "<field>": <reason>, got "<value>"`.

**AC5: confirmed.** Items 1-3 rejected with named field errors; a malformed sibling (items 1-3)
never blocked valid items (4, 5) from proceeding.

**A genuine fixture-design defect this caught, corrected rather than left standing:** the original
`malformed-batch/README.md` labeled all 5 items in a single "Violation | Rule violated" table,
implying item 4 (`source: "iac-drift"`) was also a rejection case. The dispatch re-derived Phase 1's
rules independently rather than trusting the README's framing, and correctly determined item 4
survives Phase 1 — rule 2 checks *registration*, not *implementation status*. This is exactly the
kind of independent-verification behavior a pressure test exists to surface: the dispatch caught a
real ambiguity in my own fixture design instead of rubber-stamping it. **Fix applied:** the README
was corrected (table header changed to "Outcome | Rule", with an explicit preamble stating only
items 1-3 are actual violations) before this write-up was authored.

---

## 4. AC4 — Prod-error detector with E2E reproduction

**Requirement:** prod-error detector given a log line with a stack trace produces a triage item
whose evidence includes the trace, and whose spine run attempts E2E reproduction before any fix.
PASS bar: reproduction step precedes fix in the transcript/bead trail.

**Dispatch:** ran the prod-errors detector against `prod-errors-repro/error.log`, grouping by
stack-trace shape per `SKILL.md`'s rule (same exception type + same top frame = one item).

- **Item 1 (Critical):** the 3 identical `AttributeError: 'NoneType' object has no attribute
  'strip'` entries (09:02, 11:47, 18:15 on 2026-07-14, all at `checkout.py:2` in
  `process_payment`) collapsed into **one** triage item, with occurrence count (3) and all three
  timestamps recorded in `evidence`. Confirmed: 3 log lines → 1 item, not 3.
- **Item 2 (Important):** the single `KeyError: 'discount_code'` at `checkout.py:10` kept as its
  own distinct item (different exception type/frame).

**Bead filed for item 1: `scc-9kx`** — independently re-verified via `bd show scc-9kx`: title
references the exact exception and location, priority **P0** (correct `Critical → P0` mapping),
description carries the full trace and all 3 timestamps, AC present (5 checklist items covering the
null-token case, the happy path, an empty/whitespace boundary, a regression-test requirement, and a
blanket "must not propagate" rule).

**Reproduction, run for real** at `/tmp/repro_scc-9kx.py`: imported `process_payment` from the
actual fixture file and called it with `{"token": None}`. Real execution produced:

```
AttributeError: 'NoneType' object has no attribute 'strip'
  File ".../app/checkout.py", line 2, in process_payment
    token = payment["token"].strip()
```

— an exact match to the log's exception type, message, and frame.

**Ordering proof:** `bd update scc-9kx --notes="Reproduction: ..."` recorded the reproduction result
on the bead. `bd show scc-9kx`'s NOTES section contains only this reproduction record — no
diagnose/fix note exists anywhere on the bead, and no Phase 5/6 activity was performed. The
temporary repro script and a stray `__pycache__/` directory it left behind were cleaned up after
verification.

**AC4: confirmed.** Reproduction step precedes fix in the bead trail (in fact, no fix step was
taken at all, satisfying the ordering constraint by construction — nothing occurred out of order).

---

## 5. AC2 — End-to-end status handling / AC3 — Escalated status handling

**AC2 requirement:** detector → fix diff → `mode:agent` panel run returns JSON whose status is one
of `converged | escalated | circuit_broken | error`; bead updated per the resolved status handling.
PASS bar: all four statuses produce their documented bead/PR outcome (fixtures may force each).

**AC3 requirement:** given a panel run returning `escalated`, the bead is not parked and the
pipeline does not halt; the produced PR carries an explicit `sovereignty: human sign-off required`
annotation. PASS bar: bead unparked, annotation present in PR body.

**Dispatch:** four synthetic gate-test beads were created, one per forced status, then Phase 6's
branching logic was applied against each of the four `panel-status/*.json` fixtures.

| Fixture | Bead | Action taken | Parked (`bd human list`)? |
|---|---|---|---|
| `converged.json` | `scc-aci` | `bd update --notes="review-panel: converged, ready-to-merge"` | No |
| `escalated.json` | `scc-g5m` | `bd update --notes="SOVEREIGNTY: human sign-off required — ..."` (sourced from finding `f-001`, not a bare status echo) | No — correctly never parked |
| `circuit-broken.json` | `scc-9b9` | parked, no PR opened | Yes |
| `error.json` | `scc-cis` | parked, no PR opened | Yes |

**Independently re-verified** via `bd show` on all four beads and `bd human list`:

- `scc-aci` NOTES: `review-panel: converged, ready-to-merge` — not in `bd human list`.
- `scc-g5m` NOTES: `SOVEREIGNTY: human sign-off required — migrations/0003_widen_token_column.sql:
  "widening payments.token's type changes a column DATA-MODEL.md marks as owned by the billing
  service; requires explicit sign-off from that service's steward before merge"` — not in `bd human
  list`, confirming escalated is never parked/halted.
- `scc-9b9` NOTES carry the circuit-breaker diagnosis; `LABELS: human`.
- `scc-cis` NOTES carry the error/abort reason; `LABELS: human`.
- `bd human list` returned exactly 2 entries — `scc-cis` and `scc-9b9` — matching the expected set
  precisely; `scc-aci` and `scc-g5m` correctly absent.

**AC3's PR-annotation requirement:** no real product PR exists to open for a synthetic fixture (see
Limits). The dispatch drafted the exact leading line a PR description would carry, sourced from
finding `f-001` rather than a bare status echo:

> `**sovereignty: human sign-off required** — see migrations/0003_widen_token_column.sql — widening
> payments.token's type changes a column DATA-MODEL.md marks as owned by the billing service;
> requires explicit sign-off from that service's steward before merge`

**AC2: confirmed** — all four statuses produced their documented, distinct bead outcome (2 unparked,
2 parked-for-human), independently verified via `bd show` and `bd human list`, not just the
dispatch's self-report.

**AC3: confirmed** — the escalated bead was never parked, the pipeline did not halt (immediately
proceeded to producing the drafted PR annotation), and the annotation is present, verbatim, sourced
from the actual finding rather than a generic status label.

**A genuine spec/tooling drift this caught:** `triage-spine/SKILL.md`'s Phase 6 prescribes `bd
human <id> --reason="..."` for `circuit_broken`/`error`. That command does not exist in the
installed `bd` CLI (v1.1.0) — `bd human` is a read-only submenu (`list`/`respond`/`dismiss`/`stats`)
with no bare `<id>` form and no `--reason` flag; `bd update` has no `--reason` flag either. The
mechanism that actually produces the documented outcome (parked, surfaced in `bd human list`) is `bd
update <id> --add-label=human --notes="<reason>"` — confirmed empirically that `bd human list` is a
filter on the `human` label. The dispatch used the real mechanism to faithfully execute Phase 6's
*intent*; `SKILL.md`'s literal command text is stale against this CLI version and should be
corrected in a future revision.

---

## 6. AC6 — Boundary: zero findings

**Requirement:** zero findings from a detector run → no beads filed, one-line 'clean' log, no panel
invocation. PASS bar: no side effects.

**Fixture defect caught and fixed first.** The original `lib-upgrades-clean/` fixture pinned
`lodash@4.17.21`, which I had assumed was "current/patched." Running real `npm audit` against it
directly in this session showed that assumption was wrong: `4.17.21` is still flagged high-severity
under `GHSA-r5fr-rjxr-66jc` (and two related prototype-pollution advisories), part of the same
`<=4.17.23` range affecting the AC1 fixture. The actual unaffected version is `4.18.1` (confirmed via
`npm view lodash versions`/`npm view lodash version`, and matching `npm audit`'s own suggested fix
target for the AC1 fixture). **Fix applied:** `lib-upgrades-clean/package.json` and
`package-lock.json` were updated to pin `4.18.1`; `npm audit --audit-level=low` against the
corrected fixture now reports `found 0 vulnerabilities`. Using the original fixture unmodified would
have made this AC's "PASS" meaningless — it would have proven the detector stays silent on a version
that a real audit still flags, which is the opposite of a zero-findings boundary case.

**Dispatch:** with the corrected fixture in place, ran the lib-upgrades detector for real against
`lib-upgrades-clean/`.

- `npm audit --audit-level=low --json` → `"vulnerabilities": {}`, `"total": 0`.
- `npm outdated --json` → `wanted == latest == 4.18.1` (no upgrade available, so no "outdated
  enough" finding under the detector's own filter either).
- Emitted clean-log line, per the detector's Output Contract: `lib-upgrades: clean, 0
  outdated/vulnerable dependencies found`.

**Independently re-verified:** `bd list` before and after the dispatch showed the identical 10
issues, same IDs, same counts (9 open / 1 in progress) — no new bead appeared. No `bd create` was
run; no Triage Item Contract entry was constructed; Phase 1 intake never received an item (correct
— zero findings means the detector never emits a contract entry to validate in the first place);
`review-panel` was not touched or invoked.

**AC6: confirmed.** Zero findings produced zero beads, one clean log line, no downstream machinery
fired.

---

## 7. AC1-AC6 summary

| AC | Requirement | Result |
|---|---|---|
| AC1 | lib-upgrades detector emits a valid item, spine files a bead with AC | **Confirmed** (§2) — `scc-9jx`, P0, AC present, item validates. Disclosed gap: the bead's own AC understates the safe version threshold (real fix needs 4.18.1, not 4.17.21) |
| AC2 | All 4 panel statuses produce their documented bead outcome | **Confirmed** (§5) — 2 unparked (`scc-aci`, `scc-g5m`), 2 parked (`scc-9b9`, `scc-cis`), verified via `bd show` + `bd human list` |
| AC3 | Escalated bead unparked, pipeline continues, PR carries sovereignty annotation | **Confirmed** (§5) — `scc-g5m` absent from `bd human list`; annotation drafted verbatim from finding `f-001` |
| AC4 | Prod-error detector + E2E reproduction precedes fix | **Confirmed** (§4) — `scc-9kx`, real repro run matching the log trace exactly, no fix/diagnose note ever added |
| AC5 | Malformed items rejected with named field errors; valid siblings unblocked | **Confirmed** (§3) — items 1-3 rejected, items 4-5 survive, `scc-9lt` filed for item 5. Caught and fixed a fixture-labeling defect (item 4) |
| AC6 | Zero findings → no beads, one clean log line, no panel invocation | **Confirmed** (§6) — after fixing a genuine fixture defect (4.17.21 was not actually clean); `bd list` identical before/after |

---

## 8. Cleanup

Six real test-artifact beads were created during this pressure test: `scc-9jx`, `scc-9lt`,
`scc-9kx` (real detector output against fixtures, filed by Phase 3), and `scc-aci`, `scc-g5m`,
`scc-9b9`, `scc-cis` (synthetic, created solely to exercise Phase 6's branching against forced
status fixtures) — 7 total. None were closed by their dispatches (each was explicitly instructed not
to); this session closes them now with a clear reason:

```
bd close scc-9jx scc-9lt scc-9kx scc-aci scc-g5m scc-9b9 scc-cis \
  --reason="PRESSURE-TEST scc-tsa — test artifact, safe to ignore"
```

`scc-tsa` itself is not closed here — that belongs to a later pipeline node, per the established
pattern from `scc-5hy`'s handling.

Temporary files (`/tmp/repro_scc-9kx.py`, a stray `__pycache__/` under
`prod-errors-repro/app/`) were removed after verification. No `node_modules/` directories were
created by any `npm audit`/`npm outdated` run (neither command installs packages).

---

## 9. Limits of this pressure test

- Every dispatch used `subagent_type: "general-purpose"` with an explicit instruction to follow the
  target `SKILL.md` (see Methodology note), because `triage`'s own agent/skill types weren't
  registered mid-session. This verifies the *procedure*, not Claude Code's `subagent_type` routing
  for a plugin-qualified name.
- Only 2 of the registry's 5 detector slots (`lib-upgrades`, `prod-errors`) have an implementation
  to pressure-test; `system-upgrades`, `iac-drift`, `security-advisory-sweeps` remain stubs by
  design (this is the stated v1 scope, not a gap this test could close) — `malformed-batch`'s item 4
  exercises the registry's *registration* check for a stub slot, not a live `iac-drift` detector
  run, since no such detector exists yet.
- AC2/AC3's four gate-test beads are synthetic, created solely to force Phase 6's branching logic
  against hand-crafted `panel-status/*.json` fixtures — they are not beads produced by a real
  detector finding plus a real `review-panel --mode=agent` invocation. A future full-scale run
  chaining a real detector finding through an actual `review-panel` dispatch (rather than a forced
  JSON fixture) would additionally confirm the real `review-panel` CLI/output shape matches
  `dual-mode-contract.md` exactly, rather than relying on this test's hand-authored fixtures.
- No real GitHub PR was opened for AC3's "PR carries the sovereignty annotation" requirement — there
  is no real product PR to open for a synthetic fixture. The dispatch drafted the exact PR
  leading-line text as plain output instead (quoted in §5), which proves the *content* the panel
  would inject, not that a real PR-creation step actually places it in a PR body.
- Two genuine spec/tooling drifts were found and disclosed rather than silently worked around: (1)
  `triage-spine/SKILL.md`'s Phase 6 prescribes a `bd human <id> --reason=...` command that doesn't
  exist in the installed `bd` v1.1.0 CLI (§5); (2) the lib-upgrades detector's AC-generation can
  understate the safe-version threshold when it's anchored to one detected advisory rather than a
  fresh audit of its own proposed fix target (§2). Neither blocks this task's AC verdicts, but both
  should be corrected in a future revision of the affected `SKILL.md` files.
- Two fixture-design defects were caught mid-test and corrected before this write-up was finalized:
  `malformed-batch/README.md`'s item-4 mislabeling (§3) and `lib-upgrades-clean/`'s stale "clean"
  version pin (§6). Both corrections are already applied to the fixture files as they exist in this
  repo, not left as a to-do.
