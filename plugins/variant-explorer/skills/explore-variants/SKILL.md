---
name: explore-variants
description: Use when the user wants to explore multiple independent implementation
  approaches in parallel rather than commit to one up front. Spawns N blind builders
  in isolated git worktrees against a spec + acceptance criteria, then judges results
  against AC conformance, TASTE.md, and simplicity, producing a ranked shortlist.
  N defaults to 3 (refuses N=1, clamps N>6).
argument-hint: '[spec or design question, or path to one] [--n N] [--ac <path>]'
allowed-tools: Task, Read, Write, Grep, Glob, Bash
metadata:
  category: technique
  triggers:
  - variant-exploration
  - experimentation
  - testing
---
