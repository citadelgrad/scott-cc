---
name: mental-models-economics
description: Use when a diff adds a new dependency or vendor, includes a TODO/FIXME/HACK
  marker, or the PR description discusses a trade-off or deferred work. Frames changes
  as resource-allocation decisions using mental models (Scarcity, Trade-offs, Debt,
  Build-vs-Buy, etc.). Not for code-level simplicity trade-offs (use mental-models-simplifier)
  or runtime behavior (use mental-models-systems).
argument-hint: '[file, PR, diff, or design doc with a resource/dependency/debt decision]'
allowed-tools: Read, Grep, Glob
metadata:
  category: pattern
  triggers:
  - economic-thinking
  - cost-analysis
  - tradeoffs
---
