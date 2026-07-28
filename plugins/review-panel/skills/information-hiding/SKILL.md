---
name: information-hiding
description: Use when the user asks to check information hiding, when modules seem
  to change together, when implementation details leak across boundaries, or when
  structure follows execution order rather than knowledge ownership. Detects temporal
  decomposition and false encapsulation. Not for merge/split decisions (use module-boundaries)
  or over-specialized interfaces (use general-vs-special).
argument-hint: '[file or module path]'
allowed-tools: Read, Grep
metadata:
  category: pattern
  triggers:
  - encapsulation-review
  - information-leakage
  - module-boundaries
---
