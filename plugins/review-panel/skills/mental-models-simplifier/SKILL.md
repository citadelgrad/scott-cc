---
name: mental-models-simplifier
description: "Use when a diff is primarily a performance optimization, introduces\
  \ a new abstraction/layer/pattern, or touches code already known to be complex.\
  \ Questions whether this is even the right problem/approach using mental models\
  \ (Occam's Razor, First Principles, Diminishing Returns, etc.) \u2014 conceptual,\
  \ not mechanical. Not for mechanical delete/simplify passes (use ponytail-review)\
  \ or structural quality (use design-review)."
argument-hint: '[file, PR, diff, or design doc to question]'
allowed-tools: Read, Grep, Glob
metadata:
  category: pattern
  triggers:
  - simplification
  - complexity-reduction
  - code-review
---
