# SkillOpt-Sleep: periodic full re-derivation pass (scc-ncs.23)

## Why

Every ordinary night only *patches* the current "Learned preferences &
procedures" block: bounded add/delete/replace edits against its existing
lines. That's deliberately conservative, but it means the block only ever
grows by local, one-at-a-time diffs — nothing ever re-examines it as a whole.
Individually-reasonable overrides adopted months apart can end up
contradicting each other, and dead guidance (superseded by a later entry, or
about a workflow that no longer exists) never gets pruned, because no single
incremental edit's job is to notice that. This adds the other half: a periodic
trigger that rebuilds the WHOLE block from the complete task corpus, so stale
or contradictory bullets get a chance to be dropped instead of piling up
forever.

## Where the implementation lives

Same split as scc-ncs.16: this repo (`scott-cc`) has no editable SkillOpt-Sleep
engine source — only the output artifact
`skills/skillopt-sleep-learned/SKILL.md`, written by the engine, not part of
it. The actual engine lives in the separate repo
[`microsoft/SkillOpt`](https://github.com/microsoft/SkillOpt) (remote: `microsoft/SkillOpt`,
branch `main`). The full re-derivation pass was implemented there, since that
is the only place the mechanism can be real, enforced, and tested. That change
is a legitimate, self-contained contribution to that project and is
intentionally **not** committed as part of this repo's history — see "Status"
below.

## Mechanism (implemented in SkillOpt)

- `skillopt_sleep/config.py`: new `full_rederive_every` default (`10`). Once
  this many memory edits have been *adopted* since the last full rebuild, the
  next night's memory proposal fully rebuilds the block instead of
  incrementally appending. `0`/unset disables it (pure append-only, prior
  behavior).
- `skillopt_sleep/state.py`: `SleepState` gained a durable
  `adopted_pref_count` counter (`bump_adopted_prefs()`,
  `reset_adopted_prefs()`), plus a new shared helper
  `note_adopted_prefs(state, staging_dir)` that reads `manifest.json` after an
  ACTUAL adoption and bumps (incremental) or resets (full rebuild) the
  counter. It is a no-op if the manifest is missing/unreadable or if the
  adoption didn't touch memory at all (e.g. a skill-only adoption).
- `skillopt_sleep/rederive.py` (new module): `should_full_rederive(count,
  every)` is the pure trigger check. `build_full_rederivation(...)` asks the
  backend to reflect over the **complete real-task corpus** (this project's
  task archive plus tonight's tasks, filtered to `origin == "real"` —
  synthetic dream/recall tasks never singlehandedly justify a permanent rule)
  and rebuilds the block from an **empty base**, not from
  `current_learned_lines`. The existing block's content is stripped out of the
  memory context passed to the backend's `reflect()` before calling it —
  otherwise the backend's own "don't re-propose what's already in context"
  behavior would silently turn re-derivation into a no-op for anything already
  adopted.
- `skillopt_sleep/cycle.py`: when the trigger fires, tonight's candidate
  memory document is replaced by the full-rederivation candidate *before*
  staging. The candidate is still scored against the held-out validation
  split for report transparency, but a full rebuild is allowed to stage even
  if it doesn't beat tonight's tiny val slice — its purpose is corpus-wide
  consistency, not a local-edit win. This is surfaced via a distinct
  `report.gate_action` value, `full_rederive_proposed`, rather than
  `accept`/`reject`, so a human reviewing `report.md` can immediately see
  it's a full rebuild and not an incremental patch.
- `skillopt_sleep/staging.py`: `write_staging()` records `full_rederivation:
  bool` in `manifest.json` — for `note_adopted_prefs` to read back later,
  never acted on by `write_staging`/`adopt()` themselves.
- `skillopt_sleep/__main__.py`: new `--full-rederive-every N` CLI flag; the
  `adopt` subcommand (the DEFAULT approval path, since `auto_adopt=False` by
  default) now also calls `note_adopted_prefs`, so the counter advances under
  normal manual-approval usage, not only under `--auto-adopt`.

## How this re-enters the existing propose/validate/adopt gate

Full re-derivation is **not** a separate adoption path. It produces exactly
the same shape of output as an incremental night — a candidate memory
document — and goes through the identical pipeline:

```
candidate memory doc -> held-out score gate (reported, not blocking) ->
    staging.write_staging() -> (nothing happens until) -> staging.adopt()
```

It never writes to the live `CLAUDE.md` directly, never bypasses staging, and
never auto-adopts unless the user has separately opted into `--auto-adopt`
(the same opt-in that governs every other night). The only difference from an
incremental night is *what* candidate gets staged and the `gate_action` label
used to report it.

## How rejection preserves the prior block

"Rejecting" a staged proposal means simply never running `adopt` (CLI or
auto-adopt) against that staging directory. Because:

- the live `CLAUDE.md` is only ever touched inside `staging.adopt()` (backs up
  then copies proposed files over live ones), and
- `adopted_pref_count` is only ever bumped/reset inside `note_adopted_prefs`,
  called only from the two real adopt call sites, immediately after
  `staging.adopt()` has actually run,

a rejected full-rederivation proposal leaves both the previously-adopted
block and the counter completely untouched. The same re-derivation condition
will simply be evaluated again next night (the counter never advanced), so
nothing is silently lost or considered "handled" by a rejection.

## Acceptance criteria mapping

| # | Criterion | Where enforced |
|---|-----------|----------------|
| 1 | Defined trigger (e.g. every N adopted preferences) regenerates the FULL block from the complete corpus, not just appends | `state.adopted_pref_count` + `cfg.full_rederive_every`, checked via `rederive.should_full_rederive()` in `cycle.py`; `rederive.build_full_rederivation()` rebuilds from the complete real-task corpus starting at an empty base |
| 2 | Regenerated block routed through propose-offline/validate/adopt-only-after-approval gate, not auto-committed | Same `write_staging()`/`adopt()` pipeline as every other night; `gate_action = "full_rederive_proposed"` labels it in `report.md` without changing the staging/adoption mechanics; requires the same explicit `adopt` (or already-opted-in `--auto-adopt`) |
| 3 | User rejects re-derived block -> previously adopted block unchanged | Live file and `adopted_pref_count` are mutated only inside `note_adopted_prefs`, called only after an actual `staging.adopt()` run; never calling `adopt` leaves both byte-for-byte/value-for-value unchanged |

Tests: `tests/test_sleep_engine.py::TestFullRederivation` (new — 14 tests
covering the trigger boundary, corpus-vs-stale-line rebuilding, dream-task
exclusion, the reflect-context-stripping fix, end-to-end staging with
`gate_action == "full_rederive_proposed"`, the below-threshold non-trigger
case, adopt-via-auto-adopt resetting the counter, adopt-via-CLI bumping the
counter, and — directly proving acceptance criterion 3 — that never adopting
a staged full-rederivation proposal leaves both the live file and the counter
unchanged). Full suite:
`python3.12 -m unittest tests.test_sleep_engine tests.test_run_sleep_fallback`
— 95 tests, 2 skipped (env-dependent, pre-existing), 0 failures (81 baseline +
14 new).

## Status

- SkillOpt-side implementation described here was verified only in an **uncommitted local working
  tree** and is not shipped by scott-cc or available from the linked upstream repository. Treat
  this document as a historical design/work log, not release evidence.
- This doc is the scott-cc-side record of scc-ncs.23 for this worktree/branch.
