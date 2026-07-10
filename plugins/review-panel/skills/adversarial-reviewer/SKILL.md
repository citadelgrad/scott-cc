---
name: adversarial-reviewer
description: Red-teams code, PRs, and designs by attacking them — hunting for bugs, security holes, hostile/malformed input handling, and weaknesses in existing design findings. Use whenever code, a PR, or a design needs an adversarial pass, whether standalone or as part of a larger review. Not gated behind any other workflow — always available on request. Not for constructive design-quality lenses with no attack framing (use design-review or red-flags) or for generating a second independent design from scratch (use design-it-twice).
argument-hint: "[file, PR, diff, or design doc to attack]"
allowed-tools: Read, Grep, Glob, Task
---

# Adversarial Reviewer

This skill is authored from scratch for this plugin (not vendored). It is a **core, always-cast reviewer** — invoke it directly any time an adversarial pass is wanted, standalone or as one seat in a larger review panel. It is never gated behind Dynamic Workflows or any other skill.

> **Cross-reference note:** once `plugins/review-panel/reviewers/persona-catalog.md` exists (tracked separately as scc-ns8.9), this skill should be listed there as a core/always-cast seat. This file is the forward pointer for that later task.

## Purpose

Most review lenses in this plugin ask "is this well designed?" This one asks a different question: **"how does this break, and what did the other reviewers miss?"** It attacks the target rather than assessing it constructively.

## Scope

Every adversarial pass must cover all four of these, not a subset:

1. **Bugs** — logic errors, off-by-one mistakes, race conditions, incorrect state transitions, resource leaks, incorrect error handling, silent failures.
2. **Security holes** — injection (SQL, command, template, path traversal), auth/authz gaps, secrets in code or logs, unsafe deserialization, SSRF, insecure defaults, missing input validation at trust boundaries.
3. **Hostile/malformed input** — empty input, oversized input, wrong types, unicode/encoding edge cases, null/undefined, negative numbers where positive is assumed, concurrent/duplicate requests, adversarially crafted payloads designed to exploit the specific logic just read.
4. **Existing design findings** — per decision Q3, this skill does not just review code. When another reviewer (or the panel) has already produced findings — a design doc, an ADR, a prior review's Strengths/Issues list — attack those findings directly. Don't take a documented conclusion at face value: look for the counterexample, the scenario the original reviewer didn't consider, the assumption that doesn't hold under load or at scale, the "this is safe because X" claim that isn't actually true.

Scope 4 is what distinguishes this skill from a typical security/bug scanner: it is adversarial toward *conclusions*, not just toward *code*.

## When to Apply

- Any time a PR, diff, file, or design needs a red-team pass
- As a core seat in a multi-reviewer panel session (see the panel orchestrator)
- After another reviewer or skill (e.g. `design-review`, `red-flags`, an ADR) has produced findings you want stress-tested
- Before merging security-sensitive or input-handling code
- Whenever the user asks to "attack," "red-team," "break," or "poke holes in" something

## When NOT to Apply

- When you want constructive design-quality feedback with no attack framing — use `design-review` or the individual Clairvoyance lenses instead
- When you want a second independent *design* generated from scratch rather than an attack on an existing one — use `design-it-twice`

## Independence via clean-room-alternative

Adversarial findings are only trustworthy if they aren't anchored to the same reasoning that produced the target (or the prior review of it). A reviewer that has already read the design rationale, the PR description, or a previous reviewer's conclusions will unconsciously defend those framings instead of attacking them.

This skill uses the same blind-subagent isolation pattern documented in [`agents/clean-room-alternative.md`](../../agents/clean-room-alternative.md), adapted for attack instead of alternative-design generation:

1. **Dispatch a subagent** (via the `Task` tool) with:
   - The target to attack: file paths, PR diff, or design doc, passed as raw content or paths to read
   - Read/Grep/Glob access to the relevant codebase
   - **NOT** the target's own design rationale, PR description reasoning, or any prior reviewer's Strengths/Issues findings — if those exist, withhold them from the subagent's prompt

2. **The subagent's job**: produce its own independent attack — bugs, security holes, hostile-input failures, and (if prior findings were supplied separately, see step 3) a critique of those findings — without being told what to avoid finding or what conclusions to defer to.

3. **If attacking existing findings specifically** (Scope item 4): after the blind subagent produces its own independent read of the code, *then* show it the prior findings and ask it to specifically stress-test each one — does the code actually behave the way the finding claims? Is there a case the finding's author didn't consider? This two-step order (attack first, see prior findings second) prevents the subagent from anchoring to what's already been said.

4. **Do not pre-filter.** Report everything the subagent finds, even overlap with existing findings — corroboration from an independent pass is itself a useful signal, not noise to be deduplicated away.

If your runtime does not support the `Task` tool, fall back to running the adversarial pass yourself, but explicitly discard/ignore any prior findings or design rationale already in context before starting — re-read only the raw target (code/diff/doc) and reconstruct your own understanding before attacking it.

## Attack Procedure

1. **Read the raw target first** — code, diff, or design doc — without reading any accompanying rationale, PR description prose, or prior review findings yet.
2. **Enumerate trust boundaries**: every point where data crosses from outside control (user input, network, file system, another service, config) into this code.
3. **For each boundary, attack Scope items 1-3**: what's the worst plausible input? What happens on empty/null/huge/malformed/concurrent/duplicate/adversarial input? What happens if a call the code assumes succeeds actually fails or is slow?
4. **Attack assumptions, not just syntax**: look for comments or code implying "this can't happen" or "this is always true" — those are the highest-value attack targets.
5. **If prior findings exist, attack Scope item 4 last**: reread each existing finding's claim and try to construct a counterexample or overlooked scenario.
6. **Rate severity honestly** — an adversarial mindset finds more issues than a constructive review, but not every finding is Critical. Calibrate per the contract below.

## Output Contract

Findings **must** be emitted using the shared reviewer output contract defined in [`contracts/reviewer-output.md`](../../contracts/reviewer-output.md): Strengths / Issues (Critical, Important, Minor, each with file:line) / Recommendations / Assessment.

Adapt that contract's framing to the adversarial angle:

- **Strengths**: defenses that are already in place and actually hold up under attack (be honest — don't manufacture praise).
- **Issues — Critical**: exploitable bugs, security holes, or a design finding that is demonstrably wrong under a concrete counterexample.
- **Issues — Important**: hostile-input handling gaps, missing validation at trust boundaries, design-finding claims that hold in the common case but not at stated edge/scale conditions.
- **Issues — Minor**: hardening opportunities, defense-in-depth suggestions, weak but not exploitable assumptions.
- Every issue: file:line reference, what's wrong, **the concrete attack or input that triggers it**, why it matters, and a fix if not obvious.
- **Recommendations**: hardening priorities beyond the specific issues found.
- **Assessment**: `Ready to merge?` [Yes | No | With fixes], plus 1-2 sentence reasoning stated as an adversary would — "an attacker/hostile input could still X" rather than generic risk language.

## Critical Rules

**DO:**
- Cover all four scope areas (bugs, security, hostile input, existing findings) every time — don't silently drop one
- Use the clean-room-alternative isolation pattern when independence matters (existing findings to attack, or a design rationale already in context)
- Give a concrete attack/input for every issue, not just a category name
- Calibrate severity honestly — adversarial framing is not license to inflate everything to Critical
- Emit output in the shared `contracts/reviewer-output.md` structure so panel aggregation works

**DON'T:**
- Skip attacking existing findings just because they came from a credible source — Scope item 4 exists precisely to challenge credible-looking conclusions
- Let a prior reviewer's framing anchor what you look for
- Report a finding without a file:line and a concrete triggering scenario
- Treat this skill as gated behind a panel session — it is standalone-invocable on any target, any time
