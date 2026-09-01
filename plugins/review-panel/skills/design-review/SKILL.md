---
name: design-review
description: "Use when reviewing a file, module, or PR for overall design quality\
  \ and you want a comprehensive, prioritized assessment rather than a single-lens\
  \ check. Orchestrates a structured design review via a diagnostic funnel \u2014\
  \ complexity triage through structural, interface, and surface checks to a full\
  \ red-flags sweep. Not for applying one specific lens (use that skill directly)\
  \ or evolutionary analysis (use code-evolution)."
argument-hint: '[file, module, or PR to review]'
allowed-tools: Read, Grep
metadata:
  category: technique
  triggers:
  - design-review
  - code-review
  - architecture
---

# Design Review Orchestrator

## When to Use
- Reviewing a file, module, or PR for overall design quality
- Wanting a comprehensive, prioritized assessment through a diagnostic funnel
- Running complexity triage through structural, interface, and surface checks
- Orchestrating multiple design lenses in the correct sequence

When invoked with $ARGUMENTS, scope the entire review to the specified target. Read the target code first, then proceed through the phases below in order. This skill orchestrates other skills from Clairvoyance (https://clairvoyance.fyi). It works best when the full collection is installed.

This skill does not replace individual lenses. It sequences them into a diagnostic funnel that moves from broad to narrow, skipping work when early phases find nothing actionable.

## Context architecture contract

- **Scope contract:** Before the parent reads target content, a disposable resolver writes counts to
  `design-review-scope.json`. A single-target review may contain at most **20 files** and **1,200
  changed lines** after generated/vendor exclusions. Reject larger targets with `SCOPE_TOO_LARGE`
  and suggested path/range partitions; a narrower tier never bypasses this gate.
- **Fan-out contract:** Dispatch at most **4 target workers concurrently**, **4 targets per batch**,
  **3 batches / 12 target assignments**, and retain at most **40 candidate findings**. Verification
  assigns exactly one challenger per retained candidate, in batches of at most 4, with **40 total
  validator assignments**.
- **Artifact contract:** Scope, triage, deep-dive, finding, and validation detail stays in hashed
  artifacts. Workers return manifests of at most **2 KiB**; final synthesis returns at most **4
  KiB** and the top **12 finding IDs**, with full findings available only by artifact path and
  SHA-256.
- **Failure contract:** Missing workflow isolation, scope resolver, artifact persistence, hashes,
  or schema-valid worker output stops with `ISOLATION_UNAVAILABLE` or
  `ARTIFACT_CONTRACT_FAILED`. Never read an oversized target into the parent and never fall back to
  a same-conversation per-file review.
- **Continuation contract:** This is a finite one-shot workflow and is **not resumable**. Finishing,
  rejecting, or failing a run is terminal; another scope requires a fresh invocation.
- **Mechanical-test contract:** `scripts/tests/test_design_review_context_budget.py` asserts the
  scope, worker, batch, finding, validator, manifest, summary, and no-fallback bounds.

## Diagnostic Funnel

### Phase 1: Complexity Triage

Apply **complexity-recognition** checks against the target.

- Identify the three symptoms: change amplification, cognitive load, unknown unknowns
- Trace any symptoms to root causes: dependencies or obscurity
- Weight findings by the complexity formula: high-traffic code first

This phase determines whether the target has measurable complexity problems. If it does, subsequent phases diagnose where.

### Phase 2: Structural Review

Apply these lenses to the target's module-level architecture:

- **module-boundaries**: Are the boundaries drawn around knowledge domains or around steps in a process?
- **deep-modules**: Does each module provide powerful functionality behind a simple interface? Check for classitis, pass-through methods and shallow wrappers.
- **abstraction-quality**: Does each layer provide a genuinely different way of thinking, or do adjacent layers duplicate the same abstraction?

Focus on the modules that Phase 1 identified as highest-complexity. If Phase 1 found nothing, scan the largest or most-connected modules.

### Phase 3: Interface Review

Apply these lenses to the interfaces exposed by the modules from Phase 2:

- **information-hiding**: Does the interface leak implementation details? Check for back-door leakage (shared knowledge not in any interface).
- **general-vs-special**: Does the interface mix general-purpose mechanisms with special-case knowledge? Check for boolean parameters serving one caller.
- **pull-complexity-down**: Are callers forced to handle complexity the module could absorb? Check for exposed edge cases, required configuration and exceptions that could be defined away.
- **error-design**: Are errors defined out of existence where possible? Check for catch-and-ignore, overexposed exceptions and error handling longer than the happy path.

### Phase 4: Surface Review

Apply these lenses to naming and documentation:

- **naming-obviousness**: Do names create precise mental images? Check the isolation test: seen without context, could the name mean almost anything?
- **comments-docs**: Do comments capture what the code cannot say (intent, rationale, constraints)? Check for comments that repeat code and implementation details contaminating interface documentation.

### Phase 5: Red Flags Sweep

Run the full **red-flags** 17-flag checklist against the target. Any flag triggered in Phases 1-4 will already be marked. This phase catches flags that earlier phases may not have surfaced (especially Process flags 15-17: No Alternatives Considered, Tactical Momentum, Catch-and-Ignore).

## Early Termination

If Phase 1 finds no measurable complexity AND Phase 5 triggers zero flags, stop. Report the target as clean. Do not force findings where none exist.

## Prioritization

Rank findings in this order:

1. **Syndrome clusters**: Multiple flags pointing to the same root cause (e.g., information leakage + conjoined methods + repetition all stemming from one misplaced boundary). These indicate systemic issues. Fixing the root cause resolves all flags in the cluster.
2. **Boundary issues**: Information leakage, module boundary problems and abstraction mismatches. These compound over time and infect adjacent code.
3. **Canary flags**: Hard to Pick Name, Hard to Describe, Non-obvious Code, No Alternatives Considered. These are the cheapest signals. Catch them and the structural flags never materialize.
4. **Structural issues**: Shallow modules, pass-through methods, classitis. These require refactoring but affect a bounded area.
5. **Surface issues**: Naming and documentation problems. Important but lowest cost to fix and lowest risk if deferred.

## Reviewing at Scale

The funnel above is written for one bounded target. Resolve scope counts mechanically before the
parent reads content. If the target exceeds 20 files or 1,200 changed lines, stop with
`SCOPE_TOO_LARGE` and suggest coherent path or commit-range partitions. Each partition is a new
invocation; do not process them serially in this conversation.

For an in-budget multi-file target, Dynamic Workflows are mandatory. See
[references/workflow-builder.md](references/workflow-builder.md). If isolated workflows are not
available, stop with `ISOLATION_UNAVAILABLE`; there is no same-context large-scope fallback.

## Limitations
- Use this skill only when the task clearly matches the scope described above.
- Orchestrates other skills — works best when the full Clairvoyance collection is installed.
- Rejects targets over 20 files or 1,200 changed lines; review suggested partitions separately.
- Not for applying a single specific lens — invoke that skill directly instead.
- Stop and ask for clarification if the review scope, target, or priority criteria are unclear.
