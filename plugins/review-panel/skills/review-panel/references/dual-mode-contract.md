# Dual-Mode: Human Report and `mode:agent` JSON Contract

The same 7-stage orchestrator, two output shapes, selected once at invocation and held constant
for the whole run — do not switch modes mid-loop.

## Mode selection

- **Human-interactive mode** (default): invoked via the `/review-panel` command or directly by a
  human in conversation, with no `--mode=agent` argument. Produces a readable markdown report and
  stops at its terminal status. Any follow-up review starts in a fresh process.
- **Unattended `mode:agent`**: invoked with `--mode=agent` in `$ARGUMENTS` (or by an automation
  harness that sets this programmatically, e.g. a `foundry` `post-feature` gate). Produces exactly
  one JSON blob as the final output, with no interactive prompts, no clarifying questions, and no
  partial/streaming output — the invocation runs to a terminal result (`converged`,
  `circuit_broken`, `checkpointed`, or another declared status) and emits one machine-parseable
  result. A `checkpointed` result is resumed by a new process/session.

## Final synthesis boundary

After CONVERGE chooses a terminal status, dispatch one **final synthesis worker** with artifact
paths and hashes only. It reads the detailed stage artifacts and writes the complete audit output
to `$WORKSPACE/final-report.md` (human mode) or `$WORKSPACE/final-result.json` (`mode:agent`). It
also writes `$WORKSPACE/final-summary.json`, an **at most 4 KiB** projection containing status,
counts, at most five highest-severity finding IDs with one-line summaries, coverage counts, and the
detailed artifact path plus hash. The parent reads only `final-summary.json`; the **parent never
reads the detailed report artifact**. If synthesis cannot fit a valid summary within 4 KiB, return
`final_summary_too_large` rather than copying details inline.

## Human-interactive mode

### During the run

Emit at most one short progress line per stage, derived from the stage's bounded manifest. Never
stream raw seat reports, validator reasoning, findings lists, or fixer reasoning into the parent
conversation; detailed material stays in workspace artifacts for the final synthesis worker.

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
[seat counts and coverage summary; complete cast is in the detailed artifact]

## Findings (post-VALIDATE, pre-FIX)
### Critical
[count plus at most five highest-severity finding IDs and one-line summaries across all severities]
### Important
[count]
### Minor
[count]

## Fixes Applied
[fixed/skipped counts; per-finding details are in the detailed artifact]

## Re-Review
### Regressions
[clean, or new findings]
### Domain-Intent Coherence
[clean, no CONTEXT.md, or coherence findings]

## Convergence
Status: converged | circuit_broken | escalated | capped | checkpointed
Rounds: N
[if circuit_broken: diagnosis + recommendation, per converge-and-pipeline.md]
[if escalated: unresolved sovereignty count plus at most five finding IDs and one-line summaries;
 the complete sign-off list and evidence remain in the hashed detailed artifact]
[if capped (narrowed-tier iteration cap hit with residual findings): tier-specific diagnosis +
recommendation to re-run at a wider tier, per lite-mode.md]
[if checkpointed: checkpoint path + exact `REVIEW_PANEL_FRESH_RESUME=1 claude -p
"/review-panel --resume <path> --checkpoint-sha256 <sha256>"` command; stop here]

## Coverage Honesty
[counts plus bounded notes]

## Detailed Audit Artifact
[path and sha256 for final-report.md]
```

The rendered parent response, including headings, is at most 4 KiB and is derived only from
`final-summary.json`.

### Post-report choices

After the terminal report, do no more work in this conversation. The human may accept the bounded
summary, inspect the detailed artifact outside the orchestration context, or launch a new scoped
review with `claude -p` in a fresh process. Never offer or run an additional in-conversation round.
For `escalated`, the complete sovereignty sign-off list stays in the hashed detailed artifact; the
parent shows its count and at most five summaries. Any sign-off workflow covering additional items
must start in a fresh process and must not reload the whole artifact into this parent.

## `mode:agent` JSON contract

Emit exactly one JSON object as the final and only output in this mode. Shape:

```json
{
  "status": "converged | circuit_broken | error | escalated | capped | checkpointed",
  "tier": "full",
  "narrowed_guarantees": [],
  "tier_source": "explicit",
  "rounds": 2,
  "finding_counts": {
    "total": 0,
    "unresolved": 0,
    "skipped": 0,
    "ordinary_unresolved": 0,
    "sovereignty_pending": 0
  },
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
  "artifacts": {
    "detailed_result_path": ".review-panel/workspace/final-result.json",
    "sha256": "..."
  },
  "checkpoint": null,
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

- The parent-visible JSON is `final-summary.json`, at most 4 KiB. `cast` and `findings` are bounded
  projections: `cast` may be reduced to counts, and `findings` contains at most five
  highest-severity one-line summaries. Complete schema-rich records live in
  `artifacts.detailed_result_path`; consumers needing full evidence read that artifact outside the
  orchestration conversation.
- `finding_counts` is always present and is computed from the complete detailed artifact, not the
  at-most-five `findings` projection. It is the fail-closed machine signal for unresolved, skipped,
  ordinary-unresolved, and sovereignty-pending work.
- `status`: exactly one of the six values. `error` is reserved for a run that failed to execute
  at all (e.g. artifact packaging was unavailable, no seats could be
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
  exclusively full mode's genuine-stagnation signal). `checkpointed` means a dirty round with
  remaining iteration budget persisted complete resume state and intentionally stopped before another round; it is neither a
  pass nor a failure.
- `checkpoint`: null unless `status` is `checkpointed`; otherwise an object with `path`,
  `next_round`, `resume_prompt`, `resume_command`, and `sha256`. `resume_prompt` is the slash-command
  prompt only; `resume_command` is the complete shell command including
  `REVIEW_PANEL_FRESH_RESUME=1 claude -p`. Both carry the prior invocation's
  `--checkpoint-sha256` value. Consumers must start it in a fresh process/session,
  never append it to the current conversation.
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
  sovereignty findings are outstanding; `pending: false` with an empty array otherwise.
  `sovereignty_finding_ids`
  references the `id` field of each still-pending finding in the `findings` array above, so a
  consumer can cross-reference without re-parsing evidence text.
- `convergence.capped.diagnosis`: null unless `status` is `capped`. When present, it is a tier-specific
  human-readable string naming which tier and cap was hit (e.g. "lite mode capped at 1 iteration;
  findings remain...") — see [converge-and-pipeline.md](converge-and-pipeline.md)'s "Narrowed-tier
  iteration cap" section for the exact per-tier wording. Mutually exclusive with
  `convergence.circuit_breaker.diagnosis` being non-null on the same run — a run is capped or
  circuit-broken, never both. In the combined sovereignty-plus-cap case, `status` is `capped` and
  `convergence.escalation.pending` remains true.
- `coverage`: never omit this object even when nothing was skipped — an explicit empty
  `skipped_seats`/`fallbacks_used`/`notes` is itself the coverage-honesty signal ("checked, found
  nothing to report") as opposed to the field being absent (which would leave a `foundry` gate
  unable to distinguish "fully covered" from "coverage-honesty step didn't run").

### Wiring to `foundry`

A `foundry.yaml` gate invoking this skill in `mode:agent` should treat the JSON's `status` field as
the gate's control signal: `checkpointed` → start the supplied resume command in a fresh Claude
process; `converged` → gate passes; `circuit_broken` → gate should fail with
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
          set -euo pipefail
          prompt="/review-panel $(git merge-base origin/main HEAD)..HEAD --mode=agent"
          fresh_resume=0
          # Each iteration is a new Claude process/context. Never use --resume-session here.
          for invocation in 1 2 3 4 5 6 7 8; do
            if [ "$fresh_resume" -eq 1 ]; then
              REVIEW_PANEL_FRESH_RESUME=1 claude -p "$prompt" \
                --dangerously-skip-permissions \
                --output-format json > "$FOUNDRY_RUN_DIR/claude-cli.json"
            else
              claude -p "$prompt" \
                --dangerously-skip-permissions \
                --output-format json > "$FOUNDRY_RUN_DIR/claude-cli.json"
            fi
            jq -r '.result' "$FOUNDRY_RUN_DIR/claude-cli.json" > "$FOUNDRY_RUN_DIR/review-panel.json"
            status=$(jq -er '.status | select(type == "string")' "$FOUNDRY_RUN_DIR/review-panel.json") || exit 1
            case "$status" in
              checkpointed|converged|escalated|capped|circuit_broken|error) ;;
              *) echo "review-panel: unknown status: $status" >&2; exit 1 ;;
            esac
            jq -e '
              (.coverage | type == "object") and
              (.artifacts.detailed_result_path | type == "string" and length > 0) and
              (.artifacts.sha256 | type == "string" and length == 64) and
              (.finding_counts | type == "object") and
              (if .status == "converged" then
                 .convergence.final_round_clean == true and
                 .convergence.escalation.pending == false and
                 .finding_counts.unresolved == 0 and .finding_counts.skipped == 0
               elif .status == "checkpointed" then
                 (.checkpoint.path | type == "string" and length > 0) and
                 (.checkpoint.resume_prompt | type == "string" and
                    test("--checkpoint-sha256 [0-9a-f]{64}")) and
                 (.checkpoint.sha256 | type == "string" and length == 64)
               elif .status == "escalated" then
                 .convergence.escalation.pending == true and
                 .finding_counts.ordinary_unresolved == 0 and
                 .finding_counts.sovereignty_pending > 0
               elif .status == "capped" then
                 (.convergence.capped.diagnosis | type == "string" and length > 0) and
                 .finding_counts.unresolved > 0
               elif .status == "circuit_broken" then
                 (.convergence.circuit_breaker.diagnosis | type == "string" and length > 0)
               else .status == "error"
               end)
            ' "$FOUNDRY_RUN_DIR/review-panel.json" >/dev/null || exit 1
            if [ "$status" != "checkpointed" ]; then
              break
            fi
            prompt=$(jq -er '.checkpoint.resume_prompt | select(type == "string" and length > 0)' "$FOUNDRY_RUN_DIR/review-panel.json")
            fresh_resume=1
          done
          # --output-format json wraps the CLI's own response envelope (type, subtype, result,
          # cost_usd, session_id, ...) — the skill's JSON contract is the agent's final reply,
          # which lands as a JSON *string* inside .result, not at the envelope's top level.
          status=$(jq -er '.status | select(type == "string")' "$FOUNDRY_RUN_DIR/review-panel.json") || exit 1
          case "$status" in
          checkpointed)
            echo "review-panel: still checkpointed after 8 fresh invocations" >&2
            exit 1 ;;
          escalated)
            # OQ4: escalated must never block or park unattended automation — surface it loudly,
            # then exit 0 like converged. See dual-mode-contract.md's "escalated must never block
            # or park the gate" note above.
            echo "review-panel: sovereignty finding(s) pending human sign-off — see review-panel.json convergence.escalation"
            jq -r '.convergence.escalation.sovereignty_finding_ids[]' "$FOUNDRY_RUN_DIR/review-panel.json"
            jq -r '.convergence.capped.diagnosis // empty' "$FOUNDRY_RUN_DIR/review-panel.json" ;;
          converged)
            exit 0 ;;
          capped)
            # This example invokes full mode (no --lite/--medium flag), so capped should never
            # occur here — this branch only matters if the gate is adapted to call --lite/--medium.
            # See dual-mode-contract.md's "Wiring to foundry" note on capped -> decision_on_failure:
            # warn: a project that adapts this example to a narrowed tier should move this gate to
            # its own profile with allow_failure: true / decision_on_failure: warn rather than
            # exiting 1 here, since a capped run found something but wasn't given the round budget
            # to finish, unlike a genuine circuit_broken stagnation.
            echo "review-panel: tier capped with residual findings — see review-panel.json convergence.capped.diagnosis"
            exit 1 ;;
          circuit_broken|error)
            exit 1 ;;
          *)
            echo "review-panel: unknown status: $status" >&2
            exit 1 ;;
          esac
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
- `status: checkpointed` causes the wrapper to launch the emitted resume command in a fresh Claude
  process, up to the logical run's round-8 hard cap. `status: converged` and `status: escalated` are
  the two final values that let the gate script exit `0`
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
