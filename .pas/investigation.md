# Investigation: scc-d0u — Verification & tooling gates (all phases)

## Task nature

This is a **standing/retroactive gate**, not new feature work. Phases 1a–3d (10 sub-phases)
are already merged without this gate having been actively applied. The concrete work is: audit
those 10 sub-phases against the four ACs now, fix the real gaps found, and leave tooling in a
state where Phase 4/5 (not yet built) can be gated automatically going forward.

Baseline run of the three commands cited in the task, before any changes:

```
$ uv run python3 scripts/verify_plugin.py
OK: plugin manifests parse cleanly; versions match; hook file references exist: ...

$ uv run pytest
collected 0 items  (no test_*.py / *_test.py anywhere in the repo outside .venv)

$ uv run ruff check --fix
All checks passed!
```

All three look "clean," but that's misleading for two of them — see AC1 and AC3 below.

---

## AC1 — `scripts/verify_plugin.py` runs clean

**Current behavior:** `scripts/verify_plugin.py` (repo root `scripts/`) hardcodes exactly one
comparison: `.claude-plugin/plugin.json`'s `version` (the root `scott-cc` plugin) against
`marketplace.json.plugins[0].version` (also `scott-cc`, guaranteed index 0). It never looks at
any other entry in `marketplace.json.plugins[]`, so it cannot detect a version mismatch for any
of the 7 sub-plugins (`security-suite`, `browser-automation`, `research-tools`,
`performance-optimization`, `mutation-testing`, `beads-epic-builder`, `review-panel`).

**This is a real, confirmed gap.** The task's own motivating anecdote — commit `748dff1`
("fix(marketplace): sync review-panel catalog version to 0.2.0") — was exactly a sub-plugin
version desync (`review-panel/plugin.json` said `0.2.0`, `marketplace.json`'s `review-panel`
entry still said `0.1.0`). `verify_plugin.py` predates that bug but **would not have caught it**
because it only checks index 0. It currently reports "OK" while blind to the exact class of bug
it exists to prevent.

**Secondary defect found while tracing this:** every sub-plugin manifest in this repo lives at
`plugins/<name>/.claude-plugin/plugin.json` (confirmed for `beads-epic-builder`,
`browser-automation`, `mutation-testing`, `performance-optimization`, `research-tools`,
`security-suite` — this is also the convention documented in `PUBLISHING.md:144-178`). **`review-panel` is the sole outlier**: its manifest sits at `plugins/review-panel/plugin.json`,
one level up from where every sibling puts it (added in `6e48699`, review-panel's first commit,
and never corrected). Its current version (`0.2.1`) does happen to match `marketplace.json`'s
review-panel entry (`0.2.1`) right now, so there's no live break today, but it's the plugin with
the most active development in this whole epic (10 merged phases, 2 more to come) — the highest-risk
candidate for a repeat of `748dff1`, and a generic multi-plugin check (below) can't treat it
uniformly without this fixed first.

**Files to modify:**
- `plugins/review-panel/plugin.json` → move to `plugins/review-panel/.claude-plugin/plugin.json`
  (git mv, content unchanged). No other file references the old path (checked: no hits in
  `*.md`/`*.json`/`*.py`/`*.sh`), so this is a safe, isolated move.
- `scripts/verify_plugin.py` → extend `main()` to iterate every entry in
  `marketplace.json.plugins[]`, resolve `<repo_root>/<source>/.claude-plugin/plugin.json` (skip
  the root entry, `source: "./"`, which is already handled by the existing check), and compare
  each plugin.json's `name`/`version` against its marketplace entry. Missing plugin.json should
  `fail()` with a clear message (same pattern the script already uses), not be silently skipped —
  consistent with this epic's Coverage Honesty invariant.

**Risk:** low. The plugin.json move has no other referrers. The verify_plugin.py extension is
additive to an already-passing check; test by deliberately desyncing a version locally and
confirming the script now fails before reverting.

---

## AC2 — Fixture per phase (PRESSURE-TEST.md pattern: seeded defect → expected finding)

Checked `git show --name-status` for all 10 phase-labeled commits (not just current working-tree
state, since some steps added fixtures under a different commit than the "Phase X" commit message):

| Phase | Commit | Fixture added? |
|---|---|---|
| 1a security seat | `eb5ee33` | added `review-panel/tests/fixtures/auth-token-service/` (4 seeded vulns) |
| 1b plan-security-review | `b5cf582` | added `security-suite/tests/fixtures/plan-security-review/{auth-login-plan,ui-copy-change-plan}.md` |
| 2a DATA-MODEL.md format | `3c843b6` | added `review-panel/tests/fixtures/orders-schema/` |
| 2b grill-the-schema skill | `da9e54d` | none — reuses 2a's `orders-schema` fixture as interview input |
| 2c data-steward seat | `eabbf50` | added `no-data-model-inventory/` + `orders-schema/app/diff.patch` |
| 2d data-layer-guard hook | `662110c` | **none** |
| 3a TASTE-FORMAT.md spec | `3a24056` | none at definition time (later covered by 3d's fixtures) |
| 3b grill-my-taste skill | `dbdcf54` | none — interview skill, no diff to seed |
| 3c taste feedback loop | `070d40d` | none — enhancement to 3b |
| 3d taste-review seat | `72d50da` | added `taste-preferences/`, `taste-malformed/`, `no-taste-file/` |

**Reading the gaps:** `PRESSURE-TEST.md:5-11` itself states review-panel skills are "not
executable code" — a markdown prompt set driving a Claude subagent loop, not something a
seeded-defect diff can be run against automatically. That legitimately explains 2b/3b/3c (pure
grilling/interview skills — no diff exists to seed a defect into) and softens 3a (a doc-format
spec, later exercised end-to-end by 3d's `TASTE.md` fixtures). None of those four need a new
fixture retroactively; they're consistent with the plugin's own documented nature, and it would
be process-theater to force a "seeded defect" fixture onto an interview skill that has none.

**2d is different and is a real gap.** `hooks/data_layer_guard.py` is 171 lines of plain,
importable-shape Python (`find_repo_root`, `load_globs`, `matches_glob`, `matches_data_layer`,
`has_todays_change_log_entry`, `main`) reading a JSON payload on stdin and writing a JSON
permission decision (or nothing) on stdout — this is exactly the shape `uv run pytest` is meant
to cover, and it currently has **zero** test coverage of any kind. This is the one place where
AC2 and AC3 are both failing for the same reason.

**Files to modify:**
- New: `hooks/tests/test_data_layer_guard.py` (repo has no existing hooks test directory;
  colocating under `hooks/tests/` mirrors `plugins/review-panel/tests/` and keeps the hook and
  its coverage next to each other). Invoke the hook as a subprocess (`python3
  hooks/data_layer_guard.py` with JSON on stdin) rather than importing it, since `hooks/` isn't a
  package and subprocess invocation is what actually exercises the real Claude Code contract
  (stdin JSON in, stdout JSON/exit-code out) — the same black-box, "seeded defect → expected
  finding" spirit as the markdown fixtures, just pytest-automated because this artifact actually
  is code.
- Minimum cases to cover (each is a "seeded defect" in the sense of a constructed repo-root
  fixture under `tmp_path`, git-initialized so `find_repo_root` resolves):
  1. Non-`Edit`/`Write`/`NotebookEdit` `tool_name` → silent no-op.
  2. `permission_mode: "bypassPermissions"` on a matching path → silent no-op (unattended
     deference to data-steward, per the hook's own docstring).
  3. Edit to a `migrations/`-glob path with no `DATA-MODEL.md` at all → `ask` decision with the
     glob pattern and reason in `permissionDecisionReason`.
  4. Same, but `DATA-MODEL.md` has a `## Change log` entry dated today → silent no-op.
  5. Edit to a path that matches no default glob → silent no-op.
  6. `.data-guard.json` override present → hook uses the override globs, not `DEFAULT_GLOBS`.

**Risk:** low — pure functions, no network/filesystem side effects beyond reading the two files
the test fixtures construct in `tmp_path`.

---

## AC3 — `uv run pytest` and `uv run ruff check --fix` gate every phase

**Current behavior:** both commands currently pass, but `pytest` passing is vacuous — it
collects 0 items because there are no `test_*.py`/`*_test.py` files anywhere in the repo (only
`.venv`'s vendored ones, which pytest correctly ignores). `ruff check --fix` passing is genuine
(it lints the 3 real Python files under `hooks/`, plus `scripts/verify_plugin.py`).

**Required change:** none beyond what AC2 already prescribes (the new `hooks/tests/` file gives
`pytest` something real to run). No repo config changes needed — `pyproject.toml` has no
`[tool.pytest.ini_options]` section and doesn't need one; default rootdir-based discovery already
finds `hooks/tests/test_data_layer_guard.py` once it exists (pytest already reports
`configfile: pyproject.toml` and searches from repo root).

**Risk:** none — additive only.

---

## AC4 — README.md / marketplace catalog counts in sync

**This is the largest, clearest gap found.** `README.md`'s "Sub-plugins" section (`README.md:20`,
`README.md:136-247`) enumerates exactly 6 sub-plugins: `beads-epic-builder`,
`browser-automation`, `research-tools`, `security-suite`, `performance-optimization`,
`mutation-testing`. **`review-panel` is not mentioned anywhere in `README.md`** — not in the "At
a Glance" table, not as its own `###` subsection — despite being the 7th entry in
`marketplace.json.plugins[]` and having received 10 merged phases of active development
(`review-panel` was added in `6e48699`, before this epic started, and was apparently never added
to the README even then). Every one of the 10 completed sub-phases in this epic added a skill (or
in 2d's case, a root-level hook, which *is* correctly counted in `README.md:18/113-120`) to
`review-panel` without ever touching `README.md` — this task's AC4 has been silently failing
since Phase 1a.

Actual current review-panel contents (counted directly, not from any doc):
- **Skills: 29** — `abstraction-quality, adr-skill, adversarial-reviewer, code-evolution,
  comments-docs, complexity-recognition, data-steward, deep-modules, design-it-twice,
  design-review, diagnose, domain-modeling, error-design, general-vs-special, grill-my-taste,
  grill-the-schema, grill-with-docs, improve-codebase-architecture, information-hiding,
  module-boundaries, naming-obviousness, ponytail-audit, ponytail-review, pull-complexity-down,
  red-flags, review-panel, strategic-mindset, taste-review, tdd`
- **Commands: 1** — `/review-panel` (`plugins/review-panel/commands/review-panel.md`)
- **Agents: 1** — `clean-room-alternative` (`plugins/review-panel/agents/clean-room-alternative.md`)
- Reference-only, not counted as skills/commands/agents: `reviewers/persona-catalog.md`,
  `formats/{ADR,CONTEXT,DATA-MODEL,TASTE}-FORMAT.md`, `contracts/*.md`, `scripts/{review-package,workspace}`

Secondary, lower-priority inconsistency: every other sub-plugin's `marketplace.json` description
includes a parenthetical count (e.g. `"...(2 agents, 2 skills)"`); `review-panel`'s description
does not. Given how fast review-panel's skill count is moving (29 already, Phase 4/5 still to
come), baking a count into that one-line description is exactly the kind of value that goes stale
every phase — same failure mode as the version field. Recommend leaving the marketplace
description as-is and only fixing `README.md`, where the counts already live in one canonical,
structured table per plugin.

**Files to modify:**
- `README.md`:
  - `README.md:20` — `Sub-plugins | 6 | ...` → `7`, add `review-panel` to the name list.
  - Add a new `### review-panel` subsection after `### mutation-testing` (README.md:229-247),
    following the exact structure every other sub-plugin subsection uses (one-line description,
    `**Agents (1)**` table, `**Skills (29)**` table). 29 skills likely need thematic
    sub-groupings (e.g. "Review Seats", "Grilling/Interview", "Reference Skills") to stay readable
    rather than one 29-row table — this is an editorial call, not a mechanical one.
  - `README.md:1` — intro line already covers this loosely via "and more"; no change strictly
    required, but consider naming review-panel given it's the largest sub-plugin.

**Risk:** low — pure documentation. Main effort is deciding how to sub-group 29 skills readably,
not correctness risk.

---

## Cross-cutting note for Phase 4 / Phase 5

Phases 4 (`scc-5hy`, variant-explorer) and 5 (`scc-tsa`, triage) are not yet built, so there's
nothing to retroactively audit for them. Once `scripts/verify_plugin.py` is extended (AC1) to
walk every `marketplace.json` entry generically, both new plugins get version-sync coverage for
free the moment their `.claude-plugin/plugin.json` + marketplace entries exist, provided their
implementers follow the `.claude-plugin/plugin.json` convention (not review-panel's original,
now-corrected, outlier layout). Their README/catalog-count updates (AC4) and fixtures (AC2) still
need to happen as part of those phases' own implementation work — this task doesn't need to
pre-create anything for them.

## Summary of concrete changes for this task

1. `git mv plugins/review-panel/plugin.json plugins/review-panel/.claude-plugin/plugin.json`
2. Extend `scripts/verify_plugin.py` to check every `marketplace.json.plugins[]` entry's
   `.claude-plugin/plugin.json` version, not just index 0.
3. Add `hooks/tests/test_data_layer_guard.py` covering the 6 cases listed under AC2.
4. Update `README.md`: bump Sub-plugins count 6→7, add a `### review-panel` section with
   accurate Agents(1)/Commands(1)/Skills(29) tables.
5. Re-run `uv run python3 scripts/verify_plugin.py`, `uv run pytest`, `uv run ruff check --fix`
   after each change and confirm all three stay clean, with pytest now collecting >0 items.
