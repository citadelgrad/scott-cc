---
name: naming-obviousness
description: Use when the user asks to check naming, when names feel vague or imprecise,
  when something is hard to name (a design signal, not a vocabulary problem), or when
  code behavior isn't obvious on first read. Reviews naming quality and code obviousness
  via the isolation test, scope-length principle, and consistency audit. Not for comment
  quality or documentation (use comments-docs).
argument-hint: '[file or module path]'
allowed-tools: Read, Grep
metadata:
  category: discipline
  triggers:
  - naming-review
  - code-clarity
  - readability
---
