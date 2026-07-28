---
name: adversarial-reviewer
description: "Use when code, a PR, or a design needs an adversarial pass \u2014 red-teams\
  \ by attacking for bugs, security holes, hostile/malformed input handling, and weaknesses\
  \ in existing design findings. Always available on request, not gated behind any\
  \ other workflow. Not for constructive design-quality lenses (use design-review\
  \ or red-flags) or generating a second independent design (use design-it-twice)."
argument-hint: '[file, PR, diff, or design doc to attack]'
allowed-tools: Read, Grep, Glob, Task
metadata:
  category: discipline
  triggers:
  - code-review
  - security-review
  - bug-finding
  - testing
---
