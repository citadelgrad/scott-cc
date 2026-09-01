# Orchestrator Context Architecture

Use this contract whenever a skill dispatches agents, sequences downstream skills, scans a
potentially unbounded corpus, loops across rounds or items, or resumes after a pause. Leaf skills
that inspect one already-bounded target do not need orchestration machinery.

## Required contract

Every orchestrator must contain a `## Context architecture contract` section with these exact
labels so `scripts/verify_orchestration_contracts.py` can enforce the class-level rule:

- **Scope contract:** what is measured before target content enters the parent context, every hard
  rejection threshold, and the terminal status for an oversized target.
- **Fan-out contract:** maximum concurrency, batch size, number of batches, and total assignments.
  Use workflow-specific values supported by the cost of that workflow.
- **Artifact contract:** paths and SHA-256 hashes for bulky handoffs plus byte and cardinality limits
  for every parent-visible manifest and final summary.
- **Failure contract:** fail-closed behavior when isolation, workers, artifact persistence, schema
  validation, or packaging is unavailable. An inline or same-context fallback is not fail-closed.
- **Continuation contract:** checkpoint identity, content hashes, replay/idempotency behavior, and a
  mechanically verifiable fresh-process rule. Say `not resumable` for finite one-shot workflows.
- **Mechanical-test contract:** the repository test module that asserts each declared scope,
  fan-out, byte, cardinality, and continuation bound.

## Architecture rules

Resolve scope with a deterministic tool or disposable worker and return only counts; do not read a
large target into the orchestrator and reject it afterward. Workers read bulky inputs by artifact
path. Workers write detailed results to artifacts and return bounded manifests containing status,
counts, paths, and hashes. The parent never aggregates raw worker reports.

Continuation is a new process, not another turn in an already-full conversation. A checkpoint must
bind the normalized request and all referenced artifacts by SHA-256, be atomically claimed before
side effects resume, and reject hash mismatch, duplicate consumption, or an unverifiable fresh
process. If the platform cannot provide those guarantees, stop with a named failure status.

Every limit must have a mechanical assertion. Tests that only search for words such as "bounded"
or "finite" are insufficient: assert the actual numbers, statuses, artifact names, hash algorithm,
and fresh-process marker. Register the skill and its test module in
`ORCHESTRATOR_CONTRACTS` in `scripts/verify_orchestration_contracts.py`.

## Keep leaf skills small

Do not add checkpoints, manifests, or workers to a one-shot lens with an intrinsically finite input.
The contract exists to bound real multiplicative growth, not to make every skill look like a
workflow engine.
