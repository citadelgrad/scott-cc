---
name: code-evolution
description: Use when reviewing changes to existing code (diffs, PRs, or recently
  modified files) to assess whether each change looks designed-in or bolted-on. Not
  for scanning a checklist of design smells (use red-flags) or assessing overall design
  investment (use strategic-mindset).
argument-hint: '[file, module, or PR]'
allowed-tools: Read, Grep
metadata:
  category: pattern
  triggers:
  - code-history
  - change-analysis
  - git-history
  - refactoring
---
