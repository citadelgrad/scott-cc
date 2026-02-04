# architecture-suite

> Complete feature planning and architecture workflow

## What's Included

### Agents (5)
- **backend-architect** - Design reliable backend systems with data integrity and security focus
- **frontend-architect** - Create accessible, performant UIs with modern frameworks
- **epic-planner** - Plan complete features from concept through implementation-ready tasks
- **feature-builder** - Orchestrate feature development from epic to deployment
- **requirements-analyst** - Transform ambiguous ideas into concrete specifications

## When to Use

**Install this if you**:
- Plan and design new features regularly
- Need architecture guidance for complex systems
- Work on feature roadmaps and epics
- Want structured approach to requirements gathering

**Don't install if you**:
- Only debug existing code (use scott-cc-core)
- Don't plan features systematically

## Workflow

### 1. Requirements → Specification
```
User: "I want to build a notification system"
requirements-analyst: Analyzes requirements, asks clarifying questions
Output: Structured specification document
```

### 2. Specification → Architecture
```
backend-architect: Designs data models, APIs, queues
frontend-architect: Designs UI components, state management
Output: Architecture decision records
```

### 3. Architecture → Epic
```
epic-planner: Breaks down into PRD, SPEC, tasks
Output: Implementation-ready beads tasks
```

### 4. Epic → Feature
```
feature-builder: Orchestrates implementation, quality gates
Output: Deployed feature with validation
```

## Quick Start

```bash
# Start a new feature
Ask: "Plan a user authentication system with OAuth"

# Get architecture guidance
Ask: "Design the backend architecture for real-time notifications"

# Break down an epic
Ask: "Create an epic for payment processing with Stripe"
```

## Recommended Combinations

**Complete feature workflow**:
- architecture-suite ✅
- mutation-testing ✅ (quality assurance)
- process-engine ✅ (workflow tracking)

**Architecture-only**:
- architecture-suite ✅
- scott-cc-core ✅ (for refactoring after architecture)
