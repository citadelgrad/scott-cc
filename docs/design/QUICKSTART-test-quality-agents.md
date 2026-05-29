# Quick Start: Test Quality Agents

## Step 1: Add Agents to Your Plugin

Find your scott-cc plugin manifest (likely at `~/.claude/plugins/scott-cc/manifest.json` or similar) and add the agents:

```json
{
  "name": "scott-cc",
  "version": "1.0.0",
  "agents": [
    {
      "name": "test-saboteur",
      "description": "Create semantic code mutations for test quality analysis. Use when you need to create code mutations for mutation testing. Examples: 'Create mutations for this function', 'Generate 10 semantic mutations for stripe_handler.py'",
      "tools": ["All tools"]
    },
    {
      "name": "test-executor",
      "description": "Execute test suites against mutated code and collect detailed results. Use when you need to run tests and analyze results against mutated code. Examples: 'Run tests against mutation mut-001', 'Execute pytest and collect coverage'",
      "tools": ["All tools"]
    },
    {
      "name": "test-auditor",
      "description": "Analyze mutation test results to identify low-quality tests. Calculate mutation score, find zombie tests, identify redundant tests. Use when you need to analyze test quality from mutation testing results.",
      "tools": ["All tools"]
    },
    {
      "name": "test-refactor-specialist",
      "description": "Consolidate redundant tests and improve test quality. Convert similar tests to parameterized tests, remove zombie tests, suggest minimal high-quality test sets. Use when you need to refactor tests based on quality analysis.",
      "tools": ["All tools"]
    },
    {
      "name": "test-quality-reviewer",
      "description": "Orchestrate comprehensive mutation testing workflow. Use when the user wants test quality analysis via mutation testing. Examples: 'Audit test quality for my Stripe dunning logic', 'Mutation test this module'",
      "tools": ["All tools"]
    }
  ]
}
```

## Step 2: Reload Plugin

```bash
# Restart Claude Code or reload plugins
claude-code --reload-plugins
```

## Step 3: Test with Simple Example

Create a test target:

```python
# sample.py
def calculate_late_fee(days_overdue):
    if days_overdue >= 30:
        return 50.0
    elif days_overdue >= 7:
        return 10.0
    return 0.0
```

Create a weak test:

```python
# test_sample.py
def test_late_fee():
    assert calculate_late_fee(100) == 50.0
    # This test only checks one case! Mutations will expose this.
```

Ask Claude:

> "Audit the test quality for sample.py using mutation testing"

## Step 4: Expected Workflow

The orchestrator (test-quality-reviewer) will:

1. **Launch test-saboteur**: Creates mutations like:
   - `days_overdue >= 30` → `days_overdue > 30`
   - `return 50.0` → `return None`
   - `elif days_overdue >= 7` → `elif days_overdue > 7`

2. **Launch test-executor** (parallel): Runs `pytest test_sample.py` in each mutation worktree

3. **Launch test-auditor**: Analyzes results:
   ```
   Mutation Score: 33% (1/3 mutations caught)

   Zombie Tests:
   - test_late_fee (passed despite 2 mutations)

   Recommendations:
   - Add test case for days_overdue=30 (boundary)
   - Add test case for days_overdue=7 (boundary)
   - Assert return type is float (catches None mutation)
   ```

4. **Launch test-refactor-specialist**: Proposes:
   ```python
   @pytest.mark.parametrize("days,expected", [
       (0, 0.0),
       (6, 0.0),
       (7, 10.0),   # Boundary
       (29, 10.0),
       (30, 50.0),  # Boundary
       (100, 50.0),
   ])
   def test_late_fee_all_cases(days, expected):
       assert calculate_late_fee(days) == expected
   ```

5. **Generate report**:
   ```markdown
   # Test Quality Audit

   Mutation Score: 33% → 100% (after refactoring)
   Tests: 1 → 1 (but now comprehensive)

   Your test only checked the happy path. I found 2 boundary bugs
   that your test missed. The refactored test covers all branches.
   ```

## Step 5: Use with Real Code

Now try it on your actual code:

> "Audit test quality for mlb_fantasy_jobs/dunning/stripe_handler.py"

The agents will:
- Identify your 200 tests
- Create 15-20 meaningful mutations
- Run all 200 tests against each mutation
- Report which tests are zombies
- Propose consolidation (200 → 20 tests)

## Step 6: Advanced Usage

### Focus on specific mutation types

> "Create only boundary condition mutations for the retry logic in stripe_handler.py"

### Parallel mutation testing

> "Mutation test these 5 files in parallel: [list of files]"

### Integration with beads

```bash
bd create --title="Improve test quality - Stripe dunning" --type=task
```

Then ask Claude:
> "Mutation test stripe_handler.py and track progress in beads"

The orchestrator will update the beads issue with results.

## Troubleshooting

### Issue: "Worktree creation failed"

**Solution**: Check git status. You need a clean working tree.

```bash
git status
git stash  # If you have uncommitted changes
```

### Issue: "Tests won't run in worktree"

**Solution**: Ensure dependencies are installed. The agent will run:

```bash
cd test-mutation-001
pip install -e .  # or npm install
pytest  # Verify tests work
```

### Issue: "Too many mutations"

**Solution**: Limit mutation count:

> "Create only 5 mutations focused on the most critical logic"

### Issue: "Mutation score is 100% but code has bugs"

**Solution**: Your tests might be over-mocked. Ask:

> "Analyze these tests for over-mocking. Are we testing real behavior or just mocks?"

## Performance Tips

1. **Parallel execution**: The orchestrator runs test-executor agents in parallel (one per mutation). For 15 mutations, this is ~15x faster than sequential.

2. **Incremental mutations**: Start small:
   - 5 mutations for quick feedback
   - 15 mutations for thorough analysis
   - 50+ mutations for comprehensive audit

3. **Worktree cleanup**: The orchestrator cleans up worktrees after completion. If it crashes, manually clean:
   ```bash
   git worktree list
   git worktree remove test-mutation-001
   ```

4. **Cache test results**: If you re-run on the same code, the executor can skip tests that haven't changed.

## Integration Examples

### With CI/CD

Add to your GitHub Actions:

```yaml
- name: Mutation Testing
  run: |
    claude-code --prompt "Mutation test src/ and fail if score < 80%"
```

### With Pre-commit Hook

```bash
# .git/hooks/pre-commit
if [[ $(git diff --cached --name-only | grep 'test_.*\.py') ]]; then
  echo "Running mutation testing on changed tests..."
  claude-code --prompt "Quick mutation test for changed test files"
fi
```

### With Beads Workflow

```bash
# Create epic for test quality improvement
bd create --title="Test Quality Initiative" --type=epic

# For each module, create sub-tasks
bd create --title="Mutation test Stripe dunning" --type=task
bd create --title="Mutation test KMS layer" --type=task
bd dep add beads-002 beads-001  # KMS depends on Stripe (learn from it)

# Work through tasks
bd ready  # Find next task
# Ask Claude to mutation test it
bd close beads-001 --reason="Mutation score: 85%, tests: 200→25"
```

## Next Steps

1. **Start small**: Test one file with 5 mutations
2. **Review results**: Understand the zombie test concept
3. **Apply refactoring**: Accept the proposed test consolidation
4. **Scale up**: Apply to entire module
5. **Track progress**: Use beads to track mutation scores over time

## Example Session

```
You: "Audit test quality for sample.py using mutation testing"

Claude: "I'll run mutation testing on sample.py. Creating 5 mutations..."

[Launches test-saboteur]
[Launches 5 test-executor agents in parallel]
[Launches test-auditor]
[Launches test-refactor-specialist]

Claude: "# Test Quality Audit

Mutation Score: 33% (1/3 mutations caught)

Zombie Tests:
- test_late_fee (line 3): Always passes, even with broken code

Proposed Fix:
- Add boundary test cases for days_overdue=7 and days_overdue=30
- Use parameterized test for all branches

Estimated impact: 33% → 100% mutation score

Would you like me to apply the refactoring?"

You: "Yes, apply it"

Claude: [Applies refactoring, runs tests, confirms 100% score]

Claude: "Done! Your test suite now has 100% mutation score.
All branches are covered with meaningful assertions."
```

## Resources

- **Mutation Testing Theory**: https://en.wikipedia.org/wiki/Mutation_testing
- **pytest Parameterization**: https://docs.pytest.org/en/stable/parametrize.html
- **Git Worktree Docs**: https://git-scm.com/docs/git-worktree

## Success Metrics

Track these over time (use beads to record):

- **Mutation Score**: Target >80%
- **Test Count Reduction**: Aim for 50-90% reduction
- **Test Execution Time**: Faster due to fewer tests
- **Bug Escape Rate**: Fewer bugs reach production

Good mutation scores correlate with fewer production bugs!
