---
name: mental-models-systems
description: "Use when a diff touches concurrency, queues/message buses, caching,\
  \ retries/backoff, rate limiting, service-to-service calls, or connection pooling.\
  \ Evaluates dynamic runtime behavior \u2014 feedback loops, bottlenecks, emergence,\
  \ scale \u2014 using mental models (Feedback Loops, Equilibrium, Critical Mass,\
  \ etc.). Not for static module quality (use design-review) or assumption pressure-testing\
  \ (use mental-models-adversarial)."
argument-hint: '[file, PR, diff, or design doc touching runtime/systems behavior]'
allowed-tools: Read, Grep, Glob
metadata:
  category: pattern
  triggers:
  - systems-thinking
  - architecture
  - design
---
