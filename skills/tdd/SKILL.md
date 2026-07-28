---
name: tdd
description: Use when implementing a feature or bug fix test-first, when the user requests red-green-refactor, or when behavior needs a durable regression test through a public interface.
license: MIT
metadata:
  category: discipline
  triggers: [tdd, red-green-refactor, test-first, regression-test, mutation-testing]
  source: https://github.com/mattpocock/skills/tree/main/skills/engineering/tdd
---

# Test-Driven Development

Build one behavior at a time through an observed Red → Green → Refactor cycle.

## Non-Negotiable Constraint

DO NOT write or modify implementation code until a new or changed test has failed for the expected behavioral reason.

A test that fails because of syntax, imports, fixtures, environment setup, or an unrelated defect is not Red. A test that already passes proves nothing about the requested change. If implementation was changed first, stop and remove only that unverified change before restarting from the test.

## Cycle

### 1. Choose one vertical slice

- Define one externally observable behavior and the public seam that exposes it.
- Prefer an end-to-end or integration reproduction closest to the user path; use a unit seam only when it is the correct public boundary.
- Use expected values from a specification, known-good literal, or independent worked example. Never recompute the expected result with the production algorithm.

### 2. Red

- Write one minimal test for that behavior.
- Run the narrowest command that exercises it.
- Record the failing test name, exit status, and failure reason.
- Confirm the failure is caused by missing or incorrect behavior.

No observed, relevant failure means no implementation edit.

### 3. Green

- Write the smallest implementation that makes the failing test pass.
- Do not anticipate later slices, broaden APIs, or refactor unrelated code.
- Re-run the focused test, then the relevant surrounding suite.

### 4. Refactor

- Refactor only while green.
- Remove duplication and improve names or boundaries without adding behavior.
- Re-run the focused and surrounding tests after each meaningful refactor.

### 5. Repeat

Start the next behavior with a new failing test. Do not batch all tests before all implementation; that horizontal slicing tests imagined structure instead of learned behavior.

## Test Quality Rules

- Test behavior through public interfaces, not private methods or internal call order.
- Avoid over-mocking; mocks at owned boundaries should verify a real contract.
- Name tests as behavioral specifications.
- Keep each test independent and deterministic.
- A refactor that preserves behavior should not require test rewrites.

## Mutation-Testing Gate

After the requested slices are green and refactored, use the existing mutation-testing sub-plugin on the changed behavior:

```text
/mutation-testing:mutation-test --quick <changed-file-or-directory>
```

Review surviving mutations rather than chasing a score blindly. A meaningful survivor becomes the next Red test and starts another cycle. If the sub-plugin is unavailable, report the mutation gate as unavailable; do not fabricate a result or silently substitute line coverage.

## Evidence at Handoff

Report:

- Red: command and expected failure observed
- Green: focused and surrounding test commands passed
- Refactor: what changed without behavioral expansion
- Mutation: killed/surviving mutations, or the exact availability blocker

## Anti-Rationalization

| Rationalization | Reality |
|---|---|
| "The change is trivial" | Trivial changes break. Test takes 30 seconds. Not permission to skip Red. |
| "I will add tests afterward" | Test-after is not TDD. Tests passing immediately prove nothing about the new behavior. |
| "Existing coverage already covers this" | Existing coverage is not proof the new behavior was driven by a failing test. |
| "I'll write all the tests first, then implement" | That's horizontal slicing. TDD is vertical: one test, one implementation, repeat. |
| "Refactoring while red is fine if I'm careful" | Refactoring while red destroys the diagnostic signal. Get green first. |
| "This is about spirit, not ritual" | The letter IS the spirit. TDD's value comes from the specific sequence. |

## Red Flags — STOP and Restart

- Implementation code written before a test failed
- "I already manually tested it"
- Multiple tests written before any implementation
- Refactoring while tests are failing
- "This is different because..."

All of these mean: delete the unverified code, start over with a failing test.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Testing private methods | Test behavior through public interfaces only |
| Over-mocking everything | Mock at owned boundaries; verify real contracts |
| Batching all tests before implementation | One test → one implementation → repeat |
| Chasing mutation score blindly | Review surviving mutations; meaningful survivors become new Red tests |
| Skipping the Refactor step | Refactor while green to maintain code quality |
