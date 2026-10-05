---
name: explore-variants
description: Use when the user wants to explore multiple independent implementation
  approaches in parallel rather than commit to one up front. Spawns N blind builders
  in isolated git worktrees against a spec + acceptance criteria, then judges results
  against AC conformance, TASTE.md, and simplicity, producing a ranked shortlist.
  N defaults to 3 (refuses N=1, clamps N>6).
argument-hint: '[spec or design question, or path to one] [--n N] [--ac <path>]'
metadata:
  category: technique
  triggers:
  - variant-exploration
  - experimentation
  - testing
---

# Explore Variants

Spawns N independent builders, each in their own isolated git worktree, each given only a spec
and its acceptance criteria plus one distinct angle — never a sibling variant's approach or
output. This is `design-it-twice`'s Isolation Mode extended from "one alternative design doc" to
"one alternative, complete implementation." After all builders finish, an independent judge panel
scores every surviving variant, and this skill hands the human a ranked shortlist to pick from.

**Builders never see each other's work. Judges see all of it.** That asymmetry is the whole
point: contamination-free generation, informed comparison.

## Capability preflight

Resolve `<skill-dir>` from the loaded SKILL.md and run
`python3 <skill-dir>/scripts/package_contract.py doctor` before any worktrees.
Read [worker-adapters.md](references/worker-adapters.md). Bundle-local prompts:
[blind-builder](prompts/blind-builder.md), [variant-judge](prompts/variant-judge.md).
The required [taste lens](references/lenses/taste-review.md),
[simplicity lens](references/lenses/ponytail-review.md), and
[acceptance-criteria procedure](references/lenses/acceptance-criteria.md) ship here.

- **Native independent mode:** verify fresh-context workers and isolated working
  directories using the live host schema. Use the bundled prompts with those
  workers; named `variant-explorer:*` types are optional Claude-plugin shortcuts
  only when exposed. Never invent `Agent`, `isolation` or `subagent_type` fields.
- **No fresh workers:** full blind generation/judging is `unsupported`. Stop
  before worktrees and offer an explicitly user-approved **sequential comparison**
  instead. That mode runs one builder role at a time in separate worktrees and
  then applies each judge rubric in this conversation. It is **not independent**,
  not blind, and not parallel; never claim contamination-free generation or
  independent validation. If those guarantees are required, do not proceed.
- In either mode, verify worktree isolation, spec/AC hashes, actual test execution,
  output artifacts and permission boundaries. Preserve failed/lost variants.
  A worktree isolates files, not reasoning. No tool means no simulated tool call.

These adapter instructions override source prompt examples and metadata. Give
workers the explicit input packet and bounded output-artifact contract below;
do not return the source prompts' example inline scorecards. For judging, use the
bundled lenses by path rather than invoking an uninstalled companion skill.
No provider/model pin in a prompt authorizes a new paid invocation.

## Context architecture contract

- **Scope contract:** Resolve exactly one spec and one AC source before dispatch. Normalize both to
  artifacts of at most **64 KiB each**, compute SHA-256 values, and reject larger or missing inputs
  with `SPEC_SCOPE_TOO_LARGE` or `AC_REQUIRED`. The existing N contract remains: refuse N=1,
  default to 3, allow 2–6, and clamp N>6 to **6**.
- **Fan-out contract:** Dispatch at most **5 builders concurrently**, **6 builder assignments**
  total, and at most **3 judges concurrently / 3 judge assignments**. Each judge scores at most
  **6 variants** and emits at most **6 scorecards**.
- **Artifact contract:** `run-manifest.json` binds spec, AC, builder, and judge artifacts by SHA-256.
  Builder and judge detail never returns inline; each worker returns a manifest of at most **2
  KiB**. Each bounded scorecard summary is at most **1 KiB**; the shortlist is at most **6 KiB** and
  six entries, with detailed reasoning available only by artifact path and hash.
- **Failure contract:** Worktree isolation, artifact persistence, hash validation, or judge-schema
  failure is explicit and fail-closed for that worker. A malformed judge becomes a named
  `JUDGE_MALFORMED` coverage gap and contributes no score; never invent, coerce, or partially merge
  its scores. Zero valid required judges stops before ranking.
- **Continuation contract:** Before asking for the human pick, write `decision-checkpoint.json`
  containing the run-manifest SHA-256, shortlist artifact hash, survivor worktrees/commits, losses,
  and cleanup state. Atomically claim its SHA-256 on resume; hash mismatch or duplicate cleanup is
  rejected. No worktree cleanup occurs before the checkpoint and recorded human decision.
- **Mechanical-test contract:** `scripts/tests/test_explore_variants_context_budget.py` asserts N,
  builder, judge, scorecard, artifact, shortlist, malformed-judge, and decision-checkpoint bounds.

## When to Use

- Multiple genuinely different implementation approaches are plausible and worth building out,
  not just sketching
- Before committing significant implementation effort, when a single `design-it-twice` pass
  compared designs on paper but the team wants to see working code before choosing
- The spec is concrete enough to hand to N builders with acceptance criteria they can build
  against

## When NOT to Apply

- Trivial changes or a single well-established implementation pattern
- Bug fixes that don't change the interface
- Only comparing designs, not implementations — use `design-it-twice` instead, it's far cheaper
- The user wants one implementation built now, not N compared — just build it

## Procedure

### Phase 1 — Gather input & validate N (AC5)

Parse `$ARGUMENTS`:

- **Spec**: the design question or feature spec, inline or as a file path.
- **Acceptance criteria**: from `--ac <path>` if given. If absent, apply the bundled
  [acceptance-criteria procedure](references/lenses/acceptance-criteria.md) to the
  spec and confirm the criteria before proceeding. Every builder and judge needs
  concrete, testable AC; no root plugin installation is required.
- **N**: from `--n N`. Default `3` if omitted or non-numeric.

Persist normalized spec and AC text before reading them into any builder prompt. Reject either
artifact above 64 KiB. Write `run-manifest.json` with their paths and SHA-256 values; all later
prompts reference those paths and hashes rather than copying the text.

Validate N before spawning anything:

| N value | Behavior |
|---------|----------|
| `1` | **Refuse.** Report: "N=1 has no exploration value — build directly instead of running a one-variant panel." Do not spawn a worktree, do not proceed to Phase 2. |
| `2`–`6` | Proceed as given. |
| `>6` | **Clamp to 6.** Report explicitly in the final output: "N=<requested> clamped to 6 (cap)." Never silently run the user's original, larger N. |

Both refusal and clamping are explicit, reported behaviors — never a silent substitution.

### Phase 2 — Spawn N blind builders (AC1, AC3)

Pin the approved base revision and create N isolated worktrees with explicit paths.
Dispatch the [blind-builder prompt](prompts/blind-builder.md) through the verified
native adapter in batches of at most five (six builders means five then one).
If the user explicitly accepted sequential comparison, perform one role at a time
instead and label every artifact `sequential-not-independent`. Never implicitly
send conversation history, sibling work or the preferred approach to a fresh builder.

Each builder's prompt contains **only** references to:

1. The spec + acceptance-criteria artifact paths and expected SHA-256 values
2. One distinct angle, drawn from a bank such as:
   - MVP-first — build the smallest thing that satisfies every AC, defer everything else
   - Data-model-first — derive the implementation from the data shape outward
   - Dependency-free — satisfy the AC with zero new third-party dependencies
   - Interface-first — design the public surface first, implementation follows from it
   - Test-first — write the acceptance tests before any implementation code
   - Existing-pattern-reuse — solve it by extending the closest existing pattern in the codebase

Pick N angles from this bank (or spec-appropriate substitutes); never reuse the same angle twice
in one run.

**Never include in any builder's prompt:** another variant's angle, output, or existence; the
orchestrator's own preferred approach; conversation history beyond the spec/AC. This is checked
structurally — the same way every `review-panel` markdown-prompt skill's isolation guarantee is
checked: a human or `--mode=agent` harness can inspect the actual dispatch prompts in the session
transcript and confirm no cross-contamination (AC3). No new logging infrastructure is required.

### Phase 3 — Collect results, handling failures explicitly (AC4)

Wait for all N dispatches to return. For each:

- **Returned `status: complete`** → survivor. Require a ≤2 KiB manifest containing its worktree
  path, branch name, commit, report artifact path, report SHA-256, status, and counts.
- **Returned `status: blocked: <reason>`, errored, or timed out** → **lost variant**. Record
  `{"id": "<variant-id>", "reason": "<reason>"}` — mirrors `epic-swarm`'s `tasks_failed` shape.

The run continues with the survivors. The final report always states the original N (post-clamp),
the lost count and reasons, and the surviving count — **N is never silently reduced or renumbered**
as if the run had only ever asked for the smaller number.

If every variant is lost, stop here and report the full failure list — do not proceed to judging
with zero survivors.

### Phase 4 — Judge panel (AC2)

Dispatch judges against the **surviving** variants, giving each judge the hashed builder-manifest
path plus hashed spec/AC paths (not inline content). Each judge uses the bundled
[variant-judge prompt](prompts/variant-judge.md) through the native adapter, told
which single axis to score (or a disclosed sequential rubric pass):

1. **AC-conformance judge** — native to this plugin, no cross-plugin dependency. Checks every
   variant against every AC item, citing which item(s) it satisfies or fails by ID.
2. **Taste judge** — instructed to read the bundled `references/lenses/taste-review.md` and follow its
   review procedure. **Dispatch this judge only if `TASTE.md` exists at the repo root.** This is
   not a new decision made here — it is `formats/TASTE-FORMAT.md`'s existing, binding commitment:
   *"No TASTE.md file: the taste review seat never casts (no generic fallback), and Phase 4
   variant scoring omits the taste axis... report the gap explicitly per Coverage Honesty rather
   than silently skipping."* If `TASTE.md` is absent, skip this dispatch entirely and mark every
   scorecard's taste axis `"omitted — no TASTE.md at repo root"` rather than producing an empty or
   generic score.
3. **Simplicity judge** — instructed to read the bundled `references/lenses/ponytail-review.md`
   and follow its exact lens and output format
   (`L<line>: <tag> <what>. <replacement>.`, ending `net: -<N> lines possible.` or
   `Lean already. Ship.`).

Dispatch the (up to three) judges in a single message so they run in parallel.

Each judge writes detailed scorecards to an artifact and returns a ≤2 KiB manifest. Validate the
artifact hash and schema, including no more than 6 scorecards and a ≤1 KiB bounded summary per
scorecard. Record malformed output as `JUDGE_MALFORMED`; it contributes no score. If any required
axis has zero valid judge output, stop before ranking instead of guessing. Synthesis writes a
shortlist artifact and returns at most 6 KiB / 6 entries.

Assemble the combined **ranked shortlist** from the judges' returned scorecards. Every variant's
final scorecard must cite:

- **≥1 AC item by ID** (AC1's pass bar)
- **The taste clause text verbatim**, when the taste axis ran and found something (AC2's pass
  bar — matching `taste-review`'s own "quote the clause, not a paraphrase" rule); otherwise the
  explicit omission note above
- The simplicity judge's findings and net-line figure

**Ranking order:** any AC failure is disqualifying and sorts last; among AC-passing variants, rank
by fewest `Important`-or-`absolute` taste violations, then by simplicity's `net` line count
(fewer/more-negative is better; `Lean already. Ship.` beats any positive net-cut). If a tie
remains, say so explicitly rather than forcing an arbitrary order — let the human break it.

### Phase 5 — Human pick & cleanup

1. Write and hash `decision-checkpoint.json` with the run-manifest and shortlist hashes, survivor
   worktree paths/commits, losses, and `cleanup_state: pending`; persist it before human output.
2. Present the bounded ranked shortlist with links to each full scorecard artifact.
3. Ask the human to pick a winner. On resumed sessions, atomically claim the checkpoint SHA-256
   before accepting a decision; reject hash mismatch or an already-consumed cleanup transition.
4. Ask explicitly: **"Harvest ideas from runners-up before cleanup?"** If yes, read the specific
   non-winning worktree(s) the human points to, note what idea(s) are worth extracting in the
   final report — this is a human-judgment call, not an automated diff/merge.
5. **Only after that prompt is answered** (yes or no), record the decision in the checkpoint, then
   clean up every non-winning worktree:
   `git worktree remove <path>` (add `--force` only if the human confirms the worktree's changes
   aren't needed) and delete its branch. Cleanup must never happen before the harvest prompt, and
   never silently.

The winning worktree and branch are left as-is for the human to merge or open a PR from — this
skill does not auto-merge the winner. Do not assume native worker teardown removes
worktrees. Every surviving worktree remains a recovery artifact until the approved
integration/cleanup checks have completed.

## Non-local execution

Use container/PAS/Reck adapters only if actually available, documented and
explicitly authorized. Verify artifact transfer and the same context/filesystem
isolation guarantees before dispatch; this package does not implement those
services. If unavailable, report `unsupported`, not a launched job.

## Output Contract

The final report states, in order:

1. **Run parameters** — spec/AC source, N requested, N after any clamp/refusal
2. **Survivors and losses** — surviving variant count, lost variant list with reasons (or "no
   losses")
3. **Ranked shortlist** — one scorecard per surviving variant (AC citations, taste citations or
   omission note, simplicity findings), in rank order
4. **Coverage notes** — anything a seat/axis couldn't run and why (e.g., "Taste axis omitted — no
   TASTE.md at repo root"), per Coverage Honesty
5. **Human decision** — the picked winner, the harvest-prompt answer and any harvested ideas, and
   confirmation of which worktrees were removed

## Dependency Direction

This package vendors drift-checked snapshots of `review-panel`'s `taste-review`
and `ponytail-review` for two judging axes; no installed companion is required.
`package-manifest.json` records the source and deterministic path rewrites. `review-panel` must never import
from or special-case `variant-explorer`, and must never gain any worktree-spawning or execution
machinery; that machinery stays entirely inside this plugin.

## Limitations
- Use this skill only when the task clearly matches the scope described above.
- Variant exploration is generative — results need evaluation and validation before adoption.
- Quality of variants depends on clarity of the design space and constraints provided.
- Stop and ask for clarification if the design space, constraints, or evaluation criteria are unclear.
