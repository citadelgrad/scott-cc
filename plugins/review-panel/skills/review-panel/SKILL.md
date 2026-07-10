---
name: review-panel
description: Orchestrates a full multi-reviewer code-review panel against one shared diff — casts a diverse set of reviewer seats by reading diff content (not paths), runs them concurrently, merges and deduplicates their findings with confidence scoring, independently validates each surviving finding, fixes everything in one pass, re-reviews for regressions and domain-intent coherence, and loops to convergence or a circuit-break. Use when a diff, PR, or branch needs a comprehensive verification pass before merge, when invoked as an automated foundry/CI gate (mode:agent), or whenever the user asks for a "review panel," "full review," or "panel review." Not for a single-lens check (invoke that reviewer skill directly, e.g. adversarial-reviewer, design-review, domain-modeling, ponytail-review) and not for generating a second independent design from scratch with no existing code to review (use design-it-twice).
argument-hint: "[diff, PR, branch, or base..head range to review; or --mode=agent for machine output]"
allowed-tools: Task, Read, Grep, Glob, Bash
---

# Review Panel

The orchestrator. Every other skill in this plugin — the clairvoyance lenses (via
`design-review`), `ponytail-review`/`ponytail-audit`, `domain-modeling`, `adversarial-reviewer`,
`code-evolution`, `design-it-twice`, `tdd` (test-design-quality axis only) — is a standalone
reviewer seat. This skill casts a panel of
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
CAST        judgment-based casting against persona-catalog.md (read diff CONTENT) + live-scan
              enrichment of installed skills; fail-closed on ambiguity
  ↓
SPAWN       bounded-parallel dispatch of the cast panel, read-only tools, ALL seats see the
              SAME shared diff (never re-derived per seat)
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
spine, not the complete procedure. Read the relevant reference file before executing a stage for
the first time in a run; don't try to execute from memory of this summary alone.

| Stages | Reference |
|---|---|
| CAST, SPAWN | [references/cast-and-spawn.md](references/cast-and-spawn.md) |
| MERGE, VALIDATE | [references/merge-and-validate.md](references/merge-and-validate.md) |
| FIX, RE-REVIEW | [references/fix-and-rereview.md](references/fix-and-rereview.md) |
| CONVERGE, pipeline-not-barrier | [references/converge-and-pipeline.md](references/converge-and-pipeline.md) |
| Dual-mode (human + `mode:agent` JSON) | [references/dual-mode-contract.md](references/dual-mode-contract.md) |
| Design Lineage / provenance | [references/design-lineage.md](references/design-lineage.md) |

## Setup: diff packaging and scratch workspace

Before CAST, materialize the shared diff every seat will review, using the vendored scripts
rather than re-deriving diffs ad hoc:

1. Resolve the target `BASE` and `HEAD` from `$ARGUMENTS` (a `base..head` range, a branch name
   diffed against its merge-base with the default branch, or the current working-tree diff
   against `HEAD` if no range is given — use `git merge-base` to find `BASE` when only a branch
   is named).
2. Run the plugin's `scripts/workspace` script (path relative to the plugin root:
   `plugins/review-panel/scripts/workspace`, three directories up from this skill's own
   `skills/review-panel/` location) to resolve (and create, git-ignored) the scratch directory for
   this run's artifacts. Do not invent a different scratch location — this script is the single
   source of truth so every stage's temp files land in one place.
3. Run `plugins/review-panel/scripts/review-package BASE HEAD` to write the packaged diff (commit
   list, stat summary, full diff with 10 lines of context) into that workspace as one file. This
   is the ONE shared diff every seat in SPAWN reads — pass its path, not a re-derived `git diff`
   invocation, to each seat's dispatch prompt.
4. If `scripts/workspace` or `scripts/review-package` are unavailable (non-bash environment, or
   scripts missing from this plugin's install), fall back to running `git diff -U10 BASE..HEAD`
   directly and holding the result in-conversation as the shared diff; note this fallback in the
   final report's coverage-honesty statement.

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
