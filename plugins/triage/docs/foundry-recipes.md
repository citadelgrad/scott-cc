# Foundry Recipes for the Triage Spine

Consolidates every schedulable entry this Two-System Architecture epic has produced, in one place,
using this repo's `foundry.yaml` schema (see the root `CLAUDE.md`'s "Scheduling & Automation"
section). No `foundry.yaml` file exists in this repo yet — everything below is documentation for a
project that adopts one, not a live config this plugin installs or modifies.

## What's scheduled here

| Gate | Cadence | Plugin/skill | Failure behavior |
|---|---|---|---|
| `lib-upgrades` detector | Periodic (e.g. weekly) | `plugins/triage/skills/detectors/lib-upgrades/SKILL.md` | Findings feed `triage-spine`; a clean sweep is not a failure |
| `prod-errors` detector | Periodic (e.g. hourly, or on log-source push) | `plugins/triage/skills/detectors/prod-errors/SKILL.md` | Findings feed `triage-spine`; a clean sweep is not a failure |
| `triage-spine` gate (`review-panel --mode=agent`) | Mandatory post-fix step, invoked by the spine itself | `plugins/review-panel` | `converged`/`escalated` → pass; `circuit_broken`/`error` → fail, park bead |
| `plan-security-review` | Pre-build, one-off per plan | `plugins/security-suite/skills/plan-security-review/SKILL.md` | Reports go/no-go; does not block by itself (Phase 1b) |
| `grill-my-taste --distill` | Periodic (e.g. monthly), **reminder-only** | `plugins/review-panel/skills/grill-my-taste/SKILL.md` | Never runs unattended (Invariant 5) — nudges a human to start the session |

## Detector checks

Each detector runs as its own gate, dispatched non-interactively via `claude -p`, output captured
and inspected for whether it reported findings (its own explicit "clean, 0 findings" line, per
each detector's Output Contract, is what a gate script should grep for):

```yaml
version: 1

profiles:
  triage-detectors:
    parallel: true
    gates:
      - id: lib-upgrades
        run: |
          claude -p "Run the lib-upgrades detector skill over this repo and hand any findings to
          triage-spine." --dangerously-skip-permissions --output-format json \
            > "$FOUNDRY_RUN_DIR/lib-upgrades.json"
        timeout: 15m
        allow_failure: false
        decision_on_failure: fail

      - id: prod-errors
        run: |
          claude -p "Run the prod-errors detector skill over the last 24h of production logs at
          <log-source> and hand any findings to triage-spine." --dangerously-skip-permissions \
            --output-format json > "$FOUNDRY_RUN_DIR/prod-errors.json"
        timeout: 15m
        allow_failure: false
        decision_on_failure: fail

schedules:
  weekly-lib-upgrades:
    profile: triage-detectors
    cron: '0 6 * * 1'
```

Each detector gate's `run` command is a full request in one `claude -p` call — the detector skill
finds items, and (per `triage-spine/SKILL.md`) the same session carries them through the
intake → reproduce → diagnose → fix → gate loop, since there is no separate inter-process handoff
mechanism between a detector and the spine; they run in one continuous agent session per
`SKILL.md`'s own framing ("Consumes normalized triage items from any registered detector").

## The panel gate (mandatory post-fix step)

This is not a separate Foundry gate a project wires up on its own — `triage-spine`'s Phase 6
already invokes it directly, using the exact template from
`plugins/review-panel/skills/review-panel/references/dual-mode-contract.md`'s "Concrete
`foundry.yaml` example":

```bash
claude -p "/review-panel <fix-branch> --mode=agent" \
  --dangerously-skip-permissions \
  --output-format json > claude-cli.json
jq -r '.result' claude-cli.json > review-panel.json
status=$(jq -r '.status' review-panel.json)
```

See that file's own "Trusted/internal branches only" caveat — this applies identically here, since
the fix branch triage produces is exactly the kind of agent-authored diff that caveat is about.

## Consolidating the other two schedulable entries

Both of the following were already noted as schedulable in earlier phases of this epic; this doc
is where the task asked them to be consolidated alongside the detector/gate wiring above, not
re-specified:

```yaml
profiles:
  pre-build-security:
    gates:
      - id: plan-security-review
        run: |
          claude -p "Run the plan-security-review skill over <plan-doc-path>." \
            --dangerously-skip-permissions
        timeout: 10m
        allow_failure: true
        decision_on_failure: warn   # go/no-go is advisory, per Phase 1b's own scope

schedules:
  monthly-taste-distill-nudge:
    profile: taste-distill-reminder
    cron: '0 9 1 * *'

profiles:
  taste-distill-reminder:
    gates:
      - id: distill-nudge
        run: |
          echo "Reminder: run 'grill-my-taste --distill' to resolve pending Candidate rules."
          echo "This gate only prints a reminder — the distillation session itself must never run
          unattended (Invariant 5: human artifacts are human-owned)."
        allow_failure: true
        decision_on_failure: warn
```

## Notes

- **Trusted/internal branches only**, same caveat as `dual-mode-contract.md`'s example: every gate
  above that runs `--dangerously-skip-permissions` against agent-produced content should only run
  against branches/PRs from trusted, internal sources.
- **`escalated` is not a failure.** Per `dual-mode-contract.md`'s OQ4 resolution, `triage-spine`'s
  Phase 6 already handles this — a Foundry operator reading these logs should expect to see loud
  sovereignty annotations on some runs without those runs being reported as failed.
- **Auto-merge is out of scope for v1.** A `converged` or `escalated` outcome produces a
  ready-for-human-merge PR, never an auto-merged one.
