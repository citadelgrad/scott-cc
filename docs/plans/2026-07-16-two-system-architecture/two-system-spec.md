# Two-System Architecture — SPEC

**Status:** Draft — pending agreement, then decompose to beads, then Reck/PAS build
**Date:** 2026-07-16
**Owner:** Scott
**Pairs with:** [two-system-prd.md](./two-system-prd.md)

> Technical specification for the PRD's five goals. Each phase is independently
> shippable and ordered by priority. Acceptance criteria are written to be testable
> (unambiguous PASS/FAIL) so they can seed bead ACs at decompose time per the
> `acceptance-criteria` skill rules: happy path, error states, boundary conditions;
> no Definition-of-Done items.

---

## Architecture invariants (apply to every phase)

1. **Substrate rule.** Any component that produces a diff hands it to `review-panel`
   (interactive by default, `--mode=agent` when unattended). No phase may introduce a
   second review mechanism.
2. **Dependency direction.** `triage → review-panel` and `foundry → {panel, triage}`
   only. `review-panel` never imports from, detects, or special-cases triage.
3. **Coverage honesty.** Every seat or pass added must follow the panel's existing
   rule: if it cannot run (missing skill, no `Task` support), report the gap
   explicitly — never silently skip.
4. **Graceful cross-plugin degradation.** Where one plugin references another (panel →
   security-suite), absence degrades to the current behavior plus an explicit coverage
   note, matching the persona catalog's existing "Missing skill handling" section.
5. **Human artifacts are human-owned.** `DATA-MODEL.md` and `TASTE.md` are written
   through grilling sessions with the human; agents may propose edits but the FIX
   stage never auto-modifies them.

---

## Phase 1 — Security passes (planning + review stages)

### 1a. Security seat in the panel

**Problem.** `plugins/review-panel/reviewers/persona-catalog.md` states "No
security-specific skill is vendored in this plugin" and makes the Security seat
conditional on live-scan enrichment. `plugins/security-suite/agents/security-engineer.md`
(diff-shaped: vulnerability assessment, threat modeling, OWASP/CWE) already exists in
this repo. The catalog documents a gap that is already filled.

**Changes.**

- `plugins/review-panel/reviewers/persona-catalog.md`:
  - Rewrite the Security seat entry: **Casts** `security-suite`'s `security-engineer`
    agent (precedent for casting an agent rather than a skill already exists:
    Fresh-Eyes casts `agents/clean-room-alternative.md`).
  - **Cast-when:** risk-triggered — diff touches auth, crypto, secrets, input
    validation at a trust boundary, deserialization, dependency manifests/lockfiles,
    IaC, or CI config. Fail-closed rule applies (ambiguity → cast). Note: triage-origin
    diffs (lib upgrades, IaC) hit these triggers by construction.
  - **Model tier:** top-tier (unchanged from current conditional entry).
  - **Missing-plugin fallback:** if `security-suite` is not installed, current behavior
    (adversarial-reviewer Scope item 2 + explicit coverage-gap note) — verbatim reuse
    of the existing fallback text.
  - Update the Seat Summary Table row accordingly.
- `plugins/review-panel/agents/` — **no vendoring in this phase** unless Open Question
  OQ1 resolves to "vendor" (air-gap constraint).
- Seat output must conform to the Critical/Important/Minor + verdict shape in
  `contracts/reviewer-output.md` so MERGE/VALIDATE consume it with zero special-casing.
  If `security-engineer.md`'s output section needs a conformance note, add it there.

**Acceptance criteria.**

- Given a diff modifying a dependency lockfile and `security-suite` installed, a panel
  run's Cast section lists the Security seat with a cast rationale. **PASS/FAIL:**
  seat present in Cast output.
- Given the same diff with `security-suite` absent, the final report's Coverage Honesty
  section states no dedicated security seat was cast and why. **PASS/FAIL:** explicit
  gap statement present.
- Given a docs-only diff, the Security seat is not cast. **PASS/FAIL:** seat absent
  from Cast output.
- Security-seat findings appear in MERGE with fingerprints and confidence anchors like
  any other seat's. **PASS/FAIL:** at least one seeded vulnerable-diff fixture (see
  `tests/PRESSURE-TEST.md` pattern) produces a validated security finding.

### 1b. Plan-security pass

**What.** A lightweight threat-model pass at the *end of planning*, before build — the
planning-stage counterpart of the review seat. Not a comprehensive audit (that is the
future Foundry suite); a checkpoint that asks: trust boundaries crossed? new data
flows? authn/authz surface changed? secrets introduced? third-party deps added?

**Changes.**

- New skill `plugins/security-suite/skills/plan-security-review/SKILL.md`:
  - Input: a plan/PRD/spec document (path or in-conversation).
  - Procedure: extract security-relevant deltas → map to OWASP cheatsheet topics
    (reuse `security-advisor.md`'s topic table; WebFetch when online, degrade to
    built-in checklist when air-gapped) → emit findings as
    `CLEAR/TRIGGERED/N/A` lines (same vocabulary as `domain-modeling` for future
    merge-ability) plus a one-paragraph go/no-go.
  - Explicit boundary: "Not for reviewing code diffs — that is the panel's security
    seat."
- Wire-in points (documentation edits, no new mechanism):
  - `plugins/review-panel/skills/grill-with-docs/SKILL.md`: add a closing step — offer
    the plan-security pass when the grilling session ends with a build-ready plan.
  - This spec's Foundry section (Phase 5) lists it as a schedulable pre-build gate.

**Acceptance criteria.**

- Given a plan that adds a login endpoint, the pass TRIGGERs at least authn/session
  topics with cheatsheet citations. **PASS/FAIL:** triggered lines cite topic names.
- Given a plan with no security-relevant delta (pure UI copy change), output is all
  CLEAR/N/A with an explicit "no security-relevant surface" statement — no forced
  findings. **PASS/FAIL:** zero TRIGGERED lines.
- Offline (no WebFetch): pass completes using the built-in checklist and notes the
  degraded mode. **PASS/FAIL:** completion + explicit degradation note.

---

## Phase 2 — Data steward (data-layer sovereignty)

### 2a. `DATA-MODEL.md` format (shared contract)

- New `plugins/review-panel/formats/DATA-MODEL-FORMAT.md`, sibling of
  `CONTEXT-FORMAT.md`. Sections: **Entities & relationships** (with storage mapping),
  **Invariants** (what must never be violated), **Ownership & routing** (which system
  writes what), **Agent boundary** (decisions agents may not revisit without
  escalation), **Change log** (dated, human-initialed).
- Explicit contrast with `CONTEXT.md`: CONTEXT.md is a glossary and forbids
  implementation detail; DATA-MODEL.md is *exactly* the implementation-detail record
  for data. Cross-link both files' formats to each other with this distinction.
- Explicitly declared as a **cross-system contract**: System 2 fixes (migrations in a
  library upgrade, IaC data-store changes) are bound by it identically.

### 2b. `grill-the-schema` skill (planning stage)

- New `plugins/review-panel/skills/grill-the-schema/SKILL.md`, modeled on
  `grill-with-docs` (one question at a time, recommended answers, explore codebase
  instead of asking when possible, update artifacts inline).
- Targets `DATA-MODEL.md` instead of `CONTEXT.md`: interviews the human about
  entities, invariants, lifecycle (soft-delete? audit? retention?), volume/access
  patterns, and boundaries; stress-tests with concrete scenarios; cross-references
  actual schema/migration files for contradictions; creates `DATA-MODEL.md` lazily on
  first resolved decision.
- ADR offers follow the same 3-part gate as grill-with-docs (hard to reverse,
  surprising, real trade-off) — schema decisions frequently clear it.

### 2c. `data-steward` seat (review stage, blocking)

- New entry in `persona-catalog.md` under Risk-Triggered Seats:
  - **Casts:** new skill `plugins/review-panel/skills/data-steward/SKILL.md`
    (read-only, like `domain-modeling`).
  - **Cast-when:** diff touches migration files, ORM/model definitions, schema files
    (`*.sql`, `schema.*`, `prisma/`, `alembic/`, `migrations/`, etc.), serialization
    formats, or any file `DATA-MODEL.md` maps an entity to. Fail-closed.
  - **Model tier:** top-tier.
- Skill procedure: check the diff against `DATA-MODEL.md` (invariants, agent
  boundary), then against a migration-safety checklist: reversibility/down-path,
  expand→migrate→contract sequencing, backfill strategy and volume, lock behavior,
  index-creation strategy, nullable-then-tighten, dual-write windows.
- **Sovereignty escalation (contract extension).** Findings keep the standard
  Critical/Important/Minor shape, plus an optional marker
  `sovereignty: human-required` on a finding when the diff crosses the Agent boundary
  section of `DATA-MODEL.md` or `DATA-MODEL.md` is absent while the diff changes
  schema semantics. Orchestrator handling:
  - FIX stage **never auto-fixes** sovereignty-marked findings.
  - CONVERGE cannot report a clean round while unresolved sovereignty findings exist;
    interactive mode surfaces them as an explicit human sign-off request;
    `mode:agent` emits top-level status `escalated` (extends the
    `converged | circuit_broken` status set in
    `references/dual-mode-contract.md`).
  - Files to edit: `skills/review-panel/references/fix-and-rereview.md`,
    `references/converge-and-pipeline.md`, `references/dual-mode-contract.md`,
    `references/merge-and-validate.md` (marker passes through dedupe untouched).

### 2d. Data-layer guard hook (mechanical negation)

- New `hooks/data_layer_guard.py` registered as a PreToolUse hook in `hooks/hooks.json`
  (core plugin, alongside `prefer_modern_tools.py`).
- Behavior: intercept Edit/Write/NotebookEdit targeting data-layer paths (default
  glob set: `**/migrations/**`, `**/models/**` for known ORMs, `*.sql`,
  `**/schema.*`, `prisma/schema.prisma`, `**/alembic/**`; overridable via a
  `.data-guard.json` in the repo root). On match: warn-and-confirm (hook exit code
  prompting), with an allow flag once a `DATA-MODEL.md` change-log entry for the
  current work exists. Never hard-fail CI — this is a developer-loop guard.

**Acceptance criteria (phase 2).**

- Grilling session on a fixture repo with an orders schema produces a `DATA-MODEL.md`
  containing at least entities, one invariant, and an Agent boundary section.
  **PASS/FAIL:** file exists with all required sections.
- Panel run on a diff adding a destructive migration (drop column with data) yields a
  data-steward finding at Critical with the migration-safety principle named.
  **PASS/FAIL:** finding present, severity Critical.
- Panel run on a diff violating a `DATA-MODEL.md` Agent-boundary entry ends
  `escalated` (agent mode) / explicit sign-off request (interactive); FIX did not
  modify the migration. **PASS/FAIL:** status + untouched file.
- Diff not touching data-layer paths: seat not cast. **PASS/FAIL:** absent from Cast.
- Hook: an Edit to `migrations/0002_x.py` without a DATA-MODEL change-log entry
  triggers the confirm prompt; the same edit after adding the entry passes silently.
  **PASS/FAIL:** both behaviors observed.
- Boundary: repo with no `DATA-MODEL.md` at all — seat still casts on schema diffs and
  emits a sovereignty finding recommending `grill-the-schema`. **PASS/FAIL:** finding
  present.

---

## Phase 3 — Codified taste

### 3a. `TASTE.md` format

- New `plugins/review-panel/formats/TASTE-FORMAT.md`. Sections: **Preferences**
  (each: rule, rationale, strength weak/strong/absolute, provenance — which choice or
  override produced it), **Weightings** (personal calibrations of universal principles,
  e.g. "locality beats DRY"), **Anti-preferences** (patterns to flag even when
  defensible), **Candidate rules** (captured overrides awaiting distillation — see 3c).
- Scope note in the format itself: universal quality does NOT belong here (that is the
  Ousterhout lens set / Karpathy guidelines); only personal, contested preference.

### 3b. `grill-my-taste` skill

- New `plugins/review-panel/skills/grill-my-taste/SKILL.md`, grill-family mechanics.
- Elicitation is **choice-based, not introspective**: present pairs of realistic
  alternatives (two API shapes, two error-message styles, two module layouts —
  generated from the user's actual codebase where available), user picks, agent asks
  why, distills a candidate rule, confirms wording, writes to `TASTE.md` inline.
- Evidence mining mode: when pointed at a repo/PR history, find places the human
  rewrote agent or contributor output and turn each rewrite into a forced-choice
  question (before vs after).

### 3c. Taste feedback loop

- Capture: convention + `bd remember` — whenever the human overrides a panel finding
  or rejects agent output with a reason, record it as a taste candidate. Documented in
  the skill; no new tooling required in v1.
- Distillation: a mode of `grill-my-taste` (`--distill`) that walks Candidate rules,
  promotes/merges/rejects each, and prunes stale preferences. Foundry-schedulable
  (e.g., monthly) as a prompt to run the session — the session itself stays
  interactive (human-owned artifact, invariant 5).

### 3d. Taste seat

- New `persona-catalog.md` risk-triggered entry:
  - **Casts:** new read-only skill `plugins/review-panel/skills/taste-review/SKILL.md`.
  - **Cast-when:** `TASTE.md` exists in the target repo. (No TASTE.md → seat never
    casts; no generic fallback.)
  - **Model tier:** mid-tier (applying a written preference file is procedural).
  - Findings cite the specific TASTE.md clause; severity mapped from the preference's
    strength (absolute → Important+, strong → Important, weak → Minor). Taste findings
    are never Critical and never sovereignty-marked.

**Acceptance criteria (phase 3).**

- A grill-my-taste session of ≥5 forced choices produces a `TASTE.md` where every
  preference has rule + rationale + strength + provenance. **PASS/FAIL:** all fields
  present for all entries.
- Panel run on a diff violating a strong preference yields a taste finding citing the
  clause verbatim. **PASS/FAIL:** clause quoted in finding.
- Repo without `TASTE.md`: taste seat absent from Cast; no taste findings.
  **PASS/FAIL:** absent.
- `--distill` on a TASTE.md with ≥3 candidate rules ends with zero remaining
  candidates (each promoted, merged, or rejected with the human). **PASS/FAIL:**
  Candidate section empty after session.
- Error state: malformed TASTE.md (missing strength) — seat reports the file as
  unusable in Coverage Honesty rather than guessing. **PASS/FAIL:** explicit note.

---

## Phase 4 — Variants (parallel exploration)

- New skill `plugins/review-panel/skills/explore-variants/SKILL.md` *or* standalone
  plugin — see OQ2. Spec assumes a skill co-located with the other plan-stage tooling;
  moving it is a packaging decision, not a design change.
- Procedure:
  1. Input: a design question or feature spec + acceptance criteria (generate via
     `acceptance-criteria` skill if absent) + N (default 3, cap 6).
  2. Spawn N **blind** builders — `clean-room-alternative` dispatch pattern, each in
     an isolated `git worktree`, each given the spec + AC only (no sibling output, no
     preferred approach), each with a distinct angle prompt (e.g., MVP-first,
     data-model-first, dependency-free).
  3. Judge panel: independent judges score each variant against (a) the AC, (b)
     `TASTE.md` when present, (c) simplicity (reuse `ponytail-review` lens). Judges
     see all variants; builders never do.
  4. Output: ranked shortlist with per-variant scorecard citing AC items and TASTE
     clauses; the human picks; losing worktrees are deleted after an explicit
     "harvest ideas from runners-up?" prompt.
- Execution note: local interactive runs dispatch via `Task`; Foundry/Reck runs map
  step 2 onto PAS tasks in containers (one task per variant). The skill documents
  both paths; v1 implements the local path, PAS mapping is a documented recipe.

**Acceptance criteria (phase 4).**

- A run with N=3 produces 3 worktrees, 3 scorecards, and a ranked shortlist; each
  scorecard cites ≥1 AC item. **PASS/FAIL:** counts and citations present.
- With `TASTE.md` present, at least the winning scorecard references taste clauses;
  without it, scorecards omit the taste axis and say so. **PASS/FAIL:** both modes.
- Builder isolation: no builder prompt contains another variant's content (verifiable
  from dispatch logs). **PASS/FAIL:** prompt inspection.
- Error state: a builder that fails/times out is reported as a lost variant, run
  continues with survivors, never silently reduced N. **PASS/FAIL:** explicit note.
- Boundary: N=1 refuses with guidance to build directly; N>6 clamps with a note.
  **PASS/FAIL:** both behaviors.

---

## Phase 5 — Triage spine (System 2 v1, Foundry-resident)

- New plugin `plugins/triage/` — **separate from review-panel** (invariant 2).

```
plugins/triage/
├── .claude-plugin/plugin.json
├── skills/
│   ├── triage-spine/SKILL.md        # the one loop: intake → reproduce → diagnose → fix → gate
│   └── detectors/
│       ├── lib-upgrades/SKILL.md    # v1 detector
│       └── prod-errors/SKILL.md     # v1 detector (log/Sentry-shaped input)
└── docs/foundry-recipes.md          # schedule wiring for Foundry
```

- **Spine contract.** Every detector emits a normalized *triage item*:
  `{source, severity, evidence, affected-paths, suggested-loop}` → spine files a bead
  (with AC per the acceptance-criteria rule), reproduces the issue E2E first (per
  CLAUDE.md bug-fix rule), produces a fix diff via PAS, and gates it through
  `review-panel --mode=agent`. `escalated` or `circuit_broken` panel results park the
  bead for the human; `converged` results are reported ready-to-merge (auto-merge is
  out of scope for v1).
- **v1 detectors:** library upgrades (outdated/CVE-flagged deps from manifest scan)
  and prod errors (pointed at a log source; Sentry integration is a config detail,
  not a dependency). System upgrades, IaC drift, and security-advisory sweeps are
  registered in the detector registry as stubs — the registry design (one spine, five
  detectors) is the deliverable; filling all five is not.
- **Foundry wiring:** `docs/foundry-recipes.md` documents scheduling each detector as
  a periodic Foundry check and the panel gate as the mandatory post-fix step. Also
  lists Phase 1b's plan-security pass and Phase 3c's distillation prompt as
  schedulable entries, consolidating "what Foundry runs" in one place.
- **Future-proofing (PRD §5):** detectors communicate with the spine only via the
  triage-item contract, so an org-level system can later consume the same detectors.

**Acceptance criteria (phase 5).**

- Lib-upgrade detector on a fixture repo with an outdated dep emits a valid triage
  item and the spine files a bead with AC. **PASS/FAIL:** bead exists, AC present,
  item validates against contract.
- End-to-end: detector → fix diff → `mode:agent` panel run returns JSON whose status
  is one of `converged | escalated | circuit_broken`; bead updated accordingly.
  **PASS/FAIL:** status handled in all three branches (fixtures may force each).
- Prod-error detector given a log line with a stack trace produces a triage item whose
  evidence includes the trace and whose spine run attempts E2E reproduction before any
  fix. **PASS/FAIL:** reproduction step precedes fix in the transcript/bead trail.
- Error state: detector output failing contract validation is rejected with a named
  field error; spine never processes a malformed item. **PASS/FAIL:** rejection path.
- Boundary: zero findings from a detector run → no beads filed, one-line "clean" log,
  no panel invocation. **PASS/FAIL:** no side effects.

---

## Verification & tooling (all phases)

- `scripts/verify_plugin.py` runs clean after each phase's plugin/manifest edits.
- Each phase adds at least one fixture under the owning plugin's `tests/` following
  the `review-panel/tests/PRESSURE-TEST.md` pattern (seeded defect → expected
  finding).
- `uv run pytest` and `uv run ruff check --fix` gate every phase (repo rules).
- README.md / marketplace catalog counts updated per phase (they enumerate commands/
  skills/agents explicitly).

## Decompose plan (after agreement)

1. One epic per phase (5 epics), via `pas decompose` against this spec or
   beads-epic-builder; Phase 2 splits into 2a–2d beads, others 1–3 beads each.
2. AC for each bead seeded from this spec's acceptance criteria via the
   `acceptance-criteria` skill (`--acceptance=...` per CLAUDE.md).
3. Build order strictly 1 → 2 → 3 → 4 → 5; 4 is blocked on 3 (taste is the scoring
   function); 5 is blocked on 1 (security seat should exist before triage feeds it
   dependency diffs).
4. Execution via Reck/PAS per epic (`pas scaffold` from the epic, run in containers).

## Open questions (resolve before decompose)

- **OQ1 — Vendor vs. reference security.** Review-panel's original constraint is
  air-gapped self-containment; casting `security-suite`'s agent is a cross-plugin
  reference. Options: (a) reference with graceful degradation (spec'd above; both
  plugins ship in scott-cc, so co-install is the norm), (b) vendor a seat-shaped
  security skill into review-panel and have security-suite own only the
  advisory/planning side. Recommendation: (a) now, revisit (b) if an air-gapped
  deploy actually materializes.
- **OQ2 — Variants packaging.** Co-locate in review-panel (plan-stage tooling already
  lives there) vs. standalone plugin (keeps panel lean; variants has different
  runtime needs — worktrees, PAS mapping). Recommendation: standalone
  `plugins/variant-explorer/` to avoid growing the panel beyond plan/review-stage
  *judgment* tooling; costs one more manifest.
- **OQ3 — Naming.** review-panel now demonstrably hosts planning-stage skills
  (grill-with-docs, and per this spec grill-the-schema, grill-my-taste, plan-security
  wiring). Rename/re-describe (e.g., description covering "plan + review stages of
  System 1") or split a `planning` plugin later? Recommendation: re-describe only, no
  rename — churn outweighs clarity gain today.
- **OQ4 — Escalated status consumers.** `mode:agent` gains status `escalated`
  (Phase 2c). Confirm Foundry's gate handling treats it as "park for human," distinct
  from `circuit_broken` ("loop failed"). Needs a matching Foundry-side change if its
  gate currently binary-switches on `converged`.
