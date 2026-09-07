# Beads swarm fixture provenance

- Specification: `docs/plans/2026-09-02-hermes-beads-skill/implementation-dag-v1.json`, task `t16`.
- Frozen predecessor base: `7dd010076ffd136443d757dbd072b8257f77192b`.
- Harness: Python/pytest driving the production modules under `skills/beads/scripts/`.
- Process model: bounded local child processes in distinct real Git worktrees; no network or live Beads process.
- Crash inventory: `04_crash_resume.json` is checked against hook traces recorded by executing the production modules. The lane-freeze flow owns the shared filesystem/journal/checkpoint/pointer boundary inventory; durable-handoff launch and direct tracker close add their flow-specific semantic boundaries. Bootstrap, ownership maintenance, finish-run, and rejection-only hooks are outside AC-T16-004's successful-flow scope.
- Regeneration: fixture verdicts remain reviewed source data; crash coordinates are executable expectations that must exactly equal production traces and therefore cannot validate an incomplete hardcode against itself.
- Verification: `uv run pytest scripts/tests/beads_swarm`

## Containment limitation

These fixtures prove capability refusal, bounded process supervision, immutable
handoff/result validation, and parent-side tracker readback. They do not claim
kernel isolation from a malicious same-UID process: such a process can access
any path or credential permitted to that OS user unless an external sandbox is
also configured.

The corpus contains no accepted divergences. Each JSON document declares hard process and wall-clock bounds used by the executable harness.
