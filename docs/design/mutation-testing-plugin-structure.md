# Mutation Testing Plugin - Structure & Invocation Design

## Plugin Architecture

### Marketplace Plugin Structure

```
~/.claude/plugins/marketplaces/scott-cc-marketplace/
└── plugins/
    └── mutation-testing/
        ├── manifest.json          # Plugin definition
        ├── README.md              # User-facing docs
        ├── skills/
        │   └── mutation-test/
        │       ├── SKILL.md       # Slash command skill
        │       └── examples/
        │           └── sample-workflow.md
        └── agents/
            ├── saboteur.md        # Agent-specific docs (optional)
            ├── executor.md
            ├── auditor.md
            ├── refactor.md
            └── orchestrator.md
```

---

## Hybrid Invocation Strategy

### 1. Slash Command (Explicit, Recommended for Power Users)

```json
{
  "name": "mutation-testing",
  "version": "1.0.0",
  "skills": [
    {
      "name": "mutation-test",
      "description": "Run comprehensive mutation testing to audit test quality and identify zombie tests",
      "trigger": "/mutation-test",
      "agent": "mutation-testing:test-quality-reviewer"
    }
  ]
}
```

**Usage**:
```bash
/mutation-test stripe_handler.py
/mutation-test --quick api/payments/  # 5 mutations, fast feedback
/mutation-test --deep billing/        # 50 mutations, exhaustive
```

**When to use**: User knows they want mutation testing specifically.

---

### 2. Auto-Detection Agent (Implicit, Discoverable)

Add the orchestrator agent with **clear, specific trigger patterns**:

```json
{
  "agents": [
    {
      "name": "test-quality-reviewer",
      "description": "Orchestrate comprehensive mutation testing workflow for test quality analysis. Use when the user explicitly requests mutation testing, zombie test detection, or wants to identify weak tests through code mutation.

Examples that SHOULD trigger:
- 'Mutation test this module'
- 'Find zombie tests in my test suite'
- 'Run mutation testing on stripe_handler.py'
- 'Audit test quality using mutation testing'
- 'Which tests don't actually test anything?'

Examples that SHOULD NOT trigger:
- 'Improve test quality' (too vague - could mean refactoring, better assertions, etc.)
- 'My tests are slow' (performance issue, not mutation testing)
- 'Add more tests' (wants new tests, not mutation analysis)

Only invoke this agent when the user's intent is clearly about mutation testing or finding tests that pass despite broken code.",
      "tools": ["All tools"]
    }
  ]
}
```

**Trigger Keywords** (high confidence):
- "mutation test"
- "zombie test"
- "tests that don't test anything"
- "which mutations survive"
- "test coverage is misleading"

**Don't Trigger On** (low confidence):
- "improve test quality" ← Too vague
- "fix failing tests" ← Different problem
- "add test coverage" ← Wants new tests, not mutation analysis

---

## Decision Tree for Claude

When Claude sees a test-related prompt, it should think:

```
User says: "improve test quality"
                ↓
    Does prompt mention mutation/zombie/weak tests?
                ↓
        Yes ─────────────► Use mutation-testing:test-quality-reviewer
                ↓
        No ──► Ask clarifying question:
               "Do you want to:
                1. Find zombie tests via mutation testing (deep analysis)
                2. Refactor existing tests (quick improvements)
                3. Add missing tests (expand coverage)"
```

---

## Recommended Manifest Configuration

### Full Hybrid Approach

```json
{
  "name": "mutation-testing",
  "version": "1.0.0",
  "description": "Mutation testing for identifying zombie tests and improving test quality through automated code mutation analysis",

  "skills": [
    {
      "name": "mutation-test",
      "description": "Run mutation testing workflow to find weak tests",
      "trigger": "/mutation-test",
      "agent": "mutation-testing:test-quality-reviewer",
      "parameters": [
        {
          "name": "target",
          "description": "File or directory to test",
          "required": true
        },
        {
          "name": "mode",
          "description": "quick (5 mutations) | standard (15) | deep (50+)",
          "default": "standard"
        }
      ]
    }
  ],

  "agents": [
    {
      "name": "test-saboteur",
      "description": "Create semantic code mutations for test quality analysis. Internal agent - not directly invoked by users.",
      "tools": ["All tools"]
    },
    {
      "name": "test-executor",
      "description": "Execute test suites against mutated code. Internal agent - not directly invoked by users.",
      "tools": ["All tools"]
    },
    {
      "name": "test-auditor",
      "description": "Analyze mutation test results to identify zombie tests. Internal agent - not directly invoked by users.",
      "tools": ["All tools"]
    },
    {
      "name": "test-refactor-specialist",
      "description": "Consolidate redundant tests based on mutation analysis. Internal agent - not directly invoked by users.",
      "tools": ["All tools"]
    },
    {
      "name": "test-quality-reviewer",
      "description": "Orchestrate mutation testing workflow. Trigger when user explicitly asks for mutation testing, zombie test detection, or wants to identify weak tests through code mutation. Keywords: 'mutation test', 'zombie tests', 'tests that don't test anything', 'which tests are weak'. Do NOT trigger on vague requests like 'improve test quality' - ask for clarification first.",
      "tools": ["All tools"]
    }
  ]
}
```

---

## Best Practice: Explicit > Implicit for Expensive Operations

**Guideline**: Since mutation testing is **resource-intensive** (spawns 15+ agents, creates git worktrees, runs full test suite multiple times), prefer explicit invocation.

### Conservative Auto-Detection

Only auto-trigger when **high confidence** (90%+ sure user wants mutation testing):

```python
# Conceptual confidence scoring
def should_trigger_mutation_testing(prompt):
    high_confidence_keywords = [
        "mutation test",
        "zombie test",
        "mutant surviv",  # "surviving mutants"
        "mutation score",
        "mutation coverage"
    ]

    if any(keyword in prompt.lower() for keyword in high_confidence_keywords):
        return True  # ✅ High confidence

    medium_confidence_keywords = [
        "weak test",
        "test quality audit",
        "tests don't catch bugs"
    ]

    if any(keyword in prompt.lower() for keyword in medium_confidence_keywords):
        # ⚠️ Ask for confirmation
        return ask_user("Did you want mutation testing? (This will create code mutations and run your test suite 15+ times)")

    return False  # ❌ Don't auto-trigger
```

---

## User Experience Comparison

### Scenario: User wants to improve tests

#### Approach 1: Slash Command Only

```
User: "My tests are weak, can you help?"

Claude: "I can help improve your tests. Would you like to:
1. Run mutation testing (/mutation-test) to find zombie tests
2. Refactor existing tests for clarity
3. Add missing test cases"

User: "/mutation-test stripe_handler.py"

Claude: "Running mutation testing..."
```

**Pro**: User is informed before expensive operation
**Con**: Requires extra step

---

#### Approach 2: Auto-Detection (Aggressive)

```
User: "My tests are weak"

Claude: "Running mutation testing to find weak tests..."
[Spawns 15 agents, runs for 3 minutes]

User: "Wait, I just wanted to refactor a few assertions..."
```

**Pro**: Feels magical (when right)
**Con**: Wastes resources (when wrong)

---

#### Approach 3: Hybrid (Recommended)

```
User: "My tests are weak, can you help?"

Claude: "I can help improve your tests. For deep analysis, I can run
mutation testing to identify zombie tests. This will:
- Create 15 code mutations
- Run your test suite 15 times
- Take ~3 minutes

Or I can do lighter refactoring of existing tests.

Which would you prefer?"

User: "Do the mutation testing"

Claude: "Running mutation testing..."
```

**Pro**: Informed consent + discovery
**Con**: None! (slight extra turn)

---

## Implementation: Trigger Pattern Design

### In `test-quality-reviewer` agent description:

```json
{
  "name": "test-quality-reviewer",
  "description": "Mutation testing orchestrator.

  TRIGGER CRITERIA (all must be true):
  1. User mentions testing/test quality
  2. User uses mutation-specific keywords:
     - 'mutation test/testing'
     - 'zombie test'
     - 'weak test detection'
     - 'tests that pass despite bugs'
     - 'mutation score/coverage'

  OR user explicitly invokes via /mutation-test skill.

  DO NOT TRIGGER on generic test improvement requests like:
  - 'improve test quality' (ask for clarification)
  - 'make tests better' (ask for clarification)
  - 'add more tests' (different agent)
  - 'fix failing tests' (debugging, not mutation)

  When uncertain, use AskUserQuestion to clarify intent before launching expensive mutation testing workflow.",

  "tools": ["All tools"]
}
```

---

## Recommended Configuration for Your Plugin

```json
{
  "name": "mutation-testing",
  "version": "1.0.0",

  "skills": [
    {
      "name": "mutation-test",
      "trigger": "/mutation-test",
      "agent": "mutation-testing:test-quality-reviewer",
      "description": "Explicit mutation testing invocation"
    }
  ],

  "agents": [
    {
      "name": "test-quality-reviewer",
      "description": "Auto-triggered mutation testing with conservative keywords",
      "tools": ["All tools"]
    }
  ],

  "settings": {
    "auto_trigger_enabled": true,
    "auto_trigger_confidence_threshold": "high",
    "ask_confirmation_for_expensive_ops": true
  }
}
```

---

## My Recommendation: Start Conservative, Expand Later

### Phase 1: Launch (Slash Command Only)

```json
{
  "skills": [
    {
      "name": "mutation-test",
      "trigger": "/mutation-test"
    }
  ],
  "agents": [
    {
      "name": "test-quality-reviewer",
      "description": "Internal orchestrator - only invoked via /mutation-test skill"
    }
  ]
}
```

**Why**:
- Learn how users actually use it
- Avoid false positives during beta
- Explicit control = better feedback

### Phase 2: Add Auto-Detection (Conservative)

```json
{
  "agents": [
    {
      "name": "test-quality-reviewer",
      "description": "Trigger only on explicit mutation keywords: 'mutation test', 'zombie test'"
    }
  ]
}
```

**Why**:
- High-confidence triggers only
- Monitor for false positives
- Adjust threshold based on usage

### Phase 3: Expand Triggers (Based on Data)

```json
{
  "agents": [
    {
      "name": "test-quality-reviewer",
      "description": "Trigger on mutation keywords + test quality audit requests (with confirmation)"
    }
  ]
}
```

**Why**:
- You now have data on what users actually want
- Can tune trigger patterns based on real usage
- Avoid premature optimization

---

## User Research Questions

Before deciding, consider asking beta users:

1. "Would you expect 'improve test quality' to trigger mutation testing, or something lighter?"
2. "Should mutation testing require explicit invocation (/mutation-test), or auto-detect from prompts?"
3. "If auto-detected, should Claude ask for confirmation before running 15 parallel test executions?"

My bet: **80% will want explicit control** (slash command or very clear keywords).

---

## Final Recommendation

**Use the Hybrid Approach with Conservative Auto-Detection**:

1. **Primary**: Slash command `/mutation-test` (always works, clear intent)
2. **Secondary**: Auto-trigger ONLY on high-confidence keywords:
   - "mutation test"
   - "zombie test"
   - "mutation score"
3. **Safety**: Always confirm before expensive operations if triggered by ambiguous prompt
4. **Fallback**: If unsure, ask: "Did you want mutation testing (deep) or test refactoring (light)?"

This gives you:
- ✅ Explicit control for power users
- ✅ Discovery for new users (via high-confidence keywords)
- ✅ Safety (confirmation for expensive ops)
- ✅ Flexibility (can tune triggers based on real usage)

Would you like me to create the full plugin manifest with this hybrid approach?
