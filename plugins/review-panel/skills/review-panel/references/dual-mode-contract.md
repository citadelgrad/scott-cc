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

## Narrowed Run
[rendered whenever the resolved tier is lite or medium — whether tier_source is "explicit" or
"auto"; omitted entirely for full-mode runs — this section does not exist in a full-mode report at
all, not even as an empty heading]
This was a **lite** run — narrowed for speed, not full coverage.
[or: This was a **medium** run — narrowed for speed, not full coverage.]
[if tier_source is "auto": one additional line here, immediately after the tier-naming statement
above and before the guarantee bullets below, e.g. "Tier auto-resolved to **lite** (2 files, 18
changed lines, no sensitive path matched)." — values taken verbatim from auto_signals]
[followed by that tier's narrowed-guarantee bullets, quoted verbatim from lite-mode.md's
"Narrowed guarantees, per tier" section — never re-derived or paraphrased at this call site]

[the following single line — no heading of its own — is rendered only when tier_source is "auto"
AND the resolved tier is "full": the one case where an --auto run has no "## Narrowed Run" block to
extend, since full mode never gets that heading. Omitted for every other case, including explicit
full-mode runs and any lite/medium run whose auto-resolution line already lives inside
"## Narrowed Run" above. This is the only content this template ever places directly under the
title with no section heading — deliberately minimal, so an auto-resolved-to-full report differs
from a no-flag full report by exactly this one line, nothing else added or reflowed]
*Tier auto-resolved to **full** (14 files, 260 changed lines).*
[or, when the sensitive-path override drove the resolution, e.g.:
"*Tier auto-resolved to **full** (sensitive path matched: db/migrations/0007_add_orders.sql).*"]
[no guarantee bullets follow, since full mode has none to disclose]

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
Status: converged | circuit_broken | escalated | capped
Rounds: N
[if circuit_broken: diagnosis + recommendation, per converge-and-pipeline.md]
[if escalated: explicit human sign-off request — one block per unresolved sovereignty finding,
 naming the finding, its file, the DATA-MODEL.md rule it crosses (or its absence), and why FIX
 did not and will not auto-resolve it, per converge-and-pipeline.md's Decision rule step 0]
[if capped (narrowed-tier iteration cap hit with residual findings): tier-specific diagnosis +
recommendation to re-run at a wider tier, per lite-mode.md]

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
manually — do not attempt to auto-resolve a circuit-break by guessing. If `escalated`, the apply
loop's job is to get an explicit sign-off decision from the human on each named sovereignty
finding (approve the change as-is, direct a manual edit, or reject it) — every other finding in
the run may already be `converged`-clean; `escalated` narrows the human's attention to exactly the
sovereignty-marked findings rather than re-presenting the whole report. Do not treat silence or a
generic "looks good" as sign-off on a sovereignty finding specifically — the human must engage each
one named in the Convergence block.

## `mode:agent` JSON contract

Emit exactly one JSON object as the final and only output in this mode. Shape:

```json
{
  "status": "converged | circuit_broken | error | escalated | capped",
  "tier": "full",
  "narrowed_guarantees": [],
  "tier_source": "explicit",
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
      "sovereignty": "human-required | null",
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
    },
    "escalation": {
      "pending": false,
      "sovereignty_finding_ids": []
    },
    "capped": {
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

- `status`: exactly one of the five values. `error` is reserved for a run that failed to execute
  at all (e.g. `scripts/workspace` unavailable AND the fallback also failed, no seats could be
  cast, or the post-FIX sovereignty guard detected a violation — see
  [fix-and-rereview.md](fix-and-rereview.md)'s "Sovereignty guard") — distinct from `circuit_broken`
  (the loop ran but didn't converge) and from `escalated` (the loop ran and every non-sovereignty
  finding converged, but one or more sovereignty-marked findings remain by design — see
  [converge-and-pipeline.md](converge-and-pipeline.md)'s Decision rule step 0). Do not conflate
  `escalated` with either `error` or `circuit_broken`: it is not a failure and not stagnation, it is
  the correct, expected terminal state whenever a sovereignty finding exists. `escalated` is
  unaffected by tier — reachable from any tier, identically (see "The sovereignty guard is
  untouched" in `lite-mode.md`). `capped` is used exclusively by narrowed-tier (`--lite`/`--medium`)
  runs that hit their CONVERGE iteration cap with residual findings still outstanding — full mode
  never returns `capped`, and narrowed tiers never return `circuit_broken` (that value stays
  exclusively full mode's genuine-stagnation signal).
- `tier`: string enum `"full" | "medium" | "lite"`, always present — replaces an earlier two-state
  `"lite": boolean` design, which could not represent three states. `"full"` for no tier flag (or
  `--auto` resolved to full).
- `narrowed_guarantees`: array of strings, always present. `[]` when `tier` is `"full"`; otherwise
  populated with that tier's fixed guarantee strings quoted verbatim from `lite-mode.md`'s
  "Narrowed guarantees, per tier" section — fixed vocabulary, not free text, so a downstream `jq`
  consumer can pattern-match reliably across runs.
- `tier_source`: string enum `"explicit" | "auto"`, always present. `"explicit"` for an explicit
  `--lite`/`--medium` flag or no tier flag at all; `"auto"` the instant `--auto` was requested,
  regardless of which concrete tier it resolves to.
- `auto_signals`: object with `files_changed` (integer), `lines_changed` (integer), and
  `sensitive_path_match` (boolean) — present **only** when `tier_source` is `"auto"`, absent
  entirely (not `null`, not empty) when `tier_source` is `"explicit"`. This is the one field in
  this contract that is conditionally present rather than always-emitted-possibly-empty, since it
  has no meaningful empty value for an explicit run. Values are exactly what `SKILL.md` Setup
  step 6 computed and fed into `lite-mode.md`'s "Auto resolution" decision table to produce `tier`
  — see that section for the signal definitions and decision table.
- `findings`: the array reflects the FINAL round's findings list (post-VALIDATE state at the
  moment the loop stopped) — for a `converged` run this should be an empty array or contain only
  findings whose `re_review` fields are both `true`/clean. For `circuit_broken`, include the
  still-outstanding findings so the human/downstream system knows exactly what's unresolved. For
  `escalated`, include exactly the sovereignty-marked findings still pending sign-off (every other
  finding in the run is, by definition of reaching `escalated`, already clean).
- `sovereignty`: `"human-required"` when this finding carries the data-steward seat's contract
  extension (or any other seat's, if one is later added), `null` otherwise. This field passes
  through MERGE's dedupe untouched (see `references/merge-and-validate.md`) and is never set or
  cleared by FIX — only the originating reviewer seat sets it.
- `validation.tally`: format as `"survives-refuted"` counts, e.g. `"2-0"`, `"2-1"` — always
  reflects the actual per-validator verdict split, not just the final survives/refuted call.
- `convergence.circuit_breaker.diagnosis`: null when `tripped` is `false`; when `true`, a
  human-readable string identifying which specific finding(s) failed to resolve across the last 3
  rounds — this is the same diagnosis text the human-mode escalation block would show, just placed
  in a structured field instead of markdown prose.
- `convergence.escalation`: `pending: true` with `sovereignty_finding_ids` populated whenever
  `status` is `escalated` (or, mid-run in future streaming contexts, whenever sovereignty findings
  are outstanding); `pending: false` with an empty array otherwise. `sovereignty_finding_ids`
  references the `id` field of each still-pending finding in the `findings` array above, so a
  consumer can cross-reference without re-parsing evidence text.
- `convergence.capped.diagnosis`: null unless `status` is `capped`; when present, a tier-specific
  human-readable string naming which tier and cap was hit (e.g. "lite mode capped at 1 iteration;
  findings remain...") — see [converge-and-pipeline.md](converge-and-pipeline.md)'s "Narrowed-tier
  iteration cap" section for the exact per-tier wording. Mutually exclusive with
  `convergence.circuit_breaker.diagnosis` being non-null on the same run — a run is capped or
  circuit-broken, never both.
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

**`escalated` must never block or park the gate (OQ4).** Unattended/`foundry` automation is
supposed to stay unattended by default — a sovereignty finding is a flag for a human to see, not a
reason to halt the pipeline. Map `escalated` to the same gate-passes outcome as `converged` (exit
`0`), but the gate's job is to make the flag impossible to miss: surface
`convergence.escalation.sovereignty_finding_ids` and each named finding's file/reasoning in the PR
description (or wherever this gate's output is normally surfaced) and in the gate's own log output,
even though the gate itself does not fail or pause on it. A project that wants stricter behavior
(e.g. blocking merge until a human explicitly signs off on every sovereignty finding) can opt into
that by adding its own separate check on `convergence.escalation.pending` — that is a per-project
policy choice layered on top of this contract, not this contract's default, since the default must
never surprise a team that hasn't opted in.

A gate calling `--lite --mode=agent` or `--medium --mode=agent` should additionally branch on the
`capped` value: treat it as "incomplete, needs full-panel follow-up," distinct from both
`converged` and `circuit_broken` — typically `decision_on_failure: warn` rather than a hard `fail`,
since a capped narrowed run found *something* but didn't have the iteration budget to fully
resolve it. The gate may log `tier`/`narrowed_guarantees`/`tier_source` for visibility, but must
not treat a non-`full` `tier` value as a different pass/fail signal on its own — only `status`
drives pass/fail; `tier` is informational.

#### Concrete `foundry.yaml` example

Reckoner calls `foundry run post-feature` automatically after every successful PR creation, so
defining a `post-feature` profile with a `review-panel` gate is enough to get this skill running
unattended after every PR with no other wiring:

```yaml
version: 1

profiles:
  post-feature:
    gates:
      # Trusted/internal branches only — see the note below the YAML before wiring this up.
      - id: review-panel
        run: |
          claude -p "/review-panel $(git merge-base origin/main HEAD)..HEAD --mode=agent" \
            --dangerously-skip-permissions \
            --output-format json > "$FOUNDRY_RUN_DIR/claude-cli.json"
          # --output-format json wraps the CLI's own response envelope (type, subtype, result,
          # cost_usd, session_id, ...) — the skill's JSON contract is the agent's final reply,
          # which lands as a JSON *string* inside .result, not at the envelope's top level.
          jq -r '.result' "$FOUNDRY_RUN_DIR/claude-cli.json" > "$FOUNDRY_RUN_DIR/review-panel.json"
          status=$(jq -r '.status' "$FOUNDRY_RUN_DIR/review-panel.json")
          if [ "$status" = "escalated" ]; then
            # OQ4: escalated must never block or park unattended automation — surface it loudly,
            # then exit 0 like converged. See dual-mode-contract.md's "escalated must never block
            # or park the gate" note above.
            echo "review-panel: sovereignty finding(s) pending human sign-off — see review-panel.json convergence.escalation"
            jq -r '.convergence.escalation.sovereignty_finding_ids[]' "$FOUNDRY_RUN_DIR/review-panel.json"
          elif [ "$status" = "capped" ]; then
            # This example invokes full mode (no --lite/--medium flag), so capped should never
            # occur here — this branch only matters if the gate is adapted to call --lite/--medium.
            # See dual-mode-contract.md's "Wiring to foundry" note on capped -> decision_on_failure:
            # warn: a project that adapts this example to a narrowed tier should move this gate to
            # its own profile with allow_failure: true / decision_on_failure: warn rather than
            # exiting 1 here, since a capped run found something but wasn't given the round budget
            # to finish, unlike a genuine circuit_broken stagnation.
            echo "review-panel: tier capped with residual findings — see review-panel.json convergence.capped.diagnosis"
            exit 1
          elif [ "$status" = "circuit_broken" ] || [ "$status" = "error" ]; then
            exit 1
          fi
        timeout: 20m
        allow_failure: false
        decision_on_failure: fail   # circuit_broken/error/capped -> gate fails; converged/escalated -> exit 0

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
- `status: converged` and `status: escalated` are the two values that let the gate script exit `0`
  — `escalated` is deliberately treated as passing, not as a third failure mode, per OQ4 above;
  `circuit_broken` and `error` are failures, per the mapping described above, so the script maps
  those non-passing outcomes to a nonzero exit rather than trying to distinguish
  `decision_on_failure` behavior at the shell level — use `allow_failure: true` +
  `decision_on_failure: warn` at the profile level instead if a project wants circuit-breaks to
  warn rather than block. `capped` is included in this example's failure branch purely for
  completeness (this gate calls full mode, which never returns `capped`); a project that adapts
  this gate to call `--lite`/`--medium` should move it to its own profile with
  `decision_on_failure: warn`, per "Wiring to `foundry`" above, rather than reusing this profile's
  `fail` default. A project that wants `escalated` to warn (not just log) can add its own `jq` check
  on `convergence.escalation.pending` and route it through `allow_failure: true` +
  `decision_on_failure: warn` separately — the default here stays silent-pass-with-loud-logging per
  OQ4's "must never block or park" requirement.
- The `jq -r '.result' claude-cli.json > review-panel.json` step is not optional boilerplate: the
  raw `claude -p --output-format json` file is the CLI's own envelope, and `jq -r '.status'` run
  directly against it always returns `null` (the envelope has no top-level `status` field), so the
  gate would silently never fail without this extraction step first unwrapping `.result` into the
  skill's actual JSON contract.
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
