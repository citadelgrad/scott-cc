---
name: complexity-recognition
description: Use when code feels harder to work with than it should but the specific
  problem is unclear. Diagnoses what makes code complex and why using the three-symptom
  two-root-cause framework. Not for scanning known design smells (use red-flags) or
  evaluating module depth (use deep-modules).
argument-hint: '[file or module path]'
allowed-tools: Read, Grep
metadata:
  category: pattern
  triggers:
  - complexity-analysis
  - code-review
  - refactoring
---
