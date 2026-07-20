# Two-System Architecture — PRD

**Status:** All decisions recorded (2026-07-17) — ready to decompose to beads (`pas decompose` / beads-epic-builder)
**Date:** 2026-07-16
**Owner:** Scott
**Pairs with:** [two-system-spec.md](./two-system-spec.md)

> This doc is the durable product-requirements artifact. It captures the *why* and *what*.
> The paired spec captures the *how*. Written so work can resume after a context
> compact/clear — read top-to-bottom to reconstruct the full intent.

---

## 1. Vision

Software work in this toolchain is not one system. It is **two systems with different
triggers and different loop shapes**, connected by **one shared review substrate**:

- **System 1 — Feature Development (generative).** Triggered by a product decision.
  Flows Plan ⟳ → Build → Review ⟳. Planning has its own loops (grilling, requirements,
  design-it-twice, acceptance criteria) that run *before* any code exists. The review
  panel is the review *stage* of this system — not the system itself.
- **System 2 — Operations / Triage (reactive).** Triggered by an external state change:
  a production error fired, a CVE dropped, a dependency published a new major, infra
  drifted. Flows detect → diagnose → fix → ship. Its members: **bug fix, system
  upgrades, IaC changes, library upgrades, security-advisory response.** This is not
  part of feature development and must not be architecturally tied to it.

**The shared review substrate:** both systems end in a diff, and every diff flows
through the review panel before it ships. The panel casts seats by *diff content*, so a
library-upgrade diff naturally pulls security/adversarial seats while a feature diff
pulls domain/taste seats — the panel never needs to know which system called it. The
relationship is a clean dependency (triage → panel), not coupling (triage ⟷ panel).

```
SYSTEM 1: Feature development (generative)
  Plan ⟳ (grill, requirements, design-twice, AC, security pass)
      → Build (PAS, via Reckoner)
      → Review = the panel ⟳ (incl. security seat)
                                                        │
SYSTEM 2: Operations / triage (reactive, Foundry-run)   │
  detect → diagnose → fix ──────────────────────────────┤
   bug fix · system upgrades · IaC · lib upgrades ·     │
   security advisories                                  ▼
                              ONE review substrate: review-panel
                              (interactive for humans, mode:agent for automation)
```

## 2. Placement in the stack

| Layer | Role | Which system runs there |
|---|---|---|
| **PAS** | Sole execution engine for AI tasks (DOT pipelines, budgets, checkpoints) | Build stage of System 1; fix stage of System 2 |
| **Reckoner** | Dev environment / factory setup wrapped around PAS (repos, containers, sync) | Provisioning for both |
| **Foundry** | Developer-local pipeline that runs gates and scheduled checks so the developer doesn't babysit | Panel gates for System 1; **home of System 2** (periodic triage checks) |

Foundry is the automation answer to "who invokes these loops when I'm not watching."
System 2 is *Foundry-resident by design*: its detectors run as scheduled Foundry checks,
and its fixes are PAS tasks whose diffs are gated by the panel in `mode:agent`.

## 3. Goals (what we are building)

Listed in priority order. Each maps to a phase in the spec.

1. **Security passes at the end of both stages of System 1.**
   A security review seat in the panel (review stage) and a lightweight
   plan-security pass (planning stage). Today the panel's persona catalog claims "no
   security-specific skill is vendored" while `security-suite` exists in this very
   repo — close that documented gap first. Security has not been a big focus to date;
   this makes it a standing pass without waiting for the comprehensive future suite (§5).
2. **Data-layer sovereignty ("data steward").**
   The agent may write application logic freely; the data layer requires human
   sign-off. A human-owned `DATA-MODEL.md` contract, a schema grilling session at plan
   time, a blocking data-steward seat at review time, and a mechanical guard (hook) on
   data-layer file edits. `DATA-MODEL.md` is a **shared contract honored by both
   systems** — a migration inside a System 2 upgrade must respect it too.
3. **Codified taste.**
   A personal `TASTE.md` built by elicitation through forced choices (taste is revealed
   by choices, not introspection), enforced as a panel seat, and grown by a feedback
   loop that captures every human override of agent output. Scoped to *personal*
   preference and weightings — universal quality is already codified (Ousterhout lens
   set, Karpathy guidelines).
4. **Parallel exploration ("variants").**
   Plan/build-side capability: spawn N independent blind attempts in isolated
   worktrees, judge against acceptance criteria *and* `TASTE.md`, present a ranked
   shortlist. This is the "embrace slop, filter with taste" pillar; its value is gated
   on goal 3 existing as the scoring function.
5. **The triage spine (System 2 v1).**
   One detect → diagnose → fix spine with pluggable detectors (prod errors, system
   upgrades, IaC drift, library upgrades, security advisories), run on Foundry
   schedules, filing beads, producing fix diffs that the panel gates unattended.

## 4. Non-goals (explicit)

- **Org-wide / enterprise triage system.** Desired eventually; in an enterprise
  setting triage tooling is org-level. Not a priority now — System 2 v1 is
  developer-local (Foundry).
- **Comprehensive security review process.** Future work, and it will live in
  **Foundry**, not in the panel (see §5). The near-term security passes (goal 1) are
  deliberately lightweight.
- **Merging the two systems.** Triage is not part of the SDLC feature process. It may
  share a repo/plugin *distribution* with review-panel, but no architectural tie beyond
  the review substrate dependency.
- **The panel owning planning.** Planning loops (grilling, requirements, variants)
  precede the panel and stay outside it.
- **A second review engine for ops diffs.** Rejected: two review engines drift apart
  and lose security coverage exactly where it matters (dependency bumps, IaC). Reuse
  the panel.

## 5. Future direction (recorded, not scheduled)

- **Comprehensive security suite in Foundry.** A full security review *process*
  (scheduled scanning, dependency/CVE watch, deep audits) as a Foundry pipeline —
  distinct from the per-diff security seat, which stays in the panel. The per-diff seat
  and plan-pass built in goal 1 should be designed so the future suite can subsume or
  invoke them without rework.
- **Org-wide triage.** System 2's spine should keep detector/spine separation clean so
  detectors can later feed an org-level system instead of (or in addition to) local
  Foundry.

## 6. Users

- **Primary:** Scott, solo developer running plan/build/review through PAS + Reckoner +
  Foundry, wanting unattended-by-default automation with human sovereignty over the
  data layer and taste.
- **Secondary (future):** teams/enterprise consuming the same plugins with org-level
  triage and security processes.

## 7. Success criteria (product level)

- A dependency-bump diff produced by triage gets a panel review that includes a
  security seat, with zero manual invocation (Foundry schedule → detector → fix →
  `mode:agent` panel gate).
- No agent-authored change to migrations/schema/models ships without either the
  data-steward seat passing it, explicit human sign-off, or — for unattended runs —
  an unmissable sovereignty flag surfaced in the PR description and final output
  (D10–D11). The guard hook makes silent data-layer edits impossible in interactive
  sessions; unattended enforcement is the review seat's job alone.
- A grilling session produces/updates `TASTE.md`, and a subsequent panel run
  demonstrably flags a taste violation a generic reviewer would not.
- A variants run returns a ranked shortlist where the ranking rationale cites AC and
  `TASTE.md` clauses, not generic quality prose.
- The panel remains fully usable standalone and interactive — none of the above may
  degrade the human `/review-panel` experience.

## 8. Decisions log

| # | Decision | Choice |
|---|---|---|
| D1 | One system or two? | **Two systems** (generative vs reactive), separate triggers and loops |
| D2 | How do ops diffs get reviewed? | **Reuse the panel as shared substrate** via `mode:agent`; no second review engine |
| D3 | Where does System 2 live? | **Foundry** (developer-local scheduled checks); org-wide later |
| D4 | Security in panel or ops? | **Both, split by activity**: per-diff review seat + plan pass now (panel/planning); comprehensive process later (Foundry) |
| D5 | Is triage tied to review-panel? | **No** — dependency (calls the substrate), never coupling; separate plugin |
| D6 | Where do planning-stage artifacts live? | With the existing planning skills (review-panel plugin hosts plan+review stage tooling; name notwithstanding) — see D9 below for the rename decision |
| D7 | Security-suite vendor or reference? | **Reference**; no vendoring — revisit only if an air-gapped deploy actually materializes |
| D8 | Variants co-located skill or standalone plugin? | **Standalone plugin** `plugins/variant-explorer/`; review-panel stays scoped to judgment-only tooling |
| D9 | Does review-panel get renamed? | **No** — re-describe scope only; revisit if the plan-stage skill count grows |
| D10 | Does Foundry's gate block unattended runs on `escalated`? | **No** — it must never block; instead it surfaces the flag unmissably in the PR description and the final `mode:agent` output |
| D11 | Does the data-layer guard hook (2d) enforce anything unattended? | **No** — interactive/planning-time convenience only; unattended sovereignty enforcement is entirely the data-steward review seat's job |
| D12 | Is sovereignty-marked blocking mechanically enforced, not just documented? | **Yes** — an explicit post-FIX assertion step fails the round loudly if a sovereignty-marked file changed anyway |
| D13 | Does Phase 5's build order depend on Phase 2? | **Yes** — added explicitly, alongside the existing dependency on Phase 1 |

## 9. Open questions for agreement

**Resolved 2026-07-17** — see Decisions log (D7–D13) above, and the spec's "Decisions on
open questions" and "Decisions from architecture review" sections for full rationale.
Ready to decompose.
