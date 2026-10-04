# Historical Beads planning and frozen evidence

**Current guidance:** [architecture and status](../../beads-architecture-status.md), [skill spine](../../../skills/beads/SKILL.md), and its operational references. **Release disposition: [REJECT](release-decision-v1.md); no default-profile promotion.**

These documents originated in PR #8, frozen here from `c0af1a13fbad82b887869f3f63b16ef4f7f38b19`. They are provenance, not a second active implementation plan.

## Immutable evidence retained at its original path

- `source-baseline-v1.json`
- `baseline-results-v1.json`
- `benchmark-corpus-design-v1.json`
- `discovery-benchmark-design-v2.json`
- `release-decision-v1.md`

Consumers include the evaluation manifest, harness and tests. Do not edit these artifacts or their recorded hashes to make old evidence look current. A changed evaluation identity requires new versioned evidence.

## Superseded historical design

[PRD](hermes-beads-skill-prd.md) and [specification](hermes-beads-skill-spec.md) are retained **byte-for-byte at their original paths** because frozen corpus references and historical source pointers name them. Their draft claims, including statements that implementation has not started, are not the current project status. The short architecture/status note supersedes them as current guidance. Keeping immutable sources in place is deliberate, not an instruction to maintain two manuals.

## Archived implementation tracking

The implementation DAG and task-to-Beads ID map are archived together under [`archive/`](archive/). They describe implementation work, not the runtime scheduler. Relative symlinks at the original filenames preserve historical source references (including the swarm fixture provenance) and readable JSON bytes. The archive is not a tracker; live task state remains in Beads.

The separate Hermes hybrid-router PR owns its plan, three schemas and structural test. It does not implement the upstream router or change this release decision.
