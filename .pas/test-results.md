# Test Results: scc-bqp — Phase 2c (data-steward seat)

## 0. What this covers

This is the "Run Tests" step for `scc-bqp`, which adds the new `data-steward`
review-panel seat (`plugins/review-panel/skills/data-steward/SKILL.md`) plus
its wiring into `persona-catalog.md`, `converge-and-pipeline.md`,
`dual-mode-contract.md`, and `fix-and-rereview.md` (the post-FIX sovereignty
guard and the new `escalated` terminal status).

Per `.pas/current_task.md`, five acceptance criteria must each be validated
independently:

| AC | What it tests |
|---|---|
| AC1 | Destructive migration → Critical finding naming a migration-safety principle |
| AC2 | Agent-boundary violation → sovereignty finding; pipeline ends `escalated`/sign-off; FIX doesn't touch the migration |
| AC3 | Fault injection (fixer touches a sovereignty file anyway) → post-FIX guard fails loudly, names the violation |
| AC4 | Non-data-layer diff → seat not cast |
| AC5 | No `DATA-MODEL.md` at all → seat still casts, emits sovereignty finding recommending `grill-the-schema` |

This plugin is markdown-prompt-driven with no executable test suite (confirmed:
no `package.json`, no test runner, no CI workflow in `plugins/review-panel/`).
Following the established `tests/PRESSURE-TEST.md` convention (and the prior
`scc-f9k` Run Tests step), validation combines:
1. **Live `Task` dispatches** for anything a single-turn subagent review can
   exercise (AC1, AC2, AC4, AC5 — all judgment calls the SKILL.md procedure
   makes over a diff).
2. **A hand-worked mechanical proof** for AC3, since the post-FIX sovereignty
   guard is a deterministic `git hash-object` check, not an LLM judgment call
   — the correct way to validate it is to run the actual mechanism, not to ask
   an agent to role-play it.
3. **A hand-worked walkthrough** connecting AC2's pipeline-level half (ends
   `escalated`, FIX doesn't touch the migration) to the same guard mechanism
   and to `converge-and-pipeline.md`'s new CONVERGE step 0, since exercising a
   full multi-round FIX→RE-REVIEW→CONVERGE loop live is out of scope for this
   step (matches the prior circuit-breaker precedent in `PRESSURE-TEST.md`).

**Verdict: PASS on all 5 acceptance criteria.** Details below.

## 1. Fixtures created

All new, none modify previously-committed fixtures (scope discipline: the
existing `orders-schema/schema.sql` and `DATA-MODEL.md` from `scc-f9k` were
left untouched).

### `plugins/review-panel/tests/fixtures/orders-schema/migrations/0002_drop_legacy_discount_code.sql` (AC1)
A destructive migration (`ALTER TABLE orders DROP COLUMN legacy_discount_code;`)
against the existing `orders-schema` fixture. A header comment establishes the
column holds live historical data for placed/cancelled orders (added by an
earlier migration not included in this fixture, so `schema.sql` itself is
untouched) — this is what makes the drop genuinely destructive rather than
dropping obviously-dead data.

### `plugins/review-panel/tests/fixtures/orders-schema/app/line_items_repo.{before,after}.ts` + `diff.patch` (AC2)
A small repository module. The "after" state adds `updateLineItem()`, issuing
an unconditional `UPDATE line_items SET quantity = ..., unit_price_cents = ...
WHERE id = $1` with no join to or check of `orders.state` — a direct violation
of the existing `DATA-MODEL.md`'s Agent-boundary entry: "Do not add an
`UPDATE` path to `line_items` for orders whose parent `orders.state` is
`placed` or later." `diff.patch` generated via `diff -u before after` and
verified.

### `plugins/review-panel/tests/fixtures/no-data-model-inventory/` (AC5)
A self-contained `schema.sql` + `migrations/0001_add_reserved_quantity.sql`
(warehouse inventory) with **no `DATA-MODEL.md` anywhere in the fixture
tree** — verified absent. `README.md` documents the fixture's purpose (not
shown to the review dispatch, to avoid answer-key contamination).

### AC4 — no new fixture needed
Reused `plugins/review-panel/tests/fixtures/order-fulfillment/diff.patch`
(pre-existing) as-is: it touches only a `.ts` business-logic file (interface
rename, null-check, retry-loop change) with zero migration/ORM/schema/
serialization surface — already satisfies AC4's requirement without
duplicating fixture work.

## 2. Live dispatch results

Each dispatch was instructed to read only the diff/fixture files needed for
its own review (not `PRESSURE-TEST.md`, not `test-results.md`, and — for AC5
— not the fixture's own `README.md`), to preserve independent judgment per
the plugin's documented "avoid answer-key contamination" lesson.

### AC1 — destructive migration (task `a0a3b1f44970ee0ff`)
**PASS.** Cast on the migration file per the file-pattern trigger. Emitted:
- **Critical** — `migrations/0002_...sql:8` — **migration-safety:
  reversibility/down-path** — names the principle by exact checklist name,
  ties it to the header comment's stated historical-data claim, no rollback
  provided.
- **Important** — expand→migrate→contract sequencing — flags the migration as
  a bare contract step with no evidence of a prior expand/migrate phase.
- **Important**, `sovereignty: human-required` — DATA-MODEL.md coverage gap
  (the dropped column isn't listed in DATA-MODEL.md's Key fields), recommends
  `grill-the-schema` / a DATA-MODEL.md update before merge.
- Correctly marked lock-behavior, backfill, index-creation, nullable-then-
  tighten, and dual-write-window checklist items N/A with reasoning, instead
  of forcing findings where none applied.

Satisfies AC1's literal requirement: Critical finding, migration-safety
principle named explicitly (reversibility/down-path).

### AC2 — Agent-boundary violation (task `acb40af4430842dd8`)
**PASS (finding-generation half).** Cast on `line_items_repo` diff per the
DATA-MODEL.md ownership-table mapping. Emitted:
- **Critical**, `sovereignty: human-required` — quotes the exact
  Agent-boundary text being violated, correctly identifies the missing
  `orders.state` check, explicitly states "FIX must not auto-resolve this,
  it requires human sign-off per DATA-MODEL.md."
- **Important** — Ownership & routing mismatch (unscoped write outside the
  documented draft-state window / documented writer).
- Correctly scoped out all migration-safety-checklist items as N/A (this is
  application code, not a migration).

The pipeline-level half of AC2 (ends `escalated`, FIX doesn't modify the
migration) is not exercisable by a single-turn review dispatch — see §3
(hand-worked walkthrough) for that half.

### AC4 — non-data-layer diff (task `a7bda9040c493b0b6`)
**PASS.** Verdict: **NO** cast. The dispatch checked the diff against every
cast-when trigger (migration files, ORM/model definitions, schema files,
serialization formats, DATA-MODEL.md-mapped paths) and correctly found none
present — a TS interface rename used only as a function-parameter shape is
not an ORM/model definition or schema file. Also correctly reasoned that the
fail-closed rule doesn't apply here because there's no genuine ambiguity, only
an unambiguous absence of data-layer surface.

### AC5 — missing DATA-MODEL.md (task `a1fbc343b30aaa3df`)
**PASS.** Cast on the migration file per the file-pattern trigger (independent
of DATA-MODEL.md's existence). Confirmed DATA-MODEL.md absent across the full
fixture tree. Emitted:
- **Important**, `sovereignty: human-required` — missing-DATA-MODEL.md finding,
  explicitly recommends running `grill-the-schema`, correctly hedges that it
  cannot confirm whether that skill is installed in this session.
- **Important** — nullable-then-tighten (adds `NOT NULL DEFAULT 0` in one step
  against a table with existing rows).
- **Minor** × 2 — lock-behavior engine-assumption gap, missing down-path.
- No Critical findings (correctly reasoned: additive column with a safe
  static default is not itself destructive).

Satisfies AC5 precisely: seat still casts with no DATA-MODEL.md present, and
emits the sovereignty finding recommending `grill-the-schema`.

## 3. AC3 — mechanical proof of the post-FIX sovereignty guard

AC3 tests a deterministic mechanism (`fix-and-rereview.md`'s "Sovereignty
guard (post-FIX assertion)" — hash the sovereignty-marked finding's target
file before dispatching the fixer, re-hash after, halt loudly on mismatch),
not an LLM judgment call. Validated by directly executing the mechanism
against the AC2 fixture file, rather than asking an agent to simulate it:

```
$ TARGET=plugins/review-panel/tests/fixtures/orders-schema/app/line_items_repo.after.ts

# Step 1 — pre-FIX hash, captured before "dispatching the fixer"
$ git hash-object "$TARGET"
277c366726c55c76addf26051104f81a7fc5916f

# Step 2 — FAULT INJECTION: simulate the fixer's underlying model touching
# this file despite being told not to (appended a comment to the sovereignty
# file's target)

# Step 3 — post-FIX re-hash
$ git hash-object "$TARGET"
c100635a470d09191b2226efd2a9575d0f6a7f2f    # <- differs from step 1

# Step 4 — restore fixture to its clean pre-injection state, re-verify
$ git hash-object "$TARGET"
277c366726c55c76addf26051104f81a7fc5916f    # <- matches step 1 again
```

The hash mismatch between steps 1 and 3 confirms the guard's detection
condition fires exactly when it should: any byte-level change to a
sovereignty-marked finding's target file between pre- and post-FIX snapshots
is caught, regardless of what the change was (a full rewrite, a one-line
"fix," or — as injected here — an appended comment). Per
`fix-and-rereview.md`'s guard spec, this mismatch would cause the orchestrator
to halt the FIX/RE-REVIEW loop immediately and emit **`error`** status — a
status distinct from both `circuit_broken` (3-strikes non-convergence) and
`escalated` (sovereignty findings correctly left unresolved by design) —
naming the specific finding's fingerprint, the file:line, the violated
principle/Agent-boundary text, and the file whose hash changed. Step 4
restores the fixture to a clean state so the committed tree carries no
fault-injection artifact.

### AC2's pipeline-level half (hand-worked walkthrough)

Combining the AC2 live-dispatch finding (§2) with `converge-and-pipeline.md`'s
CONVERGE step 0 and the guard mechanism just proven:

1. SPAWN/MERGE produce the Critical `sovereignty: human-required` finding
   against `updateLineItem()` (confirmed live, §2).
2. FIX is instructed never to auto-resolve sovereignty-marked findings —
   correct behavior is to leave the finding unresolved rather than edit
   `line_items_repo.after.ts`. Because FIX takes no action here, there is
   nothing for the guard to trip: pre- and post-FIX hashes of the target file
   are identical (the "no mismatch" branch of the same mechanism validated in
   §3 — mismatch-on-touch and match-on-no-touch are the same check, just
   opposite outcomes).
3. CONVERGE's new step 0 (sovereignty check, run ahead of the clean/dirty
   call) finds an unresolved sovereignty finding still open, and — because
   sovereignty findings are explicitly excluded from the 3-strikes
   progress/circuit-breaker counting — this cannot be misclassified as
   `circuit_broken`. It resolves to the new terminal status **`escalated`**,
   with `convergence.escalation.sovereignty_finding_ids` naming this finding
   (mode:agent) or an explicit human sign-off request being surfaced
   (interactive mode), per `dual-mode-contract.md`.
4. Per `converge-and-pipeline.md`'s OQ4 resolution, `escalated` must map to a
   passing gate (exit 0) in `foundry.yaml` wiring — unattended automation is
   never blocked by a correctly-functioning sovereignty escalation, only
   surfaced loudly via the PR description/log.

This satisfies AC2's full requirement: ends `escalated` (agent mode) /
explicit sign-off request (interactive), and FIX does not modify the
migration/target file.

## 4. Linting / secrets

No executable test suite applies (markdown skill files + fixture `.sql`/`.ts`
files, no build step). `gitleaks detect --no-git` run independently against
all three new/modified fixture directories:

```
plugins/review-panel/tests/fixtures/orders-schema/app         — no leaks found
plugins/review-panel/tests/fixtures/orders-schema/migrations  — no leaks found
plugins/review-panel/tests/fixtures/no-data-model-inventory   — no leaks found
```

`git status --porcelain` on `plugins/review-panel/tests/` confirms only the
new fixture directories are untracked; no previously-committed fixture file
(`orders-schema/schema.sql`, `orders-schema/DATA-MODEL.md`,
`order-fulfillment/diff.patch`) was modified. The AC3 fault-injection edit to
`line_items_repo.after.ts` was restored and its hash re-verified to match the
pre-injection value (§3, step 4) — the fixture tree is clean.

## 5. Scope check

Files touched by this Run Tests step, all additive test artifacts:
- `plugins/review-panel/tests/fixtures/orders-schema/migrations/0002_drop_legacy_discount_code.sql` (new)
- `plugins/review-panel/tests/fixtures/orders-schema/app/line_items_repo.before.ts` (new)
- `plugins/review-panel/tests/fixtures/orders-schema/app/line_items_repo.after.ts` (new)
- `plugins/review-panel/tests/fixtures/orders-schema/app/diff.patch` (new)
- `plugins/review-panel/tests/fixtures/no-data-model-inventory/schema.sql` (new)
- `plugins/review-panel/tests/fixtures/no-data-model-inventory/migrations/0001_add_reserved_quantity.sql` (new)
- `plugins/review-panel/tests/fixtures/no-data-model-inventory/README.md` (new)
- `.pas/test-results.md` (this file)

No changes made to `SKILL.md`, `persona-catalog.md`,
`converge-and-pipeline.md`, `dual-mode-contract.md`, `fix-and-rereview.md`,
or any previously-committed fixture — this step only adds test fixtures and
this results file, per the "Run Tests" step's scope.

## Limits of this pressure test

- AC2 and AC3's pipeline-level behavior (the actual multi-round FIX→
  RE-REVIEW→CONVERGE loop reaching `escalated`, and the guard halting a live
  orchestrator run) is validated by hand-worked walkthrough + direct
  mechanism execution, not a full live orchestrator run — consistent with the
  established precedent (`PRESSURE-TEST.md`'s circuit-breaker scenario) that
  multi-round loops are out of scope to run live in this step. The individual
  pieces (finding generation, hash-based detection, CONVERGE's documented
  decision rule) are each independently verified; their composition is
  reasoned through rather than executed end-to-end.
- Live dispatches are single-turn subagent reviews applying the SKILL.md
  procedure, not the full review-panel orchestrator (CAST→SPAWN→MERGE→
  VALIDATE), so MERGE-stage fingerprinting/deduplication behavior for the
  sovereignty marker (OR'd across contributing seats) is not exercised here —
  it was already read and confirmed structurally correct in
  `merge-and-validate.md` during investigation, not re-tested live.

## Summary

| AC | Check | Result |
|---|---|---|
| AC1 | Destructive migration → Critical finding, migration-safety principle named | PASS |
| AC2 | Agent-boundary violation → sovereignty finding (live) | PASS |
| AC2 | ...ends `escalated`/sign-off; FIX doesn't touch migration (walkthrough) | PASS |
| AC3 | Fault injection → guard detects mismatch, would halt with `error` status | PASS |
| AC4 | Non-data-layer diff → seat not cast | PASS |
| AC5 | No DATA-MODEL.md → seat still casts, sovereignty finding recommends `grill-the-schema` | PASS |
| Gitleaks | No leaks in any new fixture | PASS |
| Scope discipline | No non-test files touched; fixture tree left clean | PASS |

**All 5 acceptance criteria met.** No fixes required before Close Task.
