# Current Task: scc-5hy

## Phase 4 — variant-explorer plugin (parallel blind-builder exploration)

### Task ID
scc-5hy

### Status
in_progress (started 2026-07-18)

### Priority
P2

### Summary
New standalone plugin `plugins/variant-explorer/` that spawns N blind builders in isolated git worktrees against a spec + acceptance criteria, then judges the results against AC, TASTE.md, and simplicity, producing a ranked shortlist for the human to pick from.

### Description
New standalone plugin `plugins/variant-explorer/` (resolved OQ2: standalone, not co-located in review-panel) that spawns N blind builders in isolated git worktrees against a spec + acceptance criteria, then judges the results against AC, TASTE.md, and simplicity, producing a ranked shortlist for the human to pick from. Depends on review-panel to score its shortlist against TASTE.md; review-panel itself stays scoped to judgment-only tooling.

### Design Details

New skill: `plugins/variant-explorer/skills/explore-variants/SKILL.md`.

**Procedure:**

1. **Input:** a design question or feature spec + acceptance criteria (generate via the acceptance-criteria skill if absent) + N (default 3, cap 6).
2. **Spawn N blind builders** — clean-room-alternative dispatch pattern, each in an isolated git worktree, each given the spec + AC only (no sibling output, no preferred approach), each with a distinct angle prompt (e.g., MVP-first, data-model-first, dependency-free).
3. **Judge panel:** independent judges score each variant against (a) the AC, (b) TASTE.md when present, (c) simplicity (reuse ponytail-review lens). Judges see all variants; builders never do.
4. **Output:** ranked shortlist with per-variant scorecard citing AC items and TASTE clauses; the human picks; losing worktrees are deleted after an explicit 'harvest ideas from runners-up?' prompt.

**Execution note:** local interactive runs dispatch via Task; Foundry/Reck runs map step 2 onto PAS tasks in containers (one task per variant). The skill documents both paths; v1 implements the local path, PAS mapping is a documented recipe only.

### Key Constraints

- Blocked on Phase 3 in full (3a-3d) per the spec's decompose plan: "4 is blocked on 3 (taste is the scoring function)"
- review-panel must never absorb the worktree-spawning/execution machinery — that stays in this standalone plugin, matching OQ2's resolution

### Acceptance Criteria

1. **AC1 — N=3 baseline:** A run with N=3 produces 3 worktrees, 3 scorecards, and a ranked shortlist; each scorecard cites >=1 AC item. PASS/FAIL: counts and citations present.

2. **AC2 — TASTE.md handling:** With TASTE.md present, at least the winning scorecard references taste clauses; without it, scorecards omit the taste axis and say so. PASS/FAIL: both modes.

3. **AC3 — Builder isolation:** no builder prompt contains another variant's content (verifiable from dispatch logs). PASS/FAIL: prompt inspection.

4. **AC4 — Error handling:** a builder that fails/times out is reported as a lost variant, run continues with survivors, never silently reduced N. PASS/FAIL: explicit note.

5. **AC5 — Boundary cases:** N=1 refuses with guidance to build directly; N>6 clamps with a note. PASS/FAIL: both behaviors.

### Dependencies (all satisfied)
- ✓ scc-cnx: Phase 3a — TASTE.md format
- ✓ scc-3x5: Phase 3b — grill-my-taste skill
- ✓ scc-4tt: Phase 3d — Taste seat (review stage)
- ✓ scc-da0: Phase 3c — Taste feedback loop (capture + --distill)

### Parent Epic
scc-hzj: Two-System Architecture — Security, Data Stewardship, Taste, Variants, and Triage Spine
