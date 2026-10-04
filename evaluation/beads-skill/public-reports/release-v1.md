# Beads v1 public release report

Status: REJECTED — not promoted

The candidate package passes its deterministic implementation and conformance suites, but it does not have fresh, passing release evidence. The completed 135-observation model-backed report failed negative-restraint, Wilson-bound, and hard-zero safety gates and is stale against the current candidate/design/corpus/harness identities. The source report is private evidence identified by its hash, not a public artifact.

Results:

- Deterministic repository suite: 1,278 passed, 1 skipped, 0 failed.
- Acceptance re-verification: solo 51 passed; swarm 222 passed; fresh secret-boundary and fourteen-flow crash-boundary reviews both READY.
- Model-backed routing observations: 104 passed, 31 failed, 0 errored.
- Release gate: failed.
- Default-profile promotion: not attempted.
- Active skill: preserved.
- Replacement architecture: `scc-8a7`.
- Replacement comparative gate: `scc-8a7.5`.

Machine-readable evidence and exact hashes are in [`release-v1.json`](release-v1.json). The full decision and PRD traceability matrix are in [`../../../docs/plans/2026-09-02-hermes-beads-skill/release-decision-v1.md`](../../../docs/plans/2026-09-02-hermes-beads-skill/release-decision-v1.md).

Known limitation: the plugin-free design cannot guarantee pre-interception of every child output before model visibility. That remains release-blocking for claims that require such enforcement.
