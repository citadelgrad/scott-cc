---
name: grill-me
description: Use when a plan, architecture, or implementation proposal needs Socratic stress-testing before execution, especially when requirements, trade-offs, edge cases, or failure modes remain vague.
license: MIT
metadata:
  category: discipline
  triggers: [grill, stress-test, architecture-review, risk-matrix, pre-implementation, proposal-review, decision-tree, trade-offs, requirements-vague, failure-modes]
  source: https://github.com/mattpocock/skills/tree/main/skills/productivity/grill-me
---

# Grill Me

Interrogate the proposal until its important decisions are explicit and defensible. This is a pre-execution gate, not performative brainstorming.

## When to Use
- A plan, architecture, or implementation proposal is about to be executed
- Requirements, trade-offs, edge cases, or failure modes remain vague
- A decision tree has unresolved parent nodes blocking child decisions
- A team wants stress-testing of a proposal before committing resources

## Hard Stop

Do not write code, edit files, launch implementation agents, or approve execution while a material requirement or design decision is vague. "We can decide later," "probably," and unstated defaults are unresolved decisions, not answers.

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

**Violating the letter of these rules is violating the spirit of these rules.**

| Rationalization | Reality |
|---|---|
| "This is urgent, we can decide later" | Urgency does not make ambiguity safe. Ambiguous decisions under pressure create the costliest bugs. |
| "We've used this architecture before" | A familiar architecture is not evidence that it fits this system. Name the specific fit. |
| "The happy-path demo works" | A happy-path demo does not resolve failure behavior. What happens when it breaks? |
| "The agent can figure it out" | Transferring an unresolved product decision to implementation is not delegation — it's abdication. |
| "Let's just start and iterate" | Starting without clear decisions creates sunk-cost pressure to keep bad choices. |
| "The risk matrix is done" | Generic entries are paperwork. Every row must tie to this specific proposal with concrete evidence. |

### Red Flags — STOP

- Proceeding to implementation with any `STOP` recommendation active
- Risk matrix rows that could apply to any project (not this one)
- "We can decide later" on a parent decision that blocks child decisions
- Accepting "probably" as an answer to a requirement question
- Skipping the risk matrix because "this is straightforward"

All of these mean: return to the decision tree and resolve the ambiguity.

## Limitations
- Use this skill only when the task clearly matches the scope described above.
- This is a pre-execution gate — it does not produce implementation artifacts.
- Effectiveness depends on the user's willingness to engage with hard questions; it cannot force resolution.
- Does not replace domain-expert review for highly specialized fields (security, compliance, regulatory).
- Stop and ask for clarification if the proposal scope, system boundary, or decision ownership is unclear.
