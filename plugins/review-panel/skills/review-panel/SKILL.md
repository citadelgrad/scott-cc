---
name: review-panel
description: >-
  Use when a diff, PR, or branch needs a comprehensive verification pass before
  merge, when invoked as an automated Foundry/CI gate (mode:agent), or when the
  user asks for a "review panel" or "full review." Casts diverse reviewer seats,
  runs them concurrently, deduplicates and validates findings, fixes survivors,
  and loops to convergence or a circuit-break. Not for single-lens checks or
  generating alternative designs (use design-it-twice).
argument-hint: '[diff, PR, branch, or base..head range to review; --lite, --medium,
  or --auto to narrow the review tier; --mode=agent for machine output; --resume PATH --checkpoint-sha256 HEX]'
allowed-tools: Task, Read, Grep, Glob, Bash
metadata:
  category: technique
  triggers:
  - code-review
  - multi-lens-review
  - quality-assurance
---

# Review Panel

The orchestrator. Every other skill in this plugin — the clairvoyance lenses (via
`design-review`), `ponytail-review`/`ponytail-audit`, `domain-modeling`, `adversarial-reviewer`,
`code-evolution`, `design-it-twice`, `tdd` (test-design-quality axis only), `data-steward` — is a
standalone reviewer seat. This skill casts a panel of
those seats against one shared diff, merges and scores their findings, independently validates
each survivor, fixes everything in a single pass, re-reviews for regressions and domain-intent
coherence, and loops until a clean round or a circuit-break. This is the thing a human runs by
hand or a `foundry` gate invokes unattended.

## When to Use
- A diff, PR, or branch needs a comprehensive verification pass before merge
- Invoked as an automated foundry/CI gate (mode:agent)
- The user asks for a "review panel" or "full review"
- Multiple review perspectives are needed simultaneously (not just one lens)

## When to invoke this vs. a single seat

- **Invoke this skill** when the ask is comprehensive verification of a diff/PR/branch before
  merge, or when running unattended as an automation gate. The value is perspective diversity —
  multiple independent reviewers catching different classes of problem — plus the fix→re-review
  loop that gets the diff to an actually-clean state, not just a list of complaints.
- **Invoke a single seat directly instead** when the ask is narrow: "attack this for security
  holes" → `adversarial-reviewer`. "Is this over-engineered?" → `ponytail-review`. "Review this
  type design" → `domain-modeling`. "Structural design review" → `design-review`. Running the
  full panel for a narrow question wastes the diversity budget on seats that have nothing to say.
- Casting judgment (the CAST stage below) already handles the "which seats actually apply"
  question once you're inside a panel run — the choice above is only about whether to enter a
  panel run at all.

## Hard context preflight

These checks run before CAST and override the normal loop:

1. **Exactly one review target per invocation.** Resolve exactly one review target and finish or
   checkpoint it. Never chain a second panel automatically, even when two related repositories or
   PRs were changed together. A second target requires a separate invocation in a fresh Claude Code
   orchestration context.
2. **Reject oversized monolithic scope.** After packaging and reading only bounded `scope.json`, stop
   with error code `scope_too_large` when the target exceeds **25 files** or **1,500 changed lines**
   (generated, vendored, and lockfile-only changes may be excluded with disclosure). Do this before
   CAST. Report the measured counts and provide concrete commit ranges or coherent path groups that
   each fit under both limits. Sensitive files still require full-tier coverage, but not a single
   unbounded run.
3. **Artifact-only parent contract.** CAST, SPAWN, MERGE, VALIDATE, FIX, and RE-REVIEW write bulky
   output beneath the run workspace. Each dispatched worker returns only a manifest of at most
   **2 KiB** containing artifact path, status, counts, IDs, and coverage gaps. The parent never
   receives raw seat reports, validator reasoning, full findings lists, fixer reasoning, or diff
   content. If a worker cannot persist its artifact, the stage fails; it must not fall back to
   returning the bulky payload inline.
4. **Resume, do not accumulate.** `--resume PATH --checkpoint-sha256 HEX` is valid only when both
   arguments are present and the process has
   `REVIEW_PANEL_FRESH_RESUME=1` and its `REVIEW_PANEL_SESSION_ID` exists and differs from the
   checkpoint's `origin_session_id`; otherwise fail with `fresh_context_unverifiable`. It reads a
   checkpoint produced by CONVERGE, verifies its target hashes and artifact paths, and re-enters at
   the recorded stage in a fresh orchestration context. Before review work it invokes
   `scripts/checkpoint-claim PATH "$REVIEW_PANEL_SESSION_ID" HEX`; hash mismatch fails before the
   claim, and an existing content-hash claim fails with `checkpoint_already_consumed`. A resume
   invocation cannot also name a new target or tier.
5. **Terminal means stop.** Once any terminal status/report is emitted, perform no more tool calls,
   follow-up issue creation, acceptance-criteria generation, fixes, or additional review rounds.
   Never reinterpret residual findings as permission to continue after `capped` or `checkpointed`.

## The 7-stage loop

```
CAST        ONE dispatched subagent judgment-casts against persona-catalog.md (reads diff CONTENT
              in its own disposable context, never the orchestrator's) + live-scan enrichment of
              installed skills; fail-closed on ambiguity; returns only the small cast list
  ↓
SPAWN       bounded-parallel dispatch of the cast panel, read-only tools, ALL seats see the
              SAME shared diff by path (never re-derived, never inlined into the orchestrator)
  ↓
MERGE       fingerprint-dedupe (file + line±3 + normalized title) → confidence anchors
              0/25/50/75/100 → quote-the-line evidence gate
  ↓
VALIDATE    one independent, clean-room validator per SURVIVING finding; never the original
              finder; escalate to 2-3 validators for CRITICAL findings
  ↓
FIX         ONE fixer subagent, the WHOLE validated findings list in a single dispatch
  ↓
RE-REVIEW   diff-after-fixes for regressions AND coherence vs. CONTEXT.md domain decisions
  ↓
CONVERGE    clean round → done. Else loop to SPAWN with the new diff. 3-strikes circuit-breaker
              on no measurable progress → escalate to human, never loop forever
```

Full procedural detail for each stage lives in `references/` — this file is the entry point and
spine, not the complete procedure. **Read references one at a time, just-in-time**: read only the
file for the stage you are about to execute, immediately before executing it — never batch-read
multiple reference files at the start of a run. The orchestrator's own context has to survive one
complete round before CONVERGE checkpoints any permitted continuation, so it is the one place in this skill
that must stay lean; a stage's reference is cheap to re-read next time you need it but expensive to
hold unused for the many tool calls between, say, CAST and CONVERGE.

| Stage reached | Read this reference (only this one, only now) |
|---|---|
| CAST, SPAWN | [references/cast-and-spawn.md](references/cast-and-spawn.md) |
| MERGE, VALIDATE | [references/merge-and-validate.md](references/merge-and-validate.md) |
| FIX, RE-REVIEW | [references/fix-and-rereview.md](references/fix-and-rereview.md) |
| CONVERGE, artifact-path barrier | [references/converge-and-pipeline.md](references/converge-and-pipeline.md) |
| Dual-mode (human + `mode:agent` JSON) | [references/dual-mode-contract.md](references/dual-mode-contract.md) — only if invoked with `mode:agent` |
| Design Lineage / provenance | [references/design-lineage.md](references/design-lineage.md) — only if a CONTEXT.md/ADR exists to check against |
| Narrowed-tier parameters | [references/lite-mode.md](references/lite-mode.md) — only if invoked with `--lite`, `--medium`, or `--auto` |

## Setup: diff packaging and scratch workspace

Before CAST, materialize the shared diff every seat will review, using the vendored scripts
rather than re-deriving diffs ad hoc:

1. Check whether `$ARGUMENTS` names a target (ignore `--mode=agent`, `--lite`, `--medium`, and
   `--auto` when checking). In this same step, also parse the tier-selecting flags — this mirrors
   the existing precedent that `--mode=agent` is already parsed independently of target
   resolution, so `--lite`/`--medium`/`--auto` and `--mode=agent` must be order-independent and
   composable: every ordering of these flags parses to the identical internal state.
   - `--lite`, `--medium`, and `--auto` are flag-presence-only — there is no `=value` form. A
     `--lite=false` (or `--medium=false` or `--auto=false`, or any other `=`-suffixed variant) is
     malformed input: reject the invocation with a clear error naming the malformed flag, before
     CAST runs. Never silently interpret this as an inverted flag, and never silently fall back to
     flag-absent/full mode — this would mask a typo'd invocation (e.g. a CI script that meant
     `--lite=true`) as an ordinary full-mode pass.
   - `--lite`, `--medium`, and `--auto` are pairwise mutually exclusive with each other. If any two
     of the three are present together, reject the invocation with a clear error naming both
     conflicting flags, before CAST runs — never silently prefer one. (This is a 3-way pairwise
     exclusivity check.) Malformed-flag rejection above uses this same fail-closed rejection path.
   - Set `tier_source` the moment these flags are parsed: `"explicit"` for an explicit `--lite` or
     `--medium` flag, or when no tier flag is present at all (full mode); `"auto"` the instant
     `--auto` is detected. This step fully owns and writes `tier_source` for both of its values
     (contract documented in `references/dual-mode-contract.md`). Setting `tier_source` to
     `"auto"` here does **not** resolve which concrete tier (full/medium/lite) the run actually
     uses — that resolution happens later, in a separate Setup step that runs after target
     resolution and before CAST, and only fires when `tier_source` is `"auto"` (see
     `references/lite-mode.md`, "Auto resolution"). So a `--auto` invocation exits this step with
     `tier_source` already set to `"auto"` but no concrete tier chosen yet.
   - **Empty** (bare `/review-panel`, or bare aside from tier/mode flags): this is the fast path —
     the review target is the current working tree against `HEAD`. Do **not** run `git status`,
     branch discovery, `git merge-base`, or any other lookup to find a base branch; none of that is
     needed and it is the exact cost this path exists to avoid. Go straight to step 2, then invoke
     `review-package --worktree` in step 3.
   - **Non-empty**: resolve `BASE` and `HEAD` from the given target — a `base..head` range used
     as-is, or a branch name diffed against its merge-base with the default branch (`git
     merge-base` to find `BASE` when only a branch is named).
2. Run the plugin's `scripts/workspace` script (path relative to the plugin root:
   `plugins/review-panel/scripts/workspace`, two directories up from this skill's own
   `skills/review-panel/` location) to resolve (and create, git-ignored) the scratch directory for
   this run's artifacts. Capture its stdout (the workspace's absolute path, and nothing else) into
   a variable — do not invent a different scratch location, this script is the single source of
   truth so every stage's temp files land in one place.
3. Run `scripts/review-package`, passing the captured workspace path plus an explicit filename as
   the `OUTFILE` argument, so the packaged diff's path is known up front rather than parsed out of
   the script's `wrote <path>: ...` stdout summary. This file is the ONE shared diff every seat in
   SPAWN reads — pass its path, not a re-derived `git diff` invocation, to each seat's dispatch
   prompt.
   - Bare invocation: `plugins/review-panel/scripts/review-package --worktree "$WORKSPACE/review.diff"`.
   - Range/branch invocation: `plugins/review-panel/scripts/review-package BASE HEAD "$WORKSPACE/review.diff"`.
4. **Do not `Read` this file or a per-file stat into the orchestrator's own context.** Dispatch one
   disposable **scope resolver** that computes the file and line totals mechanically without
   printing `git diff --stat`, `--numstat`, or `--name-only` rows into any model context. It also
   compares changed paths against the Security criteria in `reviewers/persona-catalog.md`. The
   resolver writes `$WORKSPACE/scope.json` containing only `files_changed`, `lines_changed`,
   `sensitive_path_match`, an optional single matched-path example, and the reviewed target hash,
   then returns a manifest of at most 2 KiB. The parent reads only that bounded manifest and
   **never captures per-file output**. Every later stage that needs actual diff content reads the
   packaged file itself in its own disposable context.
5. If `scripts/workspace` or `scripts/review-package` are unavailable (non-bash environment or a
   broken plugin install), stop with error code `artifact_packaging_unavailable`. Do not run an
   inline `git diff` or hold diff content in-conversation; that fallback defeats the hard context
   contract and recreates the failure this preflight prevents. Otherwise, apply the Hard context
   preflight's 25-file/1,500-line monolithic scope gate to `$WORKSPACE/scope.json` now, for **every**
   tier source (explicit full/lite/medium and `--auto`). Stop with `scope_too_large` before CAST;
   tier selection never bypasses this gate.
6. **Resolve `--auto` to a concrete tier — only when `tier_source` is `"auto"`; a no-op for
   `"explicit"` runs**, where `tier` is already simply whichever flag (or absence of one) step 1
   parsed. This is the one point in Setup where a tier-selecting flag has a genuine data dependency
   on the resolved review target, so it runs here, after the diff is packaged and the bounded scope
   artifact is captured in step 4, and before CAST. Read these already-computed signals from
   `$WORKSPACE/scope.json`:
   - `files_changed`: count of distinct files in the stat summary.
   - `lines_changed`: total added + deleted lines across every file in the stat summary.
   - `sensitive_path_match`: true if any changed file's path matches the sensitive-path criteria
     `reviewers/persona-catalog.md`'s Security entry defines (the single source of truth for that
     path list, per Architecture invariant 2) — cited, never redefined, by
     `references/lite-mode.md`, "Auto resolution" section.

   Feed these three signals into `references/lite-mode.md`'s "Auto resolution" decision table to
   get a concrete `tier` (`"full" | "medium" | "lite"`). Record `files_changed`, `lines_changed`,
   and `sensitive_path_match` verbatim — these become the `mode:agent` JSON's `auto_signals` object
   and the human report's auto-resolution disclosure line (both in
   [references/dual-mode-contract.md](references/dual-mode-contract.md)).

   From this point forward, treat the resolved `tier` exactly as if that tier's flag had been
   passed explicitly. `tier_source` stays `"auto"` for the rest of the run regardless of which
   concrete tier it resolved to — `tier_source` records *how* the tier was chosen, `tier` records
   *what* was chosen. Every later stage (CAST/SPAWN/VALIDATE/RE-REVIEW/CONVERGE) reads `tier`,
   never `tier_source`, so no stage needs an `--auto`-specific branch of its own (Architecture
   invariant 1) — see `references/lite-mode.md`'s "Auto resolution" section for the full signal
   definitions, decision table, and safety rationale.

Every subsequent loop iteration (after FIX, before RE-REVIEW) re-runs `review-package` against
the new `HEAD` (post-fix commit or working-tree state) so RE-REVIEW and any next SPAWN operate on
a freshly packaged diff, never a stale one.

## Circuit-break and escalation summary

If the CONVERGE stage (full detail in its reference file) trips the 3-strikes circuit-breaker,
stop looping immediately — do not attempt a 4th iteration "just in case." Escalate to a human
(interactive mode: print the escalation with the last 3 rounds' finding counts and a diagnosis
of what isn't converging; `mode:agent`: set the JSON contract's top-level status to
`circuit_broken` per the dual-mode reference) and stop. Looping past 3 strikes with no progress
burns tokens without getting closer to a merge-ready diff.

## Coverage honesty

At every stage, if this run's coverage is bounded in any way — a seat skipped because its target
skill wasn't installed, a scope reduction for a very large diff, a fallback path taken because
`Task` or the vendored scripts weren't available — say so explicitly in the final report. A panel
run that silently skipped coverage and reported "clean" is worse than one that states what it
skipped and why. This rule applies across all 7 stages, not just CONVERGE's final synthesis. A
narrowed run's tier-specific guarantees (enumerated in `references/lite-mode.md`) are this same
coverage-honesty disclosure applied to `--lite`/`--medium`/`--auto` — a deliberate, disclosed scope
reduction, never a silent behavior change.

## Limitations
- Use this skill only when the task clearly matches the scope described above.
- Context-intensive — large PRs may need --lite or --medium mode to avoid context exhaustion.
- Works best when the full Clairvoyance lens collection is installed; discloses missing seats.
- Not for single-lens checks — invoke the specific reviewer directly for focused analysis.
- Stop and ask for clarification if the review scope, tier, or output format requirements are unclear.
