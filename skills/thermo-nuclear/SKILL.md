---
name: thermo-nuclear
description: >-
  Use when a diff, branch, or PR shows structural bloat: oversized files, spaghetti
  branching, ad-hoc conditionals, or code that works but leaves the codebase messier
  than before — cases worth an ambitious rewrite rather than a patch. Applies a
  zero-mercy structural-simplification doctrine grounded in Cursor's
  thermo-nuclear-code-quality-review skill (cursor-team-kit). Biases toward ambitious
  rewrites over preserving imperfect-but-working code, and blocks on structural
  regressions that review-panel and adversarial-reviewer would let pass. Also
  runnable directly via /scott-cc:thermo-nuclear for an explicit standalone pass. Not
  for security/hostile-input review (use adversarial-reviewer) or multi-lens
  consensus review (use review-panel).
license: MIT
metadata:
  category: technique
  triggers: [code-review, structural-review, simplification, thermo-nuclear]
---

# Thermo-Nuclear Code Quality Review

This skill applies one doctrine only: **delete complexity, do not rearrange it.** It is
grounded in Cursor's `thermo-nuclear-code-quality-review` skill from `cursor-team-kit`,
fetched from `https://github.com/cursor/plugins/blob/main/cursor-team-kit/skills/thermo-nuclear-code-quality-review/SKILL.md`.
It treats "the code works" as necessary but not sufficient for approval.

## How This Differs From review-panel and adversarial-reviewer

- **review-panel** casts multiple reviewer lenses, seeks convergence, and approves once
  findings are fixed and re-reviewed clean. It is consensus-seeking.
- **adversarial-reviewer** red-teams for bugs, security holes, and hostile/malformed
  input handling. It is attack-seeking.
- **thermo-nuclear** applies a single structural doctrine and is biased *against*
  approval by default. It will recommend rejecting or rewriting code that both of the
  above would pass, because "no bugs and no security holes" is not the same question as
  "does this leave the codebase simpler than it found it."

Use thermo-nuclear when you specifically want the structural-only, zero-mercy lens — not
as a replacement for the other two. This skill can be invoked automatically by the model,
or by another orchestrating skill or agent (e.g. review-panel), whenever a diff shows
structural bloat or a missed simplification opportunity — it is not limited to explicit
invocation via its slash command, though that remains available for a standalone pass.

## Core Doctrine (7 non-negotiable criteria)

1. **Structural ambition** — Push hard for reframing changes so that whole branches,
   helpers, modes, conditionals, or layers disappear entirely. A fix that only moves code
   around without reducing branch count, conditional count, or indirection is not a fix.
2. **File-size boundaries** — Flag any file the PR pushes past 1,000 lines as a
   code-quality smell requiring decomposition first, before any other feedback.
3. **Spaghetti prevention** — Treat new ad-hoc conditionals or scattered special cases as
   design problems, not stylistic nits. They do not get a "Nit:" softening.
4. **Design over function** — Refuse to rubber-stamp implementations that work but leave
   the codebase messier than before. Passing tests measures behavior, not design.
5. **Direct code preference** — Reject brittle, magical, or overly generic mechanisms in
   favor of boring, direct, maintainable approaches.
6. **Type and boundary clarity** — Question unnecessary optionality, casts, or
   loosely-shaped objects that obscure invariants.
7. **Canonical logic placement** — Prevent feature-specific logic from leaking into
   shared paths; enforce reuse of existing utilities instead of parallel one-offs.

## Approval Bar

Approval requires **all** of the following. Treat each as a presumptive blocker unless
the author explicitly and specifically justifies the exception in the CL description:

- No structural regression versus the pre-change design.
- No obvious missed simplification opportunity (an entire branch/helper/mode/layer that
  could have been deleted instead of extended).
- No unjustified growth of any file past the 1,000-line boundary.
- No increase in spaghetti-branching (ad-hoc conditionals, scattered special-casing).

## Review Process

1. **Resolve the target** — a `base..head` range, branch, PR, or (if none given) the
   current working-tree diff against `HEAD`.
2. **Read full touched files, not just diff hunks.** Structural problems live in the
   surrounding context a hunk-only view hides.
3. **Walk all 7 doctrine criteria** against the change, one at a time.
4. For every candidate finding, ask: *does this delete complexity, or just rearrange
   it?* Discard rearrangement-only observations as noise.
5. **Categorize each surviving finding as BLOCKING.** This skill does not have a "Nit:"
   tier — if it violates one of the 7 criteria, it blocks approval until addressed or the
   author justifies the exception explicitly.
6. **Produce the report**: doctrine violations found (mapped to the numbered criterion),
   at least one named ambitious restructuring recommendation (not a patch), and an
   explicit approve/block verdict against the Approval Bar.

## What NOT to Do

1. **Don't rubber-stamp because tests pass** — tests verify behavior, not design health.
2. **Don't accept "we'll clean it up later"** — later rarely comes; block now or get an
   explicit, written justification in the CL description.
3. **Don't soften structural findings into optional nits** — every one of the 7 criteria
   is blocking by default under this doctrine.
4. **Don't propose the smallest patch that satisfies CI** — always name the more
   ambitious version: the branch, mode, or layer that could be deleted outright.

## When to Use

- Runnable directly via `/scott-cc:thermo-nuclear`, or automatically by the model or an
  orchestrating skill/agent (e.g. review-panel) when a diff's structural surface area
  warrants this lens.
- Best for legacy files, load-bearing modules with a history of accreted complexity, or
  when the author explicitly wants an unflinching structural pass.
- Not the right first pass for a small, isolated bug fix with no structural surface area
  — use `review-panel` or `adversarial-reviewer` for that instead.

## Limitations

- Structural lens only. It does not check for security holes, hostile-input handling, or
  business-logic correctness — use `adversarial-reviewer` or `review-panel` for those.
- It will recommend rewrites that may not fit sprint or velocity constraints. Weighing
  that business trade-off is the user's job, not this skill's.
- Grounded in a fetch of Cursor's `thermo-nuclear-code-quality-review` skill taken on
  2026-07-31. If Cursor's upstream skill changes, this skill will drift until re-synced.
- Stop and ask for clarification if the diff, PR, or branch target cannot be resolved
  unambiguously.
