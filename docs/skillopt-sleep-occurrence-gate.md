# SkillOpt-Sleep: minimum occurrence-count gate (scc-ncs.16)

## Why

Nothing previously stopped a learned preference from being proposed for
permanent adoption based on a single extreme session. This gate requires a
candidate edit's training failures to span at least 3 independent session
transcripts before it is proposed, reducing overfitting to one-off events.

## Where the implementation lives

This repo (`scott-cc`) has no editable SkillOpt-Sleep engine source — only the
output artifact `skills/skillopt-sleep-learned/SKILL.md`, which is written by
the engine, not part of it. The `skillopt-sleep` plugin's marketplace entry
points at a live directory, not a vendored copy:

```json
{"source": "directory", "path": "<local SkillOpt clone>/plugins/claude-code"}
```

The actual engine lives in the separate
[`microsoft/SkillOpt`](https://github.com/microsoft/SkillOpt) repo (remote: `microsoft/SkillOpt`,
branch `main`). The occurrence-count gate was implemented there, since that is
the only place the mechanism can be real, enforced, and tested. That change is
a legitimate, self-contained contribution to that project and is intentionally
**not** committed as part of this repo's history — see "Status" below.

## Gate mechanism (implemented in SkillOpt)

- `skillopt_sleep/types.py`: `EditRecord` gained `occurrences: int = 1` and
  `source_sessions: List[str]`; `SleepReport` gained
  `monitoring_edits: List[EditRecord]`.
- `skillopt_sleep/consolidate.py`: added `MIN_OCCURRENCES = 3`,
  `_distinct_sessions()`, and an `_occurrence_filter()` closure wired into
  every `reflect()`/`contrastive_reflect()` call site. Candidate edits backed
  by fewer than `min_occurrences` distinct sessions (falls back to `task.id`
  when a task has no `source_sessions`) are diverted into
  `ConsolidationResult.monitoring_edits` and never reach the held-out score
  gate or `applied_edits`/`rejected_edits`.
- `skillopt_sleep/dream.py`, `config.py`, `__main__.py`: `min_occurrences`
  threaded through `dream_consolidate()`, defaulted to `3` in `DEFAULTS`, and
  exposed as `--min-occurrences` on the CLI.
- `skillopt_sleep/cycle.py`: the rendered `report.md` now shows the
  `occurrences` count on every accepted edit, and a new "Insufficient
  occurrences, monitoring (need N+ distinct sessions)" section lists withheld
  edits with their occurrence count and source session IDs.

## Acceptance criteria mapping

| # | Criterion | Where enforced |
|---|-----------|----------------|
| 1 | Requires >= 3 independent sessions before proposal | `consolidate.py::_occurrence_filter` gates on `MIN_OCCURRENCES` (default 3) before any edit reaches `_gate_apply` |
| 2 | <3-session candidates not surfaced in the proposal batch | such edits land in `monitoring_edits`, kept out of `applied_edits`/`rejected_edits`, and out of the "Accepted edits" section of `report.md` |
| 3 | Occurrence count visible in the proposal | `EditRecord.occurrences`/`.source_sessions` populated on every edit; shown on both accepted and monitoring lines in `report.md` |

Tests: `tests/test_sleep_engine.py::TestOccurrenceGate` (new — covers
withholding, the 3-session boundary, occurrence/session visibility, and the
configurable override) plus fixture updates to `TestVerifierDiscipline`
(explicit `min_occurrences=1`, since those fixtures deliberately use a single
synthetic train task to isolate the held-out score gate from this new gate).
Full suite: `python3.12 -m unittest tests.test_sleep_engine tests.test_run_sleep_fallback`
— 81 tests, 2 skipped (env-dependent), 0 failures.

## Status

- SkillOpt-side implementation described here was verified only in an **uncommitted local working
  tree** and is not shipped by scott-cc or available from the linked upstream repository. Treat
  this document as a historical design/work log, not release evidence.
- This doc is the scott-cc-side record of scc-ncs.16 for this worktree/branch.
