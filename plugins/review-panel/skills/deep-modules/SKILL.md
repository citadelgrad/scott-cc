---
name: deep-modules
description: "Use when a module's interface has too many parameters or methods, when\
  \ there are too many small classes each doing too little, or when methods just forward\
  \ calls to other methods. Measures module depth \u2014 whether the interface is\
  \ simple relative to the implementation behind it. Not for adjacent-layer abstraction\
  \ quality (use abstraction-quality) or merge/split decisions (use module-boundaries)."
argument-hint: '[file or module path]'
allowed-tools: Read, Grep
metadata:
  category: pattern
  triggers:
  - module-depth
  - interface-design
  - code-review
---
