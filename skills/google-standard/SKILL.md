---
name: google-standard
description: >-
  Use only when explicitly invoked via /scott-cc:google-standard. Applies Google's
  published "Standard of Code Review" to a diff, branch, or PR, grounded in a fresh fetch
  of https://google.github.io/eng-practices/review/reviewer/standard.html. Favors
  approving a change once it definitely improves overall code health, even if
  imperfect — the deliberate opposite pole from thermo-nuclear's zero-mercy doctrine, and
  a pragmatic, mentoring-oriented alternative to review-panel and adversarial-reviewer.
license: MIT
disable-model-invocation: true
metadata:
  category: technique
  triggers: [code-review, code-health, google-standard, mentoring]
---

# Google Standard of Code Review

This skill applies Google's own published reviewer standard, not a paraphrase of a
paraphrase. Source: `https://google.github.io/eng-practices/review/reviewer/standard.html`,
fetched 2026-07-31.

## How This Differs From review-panel, adversarial-reviewer, and thermo-nuclear

- **thermo-nuclear** is biased *against* approval by default and treats structural
  criteria as blocking with no "Nit:" tier. **google-standard** is the opposite pole: it
  is biased *toward* approval once the change clearly improves code health, even when
  imperfect, and it explicitly separates blocking comments from optional "Nit:" comments.
- **review-panel** seeks multi-lens consensus and loops fixes to convergence before
  approving. **google-standard** approves in a single pass once the code-health bar is
  met — it does not iterate to a zero-finding state, because "there is only better code,"
  not perfect code.
- **adversarial-reviewer** red-teams for bugs and security holes. **google-standard**
  also weighs mentoring value and codebase consistency, which adversarial-reviewer does
  not address.

Use google-standard when you want a pragmatic, ship-oriented review that will not block
progress over polish — the reviewer-standard equivalent of "don't let perfect be the
enemy of good."

## Core Principle

> "In general, reviewers should favor approving a CL once it is in a state where it
> definitely improves the overall code health of the system being worked on, even if the
> CL isn't perfect."

There is no perfect code, only *better* code. Do not delay a change that improves
maintainability or readability over a minor polish item.

## Review Principles

- **Technical facts and data beat personal opinion.** A finding must be justified by an
  engineering reason, not a stylistic preference.
- **The project's style guide is the absolute authority on stylistic matters.** Do not
  invent style rules the guide does not state; do not relitigate settled style-guide
  rules in review.
- **Software design decisions must rest on engineering principles**, not individual
  taste.
- **Consistency with the existing codebase is an acceptable justification** when no
  other guideline applies.
- **Never approve a change that clearly worsens overall code health**, except in a true
  emergency (see `https://google.github.io/eng-practices/review/emergencies.html` for
  Google's separate emergency-fix process — this skill does not relax the bar itself; it
  only recognizes that a documented emergency process is the sole valid exception).

## The "Nit:" Convention

Prefix trivial, optional, or educational comments with `Nit:` so the author knows they
are not blocking. A `Nit:` comment should never be the stated reason a change is not
approved. Reserve non-prefixed comments for genuine blockers under the Core Principle.

## Mentoring Function

Code review is also how engineers learn language features, framework idioms, and design
principles from more experienced reviewers. Non-critical educational comments belong
under the `Nit:` convention so they teach without blocking.

## Conflict Resolution

When the author and reviewer disagree:

1. Try to reach consensus through discussion in the review comments.
2. If discussion stalls, move to a face-to-face or video conversation, then record the
   conclusion back in a review comment for the record.
3. If still unresolved, escalate to a tech lead or manager rather than letting the change
   stall indefinitely.

## Review Process

1. **Resolve the target** — a `base..head` range, branch, PR, or (if none given) the
   current working-tree diff against `HEAD`.
2. Evaluate the change against the Core Principle: does it definitely improve overall
   code health versus the current state, even if imperfect?
3. Check each finding against the Review Principles above before raising it — is it a
   technical fact, a style-guide rule, or a design principle? Discard pure-preference
   comments that don't map to one of these.
4. Categorize every finding as **blocking** (would leave code health worse, or violates
   the style guide / an engineering principle) or **Nit:** (optional, stylistic, or
   educational).
5. If a disagreement pattern emerges in your own findings (contradictory guidance),
   apply the Conflict Resolution steps in miniature: state the technical fact that
   resolves it, and note it in the report rather than leaving it open.
6. Produce the report: blocking findings, `Nit:` findings, and an explicit
   approve/request-changes verdict tied to the Core Principle.

## What NOT to Do

1. **Don't block on polish** — if the change clearly improves code health, approve it and
   raise polish items as `Nit:`.
2. **Don't raise a finding without a technical or style-guide justification** — personal
   preference alone is not a valid blocking reason.
3. **Don't demand perfection** — there is no perfect CL, only a better one; comparing
   against an idealized rewrite is not a valid basis for blocking.
4. **Don't invoke "emergency" reasoning yourself** — only recognize it if the author has
   invoked Google's actual documented emergency process; this skill never grants that
   exception unilaterally.

## When to Use

- Only via `/scott-cc:google-standard` — this skill sets `disable-model-invocation: true`
  and never fires from automatic keyword matching.
- Best when review velocity matters and the goal is "does this leave the codebase
  better," not "is this the ideal implementation."
- Pair with `thermo-nuclear` when you want both poles represented: one review biased
  toward shipping incremental improvement, one biased toward maximal structural cleanup.

## Limitations

- This skill implements the *standard* page only (what bar to hold a review to). It does
  not implement Google's separate "what to look for in a review" checklist page or the
  emergencies process page — those are different documents at different URLs.
- Grounded in a fetch of
  `https://google.github.io/eng-practices/review/reviewer/standard.html` taken on
  2026-07-31. If Google revises that page, this skill will drift until re-synced.
- Does not check security holes or hostile-input handling — use `adversarial-reviewer`
  for that.
- Stop and ask for clarification if the diff, PR, or branch target cannot be resolved
  unambiguously.
