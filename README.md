# Scott's Claude Code Setup

My personal Claude Code configuration for productive web development. This plugin provides **15 slash commands**, **17 specialized AI agents**, and **3 skills** to supercharge your development workflow.

Copied and enhanced from https://github.com/edmund-io/edmunds-claude-code

## Quick Install

```bash
# Install from the plugins marketplace
/plugin marketplace add citadelgrad/scott-cc
```

Or browse the marketplace at [https://claudecode.dev/plugins](https://claudecode.dev/plugins) to discover this and other plugins.

## What's Inside

### Orchestration

- `/scott-cc:build-feature` - **6-phase feature development workflow** from epic to deployment
  - Phase 1: Epic setup with test requirements audit
  - Phase 2: Architecture review (conditional agent spawning)
  - Phase 3: Implementation via beads task tracking
  - Phase 4: Quality review (DRY/KISS via simplifier skills)
  - Phase 5: Validation (tests, lint, types, security, migrations, docs)
  - Phase 6: Final review and commit
  - **Context management**: Checkpointing, resume support, background agents

### Development Commands (6)

- `/scott-cc:new-task` - Analyze task complexity and create implementation plan
- `/scott-cc:code-explain` - Generate detailed explanations
- `/scott-cc:code-optimize` - Performance optimization
- `/scott-cc:code-cleanup` - Refactoring and cleanup
- `/scott-cc:lint` - Linting and fixes
- `/scott-cc:docs-generate` - Documentation generation

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

### Specialized AI Agents (17)

**Orchestration**
- **feature-builder** - 6-phase development workflow orchestrator using beads
- **epic-planner** - Structured feature planning from concept to implementation-ready tasks

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

### Hooks

- **ghostty-bell** (`Stop` event) - Ghostty terminal tab indicator when Claude finishes responding
  - Adds 🔔 to the Ghostty tab title (clears on focus)
  - Bounces the dock icon
  - Sends a macOS desktop notification with a brief summary of the work done
  - Skips if `stop_hook_active` is true (prevents double-bell)
  - Requires [Ghostty](https://ghostty.org) terminal (v1.2.0+)

#### Ghostty Bell Setup

The hook works out of the box with Ghostty's defaults (`bell-features` includes `title` and `attention`, `desktop-notifications = true`).

To make notifications **persist until clicked** (instead of auto-dismissing):

1. Open **System Settings > Notifications > Ghostty**
2. Set **Alert Style** to **Persistent**

### Reference Documentation

- `docs/MEANINGFUL_TESTS.md` - Test quality guidelines (Pytest/Vitest)
  - Z.O.M. heuristic (Zero, One, Many boundary testing)
  - Error path coverage requirements
  - Negative test case strategy

## Installation

### From Plugins Marketplace (Recommended)

```bash
/plugin marketplace add citadelgrad/scott-cc
```

You can also browse available plugins at [claudecode.dev/plugins](https://claudecode.dev/plugins).

### Update Existing Installation

```bash
/plugin marketplace update scott-cc
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
/build-feature <epic-id> [--resume]
         │
         ▼
┌─────────────────────────────────────┐
│  Phase 1: Epic Setup         [CP]   │
│  - Verify epic structure            │
│  - Test requirements audit          │
│  - Classify critical/important      │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Phase 2: Architecture Review [CP]  │
│  - system-architect (conditional)   │
│  - frontend-architect (conditional) │
│  - backend-architect (conditional)  │
│  - Agents run in background         │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Phase 3: Implementation     [CP]   │
│  - Task-by-task via beads           │
│  - Quality standards enforced       │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Phase 4: Quality Review     [CP]   │
│  - /python-simplifier               │
│  - /typescript-simplifier           │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Phase 5: Validation         [CP]   │
│  - Meaningful tests (Z.O.M.)        │
│  - Lint, types (pyright/tsc)        │
│  - Security (conditional agent)     │
│  - Migrations (alembic)             │
│  - Documentation (conditional)      │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Phase 6: Final Review       [CP]   │
│  - Verify all tasks complete        │
│  - Commit changes                   │
│  - Close epic                       │
└─────────────────────────────────────┘

[CP] = Checkpoint written (enables --resume)
```

## Epic Planner Workflow

The **epic-planner** agent guides features from initial concept through implementation-ready tasks:

```
User describes feature
         │
         ▼
┌─────────────────────────────────────┐
│  Stage 1: Research                  │
│  - Adaptive depth (simple vs deep)  │
│  - Architecture recommendations     │
│  - Technology decisions             │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Stage 2: Research Approval Gate    │
│  - Present findings to user         │
│  - Wait for explicit approval       │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Stage 3: Create PRD Document       │
│  - docs/prd-{feature}.md            │
│  - Goals, user stories, requirements│
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Stage 4: Create SPEC Document      │
│  - docs/spec-{feature}.md           │
│  - Architecture, schemas, APIs      │
│  - Complete code examples           │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Stage 5: Document Approval Gate    │
│  - Review PRD and SPEC              │
│  - Wait for explicit approval       │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Stage 6: Create Beads Epic         │
│  - Link documents to epic           │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Stage 7: Create Granular Tasks     │
│  - Self-contained implementation    │
│  - Full code in task notes          │
│  - Dependencies configured          │
└─────────────────────────────────────┘
```

**Key Features:**
- **Approval gates** - Never proceeds without explicit user approval
- **Adaptive research** - Spawns deep-research-agent for complex features, lightweight for simple ones
- **Self-contained tasks** - Each task includes all implementation details (not just doc references)
- **Beads integration** - Creates epic and linked tasks with proper dependencies

### Context Management

The feature-builder uses several strategies to avoid running out of context:

- **Checkpointing**: State saved after each phase to `.claude/feature-builder/<epic-id>/`
- **Resume support**: `--resume` flag continues from last checkpoint
- **Background agents**: Sub-agents write to files instead of returning full context
- **Conditional spawning**: Agents skipped when not needed (simple epics, no relevant changes)

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

### Plan a New Feature

```bash
# Describe a feature to the epic-planner agent
"I want to build a notification system that sends email and push notifications"

# Epic-planner will:
# 1. Research approaches (adaptive depth)
# 2. Create PRD document (docs/prd-notifications.md)
# 3. Create SPEC document (docs/spec-notifications.md)
# 4. Create beads epic with granular tasks
# All with approval gates before proceeding
```

### Build a Complete Feature

```bash
/build-feature my-epic-123
# Orchestrates architecture review → implementation → validation → commit

# If context runs out, resume from last checkpoint:
/build-feature my-epic-123 --resume
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
