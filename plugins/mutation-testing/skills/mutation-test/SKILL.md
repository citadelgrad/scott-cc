---
name: mutation-test
description: Run comprehensive mutation testing to audit test quality, find zombie tests, and propose refactoring
allowed-tools: Task(scott-cc:test-quality-reviewer)
---

# Mutation Testing Skill

Run mutation testing to identify weak tests through semantic code mutations and parallel test execution.

## Quick Start

```bash
/mutation-test stripe_handler.py              # Standard mode (15 mutations)
/mutation-test --quick api/payments/          # Quick mode (5 mutations)
/mutation-test --deep billing/                # Deep mode (30+ mutations)
/mutation-test                                # Smart mode (auto-detects target)
```

### No Path Provided? Smart Detection!

When invoked without a path (`/mutation-test`), the agent will:

1. **Check conversation context** - If discussing a specific file, test that file
2. **Check git status** - Find recently modified files that have tests
3. **Ask the user** - Present options if multiple candidates found

Example:
```bash
User: /mutation-test

Agent: "I found several recently modified files with tests:
1. stripe_handler.py (modified 5 min ago, 200 tests)
2. payment_processor.py (modified 1 hour ago, 50 tests)

Which would you like to mutation test?"
```

## What is Mutation Testing?

Mutation testing is the gold standard for measuring test quality. It works by:

1. **Creating mutations** - Making small, realistic changes to your code (introduce bugs)
2. **Running tests** - Execute your test suite against each mutation
3. **Measuring results** - Count how many mutations your tests caught
4. **Identifying zombies** - Find tests that pass even when code is broken

**Traditional coverage is misleading**: 100% line coverage ≠ good tests

**Mutation score is truth**: % of realistic bugs your tests actually catch

## Modes

### Quick Mode (--quick)
- 5 mutations
- ~1-2 minutes
- Good for: Fast feedback, iterative development, pre-commit checks

### Standard Mode (default)
- 15 mutations
- ~3-5 minutes
- Good for: Normal development workflow, feature testing

### Deep Mode (--deep)
- 30+ mutations
- ~10-15 minutes
- Good for: Critical code paths, pre-release audits, comprehensive analysis

## What You Get

### 1. Mutation Score
```
Mutation Score: 23%

This means only 23% of realistic bugs would be caught by your tests.
Target: >80% for critical code, >60% for standard code.
```

### 2. Zombie Test Identification
```
Zombie Tests: 183/200 (91%)

These tests run and pass, but don't actually test anything meaningful.
Example:
- test_retry_validation_1 (line 47)
  - Passed despite changing retry_count >= 3 to retry_count > 3
  - Missing boundary condition test
```

### 3. Refactoring Proposal
```
Before: 200 tests, 23% mutation score, 12s execution time
After:  20 tests, 85% mutation score, 1.5s execution time

Changes:
- Consolidate 150 redundant tests → 1 parameterized test
- Remove 183 zombie tests
- Add 3 boundary condition tests

Apply refactoring? [Y/n]
```

## How It Works

The skill launches the test-quality-reviewer agent, which orchestrates:

1. **test-saboteur**: Creates semantic mutations (boundary conditions, return values, boolean logic)
2. **test-executor** (×15 in parallel): Runs test suite against each mutation
3. **test-auditor**: Analyzes results, calculates mutation score, finds zombies
4. **test-refactor-specialist**: Generates refactored test suite

## Mutation Types

### 1. Boundary Conditions (Most Effective)
```python
# Original
if retry_count >= 3:
    raise MaxRetriesExceeded()

# Mutations
if retry_count > 3:   # Catches off-by-one bugs
if retry_count == 3:  # Tests exact boundary
```

### 2. Return Values
```python
# Original
return subscription.status

# Mutations
return None          # Do callers validate?
return ""            # Do callers check empty?
```

### 3. Boolean Logic
```python
# Original
if active and subscribed:

# Mutations
if active or subscribed:  # Tests logical correctness
if not (active and subscribed):  # Tests negation
```

## Examples

### Find Zombie Tests
```bash
/mutation-test stripe_handler.py
```

Output:
```
Mutation Score: 23%
Zombie Tests: 183

Your test suite has significant quality issues:
- 91% of tests never failed despite code being broken
- Most are redundant Django model validation tests

Consolidate 150 tests → 1 parameterized test?
```

### Quick Pre-Commit Check
```bash
/mutation-test --quick payments.py
```

Output:
```
Quick mutation test (5 mutations):
Mutation Score: 60% (3/5 caught)

Missing boundary test for discount calculation.
Add this test:
```python
def test_discount_at_boundary():
    assert calculate_discount(100) == 10
```

### Deep Audit Before Release
```bash
/mutation-test --deep billing/
```

Output:
```
Deep mutation test (35 mutations):
Mutation Score: 78% (27/35 caught)

Good coverage! Minor gaps:
- Add test for subscription renewal edge case
- Strengthen payment validation assertions

Estimated improvement: 78% → 85%
```

## Command-Line Options

```bash
# Target specific file or directory
/mutation-test stripe_handler.py
/mutation-test api/payments/

# Choose mutation count
/mutation-test --quick        # 5 mutations (fast)
/mutation-test                # 15 mutations (default)
/mutation-test --deep         # 30+ mutations (thorough)

# Focus on specific areas
/mutation-test --focus=retry_logic api/

# Skip test removal confirmation
/mutation-test --auto-approve
```

## Integration with Beads

Track mutation testing progress:

```bash
# Create tracking issue
bd create --title="Improve test quality - Stripe" --type=task

# Run mutation testing
/mutation-test stripe_handler.py

# Mutation testing completes, updates beads issue automatically:
# Notes: "Mutation score: 23% → 85%, Tests: 200 → 20"

# Close when done
bd close beads-xxx
```

## Interpreting Results

### Excellent (>80%)
```
✅ Mutation Score: 85%
Your tests catch most realistic bugs. Minor improvements possible.
```

### Good (60-80%)
```
👍 Mutation Score: 67%
Solid test coverage. Focus on boundary conditions and edge cases.
```

### Fair (40-60%)
```
⚠️ Mutation Score: 52%
Moderate coverage. Review zombie tests and add missing assertions.
```

### Poor (<40%)
```
🚨 Mutation Score: 23%
Significant test quality issues. Many zombie tests detected.
Recommend: Apply proposed refactoring.
```

## Common Findings

### Pattern: Redundant Model Validation Tests
```python
# 150 tests that all look like this:
def test_status_is_active():
    assert model.status == "active"

# Mutation testing reveals: All redundant!
# Consolidate → 1 parameterized test
```

### Pattern: Weak Assertions
```python
# Zombie test (always passes)
def test_process_payment():
    result = process_payment(user)
    assert result is not None  # Too weak!

# Should be:
def test_process_payment():
    result = process_payment(user)
    assert result.status == "success"
    assert result.amount == expected_amount
```

### Pattern: Over-Mocked Tests
```python
# 8 mocks - testing mocks, not real behavior
@patch('stripe.Customer')
@patch('stripe.Subscription')
@patch('stripe.Payment')
# ... 5 more mocks

# Mutation testing catches this: Tests pass despite broken logic
# Recommendation: Replace with integration test using test Stripe account
```

## Performance

- **Quick mode**: ~1-2 minutes (5 mutations, good for frequent checks)
- **Standard mode**: ~3-5 minutes (15 mutations, balanced)
- **Deep mode**: ~10-15 minutes (30+ mutations, comprehensive)

Parallelization: Runs 15 test suites simultaneously (15x speedup vs sequential)

## Safety

- Uses git worktrees (isolated mutations, no main working tree changes)
- Requires approval before deleting tests
- Shows full diff before applying refactoring
- Provides rollback instructions

## Best Practices

1. **Start small**: Run quick mode first, expand to deep for critical code
2. **Focus on risk**: Mutation test payment logic, authentication, etc.
3. **Iterate**: Fix one area, re-test, move to next
4. **Track progress**: Use beads to record mutation scores over time
5. **CI integration**: Add mutation testing to pre-release checks

## Comparison to Traditional Tools

| Tool | Mutation Score | Refactoring | Zombie Detection | Time |
|------|---------------|-------------|------------------|------|
| mutmut | ✅ Yes | ❌ No | ⚠️ Implicit | Hours |
| Stryker | ✅ Yes | ❌ No | ⚠️ Implicit | Hours |
| /mutation-test | ✅ Yes | ✅ **Auto-generated** | ✅ **Explicit** | Minutes |

## FAQ

**Q: Will this modify my code?**
A: No. Mutations are in isolated git worktrees. Main working tree is never touched.

**Q: What if I disagree with zombie test identification?**
A: Review the diff and reject specific changes. You have full control.

**Q: Can I mutation test my entire codebase?**
A: Yes, but start with high-risk areas (payments, auth, etc.). Full codebase mutation testing can take hours.

**Q: How is this different from code coverage?**
A: Coverage measures lines executed. Mutation testing measures if tests actually validate correctness. You can have 100% coverage with 0% mutation score (all zombie tests).

**Q: Should I aim for 100% mutation score?**
A: No. 80%+ is excellent. Diminishing returns above 85%. Some mutations are academic, not practical.

## When to Use

✅ **Use mutation testing when**:
- You want to verify test quality (not just quantity)
- You suspect zombie tests (tests that don't test anything)
- You have a large test suite and want to consolidate
- You're working on critical code (payments, auth, data integrity)
- You want to learn what your tests actually validate

❌ **Don't use mutation testing when**:
- You just want to add more tests (use coverage tools instead)
- You have no tests yet (write tests first)
- You need to debug failing tests (different workflow)
- You're in a rush (mutation testing takes time)

## Next Steps After Mutation Testing

1. **Review Results**: Understand why tests failed or passed
2. **Apply Refactoring**: Accept proposed test consolidation
3. **Re-run**: Verify mutation score improves
4. **Track Progress**: Record scores in beads for long-term tracking
5. **Expand**: Apply to other modules

## Example Session

```
User: /mutation-test stripe_handler.py

Claude: Running mutation testing on stripe_handler.py...
[3 minutes later]

# Test Quality Audit Report

Mutation Score: 23% (Poor)
Zombie Tests: 183/200 (91%)

Critical Finding:
150 tests validate Django model fields - all redundant

Proposed Refactoring:
Before: 200 tests, 23% score, 12s
After:  20 tests, 85% score, 1.5s

Would you like me to apply the refactoring?

User: Yes

Claude: Applied refactoring. Re-running mutation testing...
[2 minutes later]

Verified! New mutation score: 83%
Tests reduced from 200 → 22
All original passing tests still pass ✅

Committed changes and updated beads issue.
```

## Tips

- **Use beads** to track mutation scores over time
- **Start with --quick** for fast iteration
- **Focus on high-risk** code paths first
- **Review zombie tests** - they often reveal misconceptions about what you're testing
- **Pair with code review** - mutation testing finds issues human reviewers miss

---

**This skill launches the test-quality-reviewer agent which orchestrates the full mutation testing workflow using 4 specialized sub-agents.**
