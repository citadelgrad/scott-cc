---
name: review-panel
description: Run the review-panel orchestrator against a diff, PR, or branch — human-interactive by default, or unattended machine output with --mode=agent; narrow the review scope with --lite, --medium, or --auto
argument-hint: "[base..head | branch | PR] [--mode=agent] [--lite | --medium | --auto] [--resume PATH --checkpoint-sha256 HEX]"
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
- **Tier flag**: `--lite`, `--medium`, or `--auto` if present anywhere in `$ARGUMENTS`, otherwise
  default to full (unnarrowed) review scope. These three are presence-only flags, pairwise mutually
  exclusive with each other (two or more together is a hard error), and independently composable
  with `--mode=agent` in any order. `--auto` defers the concrete tier choice to a pre-CAST resolver
  over cheap diff-size and sensitive-path signals rather than selecting a tier directly. This is the
  other piece of state this command is responsible for setting; everything else about narrowed-tier
  behavior — the per-stage guarantees each tier gives, and `--auto`'s resolver and decision table —
  is owned by `skills/review-panel/references/lite-mode.md`.
- **Resume flag**: `--resume PATH --checkpoint-sha256 HEX` resumes the checkpoint at `PATH`. Both
  arguments are required together. The expected hash is supplied by the prior invocation, not
  recomputed into the command by the resumed process. Resume is mutually exclusive with
  a new review target and with tier flags: the checkpoint already owns the target, tier, cast list,
  round number, and progress counters. Accept it only when the new process has
  `REVIEW_PANEL_FRESH_RESUME=1` **and** `REVIEW_PANEL_SESSION_ID` exists and differs from the
  checkpoint's `origin_session_id`; otherwise stop with `fresh_context_unverifiable`. The plugin's
  SessionStart hook supplies the session ID. Reject a missing/unreadable path before doing any
  review work. After structure/hash checks, run
  `plugins/review-panel/scripts/checkpoint-claim PATH "$REVIEW_PANEL_SESSION_ID" HEX`; reject its
  `checkpoint_hash_mismatch` or `checkpoint_already_consumed` result. A plain slash-command
  resume in the current conversation is forbidden because it defeats the checkpoint boundary.

## Action

Invoke the **review-panel** skill (`skills/review-panel/SKILL.md`) as the orchestrator, passing
the parsed target, mode, and optional resume path through. Read `SKILL.md`, then load stage
references **one at a time, just-in-time** immediately before that stage. **Never preload all
references** or retain a completed stage's procedure in the parent context. Do not attempt to run
the panel from memory of this command file. The reference map is:

- `skills/review-panel/SKILL.md` — the 7-stage loop (CAST → SPAWN → MERGE → VALIDATE → FIX →
  RE-REVIEW → CONVERGE) and diff-packaging setup.
- `skills/review-panel/references/cast-and-spawn.md`,
  `references/merge-and-validate.md`, `references/fix-and-rereview.md`, and
  `references/converge-and-pipeline.md` — load only the file for the stage being entered.
- `skills/review-panel/references/dual-mode-contract.md` — exactly how each mode's output is
  shaped; read this before producing any final output.
- `skills/review-panel/references/lite-mode.md` — the `--lite`/`--medium`/`--auto` flag contract,
  each tier's narrowed guarantees per stage, and `--auto`'s resolver and decision table; read this
  before running a tier-flagged invocation.

**Mode selection affects only final output shape; every stage of the panel loop runs identically
in both modes.** There is no separate "agent orchestrator" or "human orchestrator" — one
orchestrator, one 7-stage loop, and the `--mode=agent` flag changes nothing about CAST, SPAWN,
MERGE, VALIDATE, FIX, RE-REVIEW, or CONVERGE. It only changes what gets emitted once CONVERGE (or
a circuit-break) is reached.

### Human-interactive mode (default — no `--mode=agent`)

Run the loop without streaming raw findings or subagent reports into the conversation. Emit at
most one short progress line per stage from its bounded manifest. When the loop ends, dispatch the
final synthesis worker and render its bounded `final-summary.json` as the `# Review Panel Report`
structure specified there (Cast, Findings, Fixes Applied, Re-Review, Convergence, Coverage
Honesty). Any requested additional round is a new target invocation launched with `claude -p` in a
fresh process, never continued in this parent conversation. If the run circuit-broke, hand off the
diagnosis clearly instead of guessing at a resolution.

### Unattended mode (`--mode=agent` present in `$ARGUMENTS`)

Run the identical loop with no interactive prompts, no clarifying questions, and no
partial/streaming output. When the invocation reaches any terminal status (including `checkpointed`, `converged`,
`circuit_broken`, or `error`), emit **exactly one JSON object** — the contract shape defined in
`dual-mode-contract.md`'s "`mode:agent` JSON contract" section — as the final and only output.
Nothing else should follow it.

### Terminal-state hard stop

After emitting any terminal status (`converged`, `capped`, `checkpointed`, `escalated`,
`circuit_broken`, or `error`), make no more tool calls and start no follow-up review, issue-creation,
acceptance-criteria, or fix round. Residual work is reported, not silently continued. Only a new
user invocation or a fresh-process `--resume` command may start more work.

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
/review-panel --lite
/review-panel main..feature/checkout-fix --medium
/review-panel feature/checkout-fix --auto --mode=agent
REVIEW_PANEL_FRESH_RESUME=1 claude -p "/review-panel --resume .review-panel/workspace/converge-state-round2.json --checkpoint-sha256 <sha256>"
```

- No arguments: reviews the current working-tree diff against `HEAD`, human-interactive.
- A range or branch: reviews that diff, human-interactive.
- `--mode=agent` anywhere: same target resolution, unattended JSON-only output — this is the form
  a `foundry.yaml` gate or other automation harness should invoke.
- `--lite` or `--medium` anywhere: same target resolution, narrowed review scope per
  `references/lite-mode.md`'s per-tier guarantees — no flag defaults to full (unnarrowed) scope.
- `--auto` anywhere: same target resolution, tier chosen for you by the pre-CAST resolver in
  `references/lite-mode.md`'s "Auto resolution" section, based on the diff's size and whether it
  touches a sensitive path.
