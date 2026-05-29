# Agent Collaboration Patterns

## Why Agents Beat Skills for Multi-Step Workflows

### Skills: Stateless, Single-Purpose
```
User → Skill executes → Result → Done
```

**Limitations**:
- No memory between invocations
- Can't pass complex data structures
- No parallelization
- User must manually chain steps

### Agents: Stateful, Collaborative
```
User → Orchestrator → Agent 1 → Agent 2 → Agent 3 → Synthesized Result
                         ↓          ↓          ↓
                      Pass data  Pass data  Pass data
```

**Benefits**:
- Agents share structured state
- Parallel execution of independent work
- Adaptive workflows (agent 2 changes based on agent 1's findings)
- Specialized expertise per agent

## Test Quality Agent Collaboration Flow

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                   test-quality-reviewer                      │
│                     (Orchestrator)                          │
└────┬──────────────────────────────────────────────┬────────┘
     │                                               │
     │ 1. Source file path                           │ 6. Final report
     ↓                                               ↑
┌────────────────────┐                              │
│  test-saboteur     │                              │
│                    │                              │
│ Creates mutations  │                              │
└────┬───────────────┘                              │
     │                                               │
     │ 2. Mutation manifest (JSON)                   │
     ↓                                               │
┌────────────────────┐                              │
│  test-executor     │ ← Launched N times in        │
│  test-executor     │   parallel (one per          │
│  test-executor     │   mutation)                  │
│  ...               │                              │
└────┬───────────────┘                              │
     │                                               │
     │ 3. Test results (JSON array)                  │
     ↓                                               │
┌────────────────────┐                              │
│  test-auditor      │                              │
│                    │                              │
│ Analyzes results   │                              │
└────┬───────────────┘                              │
     │                                               │
     │ 4. Quality report (JSON)                      │
     ↓                                               │
┌────────────────────┐                              │
│ test-refactor-     │                              │
│ specialist         │                              │
│                    │                              │
└────┬───────────────┘                              │
     │                                               │
     │ 5. Refactored test code                       │
     └───────────────────────────────────────────────┘
```

## Structured Data Contracts

### Phase 1: Saboteur → Executor

**Output from test-saboteur**:
```json
{
  "mutations": [
    {
      "id": "mut-001",
      "type": "boundary",
      "file": "mlb_fantasy_jobs/dunning/stripe_handler.py",
      "line": 47,
      "original": "retry_count >= 3",
      "mutated": "retry_count > 3",
      "worktree": "/Users/scott/projects/test-mutation-001",
      "expected_impact": "Tests with retry_count=3 should fail"
    }
  ],
  "total": 15
}
```

**Input to test-executor** (one instance per mutation):
```json
{
  "mutation_id": "mut-001",
  "worktree": "/Users/scott/projects/test-mutation-001",
  "test_command": "pytest tests/test_stripe_dunning.py -v",
  "expected_failures": ["test_retry_boundary"]
}
```

### Phase 2: Executor → Auditor

**Output from each test-executor**:
```json
{
  "mutation_id": "mut-001",
  "test_results": {
    "total": 200,
    "passed": 200,  // 🚨 All passed = zombie tests!
    "failed": 0,
    "errors": 0,
    "skipped": 0
  },
  "failures": [],  // Empty because all passed
  "coverage": "87%",
  "execution_time": "12.4s"
}
```

**Aggregated input to test-auditor**:
```json
{
  "mutations": [
    {
      "id": "mut-001",
      "type": "boundary",
      "line": 47,
      "tests_passed": 200,
      "tests_failed": 0
    },
    {
      "id": "mut-002",
      "type": "return",
      "line": 112,
      "tests_passed": 195,
      "tests_failed": 5
    }
  ],
  "source_file": "mlb_fantasy_jobs/dunning/stripe_handler.py",
  "test_file": "tests/test_stripe_dunning.py"
}
```

### Phase 3: Auditor → Refactor Specialist

**Output from test-auditor**:
```json
{
  "mutation_score": 0.23,
  "mutations_caught": 3,
  "mutations_missed": 12,
  "zombie_tests": [
    {
      "test_name": "test_retry_count_validation_1",
      "file": "tests/test_stripe_dunning.py",
      "line": 47,
      "reason": "Passed for all 12 boundary mutations"
    }
  ],
  "redundant_groups": [
    {
      "pattern": "subscription_status field validation",
      "test_count": 150,
      "tests": [
        "test_status_valid",
        "test_status_invalid",
        ...
      ],
      "recommendation": "Consolidate into parameterized test"
    }
  ]
}
```

**Input to test-refactor-specialist**:
```json
{
  "audit_report": { /* full report from above */ },
  "source_file": "mlb_fantasy_jobs/dunning/stripe_handler.py",
  "test_file": "tests/test_stripe_dunning.py",
  "refactor_actions": [
    "consolidate_redundant",
    "remove_zombies",
    "add_edge_cases"
  ]
}
```

### Phase 4: Refactor Specialist → Orchestrator

**Output from test-refactor-specialist**:
```json
{
  "refactored_test_code": "... new test file content ...",
  "changes": {
    "removed": ["test_retry_count_validation_1", ...],  // 183 tests
    "consolidated": [
      {
        "from": ["test_status_valid", "test_status_invalid", ...],  // 150 tests
        "to": "test_subscription_model_validation",
        "type": "parameterized"
      }
    ],
    "added": [
      "test_retry_boundary_at_3",
      "test_retry_boundary_at_7"
    ]
  },
  "metrics": {
    "old_test_count": 200,
    "new_test_count": 20,
    "estimated_mutation_score": 0.85
  },
  "diff": "... git diff output ..."
}
```

## Orchestrator Implementation Example

```python
# Conceptual implementation (actual implementation uses Task tool)

class TestQualityReviewer:
    def orchestrate(self, source_file):
        # Phase 1: Create mutations
        print("Creating mutations...")
        saboteur_result = self.launch_agent(
            agent="test-saboteur",
            prompt=f"Create 15 mutations for {source_file}"
        )

        mutations = saboteur_result['mutations']
        print(f"Created {len(mutations)} mutations")

        # Phase 2: Run tests in parallel
        print("Running tests against mutations...")
        executor_tasks = []
        for mutation in mutations:
            task = self.launch_agent(
                agent="test-executor",
                prompt=f"Run tests in {mutation['worktree']}",
                run_in_background=True  # Parallel!
            )
            executor_tasks.append(task)

        # Wait for all executors to complete
        test_results = []
        for task in executor_tasks:
            result = self.wait_for_agent(task)
            test_results.append(result)

        print(f"Completed {len(test_results)} test runs")

        # Phase 3: Analyze quality
        print("Analyzing test quality...")
        auditor_result = self.launch_agent(
            agent="test-auditor",
            prompt=f"""Analyze mutation results:
            Mutations: {json.dumps(mutations)}
            Test Results: {json.dumps(test_results)}
            """
        )

        mutation_score = auditor_result['mutation_score']
        zombie_count = len(auditor_result['zombie_tests'])
        print(f"Mutation score: {mutation_score*100}%")
        print(f"Zombie tests: {zombie_count}")

        # Phase 4: Generate refactoring
        print("Generating refactoring plan...")
        refactor_result = self.launch_agent(
            agent="test-refactor-specialist",
            prompt=f"""Refactor tests based on audit:
            Audit Report: {json.dumps(auditor_result)}
            """
        )

        # Phase 5: Synthesize final report
        return {
            'mutation_score': mutation_score,
            'zombies': zombie_count,
            'refactoring': refactor_result,
            'recommendation': self.generate_recommendation(
                auditor_result,
                refactor_result
            )
        }
```

## Advantages of Agent Architecture

### 1. Parallel Execution

**Skill-based** (sequential):
```
Mutation 1 → Run tests (12s)
Mutation 2 → Run tests (12s)
Mutation 3 → Run tests (12s)
...
Total: 15 × 12s = 180s (3 minutes)
```

**Agent-based** (parallel):
```
Mutation 1 → Run tests (12s) ─┐
Mutation 2 → Run tests (12s) ─┤
Mutation 3 → Run tests (12s) ─┼→ Wait for all
...                            │
Mutation 15 → Run tests (12s)─┘

Total: 12s (15× speedup!)
```

### 2. Adaptive Workflows

Agents can change strategy based on intermediate results:

```python
# If mutation score is very low, create more mutations
if auditor_result['mutation_score'] < 0.30:
    print("Mutation score very low, creating additional mutations...")
    extra_mutations = self.launch_agent(
        agent="test-saboteur",
        prompt="Create 10 more mutations focused on untested areas"
    )
```

### 3. Specialized Expertise

Each agent has focused knowledge:

- **Saboteur**: Expert in AST parsing, mutation strategies
- **Executor**: Expert in test frameworks (pytest, jest, vitest)
- **Auditor**: Expert in statistical analysis, pattern detection
- **Refactor**: Expert in test refactoring patterns (parameterization, fixtures)

### 4. State Preservation

Agents maintain context across the workflow:

```python
# Auditor remembers which mutations were caught
# Refactor specialist uses that knowledge to prioritize

if mutation['caught'] == False:
    refactor_specialist.add_test_for_mutation(mutation)
```

## Comparison: Skill vs Agent

### Skill Implementation (Hypothetical)

```bash
# User must manually chain steps
/mutation-test create stripe_handler.py
# ... wait ...
# ... manually copy mutation IDs ...

/mutation-test run mut-001
/mutation-test run mut-002
# ... run 15 times sequentially ...

/mutation-test analyze
# ... get results ...

/mutation-test refactor
```

**Problems**:
- Manual chaining (error-prone)
- Sequential (slow)
- No state sharing
- User must interpret intermediate results

### Agent Implementation

```bash
# User asks once
"Audit test quality for stripe_handler.py"

# Agent orchestrator handles everything:
# - Creates mutations
# - Runs tests in parallel
# - Analyzes results
# - Proposes refactoring
# - Generates report

# User gets final actionable report
```

**Benefits**:
- Single command
- Parallel execution
- Automatic state management
- Synthesized insights

## Real-World Example: Debugging Test Failures

### Skill Approach

```
User: "Why is test_stripe_retry failing?"

Skill: [Reads test file]
Skill: "The test checks retry_count >= 3, but your code has retry_count > 3"

User: "Are there other similar bugs?"

Skill: [Has to re-analyze from scratch, no memory of previous findings]
```

### Agent Approach

```
User: "Why is test_stripe_retry failing?"

Orchestrator:
  → Launches test-saboteur: "Create boundary mutations around retry logic"
  → Launches test-executor: "Run tests for each mutation"
  → Launches test-auditor: "Analyze which mutations expose bugs"

Auditor: "Found 3 boundary bugs in retry logic:
  1. Line 47: retry_count > 3 (should be >=)
  2. Line 89: max_retries < 5 (should be <=)
  3. Line 134: attempts == 0 (should be <= 0)

  Your test caught bug #1, but missed #2 and #3."

User: "Fix all of them"

Orchestrator: [Applies fixes, re-runs mutation testing, confirms all caught]
```

## Advanced Collaboration: Agent Teams

You can create **agent teams** for complex workflows:

### Team: "Test Quality SWAT Team"

```yaml
team: test-quality-swat
agents:
  - saboteur (creates mutations)
  - executor (runs tests)
  - auditor (analyzes results)
  - refactor (improves tests)
  - security-sentinel (checks for security implications)
  - performance-oracle (checks test execution time)

workflow:
  1. Saboteur creates mutations
  2. Executor runs tests (parallel)
  3. [FORK]
     - Auditor analyzes quality
     - Security-sentinel checks security tests
     - Performance-oracle checks test speed
  4. [JOIN] Orchestrator synthesizes all findings
  5. Refactor specialist proposes improvements
```

This multi-perspective analysis catches issues a single agent might miss!

## Conclusion

Agents enable **emergent behavior** through collaboration:

- Skills are tools (stateless, single-purpose)
- Agents are team members (stateful, collaborative)

For complex workflows like mutation testing, **agents are the clear choice**.

## Next Steps

1. Implement the orchestrator agent
2. Define data contracts (JSON schemas)
3. Add parallel execution logic
4. Test with simple example
5. Scale to real codebases

The architecture is designed for **agent collaboration first**.
