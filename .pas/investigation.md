# Investigation: scc-5hy — Phase 4: variant-explorer plugin (parallel blind-builder exploration)

## Task nature

This is **greenfield plugin creation**, not a modification of existing code.
`plugins/variant-explorer/` does not exist anywhere in the repo (confirmed: no matches for
`variant-explorer` outside `.pas/current_task.md`, the epic spec doc, and beads). Every file this
task needs is new; the only *existing* files that need touching are the three cross-cutting
registration points every prior sub-plugin phase has had to update (`marketplace.json`,
`scripts/verify_plugin.py`'s conventions — no code change needed there, just compliance —
`README.md`).

All five of scc-5hy's dependencies (scc-cnx, scc-3x5, scc-da0, scc-4tt — Phase 3a–3d) are closed.
The immediately preceding task, scc-d0u, retroactively fixed the plugin-registration gate
(`scripts/verify_plugin.py` now walks *every* `marketplace.json.plugins[]` entry generically, not
just index 0) and fixed `README.md`'s Sub-plugins count/section coverage — both directly relevant
here, since this task adds the 8th sub-plugin and must not repeat the gaps scc-d0u just closed.

---

## Current behavior (the substrate this plugin builds on)

Nothing in the repo currently does parallel blind-variant exploration. The task's design brief
explicitly models three pieces of prior art, all confirmed by direct reading:

1. **Isolation contract** — `plugins/review-panel/skills/design-it-twice/SKILL.md`'s "Isolation
   Mode" (lines 60-84) and its `agents/clean-room-alternative.md` (frontmatter `tools: Read, Grep,
   Glob`, `model: opus`): a dispatched agent gets the problem statement and codebase access only —
   never the first design, never conversation history, never a hint about approaches to avoid. This
   is read-only and produces one design doc; it does not write code and does not use worktrees
   (design-it-twice compares two *designs*, not two *implementations*).

2. **Worktree dispatch mechanics** — `plugins/beads-epic-builder/commands/epic-swarm.md`: spawns
   workers via the `Task`/`Agent` tool with **`isolation: "worktree"`** (a first-class parameter of
   this session's own `Agent` tool, confirmed directly from the tool's schema description: *"With
   isolation: 'worktree', the worktree is automatically cleaned up if the agent makes no changes;
   otherwise the path and branch are returned in the result."*). epic-swarm layers a checkpoint-file
   (`.claude/epic-swarm/<epic-id>/`, root-`.gitignore`d) on top of this for resumability across a
   long multi-wave epic, and reports failures as an explicit `tasks_failed: [{"id","reason"}]` list
   — never silently shrinking the task count.

3. **TASTE.md-conditional judging** — `plugins/review-panel/formats/TASTE-FORMAT.md` already
   contains a **binding, pre-existing spec commitment** (not a new decision this task gets to make):
   *"No TASTE.md file: the taste review seat never casts (no generic fallback), and Phase 4 variant
   scoring omits the taste axis. Both report the gap explicitly per Coverage Honesty rather than
   silently skipping."* `plugins/review-panel/skills/taste-review/SKILL.md` is the seat that
   implements this file-existence gate today (cast-when: `TASTE.md` exists at repo root; if absent,
   stop and report no taste axis — no partial casting). `plugins/review-panel/skills/ponytail-review/
   SKILL.md` is the simplicity lens the judge panel must reuse (format: `L<line>: <tag> <what>.
   <replacement>.`, ending `net: -<N> lines possible.` or `Lean already. Ship.`).

4. **CAST/SPAWN dispatch shape** —
   `plugins/review-panel/skills/review-panel/references/cast-and-spawn.md`: bounded-parallel `Task`
   dispatch (≤5 concurrent per batch), each seat given a *path* to shared artifacts rather than
   inline content, read-only tools unless a seat's own SKILL.md grants more, every seat's raw output
   collected with provenance tagging, a seat that errors is "a coverage gap, not silently dropped."
   This is the direct structural model for variant-explorer's judge panel (N variants scored by
   independent judges who, unlike the builders, *do* get to see all N variants).

5. **`skills/acceptance-criteria/SKILL.md`** (root `scott-cc` plugin, not review-panel) — the
   Gherkin/checklist/rules-based AC generator with a testability gate. This is what variant-explorer
   invokes "if AC absent," referenced across a plugin boundary the same way review-panel's own
   SPAWN references skills/agents outside itself.

**Plugin registration convention** (confirmed via `security-suite`, `beads-epic-builder`, etc., and
the scc-d0u fix): every sub-plugin lives at `plugins/<name>/.claude-plugin/plugin.json`
(name/description/version/author/license/repository/homepage), gets one entry in root
`.claude-plugin/marketplace.json` (name/source/description/version/author/tags matching the
sub-plugin's own manifest), and one `### <name>` section in root `README.md` (one-line description
+ `**Agents (N)**`/`**Commands (N)**`/`**Skills (N)**` tables), plus a bump to the "Sub-plugins"
count in the `## At a Glance` table. `scripts/verify_plugin.py` (post scc-d0u) already generically
enforces the marketplace/plugin.json name+version match for every entry — no script change needed,
just conformance to the path convention.

---

## Required changes

### New files

- **`plugins/variant-explorer/.claude-plugin/plugin.json`** — manifest, same shape as
  `security-suite`'s (name, description, version `1.0.0`, author `{"name": "Scott Nixon"}`, license
  MIT, repository/homepage URLs pointing at `plugins/variant-explorer`).

- **`plugins/variant-explorer/skills/explore-variants/SKILL.md`** — the core deliverable. Procedure,
  mapped directly to the five ACs:
  - **Phase 1 — Gather input & validate N (AC5).** Accept spec/design question, AC (dispatch
    `acceptance-criteria` skill if absent), and N (default 3). **N=1 refuses** with guidance to just
    build directly (no exploration value in a single variant) rather than running a degenerate
    1-worktree "panel." **N>6 clamps to 6** with an explicit note in the output — never silently
    proceeds with the user's original N unclamped, never silently proceeds with N=1 unrefused.
  - **Phase 2 — Spawn N blind builders (AC1, AC3).** Dispatch N `Agent` calls with
    `isolation: "worktree"`, each running a new `variant-explorer:blind-builder` agent (new file,
    below). Each dispatch prompt contains **only**: the spec + AC text (or file path) and one
    distinct angle instruction (MVP-first / data-model-first / dependency-free, or others as the
    spec suggests) — explicitly never another variant's angle, output, or existence, and never the
    orchestrator's own preferences. This is the direct extension of design-it-twice's Isolation Mode
    from "one alternative design doc" to "one alternative implementation in its own worktree." AC3's
    verifiability ("no builder prompt contains another variant's content, verifiable from dispatch
    logs") is satisfied structurally, the same way review-panel's PRESSURE-TEST.md verifies
    markdown-prompt skills: by a human or `--mode=agent` harness inspecting the actual dispatch
    prompts in the transcript — no new logging infrastructure is required, since `Agent`/`Task`
    dispatch prompts are already visible in the session transcript.
  - **Phase 3 — Collect results, handling failures explicitly (AC4).** A builder dispatch that
    errors, times out, or returns "could not complete" is recorded as a **lost variant** with a
    reason (mirrors epic-swarm's `tasks_failed: [{"id","reason"}]` shape) — the run continues with
    the survivors, and the final report always states the original N, the lost count/reasons, and
    the surviving count — N is never silently reduced/renumbered as if the run had only ever asked
    for the smaller number.
  - **Phase 4 — Judge panel (AC2).** Dispatch independent judges — modeled on CAST/SPAWN's
    bounded-parallel, read-only-unless-noted pattern — each judge given the N surviving worktree
    paths (not inline content) plus the spec/AC:
    - **AC-conformance judge** (native to this plugin, no cross-plugin dependency): checks each
      variant against every AC item, citing which item(s) it satisfies/fails.
    - **Taste judge**: dispatches `review-panel`'s `skills/taste-review/SKILL.md` instructions
      against each variant's diff, **only if `TASTE.md` exists at the repo root** — this is not a
      new decision, it's `TASTE-FORMAT.md`'s existing binding commitment (see Current Behavior #3
      above). If absent, every scorecard **omits the taste axis and says so explicitly** — Coverage
      Honesty, not silent omission.
    - **Simplicity judge**: dispatches `review-panel`'s `skills/ponytail-review/SKILL.md` lens
      against each variant, reusing its exact `L<line>: <tag> <what>. <replacement>.` output shape.
    Each judge scores every surviving variant along its one axis; the skill then assembles the
    combined **ranked shortlist**, one scorecard per variant, each citing ≥1 AC item by ID (AC1's
    concrete pass bar) and, when applicable, the taste clause text verbatim (AC2's concrete pass
    bar, matching `taste-review`'s own "quote the clause, not a paraphrase" rule).
  - **Phase 5 — Human pick & cleanup.** Present the ranked shortlist; the human picks a winner.
    Because `isolation: "worktree"` only auto-cleans a worktree when the agent made **no** changes
    (every surviving builder here, by definition, did make changes), losing worktrees are **not**
    auto-removed — this skill must explicitly run `git worktree remove <path>` (+ delete the
    variant's branch) for every non-winning worktree, **after** an explicit "harvest ideas from
    runners-up?" prompt per the task brief, never before it and never silently.
  - **Non-local execution note** (documented recipe only, not implemented in v1): describe how a
    Foundry/Reck run would map Phase 2's N builder dispatches onto N PAS tasks in containers
    instead of local `Agent` worktree dispatch — same pattern as CAST's/Fresh-Eyes' documented
    no-`Task` fallback sections, i.e. prose only, no code.

- **`plugins/variant-explorer/agents/blind-builder.md`** — new agent (cannot reuse
  `clean-room-alternative` as-is: that agent's tool grant is `Read, Grep, Glob` only and it produces
  a design doc, never code). Needs `Read, Write, Edit, Bash, Grep, Glob` (it must actually implement
  a variant inside its assigned worktree) plus the same no-hedging/no-sibling-awareness isolation
  rules as `clean-room-alternative`, adapted from "one complete independent design" to "one complete
  independent implementation satisfying the given AC."

- **`plugins/variant-explorer/agents/variant-judge.md`** (or three thin agent files if the AC/taste/
  simplicity axes warrant separate frontmatter/tool grants — taste and simplicity axes are read-only
  `Read, Grep, Glob` since they wrap existing review-panel skills; the AC-conformance axis may want
  `Bash` if "does it pass" requires actually running anything the AC specifies, e.g. tests) — scores
  variants, never edits them.

- **`plugins/variant-explorer/commands/explore-variants.md`** — thin entry point mirroring
  `plugins/review-panel/commands/review-panel.md`'s convention exactly: parse `$ARGUMENTS` into
  spec/question + N (+ optional AC path), then hand off to the skill — implements none of the
  procedure itself.

- **`plugins/variant-explorer/README.md`** — sub-plugin readme, same shape as
  `security-suite/README.md` (What's Included / When to Use / Common Use Cases / Quick Start).

- **`plugins/variant-explorer/tests/PRESSURE-TEST.md`** (+ a `tests/fixtures/<scenario>/` per AC,
  mirroring review-panel's fixture-per-scenario convention) — since `explore-variants/SKILL.md` is a
  non-executable markdown prompt file exactly like every review-panel skill, its "tests" are
  documented live-dispatch demonstrations (a concrete spec+AC fixture, expected N worktrees/
  scorecards/shortlist), not an automated pytest suite. **Exception**: if any actual helper script
  gets introduced (e.g., a small worktree-cleanup bash/python helper), that piece is real code and
  should get real `pytest`/bash test coverage the way `hooks/tests/test_data_layer_guard.py` did for
  scc-d0u — but the current design above doesn't obviously need one, since `isolation: "worktree"`
  and `git worktree remove` are used directly rather than wrapped.

### Existing files to modify

- **`.claude-plugin/marketplace.json`** — add one new entry (`variant-explorer`) with
  name/source/description/version `1.0.0`/author/tags matching the new plugin.json exactly (this is
  exactly what `scripts/verify_plugin.py` checks post-scc-d0u).
- **`README.md`** — bump `## At a Glance`'s "Sub-plugins" row 7 → 8 (current confirmed state: 7,
  post-scc-d0u fix, includes review-panel); add a new `### variant-explorer` subsection after the
  existing 7 (one-line description + Agents/Commands/Skills tables), following the exact structure
  every sibling subsection uses.
- **No change needed**: `scripts/verify_plugin.py` (already generically walks every marketplace
  entry as of scc-d0u) — the new plugin just needs to *follow* the `.claude-plugin/plugin.json`
  path convention, not be special-cased by the script.
- **No change needed**: `.gitignore` — worktrees created via the `Agent` tool's
  `isolation: "worktree"` parameter are a runtime-managed feature, not a repo-visible scratch
  directory this plugin creates/tracks itself (unlike epic-swarm's own `.claude/epic-swarm/`
  checkpoint directory, which exists for a different reason — cross-session resumability that
  variant-explorer's single-shot run doesn't need). No new `.gitignore` entry appears necessary
  unless implementation reveals a plugin-managed scratch path; confirm this during implementation
  rather than pre-adding an unused ignore rule.

---

## Risks and dependencies

- **Dependency direction compliance**: variant-explorer depends on review-panel (`taste-review`,
  `ponytail-review`) — this is explicitly sanctioned by the task brief ("Depends on review-panel to
  score its shortlist against TASTE.md; review-panel itself stays scoped to judgment-only
  tooling"). The reverse must never happen: review-panel must not gain any worktree-spawning/
  execution code — that machinery stays entirely inside `plugins/variant-explorer/`. This is the
  task's own explicit Key Constraint and must be checked during implementation (no edits to any
  `plugins/review-panel/` file beyond reading its skills as a judge-dispatch target).
- **Worktree cleanup is not automatic for successful builders.** The `Agent` tool only
  auto-cleans a worktree when the agent made no changes; every variant that actually built something
  leaves a worktree/branch that must be explicitly removed post-harvest-prompt. Getting the ordering
  wrong (deleting before the human is asked, or never deleting at all) directly breaks the task
  brief's explicit requirement ("after an explicit 'harvest ideas from runners-up?' prompt").
  Confirm during implementation whether harvesting itself needs a documented procedure (e.g., "read
  runner-up worktree X, extract idea Y, note it in final report") or is left to human judgment once
  the shortlist is presented.
  the shortlist is presented.
- **AC2's absent-TASTE.md behavior is not a new design decision** — it's a pre-existing, binding
  line in `TASTE-FORMAT.md` (Phase 3a, already merged). Implementation must honor that text exactly
  (omit the axis, state the gap) rather than inventing new behavior (e.g., a generic simplicity-only
  fallback score standing in for taste) — that would violate Invariant 3 (Coverage Honesty) and
  contradict a spec commitment made in a prior, closed phase.
- **AC3 has no new tooling need**: it's verifiable the same way every review-panel markdown-prompt
  skill's isolation guarantee is verified today — human/`--mode=agent` transcript inspection, per
  `tests/PRESSURE-TEST.md`'s documented pattern. Do not over-build a dispatch-logging subsystem this
  task doesn't need.
- **Scope discipline vs. epic-swarm**: epic-swarm's checkpoint-file/resumability machinery exists
  for long-running, multi-wave epics that might span sessions. variant-explorer's run (spawn N,
  wait, judge, present shortlist, cleanup) is a single synchronous operation with no epic-scale wave
  structure — pulling in epic-swarm's checkpoint complexity would be unwarranted scope creep; only
  its `isolation: "worktree"` dispatch mechanic and explicit-failure-list convention are directly
  reusable.
- **This is the Investigate step only.** No `plugins/variant-explorer/` files, no
  `marketplace.json`/`README.md` edits have been made in this step — all deferred to the next
  pipeline (Implement) step.
