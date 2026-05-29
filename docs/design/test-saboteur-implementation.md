# Test Saboteur Agent - Implementation Guide

## Core Mutation Strategies

### 1. Boundary Condition Mutations (Most Effective)

These catch off-by-one errors and boundary bugs:

```python
# Original Code
if retry_count >= 3:
    raise MaxRetriesExceeded()

# Mutations:
# M1: >= → >   (boundary shift)
if retry_count > 3:
    raise MaxRetriesExceeded()

# M2: >= → ==  (exact match only)
if retry_count == 3:
    raise MaxRetriesExceeded()

# M3: >= → <=  (direction flip)
if retry_count <= 3:
    raise MaxRetriesExceeded()
```

**Expected Test Impact**: If your tests only check `retry_count=5`, mutations M1 and M2 will pass (zombie tests!)

### 2. Return Value Mutations

```python
# Original Code
def get_subscription_status(user_id):
    subscription = Subscription.objects.get(user=user_id)
    return subscription.status

# Mutations:
# M1: Return None instead of actual value
def get_subscription_status(user_id):
    subscription = Subscription.objects.get(user=user_id)
    return None

# M2: Return empty/default value
def get_subscription_status(user_id):
    subscription = Subscription.objects.get(user=user_id)
    return ""

# M3: Return wrong enum value
def get_subscription_status(user_id):
    subscription = Subscription.objects.get(user=user_id)
    return SubscriptionStatus.CANCELED  # Instead of actual status
```

**Expected Test Impact**: If tests don't assert the return value, all mutations pass!

### 3. Boolean Logic Mutations

```python
# Original Code
if user.is_active and user.has_subscription:
    send_email(user)

# Mutations:
# M1: and → or
if user.is_active or user.has_subscription:
    send_email(user)

# M2: Negate condition
if not (user.is_active and user.has_subscription):
    send_email(user)

# M3: Remove one condition
if user.is_active:
    send_email(user)
```

### 4. Arithmetic Operator Mutations

```python
# Original Code
discount = base_price * 0.1

# Mutations:
# M1: * → /
discount = base_price / 0.1

# M2: * → +
discount = base_price + 0.1

# M3: * → -
discount = base_price - 0.1
```

### 5. Exception Mutations

```python
# Original Code
if invalid_data:
    raise ValueError("Invalid data")

# Mutations:
# M1: Different exception type
if invalid_data:
    raise TypeError("Invalid data")

# M2: No exception (silent failure)
if invalid_data:
    pass

# M3: Different message (tests might check message)
if invalid_data:
    raise ValueError("Data is invalid")
```

## Implementation Algorithm

### Step 1: Parse and Identify Mutation Points

```python
import ast

def find_mutation_points(source_code):
    tree = ast.parse(source_code)
    mutation_points = []

    for node in ast.walk(tree):
        # Boundary conditions
        if isinstance(node, ast.Compare):
            for op in node.ops:
                if isinstance(op, (ast.Gt, ast.GtE, ast.Lt, ast.LtE)):
                    mutation_points.append({
                        'type': 'boundary',
                        'line': node.lineno,
                        'original_op': type(op).__name__,
                        'mutations': get_boundary_mutations(op)
                    })

        # Boolean operators
        if isinstance(node, ast.BoolOp):
            mutation_points.append({
                'type': 'boolean',
                'line': node.lineno,
                'original_op': type(node.op).__name__,
                'mutations': get_boolean_mutations(node.op)
            })

        # Return statements
        if isinstance(node, ast.Return):
            mutation_points.append({
                'type': 'return',
                'line': node.lineno,
                'mutations': ['None', 'empty_value', 'default']
            })

    return mutation_points
```

### Step 2: Apply Mutations Using Git Worktree

```bash
# Agent workflow for each mutation:

# 1. Create isolated worktree
git worktree add ../test-mutation-001 HEAD

# 2. Apply mutation in worktree
cd ../test-mutation-001
# Edit the file to apply mutation

# 3. Verify it's valid Python (no syntax errors)
python -m py_compile mlb_fantasy_jobs/dunning/stripe_handler.py

# 4. Return to main worktree
cd -

# Result: Mutation ready for testing in ../test-mutation-001
```

### Step 3: Mutation Manifest Generation

The saboteur agent returns structured data:

```json
{
  "mutations": [
    {
      "id": "mut-001",
      "type": "boundary",
      "file": "mlb_fantasy_jobs/dunning/stripe_handler.py",
      "line": 47,
      "column": 12,
      "original": "retry_count >= 3",
      "mutated": "retry_count > 3",
      "worktree": "/Users/scott/projects/test-mutation-001",
      "description": "Changed >= to > to test boundary condition handling",
      "expected_impact": "Tests with retry_count=3 should fail"
    },
    {
      "id": "mut-002",
      "type": "return",
      "file": "mlb_fantasy_jobs/dunning/stripe_handler.py",
      "line": 112,
      "column": 8,
      "original": "return subscription.status",
      "mutated": "return None",
      "worktree": "/Users/scott/projects/test-mutation-002",
      "description": "Return None instead of subscription status",
      "expected_impact": "Tests asserting return value should fail"
    }
  ],
  "total_mutations": 15,
  "files_mutated": ["mlb_fantasy_jobs/dunning/stripe_handler.py"],
  "mutation_strategy": "semantic",
  "worktree_base": "/Users/scott/projects"
}
```

## Agent Prompt (System Message for test-saboteur)

```markdown
You are a Test Saboteur agent specialized in creating semantic code mutations for test quality analysis.

## Your Mission
Create controlled, semantic mutations in source code to test if the test suite catches them. Unlike random fuzzing, your mutations should represent realistic bugs that developers might introduce.

## Mutation Strategies

Apply these mutation types (in priority order):

1. **Boundary Conditions** (highest priority)
   - `>=` → `>`, `<=` → `<`
   - `>` → `>=`, `<` → `<=`
   - Off-by-one errors are extremely common

2. **Return Values**
   - Return `None` instead of actual value
   - Return empty collection instead of populated
   - Return wrong enum value

3. **Boolean Logic**
   - `and` → `or`
   - `True` → `False`
   - Remove conditions entirely

4. **Arithmetic Operators**
   - `+` → `-`, `*` → `/`
   - Only if the operation is business logic (not magic numbers)

5. **Exception Types**
   - `ValueError` → `TypeError`
   - Remove exception entirely (silent failure)

## Workflow

When asked to create mutations:

1. **Read the source file**
   - Use Read tool to get the full file content
   - Identify functions, methods, and logic branches

2. **Identify mutation points**
   - Look for comparisons, return statements, boolean logic
   - Prioritize code that should be tested (not framework boilerplate)
   - Avoid mutating imports, class definitions, or decorators

3. **Create one mutation per worktree**
   - Use Bash tool: `git worktree add ../test-mutation-{id} HEAD`
   - Use Edit tool to apply the mutation in the worktree
   - Verify syntax: `python -m py_compile {file_path}`

4. **Generate mutation manifest**
   - Return structured JSON with all mutation details
   - Include original/mutated code for comparison
   - Describe expected impact on tests

## Example

User: "Create 5 mutations for stripe_handler.py"

You:
1. Read mlb_fantasy_jobs/dunning/stripe_handler.py
2. Identify mutation points:
   - Line 47: `retry_count >= 3` (boundary condition)
   - Line 112: `return subscription.status` (return value)
   - Line 89: `if active and subscribed` (boolean logic)
   - Line 134: `raise ValueError()` (exception type)
   - Line 201: `discount = price * 0.1` (arithmetic)
3. Create 5 worktrees (test-mutation-001 through test-mutation-005)
4. Apply each mutation in its worktree
5. Return mutation manifest JSON

## Important Rules

- **One mutation per worktree** (isolation prevents interference)
- **Semantic mutations only** (no random string changes)
- **Verify syntax** after each mutation (no syntax errors)
- **Track all changes** in the manifest (original → mutated)
- **Clean worktree names** (test-mutation-{id}, no spaces)

## Error Handling

If a mutation creates syntax errors:
- Skip that mutation
- Log the failure in the manifest
- Continue with other mutations

If worktree creation fails:
- Report error to user
- Suggest fallback: sequential mutations in single worktree

## Success Criteria

A good mutation should:
- Represent a realistic bug
- Be syntactically valid
- Have clear expected test impact
- Be isolated in its own worktree

Output the mutation manifest in JSON format for the orchestrator to use.
```

## Example Agent Invocation

From the orchestrator:

```python
from anthropic import Anthropic

client = Anthropic()

response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=16000,
    tools=[...],  # All tools available
    messages=[{
        "role": "user",
        "content": """Create 15 semantic mutations for:
        - File: mlb_fantasy_jobs/dunning/stripe_handler.py
        - Focus on: boundary conditions, return values, boolean logic
        - Use git worktree prefix: test-mutation-
        - Return mutation manifest with locations and types

        Prioritize mutations that would catch the most common bugs."""
    }]
)
```

## Testing the Agent

Create a simple test file:

```python
# test_mutation_target.py
def calculate_discount(price, is_member):
    if price >= 100:
        return price * 0.1 if is_member else price * 0.05
    return 0
```

Ask the saboteur:
"Create 3 mutations for test_mutation_target.py"

Expected mutations:
1. `price >= 100` → `price > 100` (boundary)
2. `return price * 0.1` → `return None` (return value)
3. `if is_member else` → `if not is_member else` (boolean inversion)

Then verify each mutation is in its own worktree and syntactically valid.

## Performance Optimization

- Create worktrees in parallel (up to 10 concurrent)
- Cache AST parsing results
- Reuse mutation strategies across similar code patterns
- Clean up worktrees after test execution completes

## Integration with Test Executor

The saboteur passes this manifest to test-executor:

```python
# Orchestrator launches executor for each mutation
for mutation in mutation_manifest['mutations']:
    Task(
      subagent_type="scott-cc:test-executor",
      description=f"Run tests for {mutation['id']}",
      prompt=f"""
      Run test suite in worktree: {mutation['worktree']}
      Test command: pytest tests/test_stripe_dunning.py -v --tb=short
      Expected failure if tests are good: {mutation['expected_impact']}
      Report: passed count, failed count, specific failures
      """
    )
```

This creates a clean handoff from saboteur → executor → auditor → refactor specialist.
