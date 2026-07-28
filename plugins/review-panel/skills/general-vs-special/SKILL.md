---
name: general-vs-special
description: Use when the user asks to check interface generality, when a module has
  if-branches or parameters serving only one caller, when getters/setters expose internal
  representation, or when an interface is over-specialized. Evaluates general-purpose
  design, special-general mixture, and defaults. Not for information-leakage (use
  information-hiding) or configuration-parameter necessity (use pull-complexity-down).
argument-hint: '[file or module path]'
allowed-tools: Read, Grep
metadata:
  category: pattern
  triggers:
  - code-review
  - generalization
  - interface-design
---
