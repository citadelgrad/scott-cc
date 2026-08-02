# foundry.yaml Template

The auto-generated `foundry.yaml` for scheduling and automation control.

## Default Template

Create this file when foundry.yaml doesn't already exist:

```yaml
# foundry.yaml — scheduling & automation control layer for this project.
# Compare the repository's root foundry.yaml for a live, validated example.
# `foundry run <profile>` runs one locally; `foundry run <profile> --dry-run`
# previews its gates; `foundry schedule install <name>` installs its cron entry.

version: 1

# Example 1: unattended code review via the review-panel skill's mode:agent
# JSON contract, run as a post-feature gate. Reckoner calls `foundry run
# post-feature` automatically after every successful PR — no other wiring
# needed. See plugins/review-panel/skills/review-panel/references/dual-mode-contract.md
# for the full contract (status values, escalation handling, etc).
# profiles:
#   post-feature:
#     gates:
#       - id: review-panel
#         run: |
#           claude -p "/review-panel $(git merge-base origin/main HEAD)..HEAD --mode=agent" \
#             --dangerously-skip-permissions --output-format json \
#             > "$FOUNDRY_RUN_DIR/claude-cli.json"
#           jq -r '.result' "$FOUNDRY_RUN_DIR/claude-cli.json" \
#             > "$FOUNDRY_RUN_DIR/review-panel.json"
#           status=$(jq -r '.status' "$FOUNDRY_RUN_DIR/review-panel.json")
#           # converged/escalated pass; circuit_broken/error fail (escalated
#           # must never block unattended automation — see OQ4 in the
#           # dual-mode-contract.md doc above)
#           [ "$status" = "converged" ] || [ "$status" = "escalated" ]
#         timeout: 20m
#         allow_failure: false
#         decision_on_failure: fail

# Example 2: a scheduled agent gate that invokes a single review skill
# directly (not the full panel) — e.g. a nightly adversarial pass over
# recent changes, reported but never blocking on its own
# profiles:
#   adversarial-nightly:
#     gates:
#       - id: adversarial-review
#         run: |
#           claude -p "Use the adversarial-reviewer skill to review changes
#           from the last 24h and report findings." \
#             --dangerously-skip-permissions --output-format json \
#             > "$FOUNDRY_RUN_DIR/adversarial-review.json"
#         timeout: 15m
#         allow_failure: true
#         decision_on_failure: warn
#
# schedules:
#   nightly-adversarial-review:
#     profile: adversarial-nightly
#     cron: '0 3 * * *'

profiles: {}

schedules: {}
```

## Rules

- **Never overwrite:** If `foundry.yaml` already exists, skip entirely. Do not ask.
- **Customization:** Users should add their own profiles and schedules based on their project needs.
- **Documentation:** The examples show post-feature gates and scheduled reviews; see CLAUDE.md for the full schema.
