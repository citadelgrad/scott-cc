---
name: explore-variants
description: Spawns N blind builders in isolated git worktrees against a spec + acceptance criteria, then judges the results against AC conformance, TASTE.md (when present), and simplicity, producing a ranked shortlist for the human to pick from. Use when the user wants to explore multiple independent implementation approaches in parallel rather than commit to one up front. N defaults to 3 (refuses at N=1, clamps at N>6). Depends on review-panel for the taste and simplicity judging axes; review-panel itself never depends on this plugin and never gains worktree-spawning code.
argument-hint: "[spec or design question, or path to one] [--n N] [--ac <path>]"
allowed-tools: Task, Read, Write, Grep, Glob, Bash
---

# Explore Variants

Spawns N independent builders, each in their own isolated git worktree, each given only a spec
and its acceptance criteria plus one distinct angle — never a sibling variant's approach or
output. This is `design-it-twice`'s Isolation Mode extended from "one alternative design doc" to
"one alternative, complete implementation." After all builders finish, an independent judge panel
scores every surviving variant, and this skill hands the human a ranked shortlist to pick from.

**Builders never see each other's work. Judges see all of it.** That asymmetry is the whole
point: contamination-free generation, informed comparison.

## When to Apply

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
- **Acceptance criteria**: from `--ac <path>` if given. If absent, dispatch the root plugin's
  `acceptance-criteria` skill (`skills/acceptance-criteria/SKILL.md`) against the spec to generate
  one before proceeding — every builder and judge needs concrete, testable AC to work against.
- **N**: from `--n N`. Default `3` if omitted or non-numeric.

Validate N before spawning anything:

| N value | Behavior |
|---------|----------|
| `1` | **Refuse.** Report: "N=1 has no exploration value — build directly instead of running a one-variant panel." Do not spawn a worktree, do not proceed to Phase 2. |
| `2`–`6` | Proceed as given. |
| `>6` | **Clamp to 6.** Report explicitly in the final output: "N=<requested> clamped to 6 (cap)." Never silently run the user's original, larger N. |

Both refusal and clamping are explicit, reported behaviors — never a silent substitution.

### Phase 2 — Spawn N blind builders (AC1, AC3)

Dispatch N `Agent` calls with `isolation: "worktree"` and `subagent_type:
"variant-explorer:blind-builder"`, all in a **single message** so they run in parallel. If N is 6,
sub-batch as 5 then 1 (mirrors `cast-and-spawn.md`'s ≤5-concurrent-per-batch convention) rather
than firing all 6 in one burst.

Each builder's prompt contains **only**:

1. The spec + acceptance criteria (text or file path)
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

- **Returned `status: complete`** → survivor. Record its worktree path, branch name, and summary.
- **Returned `status: blocked: <reason>`, errored, or timed out** → **lost variant**. Record
  `{"id": "<variant-id>", "reason": "<reason>"}` — mirrors `epic-swarm`'s `tasks_failed` shape.

The run continues with the survivors. The final report always states the original N (post-clamp),
the lost count and reasons, and the surviving count — **N is never silently reduced or renumbered**
as if the run had only ever asked for the smaller number.

If every variant is lost, stop here and report the full failure list — do not proceed to judging
with zero survivors.

### Phase 4 — Judge panel (AC2)

Dispatch judges against the **surviving** variants, giving each judge the variants' worktree
paths (not inline content) plus the spec/AC. Each judge is one `Agent` call using
`subagent_type: "variant-explorer:variant-judge"`, told which single axis to score:

1. **AC-conformance judge** — native to this plugin, no cross-plugin dependency. Checks every
   variant against every AC item, citing which item(s) it satisfies or fails by ID.
2. **Taste judge** — instructed to follow `plugins/review-panel/skills/taste-review/SKILL.md`'s
   review procedure. **Dispatch this judge only if `TASTE.md` exists at the repo root.** This is
   not a new decision made here — it is `formats/TASTE-FORMAT.md`'s existing, binding commitment:
   *"No TASTE.md file: the taste review seat never casts (no generic fallback), and Phase 4
   variant scoring omits the taste axis... report the gap explicitly per Coverage Honesty rather
   than silently skipping."* If `TASTE.md` is absent, skip this dispatch entirely and mark every
   scorecard's taste axis `"omitted — no TASTE.md at repo root"` rather than producing an empty or
   generic score.
3. **Simplicity judge** — instructed to follow
   `plugins/review-panel/skills/ponytail-review/SKILL.md`'s exact lens and output format
   (`L<line>: <tag> <what>. <replacement>.`, ending `net: -<N> lines possible.` or
   `Lean already. Ship.`).

Dispatch the (up to three) judges in a single message so they run in parallel.

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

1. Present the ranked shortlist with each variant's full scorecard.
2. Ask the human to pick a winner.
3. Ask explicitly: **"Harvest ideas from runners-up before cleanup?"** If yes, read the specific
   non-winning worktree(s) the human points to, note what idea(s) are worth extracting in the
   final report — this is a human-judgment call, not an automated diff/merge.
4. **Only after that prompt is answered** (yes or no), clean up every non-winning worktree:
   `git worktree remove <path>` (add `--force` only if the human confirms the worktree's changes
   aren't needed) and delete its branch. Cleanup must never happen before the harvest prompt, and
   never silently.

The winning worktree and branch are left as-is for the human to merge or open a PR from — this
skill does not auto-merge the winner. `isolation: "worktree"` only auto-cleans a worktree when its
agent made no changes; every surviving builder here made changes, so every worktree (winner
included, until the human merges it) needs this explicit handling.

## Non-Local Execution (documented recipe only — not implemented in v1)

A Foundry/Reck run maps Phase 2's N builder dispatches onto N PAS tasks running in containers
instead of local `Agent` worktree dispatch — one PAS task per variant, each given the same
spec/AC/angle triple as the local path. The judge panel becomes a follow-on PAS task that runs
once all N builder tasks report complete or failed, reading each container's output the same way
Phase 4 reads worktree paths locally. This is prose only, matching `cast-and-spawn.md`'s
documented no-`Task` fallback sections — no code exists for this path in v1.

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

This skill depends on `review-panel`'s `taste-review` and `ponytail-review` skills for two of the
judge panel's three axes — this is the sanctioned direction. `review-panel` must never import
from or special-case `variant-explorer`, and must never gain any worktree-spawning or execution
machinery; that machinery stays entirely inside this plugin.
