# Adversarial review: skill installation, implementation and usage

Status: **complete for the audited distribution/packaging scope**. Fixes are in the primary working tree, full verification passed, and final independent delta review found no supported regressions. Runtime limitations and upstream defects below remain explicitly bounded; this is not a universal live-model certification.

## Scope and method

Interpret “MPX skills” as the repository's documented `npx skills` distribution surface. Audit all root/plugin packages, not only the root manifest. Three independent discovery lanes froze evidence before three separate validation/repair lanes. Two subsequent independent reviewers checked the combined result; their confirmed findings were reproduced and repaired. The final read-only delta review verified those repairs with 65 passing targeted tests plus independent real-installer controls. The parent matched every reviewed file hash against the primary working tree before acceptance.

Targets: Codex (`codex`), Hermes Agent (`hermes-agent`), Claude Code (`claude-code`), Gemini CLI (`gemini-cli`), and Pi (`pi`). Installer: locked `skills@1.7.0`, invoked against local checkout bytes with isolated profiles, caches, Git configuration and cwd. No paid model calls or real-profile installations were used for these gates.

Baseline commit: `7c15483f617563c175d573377f71d4efdf126ded`, plus the pre-existing dirty working tree captured in the target manifest. Existing user changes and genuine Beads release reports are not reset or replaced.

## Matrix and acceptance boundaries

- 73 physical packages, 71 unique install identifiers, including two byte-identical mirror pairs.
- 730 isolated individual placement cases: every physical package × five agents × project/global copy mode.
- 355 repository-root selection cases: every unique name × five agents.
- Additional malformed-metadata, unknown-selection, wrong-target, missing/truncated/extra-file, symlink, filtered-resource, doctor, runtime, reinstall and quarantine controls.
- Package copies and deterministic helpers are tested. These results do not certify every LLM's routing or authenticated workflow execution.
- Claude plugin registration is separate from installation. The corrected commands are `/plugin marketplace add citadelgrad/scott-cc`, then `/plugin install scott-cc@scott-cc` or `/plugin install <name>@scott-cc`.
- Pi/Gemini custom global homes remain unsupported by the upstream pin. Codex/Gemini share `.agents/skills`; independent removal from that shared directory is not promised.
- Triage's full workflow still requires its declared Claude/PAS/Beads/panel runtime; its prompt now preflights before side effects. Catalog maintenance requires an explicit source checkout. Sequential review is never represented as independent review.
- Beads advanced runtime remains REJECT, `release_eligible=false`. Frozen evaluator bytes, release manifests, receipts and historical decisions are not re-pinned to obtain a green installation gate.

## Findings and repairs

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| INSTALL-01 | P2 | Default discovery omits both nested triage detectors | Declare nested detector paths in the plugin manifest; verify root discovery and individual selection with the real installer on all five targets. |
| INSTALL-02 | P2 | Divergent TDD packages share one install identifier; plugin variant is silently hidden | Unify both TDD payloads byte-for-byte, preserving strict red/green behavior and design/test-quality references; enforce complete duplicate-content equality. |
| INSTALL-03 | P1 | Project-scoped remove for Hermes deletes shared skills still used by unselected agents | Upstream defect not repaired. Replace narrow project removal with a tested reversible quarantine that preserves unselected agents and shared canonical files. |
| INSTALL-04 | P1 | Update discards selected targets and --copy, expanding installation to other agents | Upstream defect not repaired. Replace generic update with explicit reinstall preserving skill, target, scope and copy/symlink mode; test stale-file removal. |
| INSTALL-05 | P2 | Pi and Gemini custom homes are ignored by the installer and skills become undiscoverable | Upstream limitation remains: explicitly reject recommending global custom Pi/Gemini homes; document tested default-home/project alternatives and native-listing verification. |
| INSTALL-06 | P2 | Hermes project install instructions omit mandatory repository trust | Document the Git-root and explicit Hermes trust requirement; installers never silently grant trust. |
| PKG-001 | P1 | init cannot run as an individually installed skill | Bundle init templates and references with a source-drift-checkable manifest and installed doctor; use installed absolute paths. |
| PKG-002 | P1 | review-panel ships no mandatory diff-packaging or checkpoint runtime | Bundle the panel diff/checkpoint runtime, contracts, worker prompts and transitive resources; detect native delegation or disclose non-independent standalone limits. |
| PKG-003 | P1 | All four mental-model lenses lose the mandatory model catalog | Bundle each mental-model catalog and output contract, with source hashes and installed missing-resource controls. |
| PKG-004 | P2 | Format-driven reviewer and interview skills depend on unbundled plugin/sibling documents | Bundle required formats and contracts; additionally close security-review and triage references exposed by stricter installed-layout checks. |
| PKG-005 | P2 | catalog-steward is a source-repository tool exposed as a portable skill | Require an explicit valid maintainer checkout; do not search for or import neighboring repositories. |
| PKG-006 | P1 | mutation-test and explore-variants cannot launch their unshipped named agents | Bundle worker prompts and capability-detected adapters; distinguish independent native delegation from truthful sequential mode. |
| PKG-007 | P2 | delegate-first requires Claude-specific fork APIs despite cross-agent publication | Replace invented Claude-specific fork requirements with live-schema capability preflight, explicit context transfer and honest unsupported/sequential handling. |
| PKG-010 | P2 | Beads bundled evaluation entrypoint imports outside the installed package | Keep evaluator and evidence adapter custodian-only at their original frozen hashes. Add a custodian CLI; the legacy installed CLI explains migration and fails evaluation with CUSTODIAN_CHECKOUT_REQUIRED. |
| PKG-011 | P2 | Beads checker reports a package healthy after required operational reference deletion | Require the complete operational reference/script/schema set and reject required symlink/path escapes. |
| PKG-012 | P2 | browser-use-e2e standalone pytest example references asyncio without importing it | Fix asyncio imports, dependency declarations and async fixture lifecycle; exercise installed helper examples with bounded deterministic dependencies. |
| PKG-013 | P3 | browser profile setup reports missing dependency with success exit status | Return nonzero on missing browser dependencies and setup errors; report success only after state verification and cleanup. |
| PKG-014 | P3 | Published float scaling property is false over its own generated domain | Replace the false unrestricted float property with exact bounded arithmetic; preserve its former counterexample as a regression control. |
| PKG-015 | P3 | ADR status updater adds a blank line on every repeated update | Make ADR status changes byte-idempotent for LF and CRLF inputs. |
| VER-001 | P2 | Distribution metadata checks approve YAML rejected by the actual installer | Use strict YAML/frontmatter/body validation including duplicate keys and name constraints; test malformed inputs through the real installer. |
| VER-002 | P2 | Canonical pytest does not enforce the checked-in distribution contract | Wire current-checkout static verifiers, inventory-wide real installs, package/runtime regressions and lifecycle tests into canonical pytest, Make and CI. |
| VER-003 | P2 | Pre-commit path filters bypass contract checks for important package changes | Cover nested resources, schemas, manifests and deletions in always-run pre-commit contract hooks. |
| VER-005 | P2 | Portable adversarial doctor treats external links and symlinks as self-contained | Reject unsafe local references and external symlink escapes in both mirrored adversarial doctors. |
| VER-006 | P2 | Installer E2E tests pass when Hermes installation is silently routed to Codex | Assert exact target placement, absence of unintended targets, copied byte hashes and post-install required-resource closure. |
| VER-007 | P2 | Documented release smoke test returns success after installer and existence checks fail | Use fail-closed publishing gates with mandatory pinned dependencies; separate public-branch discovery from local-checkout verification. |
| VER-008 | P2 | Plugin manifest verifier accepts missing required plugin name | Reject missing/invalid plugin identity and malformed manifests rather than letting later assumptions approve them. |

## Findings caught during re-review

1. Required-file filtering false green (RRV-DIST-001): skills 1.7.0 drops `metadata.json`. Comparing filtered source/installed inventories allowed both sides to omit a required linked file. A real-installer red test reproduced that false green; the oracle now validates required local links in the installed directory. The `data.json` control remains valid.
2. Custodian boundary regression (RR-RUNTIME-001): relocating the full scorer into the operational Beads package exposed custodian-only tooling to the candidate mount. Reverted that relocation, restored the original scorer/adapter bytes, moved CLI use to `evaluation/beads-skill/harness/evaluate_skill.py`, and made installed evaluation explicitly unavailable without searching sibling clones.
3. Stronger installed closure revealed security-review/triage references escaping their distribution unit. Bundled the maintained references with provenance, doctors and missing-asset controls. Detector links are explicitly external companion documentation, not undeclared local dependencies. Triage scheduling docs now preserve fresh-item execution and fail-closed JSON parsing.
4. Marketplace-only instructions did not install Claude plugins; several examples also confused repository paths/Git tags with plugin identifiers. Corrected the install flows across README, quick start, publishing and architecture docs against the official guide, and added regression assertions. Corrected the stale core-skill count in both manifests.

## Verification

Primary-worktree complete suite: **2,667 passed, 2 skipped**, zero failures/errors (521.65 seconds). The skips were the unavailable frozen Hermes source and unavailable PAS CLI in the isolated test environment—not successful runtime coverage.

Canonical `make verify-distribution`: **1,442 passed, zero skips**, zero failures/errors (227.931 seconds). `make setup-verification` completed successfully using the checked-in lockfiles. Focused canonical `uv run pytest` also passed 244 tests in both primary and integration worktrees. Scoped Ruff and whitespace checks passed. Earlier partial/interrupted runs are diagnostic evidence, not acceptance.

The first full integration run exposed a historical-receipt test that incorrectly demanded the old rejected candidate equal the new package bytes. The repaired test calls the real runtime guard and requires `FROZEN_CANDIDATE_MISMATCH`, while preserving and checking the original REJECT receipt. No frozen benchmark evidence was rewritten.

Canonical commands:

```sh
make setup-verification
make verify-distribution
make verify
```

The broader native Beads tests require bd 1.2.2. The audited machine's bd 1.3.0 is not a compatible substitute; final full verification uses a checksum-verified isolated 1.2.2 binary. Optional unavailable external probes must be reported as skips, not counted as compatibility successes.

## Evidence and limitations

Local evidence directory: `/Users/scott/.hermes/cache/scratch/scott-cc-skills-audit/`.

- `target-manifest.json`: original file hashes, baseline, threat model and scope.
- `installer-phase-a.json`, `packages-phase-a.json`, `verification-phase-a.json`: independent original findings and controls.
- `finding-ledger.json`: frozen candidate deduplication; 30 raw findings consolidated into 26 candidate issues.
- `rereview-runtime.json`, `rereview-distribution.json`: independent re-review findings and rejected hypotheses.
- `full-final.log` / `full-final.xml`: diagnostic integration run before the historical-receipt test correction.
- `full-primary.log` / `full-primary.xml`: successful complete primary-worktree gate.
- `distribution-primary.log` / `distribution-primary.xml`: successful canonical distribution gate.
- `primary-transfer-manifest.json`: pre-write primary hashes and integrated source hashes, including unchanged historical artifacts.
- `final-delta-review.json`: completed independent delta review: ready, no supported regressions, both re-review findings closed.
- [Portable verification receipt](skill-installation-verification.json): retained target/review hashes, exact suite totals and explicit skips. The diagnostic scratch directory can expire without erasing this summary receipt.

These scratch files are local evidence, not a published compatibility guarantee. Distribution acceptance is separate from optional native/live-model coverage. Remote default-branch install smoke and GitHub CI remain post-publication checks; no commit or push is part of this task.

Official installation reference: https://code.claude.com/docs/en/discover-plugins
