# Beads coordination: architecture and status

This is the current architecture/status entry point. Use the [skill spine](../skills/beads/SKILL.md) and its operational references for instructions. The [planning index](plans/2026-09-02-hermes-beads-skill/README.md) distinguishes frozen provenance from current guidance.

## Release boundary

**Advanced-runtime release: REJECT; `release_eligible=false`. No default-profile promotion.** The [unchanged decision](plans/2026-09-02-hermes-beads-skill/release-decision-v1.md) records failed discovery/restraint gates and stale candidate/design/corpus/harness identities. Local tests and package installation checks do not overturn it. No new live-model evaluation, release tag, deployment, or profile change is part of this split.

The paired evaluator's [not-evaluated report](../evaluation/beads-skill/public-reports/not-evaluated-v1.md) and the later [release report](../evaluation/beads-skill/public-reports/release-v1.md) are different historical artifacts. Neither is a passing current-head runtime release receipt.

## Implemented architecture

- **Authority:** native `bd` remains the issue tracker. The parent coordinator owns lifecycle writes, exact tracker readback, independent acceptance verification, and closure. Workers return packet-bound evidence; their success assertions cannot authorize closure.
- **Identity and isolation:** canonical workspace/run/lane identities, ownership epochs, immutable worker packets and lane packages prevent accidental cross-run reuse. Worktrees and process bounds provide cooperative isolation, not protection from a malicious same-UID process.
- **Recovery:** write-ahead operation journals, durable checkpoints, stable operation IDs, locks, and reconciliation distinguish applied, refused, unknown, and conflicting effects. An interrupted effect is not blindly retried.
- **Integration:** ready-front selection and write-conflict checks bound concurrency; lane freezes and combined-candidate review bind integration evidence to the reviewed bytes.
- **Protected actions and output:** explicit human-action gates cover protected effects. Safe transport validates executable identity and native output, redacts sensitive data, and fails closed. Plugin-free execution cannot intercept every child output before the agent sees it; this remains a disclosed release limitation.
- **Evaluation:** the custodian-only evaluator and evidence adapter live under `evaluation/beads-skill/`, outside the installable operational skill. Installed evaluation commands fail closed with `CUSTODIAN_CHECKOUT_REQUIRED`. Frozen manifests bind evidence to exact source bytes; they are not automatically regenerated for refactors.

## Compatibility and verification

The native lifecycle conformance fixtures target **Beads 1.3.1**, the version pinned in `skills/beads/scripts/safe_bd.py`. The frozen v1 [source baseline](plans/2026-09-02-hermes-beads-skill/source-baseline-v1.json) records the original 1.2.2 pin. Beads 1.3.1 claims are leases (`lease_expires_at`, `heartbeat_at`) that a supervisor can revert with `bd reclaim`. A different installed CLI version is not proof of compatibility. Use an isolated pinned executable on PATH for these tests; never downgrade or migrate the user's live tracker database as a test setup step.

`uv sync --frozen` and `uv run pytest` exercise local contracts, recovery, fixtures, and evaluation gates. Optional frozen-Hermes/PAS checks require their documented external runtimes. These tests neither spend a model-evaluation budget nor authorize default-profile promotion.

## Review scopes and historical receipts

The split separates this runtime/evaluation change from portable packaging and from the Hermes hybrid-router design. Packaging is stacked on the runtime branch: its all-package inventory, Beads custodian boundary, catalog counts and frozen release receipts genuinely include Beads. The router design is independent and supplies only schemas plus structural tests, not a routing engine.

The historical v5.8.0 release receipt belongs to original PR #8 head `c0af1a13fbad82b887869f3f63b16ef4f7f38b19`. Its recorded tests and hashes are not fresh evidence for any split branch. New branch results must identify their own tested tree and command exits; old receipts remain unchanged. The [historical release note](https://github.com/citadelgrad/scott-cc/blob/c0af1a13fbad82b887869f3f63b16ef4f7f38b19/docs/releases/v5.8.0.md) describes that original release, not a new publication.
