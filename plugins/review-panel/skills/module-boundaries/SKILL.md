---
name: module-boundaries
description: Use when deciding whether to combine or separate two specific modules,
  when two modules seem tightly coupled, or when a change to one module forces changes
  to another. Evaluates where module boundaries are drawn and whether modules should
  be merged or split. Not for module depth (use deep-modules) or abstraction layer
  quality (use abstraction-quality).
argument-hint: '[file or module path]'
allowed-tools: Read, Grep
metadata:
  category: pattern
  triggers:
  - modularity
  - coupling
  - cohesion
---
