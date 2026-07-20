---
name: triage-spine
description: Consumes normalized triage items from any registered detector (lib-upgrades, prod-errors, and three stubbed slots) and runs the one loop — intake → reproduce → diagnose → fix → gate — filing a bead per item, reproducing the issue E2E before any fix, producing a fix diff via pas-pipeline, and gating it through review-panel --mode=agent. Use when a detector has just run and produced triage item(s), or when scheduling a Foundry recipe that pipes detector output into this spine.
argument-hint: "[triage item(s) as JSON, or a detector name to run first]"
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# Triage Spine (System 2 v1)

The one loop every detector feeds: **intake → reproduce → diagnose → fix → gate**. This skill
does not detect anything itself — detectors (`skills/detectors/*/SKILL.md`) are separate,
upstream producers of triage items. This skill's only job is to turn a valid triage item into a
beads issue, prove the problem is real before touching code, produce a fix, and gate that fix
through the project's sole diff-review substrate.

**Dependency direction (Invariant 2):** this skill may invoke `/review-panel ... --mode=agent`
and read its `dual-mode-contract.md` for the JSON schema it consumes. Nothing here is ever
imported by, or special-cased in, `review-panel` — the reference direction is triage →
review-panel only, never the reverse.

## Triage Item Contract

Every detector emits zero or more items of this exact shape:

```json
{
  "source": "lib-upgrades",
  "severity": "Critical",
  "evidence": "lodash@4.17.11 flagged CVE-2021-23337 (prototype pollution) in package-lock.json",
  "affected-paths": ["package-lock.json", "package.json"],
  "suggested-loop": "bump lodash to >=4.17.21 and re-run the dependent test suite"
}
```

| Field | Type | Constraint |
|---|---|---|
| `source` | string | one of the five registered detector names (see `references/detector-registry.md`) |
| `severity` | string | one of `Critical` \| `Important` \| `Minor` |
| `evidence` | string | non-empty; a verbatim quote (log line + stack trace, manifest entry, advisory ID) — never a paraphrase |
| `affected-paths` | array of strings | non-empty; repo-relative paths the fix will touch |
| `suggested-loop` | string | non-empty; a human-readable one-line next action, not a full plan |

## Phase 1 — Intake and contract validation

Before doing anything else, validate every incoming item against the table above. This is a hard
gate — no bead, no reproduction attempt, no fix, no panel run happens for an item that fails
validation.

Check, in order, and stop at the first violation:

1. All five fields present.
2. `source` is one of the five registered detector names in `references/detector-registry.md`.
3. `severity` is exactly one of `Critical`, `Important`, `Minor`.
4. `evidence` is a non-empty string.
5. `affected-paths` is a non-empty array of strings.
6. `suggested-loop` is a non-empty string.

On the first violation, **reject with a named field error** and stop processing that item — never
guess a default, coerce a type, or partially process a malformed item:

```
REJECTED — triage item from <source or "unknown"> — field "evidence": missing required field
REJECTED — triage item from lib-upgrades — field "severity": must be one of Critical|Important|Minor, got "urgent"
REJECTED — triage item from prod-errors — field "affected-paths": must be a non-empty array of strings, got string
```

Log the rejection and move to the next item in the batch (a malformed item never blocks valid
siblings from processing). This is the spine's only error-state path (AC5).

## Phase 2 — Zero-findings boundary

If a detector run produces zero items that survive Phase 1 (either because the detector found
nothing, or every item was rejected), stop here with no further side effects:

- Emit exactly one line: `triage-spine: <detector> — clean, 0 findings`
- File **no** bead
- Invoke **no** panel gate

This is a boundary condition, not a degraded run — a clean sweep is a normal, expected outcome and
must be reported as plainly as a run with findings (AC6).

## Phase 3 — File a bead per valid item

For each item that survives Phase 1:

1. Generate acceptance criteria for the fix via the `acceptance-criteria` skill (per this repo's
   Beads Issue Creation convention — AC first, then pass via `--acceptance`). Base the story on
   the item's `suggested-loop` and `evidence`.
2. Map `severity` to beads priority: `Critical` → `P0`, `Important` → `P1`, `Minor` → `P2`.
3. File the bead:

```bash
bd create --title="<one-line summary derived from evidence>" \
  --description="Detected by <source>. Evidence: <evidence>. Affected: <affected-paths>." \
  --type=bug --priority=<mapped priority> \
  --acceptance="<AC generated in step 1>"
```

PASS bar for this phase (AC1): the bead exists, carries AC, and the originating item validates
cleanly against the contract above.

## Phase 4 — Reproduce E2E, before any fix

Per this repo's root `CLAUDE.md` bug-fix rule ("always start with reproducing the bug in an E2E
setting as closely aligned with how an end user experiences it"), this step is a **hard ordering
constraint**: it must complete, and its result must be recorded on the bead, before Phase 5
(diagnose + fix) starts. Never skip straight to a fix because the evidence "looks obviously right."

- **`prod-errors` items:** the `evidence` field carries a log line and stack trace. Reproduce by
  driving the exact code path named in the trace (write or reuse a minimal repro script/test that
  exercises that path) until the same failure is observed locally. Record the repro command/script
  and its output on the bead (`bd update <id> --notes="Reproduction: <command> → <observed
  failure, matching the stack trace>"`) before touching any fix code.
- **`lib-upgrades` items:** reproduce by running the project's existing test suite (or a minimal
  repro for the specific CVE/breaking change named in `evidence`) against the current, un-upgraded
  dependency to confirm the flagged condition is real and reachable, not just present in a
  manifest. Record the same way.
- **Stubbed detectors** (`system-upgrades`, `iac-drift`, `security-advisory-sweeps`): not
  implemented in v1 — see `references/detector-registry.md`. If one of these ever emits an item
  before its detector skill is filled in, treat it exactly like any other source for this phase:
  the ordering rule is source-agnostic.

If reproduction genuinely fails (the described problem cannot be reproduced), do not force a fix —
update the bead with the reproduction attempt and its negative result, and route it the same as a
`circuit_broken`/`error` gate outcome (Phase 5): park it for a human rather than fixing a problem
that couldn't be confirmed.

PASS bar for this phase (AC4): the bead/transcript trail shows the reproduction step's command and
result *before* any diagnose/fix entry.

## Phase 5 — Diagnose and fix via PAS

Once reproduction confirms the problem, produce a fix diff using this repo's `pas-pipeline` skill
as the execution engine (per its "sole execution engine for AI tasks" role) — this spine does not
reimplement diagnosis/fix machinery. Launch or run a PAS pipeline targeted at the bead (spec: the
bead's title/description/AC plus the reproduction evidence from Phase 4) on a dedicated branch
named after the bead ID (e.g. `triage/<bead-id>`).

## Phase 6 — Gate through review-panel `--mode=agent`

Every fix diff, with no exception, is handed to `review-panel` before it can be considered
done — this plugin never reviews its own output. Dispatch exactly the pattern
`dual-mode-contract.md`'s "Concrete `foundry.yaml` example" already documents:

```bash
claude -p "/review-panel <fix-branch> --mode=agent" \
  --dangerously-skip-permissions \
  --output-format json > claude-cli.json
jq -r '.result' claude-cli.json > review-panel.json
status=$(jq -r '.status' review-panel.json)
```

Branch on `status` exactly per the resolved OQ4 semantics (do not reinvent this — it is
review-panel's own contract, consumed here unchanged):

- **`converged`** — report the bead ready-to-merge (`bd update <id> --notes="review-panel:
  converged, ready-to-merge"`). Auto-merge is out of scope for v1; a human still merges the PR.
- **`escalated`** — a sovereignty flag, **not** a loop failure. Do **not** park the bead and do
  **not** halt the run — unattended Foundry runs stay unattended by default, exactly as
  `dual-mode-contract.md`'s "escalated must never block or park the gate" note requires. Instead:
  1. Read `convergence.escalation.sovereignty_finding_ids[]` from `review-panel.json`.
  2. Cross-reference each ID against the matching entry in `findings[]` to pull its file, severity,
     and recommendation — the annotation must be sourced from this finding detail, never a bare
     status echo.
  3. Annotate the bead: `bd update <id> --notes="SOVEREIGNTY: human sign-off required — <finding
     file>: <finding recommendation, quoted>"`.
  4. Carry the identical annotation into the PR description, in an unmissable leading line (e.g.
     `**sovereignty: human sign-off required** — see <file> — <recommendation>`).
  5. If this spine run is itself unattended (invoked via a Foundry schedule), surface the same
     annotation loudly in the spine's own final log/output — not just the PR — so a human scanning
     Foundry logs cannot miss it either.
- **`circuit_broken` / `error`** — the loop itself failed to converge or failed to execute. Park
  the bead for a human: `bd human <id> --reason="review-panel <status>: <diagnosis from
  convergence.circuit_breaker.diagnosis, or the raw error>"`. Do not open a PR for a
  `circuit_broken`/`error` result — hand off the diagnosis, do not guess a resolution.

PASS bar for this phase (AC2): all four statuses produce their documented bead/PR outcome. (AC3):
given an `escalated` result specifically, the bead is not parked, the run does not halt, and the
produced PR body carries the explicit sovereignty annotation sourced from finding detail.

## Detector registry

See [references/detector-registry.md](references/detector-registry.md) for the full five-slot
registry (two implemented, three stubbed). This spine is detector-agnostic — it consumes any item
matching the Triage Item Contract above regardless of which registered detector produced it.

## Foundry wiring

See [../../docs/foundry-recipes.md](../../docs/foundry-recipes.md) for how each detector, this
spine's gate step, and two other schedulable entries from earlier phases are wired into
`foundry.yaml`. This skill does not create or modify any `foundry.yaml` file itself — wiring is a
Foundry-side concern, same convention `plan-security-review`'s "Foundry note" already establishes.

## Coverage honesty

If any step in this loop cannot run (e.g. `pas-pipeline` unavailable, `review-panel` command not
installed in this session, `bd` unavailable), say so explicitly on the bead and in the run's final
output — never silently skip a phase and report the item as handled. This applies per Invariant 3
across the whole pipeline, not just to this plugin.
