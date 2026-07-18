# Test Results: scc-tsa (Phase 5 — Triage spine plugin, System 2 v1, Foundry-resident)

## Summary

`plugins/triage/` is a markdown-prompt plugin (a triage-spine skill + two detector skills), not
executable code — there is no `pytest`/`npm test` suite to run. Validation here means: (1) seed
concrete test fixtures per acceptance criterion, (2) live-dispatch real `Agent` calls that exercise
the actual described procedure end to end with genuine side effects (`bd` mutations, real `npm
audit`/`npm outdated` runs, real Python reproduction), (3) independently re-verify every dispatch's
claimed side effect via direct `bd show`/`bd list`/`bd human list` rather than trusting self-reports,
(4) run the plugin's mechanical gates, (5) write up results with fingerprints/evidence. All five are
done. **All 6 acceptance criteria: PASS.**

Full methodology, fixture descriptions, and per-AC dispatch evidence are in the permanent test
artifact this task also produced: `plugins/triage/tests/PRESSURE-TEST.md`. This file is the
pipeline-required summary; see that file for the complete write-up.

## Fixtures created

- `plugins/triage/tests/fixtures/lib-upgrades-vulnerable/` — pins `lodash@4.17.11` (real,
  multi-advisory-flagged version) — AC1.
- `plugins/triage/tests/fixtures/lib-upgrades-clean/` — pins `lodash@4.18.1` (real current release,
  0 findings) — AC6. **Corrected mid-test:** originally pinned `4.17.21`, which real `npm audit`
  showed is *still* flagged under a newer advisory; fixed to the actual unaffected version before
  use.
- `plugins/triage/tests/fixtures/prod-errors-repro/` — a genuine null-guard bug (`checkout.py`) +
  matching `error.log` (3 identical traces that must collapse to 1 triage item, plus 1 distinct
  error) — AC4.
- `plugins/triage/tests/fixtures/malformed-batch/` — a 5-item batch exercising all 6 of Phase 1's
  ordered validation rules (3 real violations, 2 items that correctly survive) — AC5. **Corrected
  mid-test:** the README originally mislabeled item 4 as a violation; a live dispatch caught the
  error by re-deriving the rules independently, and the README was fixed.
- `plugins/triage/tests/fixtures/panel-status/` — 4 hand-crafted JSON fixtures matching
  `review-panel`'s `dual-mode-contract.md` schema, forcing each of `converged` / `escalated` /
  `circuit_broken` / `error` — AC2/AC3.

## Live-dispatch validation

4 live `Agent` dispatches were run (methodology note: no `triage:*` `subagent_type` was registered
mid-session, so `subagent_type: "general-purpose"` was used with an explicit instruction to read and
follow the target `SKILL.md` — the same substitution `variant-explorer`'s and `review-panel`'s own
pressure tests used; disclosed, not silent). Every dispatch's claimed `bd` mutation was
independently re-verified by this session via direct `bd show`/`bd list`/`bd human list` calls
after the dispatch completed.

1. **AC1** — lib-upgrades detector vs. `lib-upgrades-vulnerable/`: real `npm audit` flagged
   `lodash@4.17.11` (multiple advisories, critical). Filed `scc-9jx` (P0, AC present) — verified.
2. **AC5** — Phase 1 validation vs. `malformed-batch/batch.json`'s 5 items: items 1-3 rejected with
   named field errors; items 4-5 survive Phase 1; bead filed for item 5 (`scc-9lt`, P2) — verified.
   Caught a fixture-labeling error on item 4 (see PRESSURE-TEST.md §3).
3. **AC4** — prod-errors detector vs. `prod-errors-repro/`: 3 identical traces collapsed into 1 item
   (`scc-9kx`, P0); real reproduction script confirmed an exact match to the log trace; reproduction
   note recorded on the bead with no diagnose/fix note ever added (ordering constraint intact) —
   verified.
4. **AC2/AC3** — Phase 6 branching vs. all 4 `panel-status/*.json` fixtures: `converged` (`scc-aci`)
   and `escalated` (`scc-g5m`) both correctly unparked; `circuit_broken` (`scc-9b9`) and `error`
   (`scc-cis`) both correctly parked. `bd human list` returned exactly the 2 parked beads — verified.
   Escalated bead's sovereignty annotation sourced verbatim from the finding, not a bare status
   echo. Found a stale `bd human <id> --reason=...` command in `SKILL.md` that doesn't exist in the
   installed `bd` CLI; the real mechanism (`--add-label=human --notes=...`) was used and the drift
   disclosed.

AC6 (zero-findings boundary) was additionally verified via a 5th dispatch plus this session's own
direct `npm audit`/`npm outdated` execution against the corrected `lib-upgrades-clean/` fixture:
`found 0 vulnerabilities`, clean-log line emitted, `bd list` identical before/after (no bead filed).

## Mechanical gates

- `python3 scripts/verify_plugin.py` → `OK: plugin manifests parse cleanly; versions match; hook
  file references exist` — exit 0.
- `plugin.json` / `marketplace.json` — both valid, name/version match (`triage`, `1.0.0`).
- `README.md` diff — Sub-plugins count correctly bumped 8→9, new `### triage` section's 3-skill
  table matches the filesystem.

## AC1-AC6 results

| AC | Requirement | Result |
|---|---|---|
| AC1 | lib-upgrades detector emits a valid item, spine files a bead with AC | **PASS** — `scc-9jx`, P0, AC present, item validates. Disclosed gap: bead's own AC understates the real safe-version threshold (needs 4.18.1, not 4.17.21) |
| AC2 | All 4 panel statuses produce their documented bead outcome | **PASS** — 2 unparked, 2 parked, verified via `bd show` + `bd human list` |
| AC3 | Escalated bead unparked, pipeline continues, PR carries sovereignty annotation | **PASS** — `scc-g5m` never parked; annotation drafted verbatim from the finding |
| AC4 | Prod-error detector + E2E reproduction precedes fix | **PASS** — `scc-9kx`, real repro matching the log exactly, no fix/diagnose note ever added |
| AC5 | Malformed items rejected with named field errors; valid siblings unblocked | **PASS** — items 1-3 rejected, items 4-5 survive, bead filed for item 5 |
| AC6 | Zero findings → no beads, one clean log line, no panel invocation | **PASS** — after fixing a genuine fixture defect; `bd list` identical before/after |

## Cleanup

7 real test-artifact beads were created during this pressure test (`scc-9jx`, `scc-9lt`, `scc-9kx`
from real detector runs against fixtures; `scc-aci`, `scc-g5m`, `scc-9b9`, `scc-cis` synthetic, for
Phase 6 branching only). None were closed by their dispatches (instructed not to); all 7 were closed
by this session with `bd close scc-9jx scc-9lt scc-9kx scc-aci scc-g5m scc-9b9 scc-cis
--reason="PRESSURE-TEST scc-tsa — test artifact, safe to ignore"`. `scc-tsa` itself remains
`in_progress`, untouched — closing it belongs to a later pipeline node, per the established pattern
from `scc-5hy`. Temporary files (`/tmp/repro_scc-9kx.py`, a stray `__pycache__/`) were removed.
`bd list` now shows the same 3 pre-existing issues (`scc-hzj`, `scc-tsa`, `scc-6lj`) as before this
pressure test began.

## Git status at handoff

```
 M .claude-plugin/marketplace.json
 M .pas/current_task.md
 M .pas/investigation.md
 M .pas/logs/two-system-architecture-e64d8f93/checkpoint.json
 M README.md
?? plugins/triage/
```

`plugins/triage/` includes the plugin itself (from the prior Implement step) plus this step's
additions: `tests/fixtures/{lib-upgrades-vulnerable,lib-upgrades-clean,prod-errors-repro,
malformed-batch,panel-status}/`, `tests/PRESSURE-TEST.md`. No beads/worktree residue. Per the
conservative git profile, no commit has been made — reporting status only.

No blocking issues. Ready for the Verify step.
