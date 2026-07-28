---
name: domain-modeling
description: "Use when reviewing a type/interface/schema definition, an entity or\
  \ aggregate with boolean/optional-field clusters, a validation layer, or a multi-step\
  \ business workflow. Reviews against 8 type-driven functional-modeling techniques\
  \ (algebraic data types, illegal-states-unrepresentable, exhaustive matching, parse-don't-validate,\
  \ smart constructors, errors-as-values, custom error types, workflows-as-functions).\
  \ FP-only \u2014 not for OOP patterns, general code-quality (use red-flags), or\
  \ glossary work (use grill-with-docs). parse-don't-validate, smart constructors,\
  \ errors-as-values, custom error types, workflows-as-functions) and produces a CLEAR/TRIGGERED/N/A\
  \ findings report"
argument-hint: '[file, directory, or domain to review]'
allowed-tools: Read, Grep
metadata:
  category: pattern
  triggers:
  - domain-driven-design
  - modeling
  - architecture
---
