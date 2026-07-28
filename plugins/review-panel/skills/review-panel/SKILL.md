---
name: review-panel
description: "Use when a diff, PR, or branch needs a comprehensive verification pass\
  \ before merge, when invoked as an automated foundry/CI gate (mode:agent), or when\
  \ the user asks for a \"review panel\" or \"full review.\" Orchestrates a multi-reviewer\
  \ code-review panel \u2014 casts diverse reviewer seats, runs concurrently, merges\
  \ and deduplicates findings, validates, fixes, and loops to convergence. Not for\
  \ single-lens checks (invoke that reviewer directly) or generating alternative designs\
  \ (use design-it-twice). deduplicates their findings with confidence scoring, independently\
  \ validates each surviving finding, fixes everything in one pass, re-reviews for\
  \ regressions and domain-intent coherence, and loops to convergence or a circuit-break"
argument-hint: '[diff, PR, branch, or base..head range to review; --lite, --medium,
  or --auto to narrow the review tier; --mode=agent for machine output]'
allowed-tools: Task, Read, Grep, Glob, Bash
metadata:
  category: technique
  triggers:
  - code-review
  - multi-lens-review
  - quality-assurance
---
