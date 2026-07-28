---
name: abstraction-quality
description: Use when adjacent layers feel redundant, when decorator/wrapper patterns
  add boilerplate without depth, or when an abstraction feels leaky. Evaluates whether
  abstractions provide a fundamentally different way of thinking or are structurally
  shallow. Not for module depth (use deep-modules) or information leakage across boundaries
  (use information-hiding).
argument-hint: '[file or module path]'
allowed-tools: Read, Grep
metadata:
  category: pattern
  triggers:
  - abstraction-review
  - layer-design
  - wrapper-pattern
  - code-review
---
