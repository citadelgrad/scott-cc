---
name: pull-complexity-down
description: Use when callers must do significant setup, handle errors the module
  could resolve, or configure things they don't understand. Checks whether complexity
  is pushed to callers or absorbed by implementations. Not for overall module depth
  (use deep-modules), knowledge leakage (use information-hiding), or exception hierarchy
  (use error-design).
argument-hint: '[file or module path]'
allowed-tools: Read, Grep
metadata:
  category: pattern
  triggers:
  - complexity-management
  - refactoring
  - code-review
---
