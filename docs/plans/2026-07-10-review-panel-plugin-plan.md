# Review-Panel Plugin — Design & Plan

**Status:** Design approved; domain-modeling resolved → **BUILD from scratch**; beads issues cut.
See `bd show scc-ns8` (Epic A) and `bd show scc-6lj` (Epic B stub) for live tracking — §10 below maps
issue numbers to beads IDs.
**Date:** 2026-07-10
**Owner:** Scott
**Location of build:** `plugins/review-panel/` inside `scott-cc`

> This doc is the durable artifact. It is written so work can resume after a context
> compact/clear. Read it top-to-bottom to reconstruct the full plan.

---

## 1. Vision

Build a **comprehensive, self-contained code-review verification system** as a single
Claude Code plugin. It is not "two skills" — it is a **review panel**: a diverse ensemble
of independent reviewers, cast per-change, run in parallel, whose findings are verified,
fixed, and re-reviewed against original intent, looping until a clean round.

The system is **hybrid (mode C)**: every skill is excellent to invoke by hand, AND the
orchestrator exposes a machine contract so it can run unattended as a `foundry` gate /
Reckoner `post-feature` hook. The goal is for this to "become just another system in my
automation process."

### The core insight (why a panel, not a loop)
Quality after writing code does not come from running one reviewer, nor from looping the
same 3 reviewers. It comes from **diversity of perspective** — multiple *independent*
reviewers, some task-specific, some given deliberately minimal context ("fresh eyes"), each
surfacing different bugs. Then: fix → re-review the fix AND the broader context against the
original decisions → converge. Combining reviewers into one skill would *reduce* the
perspective diversity that is the whole point.

---

## 2. Hard constraints

- **Air-gapped target.** The plugin must load on a coding-agent server with **no internet
  and no external packages**. Therefore: fully **self-contained**, pure **markdown + shell**,
  all teaching content written *into* skills (no runtime fetches, no external links as
  dependencies). Node scripts (e.g. adr-skill's `.js`) are copied but treated as **optional**
  with a manual markdown-template fallback, since node may be absent.
- **Self-contained after uninstall.** Scott will **uninstall clairvoyance, superpowers,
  ponytail, mattpocock** after vendoring the good parts. **compound-engineering stays
  installed.** So we cannot rely on those being present at runtime — anything the panel needs
  from them must be vendored now.
- **Vendoring is legal & clean.** All five source repos are **MIT**. Vendor verbatim with
  preserved license headers + a `CREDITS.md`. mattpocock's `domain-modeling` is the one thing
  we will NOT copy (see §6).
- **One plugin.** No benefit to splitting for this goal; a single loadable unit is the point.

---

## 3. Decisions log (answered questions)

| # | Decision | Choice |
|---|---|---|
| Q1 | End-state of the "concentric loops" | **C — hybrid**: excellent standalone skills + automatable orchestration |
| Q2 | Combine domain-modeling + adversarial-review? | **No.** Two skills + a shared artifact; merging kills perspective diversity |
| Q3 | Adversarial-reviewer scope | **Broad red-team**, standalone + pluggable (bugs, security, hostile input, AND challenge design findings) |
| Q4 | Persistence / ADRs | **Light `CONTEXT.md` decisions log**, WITH `adr-skill` vendored & callable for decisions that clear the 3-part gate |
| Q5 | Skill discovery / casting | **Hybrid**: curated `persona-catalog.md` (primary) + runtime live-scan of installed skills (secondary). Catalog is primary because sources get uninstalled |
| Q6 | Copying policy | **Vendor + attribute** (all MIT) |
| Q7 | Packaging | **One self-contained plugin**, `plugins/review-panel/` |
| Q8 | compound-engineering | **Keep installed** → cast its personas at runtime; port only its orchestration *design* (authored, not copied) |
| Q9 | domain-modeling source | **RESOLVED: BUILD from scratch.** Research confirmed nothing in the ecosystem is copy-worthy — every dedicated "domain-modeling/DDD" skill is OOP entities/aggregates/glossary (mattpocock's failure is systemic, not a one-off). Real type-driven content exists only as buried sections in general style guides. Cannibalize *code snippets only* from vibe-types (Apache-2.0) + 0xBigBoss (license TBD). See §6b |

---

## 4. Architecture

### Plugin layout
```
plugins/review-panel/
├── plugin.json
├── CREDITS.md                       # attribution: EveryInc, codybrom, obra, DietrichGebert, mattpocock (all MIT)
├── commands/
│   └── review-panel.md              # human entry (like /ce:review)
├── skills/
│   ├── review-panel/SKILL.md        # ★ NEW: the orchestrator (casting → ensemble → merge → validate → fix → re-review → converge)
│   ├── domain-modeling/SKILL.md     # ★ NEW: type-driven functional domain modeling (see §6)
│   ├── adversarial-reviewer/SKILL.md # ★ NEW: broad red-team, standalone + pluggable
│   └── <vendored clairvoyance lenses + others>  # see copy manifest §5
├── agents/
│   └── clean-room-alternative.md    # vendored: blind subagent → fresh-eyes seat + adversarial challenger
├── reviewers/
│   └── persona-catalog.md           # the manifest: seat roster + per-seat "cast when" + model tier
├── contracts/
│   └── reviewer-output.md           # shared JSON finding schema (from superpowers code-reviewer.md)
├── formats/
│   ├── CONTEXT-FORMAT.md            # vendored from mattpocock
│   └── ADR-FORMAT.md                # vendored from mattpocock
└── scripts/
    ├── review-package               # vendored (bash): one shared diff, N read-only reviewers
    └── workspace                    # vendored (bash): git-ignored scratch dir for findings
```

### The panel loop (orchestrator spine)
```
CAST        catalog judgment (read diff CONTENT, not just paths) + live-scan installed skills; FAIL-CLOSED
  ↓
SPAWN       diverse panel, bounded-parallel, model-tiered, all read-only on ONE shared diff
            seats: correctness/adversarial · simplicity(ponytail) · structural(clairvoyance design-review)
                   · security(if installed) · domain-intent(matches CONTEXT.md decisions?) · FRESH-EYES(blind)
  ↓
MERGE       fingerprint-dedupe (file+line±3+normalized title); confidence anchors 0/25/50/75/100;
            2+ independent agreers bump one anchor; quote-the-line evidence gate demotes uncited findings
  ↓
VALIDATE    independent second wave — one fresh validator per surviving finding (no self-grading)
  ↓
FIX         ONE fixer subagent gets the WHOLE findings list (not one fixer per finding)
  ↓
RE-REVIEW   the diff AND coherence-vs-intent (does the fixed code still match CONTEXT.md decisions?)
  ↓
CONVERGE    clean round → done. Else loop. 3 strikes (no progress) → CIRCUIT-BREAK, escalate to human.
```

Load-bearing rules lifted verbatim from clairvoyance `workflow-builder.md`:
- **Pipeline, not barrier**: a target that triages clean exits immediately; dirty targets move
  straight to deep-dive while others still triage. One barrier only — before final synthesis.
- **Adversarial verification**: "keep a finding only if a majority of 2–3 independent
  challengers cannot refute it." Design smells are contextual; unverified sweeps over-report.
- **Coverage honesty**: if the run bounds coverage, say what it skipped and why.

### Dual-mode (same orchestrator)
- **Human:** `/review-panel` command → readable markdown report + interactive apply loop.
- **Unattended:** `mode:agent` → single JSON blob; wired to a `foundry` `post-feature` gate.

### Casting (§ resolves Q5, informed by compound-engineering)
`/ce:review` casts from a `persona-catalog.md` via **LLM judgment against diff content**, not
keyword matching: a small always-on core + risk-triggered additions, **fail-closed** on
ambiguity, with **model tiering** (top-tier model for correctness/security/adversarial,
mid-tier for the rest) and an optional **cross-model** adversarial pass for independence.
Our catalog is primary (sources get uninstalled); live-scan of `~/.claude/skills` +
plugin skills is the secondary enrichment that picks up compound-engineering + anything else.

---

## 5. COPY MANIFEST (what gets vendored, verbatim unless noted)

Actions: **COPY** = vendor file ~verbatim + license header · **ADAPT** = author new, borrowing ·
**LIFT** = embed rule/pattern into orchestrator, no separate file · **CAST** = keep installed,
discover at runtime · **SKIP** = don't vendor.

### clairvoyance (MIT) — COPY the whole design-review system (only works as a set)
- **COPY** all 16 lens skills + their `references/`: design-review, red-flags, diagnose,
  complexity-recognition, abstraction-quality, deep-modules, module-boundaries,
  information-hiding, strategic-mindset, design-it-twice, error-design, naming-obviousness,
  general-vs-special, pull-complexity-down, code-evolution, comments-docs.
- **COPY** `agents/clean-room-alternative.md` (blind Opus subagent) → fresh-eyes seat + challenger.
- **LIFT** `workflow-builder.md` pipeline-not-barrier + majority-survives-challenge rules into orchestrator.

### superpowers (MIT) — COPY only the review bits
- **COPY** `requesting-code-review/code-reviewer.md` → `contracts/reviewer-output.md`
  (Strengths / Issues=Critical·Important·Minor w/ file:line / Ready-to-merge? Yes·No·With-fixes).
- **COPY** `scripts/review-package`, `scripts/sdd-workspace` (bash).
- **COPY** `verification-before-completion` → the panel's hard "clean" gate.
- **LIFT** 3-strikes circuit-breaker (systematic-debugging), "one fixer, whole findings list"
  (subagent-driven-development), fixer discipline (receiving-code-review) into prompts.
- **⚠️ OUT OF SCOPE:** superpowers' `brainstorming`, `writing-plans`, `executing-plans`, `tdd`,
  `using-git-worktrees` are NOT review artifacts. Do not put them in review-panel. Uninstalling
  superpowers wholesale kills them — that is a **separate consolidation decision** (see §8).

### ponytail (MIT) — COPY the two reviewers
- **COPY** `ponytail-review` (diff-scoped simplicity seat), `ponytail-audit` (repo-scoped).
- **SKIP** `ponytail-debt` (unless we adopt the `ponytail:` comment convention).
- **SKIP** base `ponytail` mode + hooks + statusline + MCP (generation-time persona, not a seat;
  uninstalling ponytail removes it — separate UX decision, see §8).

### mattpocock (MIT) — COPY formats, ADAPT the skill
- **COPY** `CONTEXT-FORMAT.md`, `ADR-FORMAT.md` → `formats/`.
- **ADAPT / DO NOT COPY** `domain-modeling/SKILL.md` — misnamed, zero type-driven content.
  We author our own (§6).
- **SKIP** code-review, codebase-design, grill-with-docs, writing-great-skills (overlap).

### compound-engineering (MIT) — KEEP installed, CAST not COPY
- **CAST** its 15 review personas at runtime (do not vendor).
- **Port (author) its orchestration design** into our orchestrator: judgment casting, confidence
  anchors, independent-validation pass, JSON `mode:agent`, model tiering, cross-model adversarial.
- **DEFER** `ce-dogfood` (live-browser QA) — a genuinely novel future seat; note, don't build now.

### local-only trial-copies (Scott confirmed these were trial copies from OSS plugins) — COPY
- **COPY** `adr-skill` (incl. its `.js` scripts; provide manual template fallback for no-node).
- **COPY** `improve-codebase-architecture` (codebase-wide refactor-finder seat; reads CONTEXT.md/ADR).
- **COPY** `grill-with-docs` (plan pressure-test against domain model) — evaluate necessity during build.
- **COPY** `tdd` (broadly useful; confirm not redundant with scott-cc's own).
- Record provenance/license header for each in CREDITS at copy time.

---

## 6. The three NEW authored skills

### 6a. `review-panel` (orchestrator) — the centerpiece
Implements the §4 loop. Casting + ensemble + merge/confidence + independent validation + fix
loop + re-review-vs-intent + convergence/circuit-break. Dual-mode. Reads `persona-catalog.md`,
emits the shared `reviewer-output.md` contract.

### 6b. `domain-modeling` — type-driven functional modeling  (RESOLVED: BUILD from scratch)

**Verdict (research complete).** Author from scratch, grounded directly in Wlaschin ("Domain
Modeling Made Functional"), Alexis King ("Parse, Don't Validate"), Minsky (illegal-states essay).
Nothing in the ecosystem is vendor-able whole — dedicated DDD skills are uniformly OOP
(entities/aggregates/repositories/glossary); real type-driven content only exists as buried
sections in general TS/Rust style guides. **Cannibalize code snippets only** (not structure):
- `vibe-types` (jpablo, **Apache-2.0** — permissive, attribute) — pull per-language patterns from its
  `T01-algebraic-data-types`, `T03-newtypes-opaque`, `T14-type-narrowing`, `T57-typestate` catalog
  entries; steal its **branded-type gotchas** (e.g. JSON round-trips silently erasing brands).
- `0xBigBoss/claude-code` `typescript-best-practices` (**license UNVERIFIED — no root LICENSE; must
  confirm before lifting any text**) — its "Make Illegal States Unrepresentable" TS section.
- `0xMassi/claude-skills` (MIT) — minor: steal only the `assertNever` exhaustiveness pattern.

**8 core techniques** (teaching order = dependency order, not table order):
1. ADTs: sum vs product (foundation vocabulary)
2. Make illegal states unrepresentable (the payoff/goal of #1)
3. Exhaustive matching (compiler enforces #2 stays true as model grows; `assertNever`/`assert_never`/native)
4. Parse, don't validate (move the boundary — runtime checks become type proofs)
5. Smart constructors / branded (newtype) primitives (mechanism that makes #4 concrete)
6. Errors as values — Result/Either (what a failed parse/step returns instead of throwing)
7. Custom error types (structure #6's channel as its own sum type — the ONE sanctioned "class")
8. Workflows as functions; state-machines-over-booleans (composes all above → worked example)

**File structure** (SKILL.md < 100 lines per write-a-skill convention; references one level deep):
```
domain-modeling/
├── SKILL.md            # teaching spine + trigger description + when-to-apply + workflow
├── TECHNIQUES.md       # the 8 techniques in full depth, TS/Python/Rust each inlined
├── WORKED-EXAMPLE.md   # order→payment→fulfillment, before/after, all 3 languages
├── RED-FLAGS.md        # the scan checklist (CLEAR/TRIGGERED/N/A, styled like clairvoyance red-flags)
└── CONTEXT-AND-ADR.md  # how this skill writes CONTEXT.md / emits ADRs
```

**Worked example** = order→payment→fulfillment. *Before:* one `Order` interface with
`isPaid`/`isRefunded`/`isShipped` booleans + optional `paymentId?`/`trackingNumber?` — can represent
"shipped without payment", "refunded AND cancelled", flag/data desync, all compiling fine. *After:* a
`status`-tagged union (`cart|placed|paid|fulfilled|cancelled|refunded`) where each variant carries only
its valid fields, and each workflow step is a pure `PrevState -> Result<NextState, StepError>` — so
`fulfill` literally cannot accept a `"cart"` order (doesn't type-check). Rust note: transitions consume
`self` by value so a stale state can't be reused.

**Red-flags checklist** (8): boolean-pair/flag-cluster fields · stringly-typed domain values ·
validation scattered past the boundary · non-exhaustive switch/match · primitive obsession (3+
same-typed params) · optional fields that should be a variant · exceptions for expected domain
failures · lifecycle-via-nullable-fields instead of a tagged union.

**Output contract = MARKDOWN, not JSON** (decisive: matches clairvoyance `red-flags`/`design-review`
CLEAR/TRIGGERED/N/A verdict vocab so the panel merges results with zero translation — nothing else in
this ecosystem emits JSON findings). `allowed-tools: Read, Grep` (read-only); input `$ARGUMENTS` =
target file/dir/domain; output = findings with location + principle-violated + candidate-fix.

**CONTEXT.md / ADR wiring** — reuse the vendored `grill-with-docs`/mattpocock schema *verbatim*, do
NOT invent a new one. CONTEXT.md stays a pure domain glossary (no code, no Result/branding mechanics),
written lazily/inline as terms resolve. ADR only when the 3-part gate clears (hard-to-reverse AND
surprising AND real trade-off): choosing an entity's state-machine shape clears it; picking Result over
exceptions for *one* function does NOT (that's style) — adopting it *project-wide* does.

**Buildability:** pure markdown, no runtime scripts warranted (no deterministic op to automate).
Style: FP, immutability, errors-as-values, avoid OOP except custom error types. TS + Python primary,
Rust noted (it's Rust's home turf). Verify against write-a-skill checklist before shipping.

### 6c. `adversarial-reviewer` — broad red-team, standalone + pluggable
Attacks existing code/PRs/designs for bugs, security holes, hostile inputs, AND challenges design
findings. Always available (not gated behind Dynamic Workflows). Uses the blind
`clean-room-alternative` subagent pattern for independence. Emits the shared finding contract.
The panel calls it as a core seat; also invokable alone.

---

## 7. Attribution plan (`CREDITS.md`)
Per-source section crediting: EveryInc/compound-engineering-plugin, codybrom/clairvoyance,
obra/superpowers, DietrichGebert/ponytail, mattpocock/skills — all MIT, © preserved. Note which
files were copied verbatim vs adapted. Preserve original license headers inside copied files.

**Snippet-source credits (domain-modeling, §6b):** jpablo/vibe-types (Apache-2.0 — retain NOTICE if
present) and, *only if its license verifies*, 0xBigBoss/claude-code. Credit ideas by name in prose:
Wlaschin, Alexis King, Minsky. These are cannibalized code patterns, not vendored files — credit them
as inspiration/snippet sources, distinct from the verbatim-vendored MIT plugins above.

---

## 8. Explicitly deferred / separate decisions
1. **superpowers workflow skills** (brainstorming/writing-plans/tdd/git-worktrees): if Scott wants
   these offline too, they need a *separate* vendored "workflow" plugin — NOT review-panel. Decide later.
2. **ponytail base mode** (lazy-dev persona + hooks): keeping or dropping is a UX choice independent
   of the panel. Panel only needs ponytail-review/audit.
3. **ce-dogfood** live-browser QA seat: future addition.
4. **Epic B — skill catalog/audit meta-project**: the cross-skill "where are the holes / evaluate a
   new external skill" workflow. Same catalog viewed as a maintenance problem; it keeps casting good
   over time. Stub now, build later.

---

## 9. Open items before/within build
- [x] **domain-modeling copy-vs-build** — RESOLVED: build from scratch; blueprint folded into §6b.
- [ ] **Verify `0xBigBoss/claude-code` license** before lifting any of its text (no root LICENSE found). vibe-types is Apache-2.0 (clear); attribute both snippet sources in CREDITS.
- [ ] Confirm node availability on the air-gapped target (affects adr-skill scripts vs manual fallback).
- [ ] Read each local-only trial-copy for a license header when copying (adr-skill, improve-codebase-architecture, grill-with-docs, tdd).
- [ ] Final `persona-catalog.md` seat roster + per-seat model tier.
- [x] Beads workspace fixed: this repo's `bd init` had never set `issue-prefix` (db existed but empty, 0 issues across 3 export snapshots). Reinitialized via `bd init --reinit-local --prefix scc` after verifying zero data risk. Prefix is `scc`.

---

## 10. Plan decomposition → beads

**Status: CUT.** All 16 issues created (`bd lint` clean, dependency graph verified — only the
scaffold task is in the ready queue, everything else correctly blocked). Beads prefix for this
repo is `scc` (repo's `bd init` was missing its issue-prefix config; fixed via `bd init
--reinit-local --prefix scc` — database was empty, zero data risk, verified via `bd stats` +
export-safety check before touching it).

### Epic A — Build the review-panel plugin  → `scc-ns8`
Each issue below got testable acceptance criteria via the `acceptance-criteria` skill at creation
time (rules/checklist format — these are engineering build tasks, not user stories).

1. `scc-ns8.1` **Scaffold** `plugins/review-panel/` (plugin.json, dir tree, CREDITS.md skeleton, license-header policy). *(dep: none — unblocks everything)*
2. `scc-ns8.2` **Vendor clairvoyance set** (16 lenses + references + clean-room-alternative agent) w/ headers. *(dep: 1)*
3. `scc-ns8.3` **Vendor superpowers review bits** (reviewer-output contract, review-package + workspace scripts, verification-before-completion). *(dep: 1)*
4. `scc-ns8.4` **Vendor ponytail** (ponytail-review, ponytail-audit). *(dep: 1)*
5. `scc-ns8.5` **Vendor mattpocock formats** (CONTEXT-FORMAT.md, ADR-FORMAT.md). *(dep: 1)*
6. `scc-ns8.6` **Vendor local-only trial-copies** (adr-skill + scripts + manual fallback, improve-codebase-architecture, grill-with-docs, tdd) w/ provenance. *(dep: 1)*
7. `scc-ns8.7` **Author `domain-modeling` skill** (from §6b blueprint — 5 files, 8 techniques, order→payment→fulfillment worked example, markdown findings contract; cannibalize vibe-types/0xBigBoss snippets w/ attribution). *(dep: 5, 6)*
8. `scc-ns8.8` **Author `adversarial-reviewer` skill** (broad red-team, uses clean-room-alternative). *(dep: 2, 3)*
9. `scc-ns8.9` **Author `persona-catalog.md`** (seat roster, cast-when criteria, model tier). *(dep: 2, 3, 4, 7, 8)*
10. `scc-ns8.10` **Author `review-panel` orchestrator** (casting + pipeline + merge/confidence + validation + fix loop + re-review + converge/circuit-break; ports compound-engineering design). *(dep: 9)*
11. `scc-ns8.11` **Discovery mechanism** (catalog primary + live-scan of installed skills). *(dep: 10)*
12. `scc-ns8.12` **Dual entry** (`/review-panel` command + `mode:agent` JSON + `foundry` post-feature integration). *(dep: 10)*
13. `scc-ns8.13` **CONTEXT.md/ADR wiring** (domain-modeling writes log; adr-skill callable; no-node fallback). *(dep: 6, 7)*
14. `scc-ns8.14` **Pressure-test harness** (run the panel on a known-buggy diff — superpowers "TDD-for-skills": baseline fails without panel, passes with; verify circuit-breaker + coverage-honesty). *(dep: 10, 11, 12)*

### Epic B — Skill catalog / audit (STUB)  → `scc-6lj`
Cross-skill hole-finding + new-external-skill evaluation workflow that maintains the catalog.
Created as a stubbed epic (P3, no children yet) per plan §8.4 — do not build yet.
