# Test Results: scc-5hy (Phase 4 — variant-explorer plugin)

## Summary

`plugins/variant-explorer/` is a markdown-prompt plugin (a skill + two agent definitions), not
executable code — there is no `pytest`/`npm test` suite to run. Per this repo's "reproduce/validate
in as close to real conditions as possible" standard, validation here means: (1) seed concrete test
fixtures, (2) live-dispatch real `Agent` calls that exercise the actual described procedure end to
end, (3) run the plugin's own mechanical gates, (4) write up the results with fingerprints/evidence,
not just a pass/fail assertion. All four are done. **All 5 acceptance criteria: PASS.**

Full methodology, live-dispatch prompts, and per-axis judge output are in the permanent test
artifact this task also produced: `plugins/variant-explorer/tests/PRESSURE-TEST.md`. This file is
the pipeline-required summary; see that file for the complete write-up.

## Fixtures created

- `plugins/variant-explorer/tests/fixtures/palindrome-checker/{spec.md,ac.md}` — a small, concrete
  spec (`is_palindrome(s: str) -> bool`) with 5 testable AC, used for the main N=3-equivalent
  builder+judge dispatch.
- `plugins/variant-explorer/tests/fixtures/impossible-ac/{spec.md,ac.md}` — a single, deliberately
  unsatisfiable AC (a "pure" `paradox()` function that must return different values across two
  identical calls), used to force a genuine `blocked` builder result to validate AC4 without an
  artificial timeout.

## Live-dispatch validation

7 live `Agent` dispatches were run (methodology note: `variant-explorer:blind-builder` /
`variant-explorer:variant-judge` weren't yet registered as live `subagent_type`s mid-session, so
`subagent_type: "general-purpose"` was used with an explicit instruction to read and follow the
target `.md` file — the same substitution `review-panel/tests/PRESSURE-TEST.md` used for its own
pressure test; disclosed, not silent):

1. Blind-builder Variant A (`palindrome-checker`, angle: MVP-first) → `complete`
2. Blind-builder Variant B (`palindrome-checker`, angle: dependency-free) → `complete`
3. Blind-builder Variant C (`impossible-ac`, angle: MVP-first) → `blocked: paradox() is logically
   unsatisfiable for a pure, argument-free function` (worktree auto-removed — zero file changes)
4. AC-conformance judge → both A and B PASS all 5 AC; surfaced a real tooling-dependency asymmetry
   (A's tests require an ambient `pytest`; B's `unittest` suite is fully self-contained)
5. Simplicity judge (ponytail-review format) → A: "Lean already. Ship."; B: 4 findings, `net: -35
   lines possible.`
6. Taste judge, TASTE.md absent → both variants: `axis not applicable: no TASTE.md at repo root`
   (explicit, not silent)
7. Taste judge, TASTE.md present (fixture placed only in the two survivor worktrees, never at the
   real repo root) → A: clean; B: 1 Minor finding, quoting the fixture's `weak`-strength Preference
   clause verbatim against B's `Args:`/`Returns:` docstring (correct `weak` → `Minor` severity
   mapping per `TASTE-FORMAT.md`)

## Mechanical gates

- `python3 scripts/verify_plugin.py` → `OK: plugin manifests parse cleanly; versions match; hook
  file references exist` — exit 0 (covers `variant-explorer`'s `plugin.json`/`marketplace.json`
  version match generically, same gate scc-d0u fixed).
- `plugin.json` / `marketplace.json` — both valid JSON, name/version match (`variant-explorer`,
  `1.0.0`).
- `README.md` diff — Sub-plugins count correctly bumped 7→8 (both occurrences), new
  `### variant-explorer` section's Commands(1)/Agents(2)/Skills(1) tables match the filesystem
  exactly.

## AC1-AC5 results

| AC | Requirement | Result |
|---|---|---|
| AC1 | N=3 → 3 worktrees, 3 scorecards, ranked shortlist, each scorecard cites ≥1 AC item | **PASS** — 3 worktrees spawned; A and B produced full scorecards citing all 5 AC items each plus Simplicity/Taste findings, ranked A > B; C's blocked outcome is itself an accounted-for result, not a missing scorecard |
| AC2 | TASTE.md handling — present → clauses referenced; absent → axis omitted, explicitly | **PASS** — both branches live-dispatched: absent → explicit `axis not applicable` for both variants; present → verbatim-quoted clause + correctly severity-mapped Minor finding on B, clean on A |
| AC3 | Builder isolation — no builder prompt contains another variant's content | **PASS** — all 3 dispatch prompts inspected directly; each contains only its own fixture + one angle, no cross-references to siblings |
| AC4 | Error handling — failed builder reported as lost variant, run continues with survivors, N never silently reduced | **PASS** — Variant C's `blocked` status recorded with its reason; run proceeded to judge A/B; N=3, 1 lost, 2 survivors stated explicitly, never renumbered |
| AC5 | N=1 refuses with guidance; N>6 clamps with a note | **PASS** — confirmed by direct citation of `SKILL.md` lines 49-55 (both are pre-Phase-2 checks with mandatory explicit-reporting language, no dispatch needed since this is deterministic boundary logic) |

## Cleanup

Both survivor worktrees and their branches (`agent-aca69458ab1e667ba`, `agent-a0ac67197c4938b31`)
were removed after their contents were captured in `PRESSURE-TEST.md` — `git worktree remove` +
`git branch -d`, both clean (no unmerged-work warnings, since the agents wrote directly to the
worktree filesystem without committing). `git worktree list` / `git branch --list
"worktree-agent-*"` are now empty. No `TASTE.md` fixture was ever created at the real repo root
(confirmed absent both before and after) — the taste-axis presence test used copies placed only
inside the two ephemeral test worktrees.

## Git status at handoff

```
 M .claude-plugin/marketplace.json
 M .pas/current_task.md
 M .pas/investigation.md
 M .pas/logs/two-system-architecture-e64d8f93/checkpoint.json
 M README.md
?? plugins/variant-explorer/
```

`plugins/variant-explorer/` now includes the plugin itself (from the prior Implement step) plus
this step's additions: `tests/fixtures/palindrome-checker/`, `tests/fixtures/impossible-ac/`,
`tests/PRESSURE-TEST.md`. No worktree/branch residue. Per the conservative git profile, no commit
has been made — reporting status only.

No blocking issues. Ready for the Verify step.
