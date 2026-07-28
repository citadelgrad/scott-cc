---
name: red-flags
description: Use when reviewing a PR for design quality, evaluating unfamiliar code
  against a comprehensive checklist, or when the user asks for a red flags scan. Scans
  code against 17 design smells (14 from the book's named Red Flags plus 3 process-stage
  signals) and produces a structured diagnostic report. Not for diagnosing why code
  feels complex (use complexity-recognition) or design trajectory (use code-evolution).
argument-hint: '[file or directory]'
allowed-tools: Read, Grep
metadata:
  category: discipline
  triggers:
  - code-review
  - anti-pattern
  - warning-signs
---
