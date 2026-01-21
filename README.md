# Scott's Claude Code Setup

My personal Claude Code configuration for productive web development. This plugin provides **19 slash commands**, **16 specialized AI agents**, and **3 skills** to supercharge your development workflow.

Copied and enhanced from https://github.com/edmund-io/edmunds-claude-code

## Quick Install

```bash
# Install the plugin
/plugin install citadelgrad/scott-cc
```

## What's Inside

### Orchestration

- `/scott-cc:build-feature` - **6-phase feature development workflow** from epic to deployment
  - Phase 1: Epic setup with test requirements audit
  - Phase 2: Architecture review (spawns system/frontend/backend architects)
  - Phase 3: Implementation via beads task tracking
  - Phase 4: Quality review (DRY/KISS via simplifier skills)
  - Phase 5: Validation (tests, lint, types, security, migrations, docs)
  - Phase 6: Final review and commit

### Development Commands (7)

- `/scott-cc:new-task` - Analyze task complexity and create implementation plan
- `/scott-cc:code-explain` - Generate detailed explanations
- `/scott-cc:code-optimize` - Performance optimization
- `/scott-cc:code-cleanup` - Refactoring and cleanup
- `/scott-cc:feature-plan` - Feature implementation planning
- `/scott-cc:lint` - Linting and fixes
- `/scott-cc:docs-generate` - Documentation generation

### API Commands (3)

- `/scott-cc:api-new` - Create new API endpoints
- `/scott-cc:api-test` - Test API endpoints
- `/scott-cc:api-protect` - Add protection & validation

### UI Commands (2)

- `/scott-cc:component-new` - Create React components
- `/scott-cc:page-new` - Create Next.js pages

### Security Commands (1)

- `/scott-cc:security-cheatsheet` - Comprehensive security reference

### Process Engine Commands (5)

- `/scott-cc:process-start` - Start 5-phase validation for a beads epic
- `/scott-cc:process-status` - Check process status
- `/scott-cc:process-approve` - Approve architecture gate
- `/scott-cc:process-list` - List running processes
- `/scott-cc:process-retry` - Retry failed processes

### Specialized AI Agents (16)

**Orchestration**
- **feature-builder** - 6-phase development workflow orchestrator using beads

**Architecture & Planning**
- **tech-stack-researcher** - Technology choice recommendations with trade-offs
- **system-architect** - Scalable system architecture design
- **backend-architect** - Backend systems with data integrity & security
- **frontend-architect** - Performant, accessible UI architecture
- **requirements-analyst** - Transform ideas into concrete specifications

**Code Quality & Performance**
- **refactoring-expert** - Systematic refactoring and clean code
- **performance-engineer** - Measurement-driven optimization
- **security-engineer** - Vulnerability identification and security standards
- **security-advisor** - Security guidance and best practices

**Testing & Validation**
- **api-debugger** - Full-stack API debugging with browser integration
- **browser-validator** - UI validation via Playwright MCP
- **process-monitor** - Track Process Engine execution and gates

**Documentation & Research**
- **technical-writer** - Clear, comprehensive documentation
- **learning-guide** - Teaching programming concepts progressively
- **deep-research-agent** - Comprehensive research with adaptive strategies

### Skills (3)

- **python-simplifier** - DRY/KISS code quality standards for Python
- **typescript-simplifier** - DRY/KISS code quality standards for TypeScript/JavaScript
- **context7** - Fetch up-to-date documentation for any library

### Reference Documentation

- `docs/MEANINGFUL_TESTS.md` - Test quality guidelines (Pytest/Vitest)
  - Z.O.M. heuristic (Zero, One, Many boundary testing)
  - Error path coverage requirements
  - Negative test case strategy

## Installation

### From GitHub (Recommended)

```bash
/plugin install citadelgrad/scott-cc
```

### Update Existing Installation

```bash
/plugin update scott-cc
```

### From Local Clone (for development)

```bash
git clone https://github.com/citadelgrad/scott-cc.git
cd scott-cc

# Install from local path
/plugin install /path/to/scott-cc
```

## Feature Builder Workflow

The `/build-feature` command orchestrates complete feature development:

```
/build-feature <epic-id>
         │
         ▼
┌─────────────────────────────────────┐
│  Phase 1: Epic Setup                │
│  - Verify epic structure            │
│  - Test requirements audit          │
│  - Classify critical/important      │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Phase 2: Architecture Review       │
│  - system-architect (always)        │
│  - frontend-architect (if needed)   │
│  - backend-architect (if needed)    │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Phase 3: Implementation            │
│  - Task-by-task via beads           │
│  - Quality standards enforced       │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Phase 4: Quality Review            │
│  - /python-simplifier               │
│  - /typescript-simplifier           │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Phase 5: Validation                │
│  - Meaningful tests (Z.O.M.)        │
│  - Lint, types (pyright/tsc)        │
│  - Security (bandit + agent)        │
│  - Migrations (alembic)             │
│  - Documentation (technical-writer) │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Phase 6: Final Review              │
│  - Verify all tasks complete        │
│  - Commit changes                   │
│  - Close epic                       │
└─────────────────────────────────────┘
```

## Code Quality Standards

All code follows these principles (enforced by simplifier skills):

- **DRY** - Remove duplicate code
- **KISS** - Straightforward over clever
- **Thin Handlers** - Business logic in services
- **No Hardcoded Values** - Use config/env
- **No Silent Failures** - Fail fast, specific exceptions
- **Function Size** - ~20 lines max
- **No Premature Abstraction** - Wait for 3+ patterns

## Best For

- Full-stack engineers
- Next.js / React developers
- Python (FastAPI, Django) developers
- TypeScript projects
- Teams using beads for task tracking

## Usage Examples

### Build a Complete Feature

```bash
/build-feature my-epic-123
# Orchestrates architecture review → implementation → validation → commit
```

### Planning a Feature

```bash
/scott-cc:feature-plan
# Then describe your feature idea
```

### Creating an API

```bash
/scott-cc:api-new
# Scaffolds complete API route with types, validation, error handling
```

### Code Quality Review

```bash
/python-simplifier
# or
/typescript-simplifier
# Reviews code for DRY/KISS violations
```

## Requirements

- Claude Code CLI
- Works with any project (optimized for Next.js, FastAPI, TypeScript)
- Beads plugin recommended for `/build-feature` workflow

## Customization

After installation, customize by editing files in:
- `commands/` - Slash commands
- `agents/` - AI agent personas
- `skills/` - Reusable skill definitions
- `docs/` - Reference documentation

## Contributing

Feel free to:
- Fork and customize for your needs
- Submit issues or suggestions
- Share your improvements

## License

MIT - Use freely in your projects

---

**Note**: This is my personal setup refined over time. Commands are optimized for modern full-stack workflows but work great with any web stack.
