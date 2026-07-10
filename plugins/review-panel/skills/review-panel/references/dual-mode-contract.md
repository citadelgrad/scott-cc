# Dual-Mode: Human Report and `mode:agent` JSON Contract

The same 7-stage orchestrator, two output shapes, selected once at invocation and held constant
for the whole run — do not switch modes mid-loop.

## Mode selection

- **Human-interactive mode** (default): invoked via the `/review-panel` command or directly by a
  human in conversation, with no `--mode=agent` argument. Produces a readable markdown report and
  drives an interactive apply loop (the human can approve/adjust before FIX commits, ask
  follow-up questions about a finding, or direct another round manually).
- **Unattended `mode:agent`**: invoked with `--mode=agent` in `$ARGUMENTS` (or by an automation
  harness that sets this programmatically, e.g. a `foundry` `post-feature` gate). Produces exactly
  one JSON blob as the final output, with no interactive prompts, no clarifying questions, and no
  partial/streaming output — the loop runs to completion (converged or circuit-broken) and emits
  one machine-parseable result.

## Human-interactive mode

### During the run

Report progress narratively as each stage completes — which seats were cast and why, notable
findings as MERGE/VALIDATE process them, what FIX changed, RE-REVIEW's verdict. This is
conversational, not a rigid template; use judgment on how much detail to surface live versus
saving for the final report.

### Final report structure

```markdown
# Review Panel Report

## Cast
[seat list with cast rationale, model tier, live-scan additions]

## Findings (post-VALIDATE, pre-FIX)
### Critical
[each: file:line, quote, seat(s), confidence anchor, validator verdict]
### Important
[...]
### Minor
[...]

## Fixes Applied
[per finding: fixed / skipped + reason]

## Re-Review
### Regressions
[clean, or new findings]
### Domain-Intent Coherence
[clean, no CONTEXT.md, or coherence findings]

## Convergence
Status: converged | circuit_broken
Rounds: N
[if circuit_broken: diagnosis + recommendation, per converge-and-pipeline.md]

## Coverage Honesty
[anything skipped, scoped down, or run via fallback, and why]
```

### Interactive apply loop

After the final report, if the run is `converged` with fixes already applied (FIX already ran
during the loop — fixes are not held back for a final human approval gate, since VALIDATE already
provides the independence check that stands in for human review of each finding), offer the human
the chance to: review the diff as committed, request a manual additional round on a specific
finding they disagree with the panel's verdict on, or accept as final. If `circuit_broken`, the
apply loop's job is to hand off the diagnosis clearly enough that the human knows where to start
manually — do not attempt to auto-resolve a circuit-break by guessing.

## `mode:agent` JSON contract

Emit exactly one JSON object as the final and only output in this mode. Shape:

```json
{
  "status": "converged | circuit_broken | error",
  "rounds": 2,
  "cast": [
    {
      "seat": "Correctness/Adversarial",
      "skill": "skills/adversarial-reviewer/SKILL.md",
      "model_tier": "top",
      "source": "catalog | live-scan",
      "cast_rationale": "core seat, always cast"
    }
  ],
  "findings": [
    {
      "id": "f-001",
      "fingerprint": {
        "file": "src/orders/checkout.ts",
        "line": 142,
        "normalized_title": "missing null check on payment token"
      },
      "severity": "Critical | Important | Minor",
      "confidence": 100,
      "contributing_seats": ["Correctness/Adversarial", "Fresh-Eyes"],
      "evidence_quote": "const token = payment.token.value;",
      "recommendation": "guard payment.token before dereferencing .value",
      "validation": {
        "validator_count": 2,
        "verdict": "survives",
        "tally": "2-0"
      },
      "fix": {
        "applied": true,
        "skipped_reason": null
      },
      "re_review": {
        "regression_clean": true,
        "coherence_clean": true
      }
    }
  ],
  "convergence": {
    "final_round_clean": true,
    "circuit_breaker": {
      "tripped": false,
      "consecutive_no_progress_rounds": 0,
      "diagnosis": null
    }
  },
  "coverage": {
    "skipped_seats": [],
    "fallbacks_used": [],
    "notes": []
  }
}
```

Field notes for an agent emitting this:

- `status`: exactly one of the three values. `error` is reserved for a run that failed to execute
  at all (e.g. `scripts/workspace` unavailable AND the fallback also failed, or no seats could be
  cast) — distinct from `circuit_broken`, which means the loop ran but didn't converge.
- `findings`: the array reflects the FINAL round's findings list (post-VALIDATE state at the
  moment the loop stopped) — for a `converged` run this should be an empty array or contain only
  findings whose `re_review` fields are both `true`/clean. For `circuit_broken`, include the
  still-outstanding findings so the human/downstream system knows exactly what's unresolved.
- `validation.tally`: format as `"survives-refuted"` counts, e.g. `"2-0"`, `"2-1"` — always
  reflects the actual per-validator verdict split, not just the final survives/refuted call.
- `convergence.circuit_breaker.diagnosis`: null when `tripped` is `false`; when `true`, a
  human-readable string identifying which specific finding(s) failed to resolve across the last 3
  rounds — this is the same diagnosis text the human-mode escalation block would show, just placed
  in a structured field instead of markdown prose.
- `coverage`: never omit this object even when nothing was skipped — an explicit empty
  `skipped_seats`/`fallbacks_used`/`notes` is itself the coverage-honesty signal ("checked, found
  nothing to report") as opposed to the field being absent (which would leave a `foundry` gate
  unable to distinguish "fully covered" from "coverage-honesty step didn't run").

### Wiring to `foundry`

A `foundry.yaml` gate invoking this skill in `mode:agent` should treat the JSON's `status` field as
the gate's pass/fail signal: `converged` → gate passes; `circuit_broken` → gate should fail with
`decision_on_failure: fail` (or `warn` if the profile allows manual override) and the
`agent`/`explain` integrations can consume `convergence.circuit_breaker.diagnosis` directly for
their explanation/escalation text; `error` → gate fails, treat as an infrastructure problem with
the panel run itself rather than a code-quality signal.

#### Concrete `foundry.yaml` example

Reckoner calls `foundry run post-feature` automatically after every successful PR creation, so
defining a `post-feature` profile with a `review-panel` gate is enough to get this skill running
unattended after every PR with no other wiring:

```yaml
version: 1

profiles:
  post-feature:
    gates:
      - id: review-panel
        run: |
          claude -p "/review-panel $(git merge-base origin/main HEAD)..HEAD --mode=agent" \
            --dangerously-skip-permissions \
            --output-format json > "$FOUNDRY_RUN_DIR/review-panel.json"
          status=$(jq -r '.status' "$FOUNDRY_RUN_DIR/review-panel.json")
          if [ "$status" = "circuit_broken" ] || [ "$status" = "error" ]; then
            exit 1
          fi
        timeout: 20m
        allow_failure: false
        decision_on_failure: fail   # circuit_broken/error -> gate fails; converged -> exit 0 above

integrations:
  explain:
    on_failure: true
  agent:
    on_failure: true
    # {run_dir} is interpolated by foundry; the gate already wrote the JSON blob there, so the
    # explain/agent integrations can jq the diagnosis straight out of it instead of re-deriving one.
    command: >-
      claude -p "Read {run_dir}/review-panel.json and summarize why the review-panel gate failed,
      quoting convergence.circuit_breaker.diagnosis if status is circuit_broken, or the raw error
      if status is error." --dangerously-skip-permissions
```

Notes on this example:
- The gate's `run` command is exactly the `/review-panel` slash command from `commands/` invoked
  with `--mode=agent`, non-interactively via `claude -p`, over the PR's merge-base range — this is
  the same target-resolution the command performs for a human, just with the flag set and no TTY.
- `status: converged` is the only value that should let the gate script exit `0`; both
  `circuit_broken` and `error` are failures, per the mapping described above, so the script maps
  both non-`converged` outcomes to a nonzero exit rather than trying to distinguish
  `decision_on_failure` behavior at the shell level — use `allow_failure: true` +
  `decision_on_failure: warn` at the profile level instead if a project wants circuit-breaks to
  warn rather than block.
- Writing the JSON blob into `$FOUNDRY_RUN_DIR` (foundry's per-run directory, the same one
  `{run_dir}` refers to in `integrations`) means `integrations.agent`'s command can read the exact
  same structured result the gate already produced instead of re-invoking the panel or re-parsing
  `explanation.md`.
- **Trusted/internal branches only.** This gate should run only against branches/PRs from
  trusted, internal sources (e.g. branches pushed by team members within the same repo) — never
  wired to run unattended against arbitrary external fork PRs. Two compounding reasons: FIX's
  fixer subagent has `Read`/`Edit`/`Write`/`Bash` access to the working tree (see
  [fix-and-rereview.md](fix-and-rereview.md)'s "Fixer dispatch contract" and its Bash-usage
  boundary), and every stage that reads diff/code/comment content is instructed to treat that
  content as data, never as instructions (see the same file, and
  [cast-and-spawn.md](cast-and-spawn.md)) — but an untrusted external PR is exactly the scenario an
  adversary would target with a crafted diff or comment designed to probe those boundaries. Running
  this gate with `--dangerously-skip-permissions` against untrusted fork content multiplies that
  risk. If a project wants review coverage on external PRs, run this gate in human-interactive mode
  with a maintainer supervising, not as an unattended `post-feature` gate.
