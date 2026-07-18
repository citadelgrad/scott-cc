# Investigation: scc-tsa — Phase 5: triage spine plugin (System 2 v1, Foundry-resident)

## Task nature

This is **greenfield plugin creation**, not a modification of existing code.
`plugins/triage/` does not exist anywhere in the repo. Every file this task needs is new; the only
*existing* files that need touching are the same three cross-cutting registration points every
prior sub-plugin phase has had to update (`marketplace.json`, `README.md`, and conformance-only
with `scripts/verify_plugin.py`).

This is the **final task in the epic** (scc-hzj). All three dependencies (scc-4xa Phase 1a security
seat, scc-g12 Phase 1b plan-security pass, scc-bqp Phase 2c data-steward seat) are closed. Once this
task closes, `check_remaining` should find no further work in the epic.

---

## Current behavior (the substrate this plugin builds on)

Nothing in the repo currently runs an automated detect→bead→fix→gate loop. The task depends on and
must exactly reuse (not reinvent) several pieces of prior art, all confirmed by direct reading:

1. **`mode:agent` JSON contract** — `plugins/review-panel/skills/review-panel/references/
   dual-mode-contract.md`: the full schema the gate step must consume — top-level `status:
   converged|escalated|circuit_broken|error`, `findings[]`, `convergence.escalation.
   sovereignty_finding_ids[]`, `coverage{}`. This file already contains a complete, copy-pasteable
   `foundry.yaml` `post-feature` profile example: `claude -p ... --output-format json` → `jq -r
   '.result'` unwrap → `jq -r '.status'` → branch on the four statuses. This is the direct template
   for both the spine's own gate-invocation logic and for `docs/foundry-recipes.md`'s panel-gate
   entry. It also notes a "trusted/internal branches only" security caveat worth carrying into the
   new doc.

2. **`escalated` vs `circuit_broken` semantics** — `.../references/converge-and-pipeline.md`'s
   CONVERGE section: `escalated` is an intentional, by-design terminal state for sovereignty-marked
   findings (never a loop failure) and must never block/park unattended automation; `circuit_broken`
   (3-strikes or 8-round hard cap) and `error` are genuine failures. This distinction is exactly what
   `current_task.md`'s "Status handling (resolved — OQ4)" section restates for triage — the spine
   must not reinvent this, only consume it: `circuit_broken`/`error` → park the bead for a human;
   `escalated` → do not block/park, but annotate the bead and PR with an unmissable sovereignty
   marker; `converged` → ready-to-merge (auto-merge stays out of scope for v1).

3. **Sovereignty marker mechanism** — `plugins/review-panel/skills/data-steward/SKILL.md` (Phase
   2c): `sovereignty: human-required` is set only by the originating reviewer seat and never cleared
   by FIX. Triage does not redefine this vocabulary — it only reads `convergence.escalation.
   sovereignty_finding_ids[]` plus the corresponding `findings[]` entries to build a human-readable
   annotation for the bead/PR (AC3 requires the annotation be "sourced from the panel finding
   detail," not a bare status echo).

4. **review-panel invocation contract** — `plugins/review-panel/commands/review-panel.md`: `/review-
   panel [base..head|branch|PR] [--mode=agent]`, `allowed-tools: Task, Read, Grep, Glob, Bash`. This
   is exactly what the spine's gate step dispatches against the fix diff/branch.

5. **Detector-shaped precedent** — `plugins/security-suite/skills/plan-security-review/SKILL.md`:
   the closest existing analog to a "detector" skill — frontmatter shape (`name`, `description`,
   `argument-hint`, `allowed-tools`), a documented `CLEAR`/`TRIGGERED`/`N/A` output vocabulary, and
   an explicit "Foundry note" section stating the pass is schedulable but that the skill itself
   writes no `foundry.yaml` (prose only, wiring is a Foundry-side concern). v1 triage detectors
   should follow the same frontmatter/Foundry-note pattern, but their actual output contract differs:
   they emit the normalized triage-item shape (`{source, severity, evidence, affected-paths,
   suggested-loop}`), not `CLEAR/TRIGGERED` lines, because findings feed a spine loop rather than
   terminate in a standalone report.

6. **Second Foundry schedulable-entry precedent** — `plugins/review-panel/skills/grill-my-taste/
   SKILL.md` line 95: `--distill` is nudged via a scheduled Foundry profile as a **periodic
   reminder-only prompt** (e.g. monthly), and the distillation conversation itself must never run
   unattended (Invariant 5 — human artifacts are human-owned). The task explicitly requires `docs/
   foundry-recipes.md` to list this entry alongside Phase 1b's plan-security pass and the triage
   detectors/gate, "consolidating what Foundry runs in one place."

7. **`skills/acceptance-criteria/SKILL.md`** (root `scott-cc`, not review-panel) — the Gherkin/
   checklist/rules-based AC generator with a testability gate, invoked whenever the spine files a
   bead ("spine files a bead (with AC per the acceptance-criteria rule)").

8. **Structural precedent for a new orchestrator skill** — `plugins/variant-explorer/` (Phase 4,
   most recent full scaffold): `skills/<name>/SKILL.md` as orchestrator + flat sibling agent `.md`
   files (`blind-builder.md`, `variant-judge.md`) + `commands/<name>.md` thin entry point + `README.
   md` + `tests/PRESSURE-TEST.md` fixture-per-scenario convention. This maps directly onto the
   task's prescribed layout: `skills/triage-spine/SKILL.md` as orchestrator, `skills/detectors/{lib-
   upgrades,prod-errors}/SKILL.md` as sibling *skills* (not `agents/`, since detectors — like plan-
   security-review — are markdown-prompt skills, not `Task`-dispatched agents).

9. **Plugin registration convention** — confirmed via `security-suite`/`variant-explorer`'s
   `plugin.json` shape and `scripts/verify_plugin.py`: every sub-plugin lives at `plugins/<name>/.
   claude-plugin/plugin.json` (`name`, `description`, `version`, `author: {"name": "Scott Nixon"}`,
   `license: "MIT"`, `repository`/`homepage` URLs), gets one matching entry in root `.claude-plugin/
   marketplace.json`, and one `### <name>` section plus an At-a-Glance count bump in root `README.
   md`. `scripts/verify_plugin.py` already walks every `marketplace.json.plugins[]` entry
   generically — no script change needed, just path/name/version conformance. Current state: 8 sub-
   plugins registered (`README.md`'s "At a Glance" table, line 20); adding `triage` makes 9.

---

## Required changes

### New files (`plugins/triage/`)

- **`.claude-plugin/plugin.json`** — manifest, same shape as `security-suite`'s/`variant-explorer`'s
  (name `triage`, version `1.0.0`, author, license MIT, repository/homepage pointing at
  `plugins/triage`).

- **`skills/triage-spine/SKILL.md`** — the core deliverable, the one loop, mapped to the ACs:
  - **Intake.** Accept one or more detector-emitted items. Validate each against the contract
    `{source, severity, evidence, affected-paths, suggested-loop}` before doing anything else
    (AC5): any item failing validation is rejected with a **named field error**, and the spine never
    processes a malformed item further.
  - **Zero-findings boundary (AC6).** A detector run that produces zero valid items short-circuits
    here: emit a one-line "clean" log, file no bead, invoke no panel — no other side effect.
  - **File bead.** For each valid item, `bd create` a bead, generating AC via the
    `acceptance-criteria` skill per repo convention (AC1's concrete pass bar: "bead exists, AC
    present, item validates against contract").
  - **Reproduce E2E, before any fix.** Per CLAUDE.md's project-wide bug-fix rule and AC4's explicit
    ordering requirement: for prod-errors items in particular (log line + stack trace in `evidence`),
    the spine must attempt E2E reproduction and that step must precede the diagnose/fix step in the
    transcript/bead trail — this is a hard ordering constraint, not just a recommendation.
  - **Diagnose + fix via PAS.** Produce a fix diff (references `pas-pipeline` skill/launch
    mechanics already documented elsewhere in the repo — not reinvented here).
  - **Gate.** Dispatch `/review-panel <fix-branch> --mode=agent`, parse the returned JSON `status`.
    Branch on all four values exactly per OQ4 (AC2): `converged` → report ready-to-merge;
    `escalated` → do **not** block/park; build the sovereignty annotation from `convergence.
    escalation.sovereignty_finding_ids[]` + matching `findings[]` detail and surface it in both the
    bead and the PR body (AC3); `circuit_broken`/`error` → park the bead for a human.

- **`skills/detectors/lib-upgrades/SKILL.md`** — v1 detector #1: scans a manifest for
  outdated/CVE-flagged dependencies, emits one triage item per finding (AC1's fixture target).

- **`skills/detectors/prod-errors/SKILL.md`** — v1 detector #2: consumes log-source input
  (Sentry-shaped; the integration itself is a config detail, not a code dependency), emits triage
  item(s) whose `evidence` field carries the stack trace verbatim (AC4).

- **Detector registry artifact.** The task states "the registry design (one spine, five detectors)
  is the deliverable; filling all five is not" — this needs a concrete, small artifact (most likely
  a `references/detector-registry.md` under `skills/triage-spine/`, or a table inside `triage-spine/
  SKILL.md` itself) enumerating all five detector slots: `lib-upgrades` and `prod-errors`
  implemented; `system-upgrades`, `iac-drift`, `security-advisory-sweeps` registered as explicit
  stubs (one-line "not yet implemented" placeholder each, same shape so a future phase can fill
  them in without restructuring the registry).

- **`docs/foundry-recipes.md`** — schedule-wiring documentation: each detector as a periodic
  Foundry check, the panel gate as the mandatory post-fix step (adapting dual-mode-contract.md's
  existing `foundry.yaml` example), **plus** Phase 1b's `plan-security-review` pre-build gate and
  Phase 3c's `grill-my-taste --distill` reminder-only nudge, consolidating "what Foundry runs" in
  one place as the task explicitly requires. No `foundry.yaml` file exists anywhere in this repo
  yet, so this is pure documentation with no live file to wire against.

- **`README.md`** (plugin-level) — same shape as `security-suite/README.md` (What's Included / When
  to Use / Common Use Cases / Quick Start).

- **`tests/PRESSURE-TEST.md`** + **`tests/fixtures/<scenario>/`** — since every skill here is a
  non-executable markdown-prompt file (same as review-panel/variant-explorer), tests are documented
  live-dispatch demonstrations, not a pytest suite. One fixture per AC: AC1 (fixture repo with an
  outdated dep), AC2 (four fixtures, one per forced status), AC3 (an escalated-status fixture with a
  sovereignty finding), AC4 (a log line with a stack trace), AC5 (a malformed/contract-violating
  item), AC6 (a zero-findings detector run).

### Existing files to modify

- **`.claude-plugin/marketplace.json`** — add one new `triage` entry (name/source/description with
  skill counts/version `1.0.0`/author/tags), matching the new `plugin.json` exactly (this is exactly
  what `scripts/verify_plugin.py` checks).
- **`README.md`** — bump `## At a Glance`'s "Sub-plugins" row 8 → 9, add `triage` to the names list,
  and add a new `### triage` subsection after the existing 8 (one-line description + Skills table),
  following the exact structure every sibling subsection uses.
- **No change needed**: `scripts/verify_plugin.py` — already generic; the new plugin only needs to
  follow the `.claude-plugin/plugin.json` path convention.

---

## Risks and dependencies

- **Dependency direction (Invariant 2) is the single highest-risk item.** `triage → review-panel`
  only. Triage's `SKILL.md` may invoke `/review-panel ... --mode=agent` and read `dual-mode-
  contract.md` for its schema, but nothing in `review-panel` may import, detect, or special-case
  triage. No edits to any file under `plugins/review-panel/` are in scope for this task.
- **OQ4 status handling must be reproduced exactly as already resolved**, not reinvented. In
  particular, `escalated` is expected/by-design and must never halt unattended automation, while
  `circuit_broken`/`error` are the only two statuses that park the bead — collapsing these
  distinctions (e.g. treating `escalated` as a park condition) would directly violate the task's own
  resolved OQ4 decision and AC3.
- **Sovereignty annotation must be sourced from panel finding detail**, not a bare status string —
  the spine needs to read `convergence.escalation.sovereignty_finding_ids[]` and cross-reference the
  matching `findings[]` entries to build a meaningful human-readable annotation for the bead and PR
  body.
- **AC4's ordering requirement is transcript/bead-trail-verifiable** — the SKILL.md's documented
  procedure must state E2E reproduction as an unconditional prerequisite gate before diagnose/fix
  for the prod-errors path (and arguably spine-wide, consistent with the project's global
  reproduce-before-fix rule in this repo's root CLAUDE.md).
- **Detector registry scope discipline.** Only 2 of 5 detectors get real implementations; the other
  3 are deliberately stubs. Risk of scope creep is building out logic for the stub detectors beyond
  a registry placeholder entry — the task is explicit that filling all five is not the deliverable.
- **No live `foundry.yaml` exists in this repo yet** — `docs/foundry-recipes.md` is pure
  documentation with nothing to wire against; it must not fabricate a schema that diverges from the
  global CLAUDE.md's `foundry.yaml` schema or `dual-mode-contract.md`'s existing example.
- **This is the Investigate step only.** No `plugins/triage/` files, and no `marketplace.json`/
  `README.md` edits, have been made in this step — all deferred to the next pipeline (Implement)
  step, per `pipelines/two-system-architecture.dot`'s node scope boundaries.
