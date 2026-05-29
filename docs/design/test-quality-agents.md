# Test Quality Agent Group Design

## Overview

A multi-agent system for identifying low-quality tests and refactoring test suites using mutation testing principles.

## Agent Roles

### 1. test-saboteur (The Mutation Agent)

**Purpose**: Create semantic mutations in source code to test if the test suite catches them.

**Capabilities**:
- Parse Python/TypeScript/etc code to identify mutation points
- Apply semantic mutations (not random):
  - Boundary conditions: `>` → `>=`, `<` → `<=`
  - Boolean inversions: `and` → `or`, `True` → `False`
  - Return value mutations: `return x` → `return None`
  - Arithmetic operators: `+` → `-`, `*` → `/`
- Track which mutations were applied
- Use git worktree to safely isolate mutations

**Tools**: All tools (needs Read, Edit, Bash for git worktree)

**Trigger Pattern**:
```
Use when you need to create code mutations for test quality analysis.
Examples: "mutate this function", "create test mutations", "apply semantic mutations"
```

**Workflow**:
1. Create isolated git worktree for mutations
2. Identify mutation targets (functions, methods, conditionals)
3. Apply one mutation at a time
4. Return mutation metadata (location, type, original → mutated)

---

### 2. test-executor (The Test Runner)

**Purpose**: Execute test suites against mutated code and collect detailed results.

**Capabilities**:
- Run pytest/jest/vitest with coverage reporting
- Parse test output (failures, passes, skips)
- Collect stack traces and assertion errors
- Track execution time per test
- Generate coverage reports

**Tools**: All tools (needs Bash for test execution, Read for parsing results)

**Trigger Pattern**:
```
Use when you need to run tests and analyze results.
Examples: "run tests against mutation", "execute test suite", "collect test coverage"
```

**Workflow**:
1. Run test suite in the mutation worktree
2. Capture stdout/stderr with detailed formatting
3. Parse results into structured data:
   - Tests that passed (potential issues if mutation should've failed them)
   - Tests that failed (good - caught the mutation)
   - Coverage percentage
4. Return test execution report

---

### 3. test-auditor (The Quality Analyst)

**Purpose**: Analyze mutation test results to identify low-quality tests.

**Capabilities**:
- Compare mutation results against expectations
- Identify "zombie tests" (pass despite code being broken)
- Calculate mutation score (% of mutations caught)
- Find redundant tests (multiple tests covering same logic)
- Detect over-mocked tests (too many mocks = not testing real behavior)
- Generate quality metrics per test file

**Tools**: All tools (needs Read to analyze test code, Grep to find patterns)

**Trigger Pattern**:
```
Use when you need to analyze test quality from mutation results.
Examples: "analyze test quality", "find zombie tests", "calculate mutation score"
```

**Workflow**:
1. Receive mutation + test execution data
2. Classify each test:
   - **High Quality**: Caught the mutation
   - **Zombie**: Passed despite semantic mutation
   - **Redundant**: Overlaps with other tests
   - **Over-Mocked**: Too many mocks, testing mocks not logic
3. Generate quality report with specific recommendations
4. Calculate overall mutation score

---

### 4. test-refactor-specialist (The Optimizer)

**Purpose**: Consolidate redundant tests and improve test quality.

**Capabilities**:
- Identify test patterns (similar setup, similar assertions)
- Convert multiple similar tests into parameterized tests
- Remove zombie tests (with user approval)
- Suggest minimal high-quality test set
- Add missing edge case tests based on mutation analysis

**Tools**: All tools (needs Edit, Write for refactoring)

**Trigger Pattern**:
```
Use when you need to refactor and consolidate tests.
Examples: "consolidate redundant tests", "parameterize tests", "refactor test suite"
```

**Workflow**:
1. Analyze test suite for patterns
2. Group similar tests by:
   - Same function under test
   - Similar setup/teardown
   - Same assertion patterns
3. Propose parameterized test rewrites
4. Identify tests that can be removed (zombie tests)
5. Generate refactored test code for user review

---

### 5. test-quality-reviewer (The Orchestrator)

**Purpose**: Coordinate the full mutation testing workflow and synthesize results.

**Capabilities**:
- Launch saboteur, executor, auditor agents in sequence
- Manage git worktree lifecycle
- Aggregate results across multiple mutations
- Generate executive summary
- Provide actionable recommendations

**Tools**: All tools (needs Task to launch sub-agents)

**Trigger Pattern**:
```
Use when the user wants comprehensive test quality analysis.
Examples: "audit test quality", "review test suite", "mutation test my code"
```

**Workflow**:
1. Identify target files (source + test files)
2. Launch test-saboteur to create N mutations
3. For each mutation:
   - Launch test-executor to run tests
   - Collect results
4. Launch test-auditor to analyze aggregate results
5. Launch test-refactor-specialist to propose improvements
6. Generate final report with:
   - Mutation score (% mutations caught)
   - List of zombie tests
   - Refactoring suggestions
   - Estimated test suite reduction (e.g., "200 tests → 45 tests")

---

## Example Usage

```bash
# User invokes the orchestrator
User: "Audit the test quality for my Stripe dunning logic"

# Agent workflow:
1. test-quality-reviewer identifies:
   - Source: mlb_fantasy_jobs/dunning/stripe_handler.py
   - Tests: tests/test_stripe_dunning.py (200 tests)

2. test-saboteur creates 15 mutations:
   - Mutation 1: change `>= 3` to `> 3` in retry logic
   - Mutation 2: return `None` instead of `SubscriptionStatus.ACTIVE`
   - ... etc

3. test-executor runs tests against each mutation:
   - Mutation 1: 200/200 tests passed (🚨 zombie tests!)
   - Mutation 2: 5/200 tests failed (good, but only 5?)

4. test-auditor reports:
   - Mutation score: 23% (very low!)
   - 183 zombie tests identified
   - 150 tests are redundant (testing same model validation)

5. test-refactor-specialist proposes:
   - Consolidate 150 model validation tests → 1 parameterized test
   - Remove 33 tests that don't assert anything meaningful
   - Add 3 edge case tests for retry boundary conditions
   - Final: 200 tests → 20 high-quality tests

6. test-quality-reviewer summarizes:
   "Your test suite has a 23% mutation score. I found 183 zombie tests
   that pass even when the code is broken. I can reduce 200 tests to 20
   high-quality tests that actually validate behavior. Approve refactor?"
```

## Implementation in Plugin Manifest

Add to your scott-cc plugin manifest:

```yaml
agents:
  - name: test-saboteur
    description: "Create semantic code mutations for test quality analysis"
    tools: ["All tools"]

  - name: test-executor
    description: "Execute test suites and collect detailed results"
    tools: ["All tools"]

  - name: test-auditor
    description: "Analyze mutation test results to identify low-quality tests"
    tools: ["All tools"]

  - name: test-refactor-specialist
    description: "Consolidate redundant tests and improve test quality"
    tools: ["All tools"]

  - name: test-quality-reviewer
    description: "Orchestrate mutation testing workflow and synthesize results. Use when user wants comprehensive test quality analysis."
    tools: ["All tools"]
```

## Benefits Over Skills

1. **Stateful collaboration**: Agents pass structured data between steps
2. **Parallel execution**: Can test multiple mutations concurrently
3. **Real code execution**: Actually runs tests, not just static analysis
4. **Adaptive behavior**: Auditor learns patterns as it sees more mutations
5. **Safety**: Git worktrees prevent corrupting actual code

## Next Steps

1. Implement agents in plugin manifest
2. Create mutation strategies for target languages (Python, TypeScript)
3. Build test result parsers (pytest, jest, vitest)
4. Add user approval gates before deleting tests
5. Integrate with beads for tracking improvements across sessions
