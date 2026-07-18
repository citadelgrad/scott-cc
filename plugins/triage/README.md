# triage

Foundry-resident triage spine: detect → bead → reproduce → fix → gate. Turns detector findings
into beads issues, E2E-reproduced fixes, and `review-panel --mode=agent`-gated PRs — a System 2
loop that runs unattended, on a schedule, without a human kicking off each cycle by hand.

## What's Included

**Skills (3):**

| Skill | Purpose |
|---|---|
| [`triage-spine`](skills/triage-spine/SKILL.md) | The loop itself: intake/validate → file a bead → reproduce E2E → diagnose+fix via PAS → gate through `review-panel --mode=agent` |
| [`detectors/lib-upgrades`](skills/detectors/lib-upgrades/SKILL.md) | Scans manifest/lockfiles for outdated or CVE-flagged dependencies |
| [`detectors/prod-errors`](skills/detectors/prod-errors/SKILL.md) | Scans a log/Sentry-shaped source for stack-trace-bearing production errors |

No Agents, no Commands — this plugin is Foundry-resident, not conversation-driven. It's invoked
either by a scheduled `claude -p` dispatch (see [`docs/foundry-recipes.md`](docs/foundry-recipes.md))
or directly by a human handing it a detector's output.

Two of five detector slots are implemented in v1. The other three (`system-upgrades`, `iac-drift`,
`security-advisory-sweeps`) are registered but stubbed — see
[`skills/triage-spine/references/detector-registry.md`](skills/triage-spine/references/detector-registry.md).
Filling the remaining slots is explicitly out of scope for v1.

## When to Use

**Install if:**
- You want dependency-health or production-error triage to run on a schedule instead of waiting
  for a human to notice.
- You already use `review-panel` as your diff-review substrate and want triage's fixes gated
  through it rather than merged unreviewed.
- You use `bd` (beads) for issue tracking and want triage findings to land there automatically.

**Don't install if:**
- You don't have `review-panel` installed — this plugin's gate step is a hard dependency, not
  optional (Phase 6 of `triage-spine`).
- You want an interactive, conversational triage assistant — this plugin is designed to run
  unattended; use it directly in conversation only when handing it a detector's output by hand.

## Common Use Cases

- **Scheduled dependency sweep:** a Foundry cron gate runs `lib-upgrades` weekly; any CVE finding
  becomes a bead, a reproduced+fixed branch, and a gated PR — all before a human looks at it.
- **Production error triage:** point `prod-errors` at a log export or Sentry issue; the spine
  reproduces the exact stack trace locally before proposing a fix.
- **Ad hoc bug triage:** hand `triage-spine` a single triage item (JSON matching the Triage Item
  Contract) directly in conversation to run the loop once, without waiting for a scheduled sweep.

## Quick Start

1. Run a detector (e.g. `lib-upgrades`) over the repo, or hand `triage-spine` a triage item
   directly.
2. `triage-spine` files a bead, reproduces the issue, and produces a fix via `pas-pipeline`.
3. The fix branch is gated through `/review-panel --mode=agent`; the bead and PR are annotated per
   the resulting status (`converged`, `escalated`, `circuit_broken`, or `error`).
4. A human merges the PR — auto-merge is out of scope for v1.

## Dependency Direction

**Triage → review-panel, one-way only (Invariant 2).** `triage-spine` invokes
`/review-panel ... --mode=agent` as a subprocess dispatch to gate its own fix diffs.
`review-panel` never imports from, or special-cases, `triage` — it has no knowledge this plugin
exists. If you ever see a change proposed to `review-panel` that references `triage` by name,
that's the invariant being violated; reject it.

## Recommended Combinations

- **`review-panel`** — required. `triage-spine`'s Phase 6 gate cannot run without it.
- **`security-suite`** — its `plan-security-review` skill is a complementary pre-build gate; see
  [`docs/foundry-recipes.md`](docs/foundry-recipes.md) for how both are scheduled alongside this
  plugin's detectors.
