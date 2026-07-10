---
name: review-panel
description: Run the review-panel orchestrator against a diff, PR, or branch — human-interactive by default, or unattended machine output with --mode=agent
argument-hint: "[base..head | branch | PR] [--mode=agent]"
allowed-tools: Task, Read, Grep, Glob, Bash
---

# Review Panel

Human entry point for the review-panel plugin's orchestrator. This command's only job is to
resolve arguments into a review target and a mode, then hand off to the orchestrator skill — it
does not itself implement any part of the 7-stage panel loop.

## Arguments

$ARGUMENTS

Parse the arguments to extract:
- **Review target**: a `base..head` range, a branch name, a PR reference, or (if omitted) the
  current working-tree diff against `HEAD`. Pass this through unparsed to the orchestrator, which
  owns target resolution (including `git merge-base` handling for branch names) per
  `skills/review-panel/SKILL.md`'s "Setup: diff packaging and scratch workspace" section — do not
  re-derive or re-resolve the diff yourself here.
- **Mode flag**: `--mode=agent` if present anywhere in `$ARGUMENTS`, otherwise default to
  human-interactive mode. This is the one piece of state this command is responsible for setting;
  everything else about mode-specific behavior is owned by
  `skills/review-panel/references/dual-mode-contract.md`.

## Action

Invoke the **review-panel** skill (`skills/review-panel/SKILL.md`) as the orchestrator, passing
the parsed review target and mode through. Read `SKILL.md` and its `references/` files — do not
attempt to run the panel from memory of this command file. In particular:

- `skills/review-panel/SKILL.md` — the 7-stage loop (CAST → SPAWN → MERGE → VALIDATE → FIX →
  RE-REVIEW → CONVERGE) and diff-packaging setup.
- `skills/review-panel/references/cast-and-spawn.md`,
  `references/merge-and-validate.md`, `references/fix-and-rereview.md`,
  `references/converge-and-pipeline.md` — full procedural detail per stage.
- `skills/review-panel/references/dual-mode-contract.md` — exactly how each mode's output is
  shaped; read this before producing any final output.

**Mode selection affects only final output shape; every stage of the panel loop runs identically
in both modes.** There is no separate "agent orchestrator" or "human orchestrator" — one
orchestrator, one 7-stage loop, and the `--mode=agent` flag changes nothing about CAST, SPAWN,
MERGE, VALIDATE, FIX, RE-REVIEW, or CONVERGE. It only changes what gets emitted once CONVERGE (or
a circuit-break) is reached.

### Human-interactive mode (default — no `--mode=agent`)

Run the full loop while narrating progress conversationally as each stage completes, per
`dual-mode-contract.md`'s "Human-interactive mode" section. When the loop ends, produce the
`# Review Panel Report` markdown structure specified there (Cast, Findings, Fixes Applied,
Re-Review, Convergence, Coverage Honesty), then drive the interactive apply loop described in
that same file: offer to show the diff as committed, run a manual additional round on a specific
disputed finding, or accept as final. If the run circuit-broke, hand off the diagnosis clearly
instead of guessing at a resolution.

### Unattended mode (`--mode=agent` present in `$ARGUMENTS`)

Run the identical loop with no interactive prompts, no clarifying questions, and no
partial/streaming output. When the loop reaches `converged` or `circuit_broken` (or fails to
execute at all, i.e. `error`), emit **exactly one JSON object** — the contract shape defined in
`dual-mode-contract.md`'s "`mode:agent` JSON contract" section — as the final and only output.
Nothing else should follow it.

## Wiring into automation

This mode exists specifically so the same panel can run unattended as a `foundry.yaml`
`post-feature` gate. See `skills/review-panel/references/dual-mode-contract.md`'s "Wiring to
`foundry`" section for the concrete, copy-pasteable gate example and how the JSON's `status`
field maps to `decision_on_failure`.

## Example usage

```
/review-panel
/review-panel main..feature/checkout-fix
/review-panel feature/checkout-fix --mode=agent
/review-panel 1a2b3c4..HEAD --mode=agent
```

- No arguments: reviews the current working-tree diff against `HEAD`, human-interactive.
- A range or branch: reviews that diff, human-interactive.
- `--mode=agent` anywhere: same target resolution, unattended JSON-only output — this is the form
  a `foundry.yaml` gate or other automation harness should invoke.
