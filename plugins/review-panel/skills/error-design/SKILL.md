---
name: error-design
description: Use when the user asks to review error handling, when a module throws
  too many exceptions, or when callers must handle errors they shouldn't need to know
  about. Applies the "define errors out of existence" principle with a decision tree
  for exception strategies. Not for general interface complexity (use pull-complexity-down).
argument-hint: '[file or module path]'
allowed-tools: Read, Grep
metadata:
  category: pattern
  triggers:
  - error-handling
  - exception-design
  - error-messages
---
