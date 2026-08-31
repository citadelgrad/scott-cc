# Review Panel 1.0: Context-Bounded and Restartable

Review Panel 1.0 changes the orchestration contract so a comprehensive review can no longer grow the parent Claude Code conversation without bound. Detailed stage data stays in filesystem artifacts, the parent receives small manifests, and every continuing full review round resumes in a fresh process from a verified one-shot checkpoint.

See the [visual engineering brief](reports/review-panel-context-hardening.html) for a diagrammed summary.

## Why this is a major release

The old workflow treated one conversation as the lifetime of the review. That made raw stage output, validation detail, fixes, and repeated convergence rounds compete for the same context window. Session analysis found repeated compaction in 7 of 10 exact Review Panel invocations and captured prompt-length failures above Claude Code's 200,000-token maximum.

Version 1.0 deliberately breaks several permissive behaviors:

- One invocation accepts exactly one review target.
- Targets above 25 files or 1,500 changed lines fail before CAST and must be split.
- Missing artifact packaging or subagent support fails closed; there is no inline-diff fallback.
- Continuing dirty rounds stop at a checkpoint instead of dispatching another SPAWN in the same conversation.
- Resume requires a fresh Claude Code process, a different session ID, and the checkpoint SHA-256 emitted by the prior invocation.
- A consumed, copied, hard-linked, or mutated checkpoint cannot be replayed.

## New orchestration contract

### Bounded setup

A disposable scope resolver writes `$WORKSPACE/scope.json` with only file count, changed-line count, sensitive-path status, and the reviewed-target hash. The parent never captures the full per-file stat or packaged diff.

### Artifact-only stages

CAST, SPAWN, MERGE, VALIDATE, FIX, and RE-REVIEW write detailed output under `.review-panel/workspace/`. Each worker returns a manifest of at most 2 KiB containing paths, hashes, statuses, counts, and bounded coverage notes.

Primary artifacts include:

- `cast.json`
- `seat-artifacts/<seat-id>.json`
- `merged-findings.json`
- `validator-artifacts/<batch-id>.json`
- `validated-findings.json`
- `fix-report.json`
- `sovereignty-guard.json`
- `rereview-report.json`
- `final-report.md` or `final-result.json`
- `final-summary.json`

### Finite fan-out

- At most 8 total seats and 2 supplementary seats.
- At most 12 bounded agent-type candidates.
- At most 25 validator assignments after applying Critical-finding multipliers.
- At most 5 validator batches and 5 concurrent validator workers.
- Oversized finding sets return `finding_scope_too_large`; they are never truncated or under-validated.

### Checkpointed convergence

Every dirty full-mode round that may continue writes a checkpoint of at most 2 KiB and terminates the current invocation. The checkpoint references separately hashed progress, sovereignty, cast, and packaged-diff artifacts rather than embedding findings or reasoning.

The emitted continuation command has this shape:

```bash
REVIEW_PANEL_FRESH_RESUME=1 claude -p "/review-panel --resume .review-panel/workspace/converge-state-round2.json --checkpoint-sha256 <sha256>"
```

The standalone Review Panel plugin registers a `SessionStart` hook that exposes `REVIEW_PANEL_SESSION_ID`. Resume fails unless the new session differs from the checkpoint's `origin_session_id`.

Before any review work, `scripts/checkpoint-claim` verifies the externally supplied SHA-256 and atomically claims that content hash. Replay returns `checkpoint_already_consumed`; mutation returns `checkpoint_hash_mismatch`.

### Bounded final output

A final synthesis worker reads detailed artifacts and writes the complete audit. The parent reads only `final-summary.json`, capped at 4 KiB and five finding summaries. Detailed evidence remains available by path and SHA-256 without being reloaded into the orchestration conversation.

## Status and automation semantics

Terminal statuses are explicit and fail closed:

- `converged`: final round is clean with no unresolved or skipped findings.
- `checkpointed`: continuation is available only through the emitted fresh-process resume command.
- `escalated`: only sovereignty-required findings remain.
- `capped`: a narrowed tier exhausted its round budget with ordinary findings unresolved.
- `circuit_broken`: convergence stalled or reached the hard invocation cap.
- `error`: packaging, contract, sovereignty, or execution failure.

Foundry validates required fields for each status with `jq -e`. Unknown, null, or malformed statuses fail the gate. Skipped fixes remain unresolved, and ordinary residual findings cannot pass under `escalated`.

## Operational limits

| Boundary | Limit |
|---|---:|
| Review target | 25 files / 1,500 changed lines |
| Parent stage manifest | 2 KiB |
| Total seats | 8 |
| Supplementary seats | 2 |
| Agent-type candidates | 12 entries / 2 KiB |
| Validator assignments | 25 |
| Validator batches | 5 |
| Concurrent validator workers | 5 |
| Checkpoint | 2 KiB |
| Final parent summary | 4 KiB / 5 finding summaries |
| Logical review run | 8 fresh invocations |

## Upgrade notes

1. Update the Review Panel plugin to 1.0.0 and restart Claude Code so the new `SessionStart` hook is loaded.
2. Do not paste a checkpoint resume command into the conversation that produced it. Run the emitted `claude -p` command as a new process.
3. Split targets that exceed the scope gate into coherent commit ranges or path groups.
4. Ensure the runtime supports subagents and can write `.review-panel/workspace/`; Review Panel no longer degrades to inline execution.
5. Update automation to recognize `checkpointed`, `capped`, `escalated`, `circuit_broken`, and `error` as distinct statuses and validate the complete status-specific contract.

## Verification

The release implementation was checked with:

- the full repository pytest suite;
- dedicated context-budget regression tests;
- black-box checkpoint claim and replay tests;
- SessionStart identity-hook tests;
- Ruff on changed Python files;
- plugin manifest and skills-distribution verifiers;
- Claude plugin validation and component inspection; and
- `git diff --check`.
