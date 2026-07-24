# ADR: Long-term shape of the 5 thin top-level agents (scc-ncs.27)

## Status

Decided. Implementation tracked as separate follow-up work (not required by scc-ncs.27).

## Context

Five top-level agents — `agents/backend-architect.md`, `agents/frontend-architect.md`,
`agents/system-architect.md`, `agents/refactoring-expert.md`, `agents/requirements-analyst.md`
— are "thin": 48 lines each, all persona framing (Triggers / Behavioral Mindset / Focus Areas /
Key Actions / Outputs / Boundaries) with no prescriptive internal workflow, unlike
`agents/api-debugger.md` (216 lines, numbered Debugging Workflow with concrete
bash/curl/Python/JS snippets, a Playwright MCP tool table, and worked examples).

scc-ncs.9 (already merged to `feat/scc-ncs`) applied a cheap interim fix: it added a
"**Not for:** ... (use `X` instead)" scope-boundary line to each of the 5 agents to resolve
overlapping trigger confusion (e.g. `backend-architect` pointing to `api-debugger` for live
debugging, and to `system-architect` for cross-cutting concerns). That fix stands as the interim
state and is not superseded or removed by this decision — it addresses confusability between
agents, not depth. This ADR decides the deeper, longer-term question scc-ncs.9 explicitly
deferred.

Three candidate directions were proposed:

- **(a) Deepen** each of the 5 to `api-debugger.md`-level workflow depth.
- **(b) Fold** all 5 into `general-purpose` plus a shared skill (delete the 5 agent files).
- **(c) Multi-agent orchestrator**: treat "architecture design" as a review-panel-style
  CAST/SPAWN/MERGE/VALIDATE/FIX/RE-REVIEW/CONVERGE pipeline (`plugins/review-panel`), applied to
  `agents/`.

## Decision

**(a) Deepen — applied selectively, prioritized by actual usage, not uniformly across all 5.**

Priority 1 (deepen first): `system-architect`, `frontend-architect`, `backend-architect`.
Priority 2 (deepen on the same bar, lower priority): `requirements-analyst`, `refactoring-expert`.

## Evidence

- **Usage signal** (`rg` across the repo for these 5 names, excluding `agents/*.md` themselves
  and README/QUICK-START listing tables): only `plugins/beads-epic-builder/agents/feature-builder.md`
  and `plugins/beads-epic-builder/commands/build-feature.md` programmatically dispatch these
  agents. `system-architect` is spawned unconditionally in Phase 2; `frontend-architect` and
  `backend-architect` are spawned conditionally (skipped for "≤2 component changes with clear
  patterns" / "simple CRUD only"). Each is a single-shot `Task` dispatch producing one scoped
  output file (`system-arch.md`, `frontend-arch.md`, `backend-arch.md`) consumed by a later
  phase — never iterative, never multi-round.
  `requirements-analyst` and `refactoring-expert` have **zero** programmatic call sites anywhere
  in `commands/`, `skills/`, or other `agents/` files — they exist only as manually-selectable
  agents and README/QUICK-START listing entries.
- **Depth reference bar**: `api-debugger.md` is 216 lines with a numbered workflow (Symptom
  Collection → Hypothesis Formation → Investigation Strategy → Browser Validation → Fix
  Verification Checklist), concrete code snippets, and a tool-use table. The 5 thin agents are
  48 lines each with no equivalent internal procedure.
- **Review-panel's machinery scale**: `plugins/review-panel/skills/review-panel/references/*.md`
  is ~2,100 lines across 7 reference files (CAST/SPAWN, MERGE/VALIDATE, FIX/RE-REVIEW,
  CONVERGE/pipeline-not-barrier, lite-mode, dual-mode-contract, design-lineage) plus a 191-line
  `SKILL.md` — persona catalogs with cast-when criteria, confidence/fingerprint-based merge and
  dedup, iterative fix-and-rereview convergence loops, 3-strikes circuit breakers, sovereignty
  guards, and tiered (`--lite`/`--medium`/full) dispatch filtering. This machinery exists to
  reconcile **multiple independent, potentially-disagreeing perspectives on one shared diff**
  that must converge to a single verdict.

## Reasoning

1. **Why not (b) fold into general-purpose + skill:** For the 3 agents with real call sites,
   `feature-builder.md`'s Phase 2 gate wants a dedicated, addressable `Task` `subagent_type` per
   architecture domain producing one scoped output file. Collapsing these into
   "`general-purpose` + invoke a skill" adds indirection (general-purpose still has to load and
   follow the skill) with no benefit over a dedicated agent file, and complicates
   `feature-builder`'s existing dispatch table for no gain. It also doesn't fix
   `requirements-analyst`/`refactoring-expert`'s actual problem (unclear value) — it just
   relocates the thinness into a skill file instead of an agent file.

2. **Why not (c) multi-agent orchestrator:** These 5 agents are dispatched individually, at
   different times, for different scoped questions — never as N parallel perspectives on one
   shared artifact needing fingerprint-based merge and iterative convergence, which is the
   entire reason review-panel's CAST/SPAWN/MERGE/CONVERGE machinery exists. Building ~2,000+
   lines of orchestration to wrap 2-3 lightly-used single-shot advisory personas fails this
   repo's own stated bar (CLAUDE.md: prefer quality/simplicity/robustness/long-term
   maintainability) on its own terms — more moving parts, more failure modes, more surface to
   keep in sync, for agents invoked a handful of times via one fixed call site. This is
   overengineering, not rigor.

3. **Why (a), and why prioritized rather than uniform:** Deepening `system-architect`,
   `frontend-architect`, and `backend-architect` first directly improves an existing, live
   pipeline's output quality (`feature-builder`'s Phase 2 architecture-review gate consumes their
   output today). `requirements-analyst` and `refactoring-expert` should reach the same depth
   eventually for consistency — they remain first-class, README-listed agents that may be invoked
   ad hoc — but nothing in the repo depends on their output today, so deepening them should not
   block or gate the higher-value 3.

## Consequences

- The scc-ncs.9 scope-boundary lines remain in place, unchanged, in all 5 files — they are
  orthogonal to depth and still correctly resolve trigger-overlap confusion regardless of how
  deep each agent's internal workflow eventually becomes.
- Follow-up work (separate from scc-ncs.27, not required by its acceptance criteria): file a new
  beads task to deepen `system-architect.md`, `frontend-architect.md`, `backend-architect.md` to
  `api-debugger.md`-level depth first — a numbered internal workflow with concrete checklists/
  templates aligned to the output files `feature-builder` already expects
  (`system-arch.md`/`frontend-arch.md`/`backend-arch.md`) — then bring
  `requirements-analyst.md` and `refactoring-expert.md` to the same bar at lower priority.
- No implementation (deepening, folding, or orchestrator-building) is performed as part of this
  decision — this ADR records the decision only, per scc-ncs.27's acceptance criteria.
