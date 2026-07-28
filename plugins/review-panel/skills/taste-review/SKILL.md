---
name: taste-review
description: Use when TASTE.md exists at the repo root and diffs need reviewing against
  the user's declared Preferences, Weightings, and Anti-preferences. Cites specific
  clauses violated and maps severity from declared strength. Never casts on TASTE.md
  absence; ignores Candidate rules. Not a substitute for universal-quality lenses
  (design-review, ponytail-review).
argument-hint: '[diff, file, or directory to review]'
allowed-tools: Read, Grep
metadata:
  category: discipline
  triggers:
  - taste
  - subjective-quality
  - code-review
---
