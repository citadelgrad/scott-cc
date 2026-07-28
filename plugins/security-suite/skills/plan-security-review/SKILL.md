---
name: plan-security-review
description: "Use when a planning or grilling session ends with a build-ready plan,\
  \ or when the user asks for a \"plan security review\", \"threat-model checkpoint\"\
  , or \"pre-build security pass\". Runs a lightweight threat-model checkpoint over\
  \ a plan/PRD/spec \u2014 trust boundaries, data flows, authn/authz, secrets, third-party\
  \ deps \u2014 producing a CLEAR/TRIGGERED/N/A findings report. Not for reviewing\
  \ code diffs or comprehensive security audits."
argument-hint: '[plan/PRD/spec document path, or none if already in conversation]'
allowed-tools: Read, Grep, Glob, WebFetch
metadata:
  category: discipline
  triggers:
  - security-review
  - security-planning
  - threat-assessment
---
