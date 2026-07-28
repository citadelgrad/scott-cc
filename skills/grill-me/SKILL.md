---
name: grill-me
description: Use when a plan, architecture, or implementation proposal needs Socratic stress-testing before execution, especially when requirements, trade-offs, edge cases, or failure modes remain vague.
license: MIT
metadata:
  category: discipline
  triggers: [grill, stress-test, architecture, risk-matrix, pre-implementation]
  source: https://github.com/mattpocock/skills/tree/main/skills/productivity/grill-me
---

# Grill Me

Interrogate the proposal until its important decisions are explicit and defensible. This is a pre-execution gate, not performative brainstorming.

## Hard Stop

Do not write code, edit files, launch implementation agents, or approve execution while a material requirement or design decision is vague. “We can decide later,” “probably,” and unstated defaults are unresolved decisions, not answers.

Facts belong to discovery: inspect the repository, documentation, and runtime instead of asking the user to recall retrievable information. Decisions belong to the user: present a recommendation, ask for justification, and wait.

## Interview Protocol

1. Restate the objective, constraints, and success criteria in testable terms.
2. Build a dependency-ordered decision tree covering:
   - system boundaries, ownership, and data flow;
   - invariants, trust boundaries, and destructive operations;
   - edge cases, degraded modes, retries, rollback, and recovery;
   - scale, concurrency, performance, observability, and operability;
   - alternatives rejected and the trade-off that rejects each one.
3. Ask one question at a time. Include your recommended answer and its trade-off.
4. Resolve parent decisions before questions that depend on them.
5. Challenge answers with a concrete counterexample or failure scenario.
6. Stop when the user cannot justify a material choice. Offer narrower, safer options; do not silently choose one.
7. Repeat until the user confirms shared understanding.

## Required Risk Matrix

Before any handoff to execution, emit this matrix. Every material risk needs evidence, mitigation, or an explicit owner accepting it.

| Risk | Assumption | Failure mode | Likelihood | Impact | Evidence / mitigation | Decision owner |
|---|---|---|---|---|---|---|
| ... | ... | ... | Low/Med/High | Low/Med/High | ... | ... |

After the matrix, list:

- Resolved decisions
- Rejected alternatives and why
- Open blockers
- Execution recommendation: `PROCEED`, `PROCEED WITH CONDITIONS`, or `STOP`

Only `PROCEED` may flow directly into implementation. `PROCEED WITH CONDITIONS` requires the named conditions to be satisfied first. `STOP` returns to the unresolved decision tree.

## Anti-Rationalization

- Urgency does not make ambiguity safe.
- A familiar architecture is not evidence that it fits this system.
- A happy-path demo does not resolve failure behavior.
- “The agent can figure it out” transfers an unresolved product decision to implementation.
- A risk matrix with generic entries is paperwork; tie every row to this proposal.
