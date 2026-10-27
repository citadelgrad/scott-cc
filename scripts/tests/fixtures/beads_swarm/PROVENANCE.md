# Beads swarm fixture provenance

- Specification: `docs/plans/2026-09-02-hermes-beads-skill/implementation-dag-v1.json`, task `t16`.
- Frozen predecessor base: `7dd010076ffd136443d757dbd072b8257f77192b`.
- Harness: Python/pytest driving the production modules under `skills/beads/scripts/`.
- Process model: bounded local child processes in distinct real Git worktrees; no network or live Beads process.
- Crash inventory: `04_crash_resume.json` is checked against hook traces recorded by executing fourteen production flows: initial start publication, lane freeze/verification/review, candidate build/apply, durable handoff launch/accept, direct tracker close, front claim, eligible lane close, protected-action resolution, one-shot approval consume, and finish-run. Exact boundary-family membership prevents journal/native/checkpoint/pointer/approval omissions; every declared point is crash-injected and resumed or classified from durable state, with native-effect counts proving no blind replay.
- Recovery breadth: the suite also interrupts one direct close on two successive attempts before proving third-attempt convergence, and runs two distinct root run IDs consecutively against one physical repository/run root.
- Regeneration: fixture verdicts remain reviewed source data; crash coordinates are executable expectations that must exactly equal production traces and therefore cannot validate an incomplete hardcode against itself.
- Verification: `uv run pytest scripts/tests/beads_swarm`

## Containment limitation

These fixtures prove capability refusal, bounded process supervision, immutable
handoff/result validation, and parent-side tracker readback. They do not claim
kernel isolation from a malicious same-UID process: such a process can access
any path or credential permitted to that OS user unless an external sandbox is
also configured.

The corpus contains no accepted divergences. Each JSON document declares hard process and wall-clock bounds used by the executable harness.
