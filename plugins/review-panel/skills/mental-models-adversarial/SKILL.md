---
name: mental-models-adversarial
description: Use when a diff introduces a new algorithm, heuristic, threshold, retry/backoff
  policy, or config value that shapes downstream behavior, or when a design rationale
  makes a "this is safe because X" claim. Pressure-tests reasoning using mental models
  (Inversion, Second-Order Thinking, Margin of Safety, Incentives, etc.). Not for
  hunting bugs/exploits in code (use adversarial-reviewer) or module structure (use
  design-review). Hanlon's Razor, and others)
argument-hint: '[file, PR, diff, or design rationale to pressure-test]'
allowed-tools: Read, Grep, Glob
metadata:
  category: pattern
  triggers:
  - adversarial-thinking
  - threat-modeling
  - security
---
