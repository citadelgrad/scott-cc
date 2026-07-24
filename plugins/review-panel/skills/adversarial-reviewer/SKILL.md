---
name: adversarial-reviewer
description: Red-teams code, PRs, and designs by attacking them — hunting for bugs, security holes, hostile/malformed input handling, and weaknesses in existing design findings. Use whenever code, a PR, or a design needs an adversarial pass, whether standalone or as part of a larger review. Not gated behind any other workflow — always available on request. Not for constructive design-quality lenses with no attack framing (use design-review or red-flags) or for generating a second independent design from scratch (use design-it-twice).
argument-hint: "[file, PR, diff, or design doc to attack]"
allowed-tools: Read, Grep, Glob, Task
---

# Adversarial Reviewer

This skill is authored from scratch for this plugin (not vendored). It is a **core, always-cast reviewer** — invoke it directly any time an adversarial pass is wanted, standalone or as one seat in a larger review panel. It is never gated behind Dynamic Workflows or any other skill.

> **Cross-reference:** listed as the core/always-cast "Correctness / Adversarial" seat in [`plugins/review-panel/reviewers/persona-catalog.md`](../../reviewers/persona-catalog.md).

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
7. **Must-find-at-least-one-issue fallback**: if steps 1-5 genuinely turn up nothing — no bug, no security hole, no hostile-input gap, no attackable prior finding — do not emit an empty Issues section and do not manufacture a fake bug either. Instead, note the single most fragile assumption the code relies on (the "this is safe because X" claim that is *least* battle-tested, even without a concrete counterexample to prove it wrong yet). This keeps "nothing found" and "not looked hard enough" distinguishable, and gives a human a starting point if they want to push further. **This fallback finding is manufactured, not discovered** — it must be tagged per the Output Contract below and is never treated as equivalent to a genuine attack finding downstream (see the MERGE promotion exclusion in [`references/merge-and-validate.md`](../review-panel/references/merge-and-validate.md)).

## Output Contract

Findings **must** be emitted using the shared reviewer output contract defined in [`contracts/reviewer-output.md`](../../contracts/reviewer-output.md): Strengths / Issues (Critical, Important, Minor, each with file:line) / Recommendations / Assessment.

This is the **human-interactive** output shape (the default). For unattended/algorithmic use —
wiring this skill into a `foundry.yaml` gate or a triage-style pipeline — invoke with
`--mode=agent` instead, which emits a single machine-parseable JSON blob (top-level `verdict` +
`findings` array, each finding carrying `persona`, `severity`, `promoted`, and `manufactured`
fields) instead of the narrative report below. See
[`references/dual-mode-contract.md`](references/dual-mode-contract.md) for the full JSON shape,
field-by-field notes, and a concrete `foundry.yaml` gate example. That contract deliberately reuses
review-panel's own `--mode=agent` field naming (`references/dual-mode-contract.md` in the
`review-panel` skill) so downstream tooling can consume both skills' agent-mode output with one
shared parsing path.

Adapt that contract's framing to the adversarial angle:

- **Strengths**: defenses that are already in place and actually hold up under attack (be honest — don't manufacture praise).
- **Issues — Critical**: exploitable bugs, security holes, or a design finding that is demonstrably wrong under a concrete counterexample.
- **Issues — Important**: hostile-input handling gaps, missing validation at trust boundaries, design-finding claims that hold in the common case but not at stated edge/scale conditions.
- **Issues — Minor**: hardening opportunities, defense-in-depth suggestions, weak but not exploitable assumptions.
- Every issue: file:line reference, what's wrong, **the concrete attack or input that triggers it**, why it matters, and a fix if not obvious.
- **Recommendations**: hardening priorities beyond the specific issues found.
- **Assessment**: `Ready to merge?` [Yes | No | With fixes], plus 1-2 sentence reasoning stated as an adversary would — "an attacker/hostile input could still X" rather than generic risk language.

### Manufactured-finding marker (must-find-at-least-one-issue fallback output)

A finding produced via Attack Procedure step 7 (the bulletproof-code fallback) is **not** a normal Issue and must be marked so it can never be mistaken for one downstream:

- **Severity is always Minor** — the panel's severity enum is closed to `Critical`/`Important`/`Minor` (same closed-enum rule `taste-review` follows per `persona-catalog.md`), so a manufactured finding is filed under **Minor** and capped there. It is never Critical or Important regardless of how it's worded or how many other seats independently produce a similar fallback note for the same target.
- **Carries an explicit `manufactured: true` marker**, appended inline exactly like the existing `sovereignty: human-required` marker convention (see `skills/data-steward/SKILL.md`'s Output Contract): `Minor — file:line — <fragile assumption> — manufactured: true`.
- **The marker is permanent** — it travels with the finding through MERGE/VALIDATE/FIX like `sovereignty` does, and no downstream stage may strip it, upgrade the finding's severity past Minor, or treat it as a genuine attack finding.

Example (illustrates the distinction from a genuine finding in the same output):

```
### Issues

#### Minor
1. **Retry loop assumes the downstream queue never permanently rejects a message**
   - File: worker.py:142
   - Issue: no bug or hostile-input path could be constructed against this file — the retry/backoff
     logic, input validation, and error handling all held up under attack. The most fragile
     surviving assumption is that `queue.publish()` will eventually succeed on retry; there's no
     concrete counterexample today, but no dead-letter path exists if that assumption ever breaks.
   - manufactured: true
   - Fix: none required now; consider a dead-letter queue if this assumption is ever violated.
```

## Critical Rules

**DO:**
- Cover all four scope areas (bugs, security, hostile input, existing findings) every time — don't silently drop one
- Use the clean-room-alternative isolation pattern when independence matters (existing findings to attack, or a design rationale already in context)
- Give a concrete attack/input for every issue, not just a category name
- Calibrate severity honestly — adversarial framing is not license to inflate everything to Critical
- Emit output in the shared `contracts/reviewer-output.md` structure so panel aggregation works
- Tag any must-find-at-least-one-issue fallback finding with `manufactured: true` and file it as Minor, every time — never leave it unmarked or let it masquerade as a genuine finding

**DON'T:**
- Skip attacking existing findings just because they came from a credible source — Scope item 4 exists precisely to challenge credible-looking conclusions
- Let a prior reviewer's framing anchor what you look for
- Report a finding without a file:line and a concrete triggering scenario
- Treat this skill as gated behind a panel session — it is standalone-invocable on any target, any time
- Rate a manufactured (fallback) finding above Minor, or omit its `manufactured: true` marker, under any circumstance — including when another seat happens to raise a similar note independently
