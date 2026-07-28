---
name: triage-spine
description: "Use when a detector has just run and produced triage item(s), or when\
  \ scheduling a Foundry recipe that pipes detector output into this spine. Consumes\
  \ normalized triage items from registered detectors and runs the intake \u2192 reproduce\
  \ \u2192 diagnose \u2192 fix \u2192 gate loop, filing beads, reproducing issues\
  \ E2E, producing fix diffs via pas-pipeline, and gating through review-panel."
argument-hint: '[triage item(s) as JSON, or a detector name to run first]'
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
metadata:
  category: technique
  triggers:
  - issue-triage
  - prioritization
  - issue-management
---
