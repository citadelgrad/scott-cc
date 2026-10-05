# PR #8 review split

Source comparison: `2914cdbccc35a4c73023f3302ed93f5f567c28b4` → `c0af1a13fbad82b887869f3f63b16ef4f7f38b19` (original PR #8). Uncommitted primary-checkout work is excluded.

| Branch | Review base | Ownership |
|---|---|---|
| `split/pr8-beads` | `main` | Beads runtime, safety/recovery contracts, fixtures, evaluator, frozen evidence, runtime catalog registration and current architecture/status |
| `split/pr8-distribution` | `split/pr8-beads` | Cross-agent package payloads, installer/contracts, v5.8.0 metadata, helpers, publishing docs and distribution CI |
| `split/pr8-router` | `main` | Hybrid-router plan, three schemas, structural test and locked test dependencies; no router implementation |

## Why packaging is stacked

The original packaging change verifies the full inventory including Beads and its custodian-only evaluator boundary. Its release receipts bind Beads evidence, and its catalog/version surfaces count the Beads package. Removing Beads would turn this into a different release, invalidate its inventory assertions, and require rewriting historical evidence. Instead, the packaging PR explicitly depends on the runtime PR and shows only the incremental packaging diff. It does not include the router design.

The runtime PR owns Beads' source and tests at the final original snapshot, including the custodian evaluator relocation. Shared root catalogs first add Beads in the runtime PR; packaging then applies its installation instructions and version updates. Root plugin/marketplace counts are correct in both branches. Locked Python verification dependencies originate in the runtime PR; the independent router PR declares its own equivalent test tools so it can run without Beads. Combining those independent branches requires reconciling `pyproject.toml`/`uv.lock`, preserving the Beads type-checker path and pytest settings.

## Documentation and historical evidence

The [architecture/status note](beads-architecture-status.md) is the current short guide. PRD/spec remain immutable at their original paths, explicitly classified as superseded historical sources by the [planning index](plans/2026-09-02-hermes-beads-skill/README.md). Implementation DAG and task-ID map are archived together with compatibility symlinks and an updated swarm provenance pointer. The four evidence JSONs and rejection decision remain unchanged in place.

**The old release receipt is historical, not fresh verification of these branches.** `docs/reports/release-v5.8.0-verification.json`, the earlier audit receipts, HTML report, and `docs/releases/v5.8.0.md` preserve their original bytes and original claims. They describe the original combined source/tag, not a newly published release or the split heads. New documentation, symlink layout, and separated router scope mean these branches must not be called the same historical release bytes. New verification must name its branch/tree, commands, exit codes, skips and limitations separately.

**Beads advanced-runtime release remains REJECT (`release_eligible=false`); no default-profile promotion.** Package installation success is not model-routing certification. No new model-backed evaluation, release tag, deployment, merge, or active-profile mutation is authorized by this split.

Review/merge order: runtime before packaging; router is independently reviewable. Retarget packaging to `main` only after the runtime changes are present there, and inspect the resulting exact diff before merging. Original PR #8 remains open for independent reconciliation; no branch is deleted or force-pushed.
