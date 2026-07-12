# Design Lineage

This orchestrator is authored from scratch for this plugin — no file from any upstream source is
copied or adapted here. This section documents where its *design* comes from, distinguishing
**ported-by-authorship** (an idea re-expressed in original prose/procedure, source stays
uninstalled) from **vendored-as-files** (source text copied verbatim into this plugin, tracked in
`CREDITS.md`). Nothing in this file or in `SKILL.md`/the other `references/` files is vendored;
`CREDITS.md` is intentionally not touched by this skill's authorship.

## From compound-engineering's `/ce:review` — ported by authorship, not vendored

Per plan decision Q8, compound-engineering **stays installed** as a plugin in this ecosystem; it
was never vendored into `review-panel`, and this orchestrator does not read, copy, or depend on
any of its files existing. What's ported here is the *orchestration design* compound-engineering's
`/ce:review` pioneered, re-expressed independently in this skill's own words and mechanisms:

- **Judgment-based casting against diff content, not keyword/path matching** — CAST (see
  [cast-and-spawn.md](cast-and-spawn.md)) reads the packaged diff's actual content before matching
  it against `persona-catalog.md`'s cast-when criteria, exactly as `/ce:review` reads diff content
  rather than pattern-matching file extensions to decide which personas to cast.
- **Confidence-anchor scoring** — MERGE's five fixed anchors (0/25/50/75/100, see
  [merge-and-validate.md](merge-and-validate.md)) are this orchestrator's own re-derivation of the
  anchored-confidence-scale idea, with its own concrete rules for what pushes a finding to each
  level (quote-the-line evidence gate, 2+ independent agreement) — not copied thresholds or
  copied prose from any compound-engineering file.
- **An independent validation pass with no self-grading** — VALIDATE's rule that a finding's
  validator can never be the seat that originally found it is this orchestrator's own
  implementation of the same no-self-grading principle `/ce:review` established.
- **A JSON `mode:agent` machine contract** — [dual-mode-contract.md](dual-mode-contract.md)'s JSON
  shape is authored fresh for this plugin's specific finding schema
  (`contracts/reviewer-output.md`) and this plugin's specific stage names and circuit-breaker
  semantics; it is not compound-engineering's JSON schema copied or adapted field-by-field.
- **Model tiering** — the top-tier/mid-tier split this orchestrator reads from
  `persona-catalog.md` (itself already authored from scratch, informed by the same
  compound-engineering casting philosophy per its own header note) mirrors `/ce:review`'s general
  practice of reserving stronger models for adversarial/correctness-critical judgment.
- **An optional cross-model adversarial pass** — noted as a design idea informing this plugin's
  approach (a genuinely different model family reviewing the same diff is a stronger independence
  signal than a same-model second pass); this orchestrator's Fresh-Eyes and VALIDATE mechanisms
  are where that independence need is actually served today, using `Task`-dispatched subagents
  rather than a specific cross-model integration, since this plugin's air-gapped constraint (see
  the plan's §2 Hard Constraints) means it cannot assume a second model provider is reachable at
  runtime. A future enhancement could wire an actual cross-model dispatch into VALIDATE's
  validator selection when the runtime environment supports it; this orchestrator's VALIDATE stage
  is written so that swapping "a fresh same-model subagent" for "a fresh different-model subagent"
  is a runtime configuration choice, not a redesign.

## From clairvoyance's `workflow-builder.md` — lifted by re-expression, not by file copy

`plugins/review-panel/skills/design-review/references/workflow-builder.md` is a **vendored file**
(verbatim, MIT-licensed, attributed in `CREDITS.md`) that documents how to turn `design-review`'s
five-phase funnel into a Dynamic Workflow script. This orchestrator does not copy that file's text.
It re-expresses two of that file's load-bearing rules, in this orchestrator's own words, adapted to
this orchestrator's own 7-stage shape rather than `design-review`'s 5-phase funnel:

- **Pipeline-not-barrier** — `workflow-builder.md` states it (for `design-review`'s funnel) as: use
  a pipeline over targets, not a `parallel()` triage pass followed by a separate `parallel()`
  deep-dive pass; a file that triages clean should exit immediately, a barrier is justified in
  exactly one place (before final synthesis). This orchestrator's own re-expression, applied to
  panel seats and loop stages instead of files and funnel phases, lives in full in
  [converge-and-pipeline.md](converge-and-pipeline.md)'s "Pipeline-Not-Barrier" section: seats that
  finish clean feed MERGE immediately rather than waiting on the slowest seat in their batch, and
  the one hard barrier is CONVERGE's decision, which — like `design-review`'s final synthesis —
  genuinely needs the complete picture across all seats and both RE-REVIEW axes.
- **Adversarial verification / majority-survives-challenge** — `workflow-builder.md` states it as:
  spawn 2-3 independent agents per candidate finding, each arguing it's *not* real, and keep a
  finding only if a majority survive the challenge, because design-quality findings are contextual
  judgment calls rather than binary compile errors. This orchestrator's own re-expression is
  VALIDATE's validator mechanism (see [merge-and-validate.md](merge-and-validate.md)): every
  surviving finding gets at least one independent, clean-room validator explicitly tasked with
  trying to refute it before confirming it, and Critical-severity findings escalate to 2-3
  validators with an explicit majority-survives rule — the same underlying principle, scaled down
  to 1 validator for the common case (this orchestrator's findings include concrete correctness
  bugs as well as contextual design judgment calls, so a single independent check is often
  sufficient where `design-review`'s pure design-smell findings warranted 2-3 every time) and
  scaled up to match `workflow-builder.md`'s own 2-3 recommendation specifically where the
  contextual-judgment risk is highest.
- **Coverage honesty** — `workflow-builder.md`'s "Scale and Cost" section states it as: if a run
  bounds coverage in any way, say what it skipped and why. This orchestrator applies the same
  principle throughout (see SKILL.md's "Coverage honesty" section and every stage's own
  coverage-gap handling) as an explicit, repeated rule rather than a one-time note.

## What is NOT ported or lifted

- No compound-engineering file, prompt text, or persona definition is read, copied, or required to
  exist at runtime by this orchestrator. If compound-engineering is uninstalled, this orchestrator
  still functions fully — it only loses whatever supplementary seats live-scan would have found
  among its personas (see [cast-and-spawn.md](cast-and-spawn.md) Step 4), which is by design an
  additive, not load-bearing, enrichment layer.
- No text from `skills/design-review/references/workflow-builder.md` is copied into this
  orchestrator's files. That file remains a vendored artifact in its own location, credited in
  `CREDITS.md` under clairvoyance's attribution section; this orchestrator's references to it are
  citations to a re-expressed idea, not excerpts.
- This file does not modify, and is not a substitute for, `CREDITS.md` — `CREDITS.md` records
  vendored files with preserved license headers; this orchestrator has none to add there, since
  everything in `skills/review-panel/` is original authorship.
