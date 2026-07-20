---
name: review-panel
description: Orchestrates a full multi-reviewer code-review panel against one shared diff — casts a diverse set of reviewer seats by reading diff content (not paths), runs them concurrently, merges and deduplicates their findings with confidence scoring, independently validates each surviving finding, fixes everything in one pass, re-reviews for regressions and domain-intent coherence, and loops to convergence or a circuit-break. Use when a diff, PR, or branch needs a comprehensive verification pass before merge, when invoked as an automated foundry/CI gate (mode:agent), or whenever the user asks for a "review panel," "full review," or "panel review." Not for a single-lens check (invoke that reviewer skill directly, e.g. adversarial-reviewer, design-review, domain-modeling, ponytail-review) and not for generating a second independent design from scratch with no existing code to review (use design-it-twice).
argument-hint: "[diff, PR, branch, or base..head range to review; or --mode=agent for machine output]"
allowed-tools: Task, Read, Grep, Glob, Bash
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
multiple reference files at the start of a run. The orchestrator's own context has to survive the
entire loop, potentially across several CONVERGE iterations, so it is the one place in this skill
that must stay lean; a stage's reference is cheap to re-read next time you need it but expensive to
hold unused for the many tool calls between, say, CAST and CONVERGE.

| Stage reached | Read this reference (only this one, only now) |
|---|---|
| CAST, SPAWN | [references/cast-and-spawn.md](references/cast-and-spawn.md) |
| MERGE, VALIDATE | [references/merge-and-validate.md](references/merge-and-validate.md) |
| FIX, RE-REVIEW | [references/fix-and-rereview.md](references/fix-and-rereview.md) |
| CONVERGE, pipeline-not-barrier | [references/converge-and-pipeline.md](references/converge-and-pipeline.md) |
| Dual-mode (human + `mode:agent` JSON) | [references/dual-mode-contract.md](references/dual-mode-contract.md) — only if invoked with `mode:agent` |
| Design Lineage / provenance | [references/design-lineage.md](references/design-lineage.md) — only if a CONTEXT.md/ADR exists to check against |

## Setup: diff packaging and scratch workspace

Before CAST, materialize the shared diff every seat will review, using the vendored scripts
rather than re-deriving diffs ad hoc:

1. Check whether `$ARGUMENTS` names a target (ignore `--mode=agent` when checking).
   - **Empty** (bare `/review-panel`): this is the fast path — the review target is the current
     working tree against `HEAD`. Do **not** run `git status`, branch discovery, `git
     merge-base`, or any other lookup to find a base branch; none of that is needed and it is
     the exact cost this path exists to avoid. Go straight to step 2, then invoke
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
4. **Do not `Read` this file into the orchestrator's own context.** The packaged diff can be large
   (real panel runs have seen 100K+ characters), and the orchestrator's context has to survive the
   whole loop, so it is the one context that must not hold full diff content. Capture only the
   path plus a stat summary (`git diff --stat BASE..HEAD`, or `git diff --stat HEAD` for the bare
   working-tree case: file list + added/removed line counts per file) directly into the
   orchestrator's context — that's enough to sanity-check scope (e.g. flagging a 79-commit,
   112-file diff before spending a full CAST pass on it) without paying for full hunk content.
   Every stage that needs the diff's actual content — CAST's dispatched subagent, each SPAWN seat,
   the FIX fixer, RE-REVIEW's re-cast seats — reads the file itself in its own disposable context,
   never in the orchestrator's. See `references/cast-and-spawn.md` for how CAST applies this.
5. If `scripts/workspace` or `scripts/review-package` are unavailable (non-bash environment, or
   scripts missing from this plugin's install), fall back to running `git diff -U10 BASE..HEAD`
   (or `git diff -U10 HEAD` for the bare working-tree case) directly and holding the result
   in-conversation as the shared diff; note this fallback in the final report's coverage-honesty
   statement — this is the one path where the orchestrator ends up holding full diff content,
   since there's no file to point subagents at instead.

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
skipped and why. This rule applies across all 7 stages, not just CONVERGE's final synthesis.
