# Beads swarm fixture provenance

- Specification: `docs/plans/2026-09-02-hermes-beads-skill/implementation-dag-v1.json`, task `t16`.
- Frozen predecessor base: `7dd010076ffd136443d757dbd072b8257f77192b`.
- Harness: Python/pytest driving the production modules under `skills/beads/scripts/`.
- Process model: bounded local child processes in distinct real Git worktrees; no network or live Beads process.
- Regeneration: fixtures are reviewed source data, not generated goldens.
- Verification: `uv run pytest scripts/tests/beads_swarm`.

The corpus contains no accepted divergences. Each JSON document declares hard process and wall-clock bounds used by the executable harness.
