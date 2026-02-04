# Mutation Testing Plugin

> Comprehensive test quality auditing through semantic code mutations and parallel test execution

## What This Plugin Does

Measures **actual** test quality (not just coverage) by:
1. Creating realistic code mutations (introducing bugs)
2. Running your test suite against each mutation in parallel
3. Identifying which tests caught the bugs vs which didn't (zombie tests)
4. Auto-generating refactored test suites with consolidated, high-quality tests

## Quick Start

```bash
/mutation-test stripe_handler.py              # Standard mode (15 mutations)
/mutation-test --quick api/payments/          # Quick mode (5 mutations)
/mutation-test --deep billing/                # Deep mode (30+ mutations)
/mutation-test                                # Smart mode (auto-detects target)
```

## What You Get

### Input
```bash
/mutation-test stripe_handler.py
```

### Output (3-5 minutes)
```
# Test Quality Audit Report

Mutation Score: 23% → 85% (estimated after refactoring)
Quality Rating: Poor → Excellent

Critical Findings:
- 183/200 tests are zombies (never failed despite broken code)
- 150 tests validate same Django model (redundant)

Proposed Refactoring:
Before: 200 tests, 23% score, 12s execution time
After:  20 tests, 85% score, 1.5s execution time (8x faster)

Changes:
✂️  Remove 183 zombie tests
🔄 Consolidate 150 → 1 parameterized test
✅ Add 3 boundary condition tests

Would you like me to apply this refactoring?
```

## Why Use This?

**Traditional test coverage is misleading:**
- 100% line coverage ≠ good tests
- Tests can run without validating anything
- No insight into which tests provide value

**Mutation testing is truth:**
- Creates realistic bugs developers might introduce
- Measures which bugs your tests actually catch
- Identifies tests that provide no value (zombies)
- Auto-generates improvements

## 5 Specialized Agents

1. **test-quality-reviewer** - Orchestrates the full workflow
2. **test-saboteur** - Creates semantic mutations in git worktrees
3. **test-executor** (×15 parallel) - Runs tests against each mutation
4. **test-auditor** - Calculates mutation score, finds zombies
5. **test-refactor-specialist** - Generates production-ready refactored code

## Key Features

### 🚀 Parallel Execution
- Runs 15 test suites simultaneously (15x speedup)
- Uses git worktrees for isolation (no race conditions)
- ~3-5 minutes vs hours with traditional tools

### 🧠 Context-Aware Mutations
- LLM identifies business logic (not framework boilerplate)
- Semantic mutations (realistic bugs, not random changes)
- Focuses on boundary conditions, return values, boolean logic

### 🔧 Automated Refactoring
- Consolidates redundant tests into parameterized tests
- Removes zombie tests (with your approval)
- Generates production-ready code (not just suggestions)

### 📊 Comprehensive Analysis
- Mutation score calculation (target: >80%)
- Zombie test identification with line numbers
- Redundancy pattern detection
- Over-mocking detection

## Comparison with Existing Tools

| Feature | mutmut | Stryker | This Plugin |
|---------|--------|---------|-------------|
| Mutation score | ✅ | ✅ | ✅ |
| Time to result | 2-6 hours | 2-6 hours | **3-5 minutes** |
| Actionable output | "Score: 23%" | "Score: 23%" | **"Here's the refactored code"** |
| Zombie detection | Implicit | Implicit | **Explicit with line numbers** |
| Test refactoring | ❌ | ❌ | ✅ **Auto-generated** |
| Parallelization | Limited | Limited | **15x with git worktrees** |
| Conversational | ❌ | ❌ | ✅ **Natural language** |

## Installation

This plugin is available in the scott-cc marketplace:

1. Open Claude Code
2. Go to Plugins → Marketplaces → scott-cc
3. Find "mutation-testing" in the list
4. Click to install

## Usage Examples

### Find Zombie Tests
```bash
/mutation-test stripe_handler.py
```

### Quick Pre-Commit Check
```bash
/mutation-test --quick payments.py
```

### Deep Audit Before Release
```bash
/mutation-test --deep billing/
```

### Smart Auto-Detection
```bash
# After discussing a file in conversation:
/mutation-test
# Agent: "I'll test stripe_handler.py (from our discussion)"
```

## Mutation Strategies

### 1. Boundary Conditions (Highest Priority)
```python
if retry_count >= 3:  →  if retry_count > 3:
```
Catches off-by-one errors (most common bug type)

### 2. Return Values
```python
return subscription.status  →  return None
```
Tests if callers validate return values

### 3. Boolean Logic
```python
if active and subscribed:  →  if active or subscribed:
```
Tests logical correctness

### 4. Arithmetic Operators
```python
discount = price * 0.1  →  discount = price / 0.1
```
Tests calculation logic

### 5. Exception Types
```python
raise ValueError()  →  raise TypeError()
```
Tests exception handling

## Real-World Impact

### Before
```python
# 150 nearly identical tests
def test_status_is_active():
    assert model.status == "active"

def test_status_is_canceled():
    assert model.status == "canceled"

# ... 148 more ...
```

### After
```python
# 1 parameterized test
@pytest.mark.parametrize("status", [
    "active", "canceled", "trialing", ...  # 150 cases
])
def test_subscription_status_validation(status):
    assert model.status == status
```

**Result**: 150 tests → 1 test, same coverage, 99% less code

## Safety Features

- ✅ Git worktrees (mutations isolated, main tree untouched)
- ✅ User approval before deleting tests
- ✅ Full diff before applying refactoring
- ✅ Rollback instructions provided
- ✅ Verification step (re-runs tests after changes)

## Performance

- **Quick mode** (5 mutations): ~1-2 minutes
- **Standard mode** (15 mutations): ~3-5 minutes
- **Deep mode** (30+ mutations): ~10-15 minutes

## Integration with Beads

```bash
# Create tracking issue
bd create --title="Improve test quality - Stripe" --type=task

# Run mutation testing (auto-updates beads issue)
/mutation-test stripe_handler.py

# Issue updated with metrics
bd close beads-xxx
```

## Documentation

See [MUTATION-TESTING.md](docs/MUTATION-TESTING.md) for comprehensive documentation.

## Success Metrics

Track these over time:
- **Mutation Score**: Target >80%
- **Test Count Reduction**: Aim for 50-90%
- **Test Execution Time**: Faster due to fewer tests
- **Bug Escape Rate**: Fewer bugs reach production

## FAQ

**Q: Will this modify my code?**
A: No. Mutations are in isolated git worktrees. Main working tree never touched.

**Q: How long does it take?**
A: 3-5 minutes for standard mode (15 mutations). Quick mode available (~1-2 min).

**Q: What if I disagree with the refactoring?**
A: You review and approve all changes. Full diff provided. You have final say.

**Q: Can I run this in CI?**
A: Yes, but start with manual workflow. CI integration can be added later.

## License

MIT

## Author

Scott Nixon

## Citation

This mutation testing system is inspired by:
- Academic mutation testing research (1980s-1990s)
- Modern tools: mutmut (Python), Stryker (JavaScript), PITest (Java)
- Agent collaboration patterns from LangGraph/CrewAI
- Git worktree isolation technique from Google's Bazel

**Novel contribution**: First mutation testing tool with automated test refactoring and conversational interface.
