# Hardened Skills Catalog

These skills have repository-enforced orchestration contracts and mechanical
context-budget tests. The registry in
[`scripts/verify_orchestration_contracts.py`](../scripts/verify_orchestration_contracts.py)
is authoritative; this page is the human-facing catalog.

## Release status is separate from integrity

**Beads advanced swarm/runtime candidate: REJECT; `release_eligible=false`.**
The genuine [release decision](plans/2026-09-02-hermes-beads-skill/release-decision-v1.md)
records failed/stale model-backed evidence and says not to promote this candidate.
The associated receipt is `evaluation/beads-skill/public-reports/release-v1.json`
when supplied with the evaluation bundle. Portable installation is possible;
mechanical package, schema, context-budget and installer checks do **not** establish
production readiness or live-model safety. A new release needs new authorized
model-backed evidence and an explicit acceptance decision, not a green copy test.

## Portable orchestration

| Skill | Contract | Context budget |
|---|---|---|
| [Beads](../skills/beads/README.md) (`beads`) | Parent-only lifecycle writes, bounded isolated workers, artifact-backed handoffs, exact readback, and fail-closed recovery | Preferred: 150–220 lines and at most approximately 2,500 tokens. Hard maximum: 500 lines and approximately 5,000 tokens. |

The canonical package is `skills/beads/`. Scott Nixon is its adaptation author;
the upstream Beads Contributors, `gastownhall/beads` source, immutable revision,
and MIT notice remain in the package's [source record](../skills/beads/references/sources.md)
and [license](../skills/beads/LICENSE.txt).

Install the portable package for supported agents with:

```bash
npx --yes skills@1.7.0 add citadelgrad/scott-cc --copy --skill beads --agent codex --agent hermes-agent
```

Use a sandboxed `HOME` for maintainer install tests. Repository verification does
not install or mutate a user's default Hermes profile.

## Plugin orchestration

The registry also covers these plugin-owned orchestrators:

- `mutation-test`
- `design-review`
- `triage-spine`
- `explore-variants`
- `browser-use`
- `browser-use-e2e`
- `ponytail-audit`
- `improve-codebase-architecture`
- `prod-errors`
- `grill-with-docs`
- `grill-my-taste`
- `grill-the-schema`

Run both contract verifiers after changing this catalog or a registered skill:

```bash
uv run python scripts/verify_skills_distribution.py
uv run python scripts/verify_orchestration_contracts.py
```
