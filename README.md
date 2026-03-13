# Scott's Claude Code Setup

Modular Claude Code plugin suite for productive development. The core plugin provides **9 slash commands**, **8 specialized AI agents**, and **4 skills**. Specialized sub-plugins add beads epic workflows, browser automation, mutation testing, and more.

## Quick Install

```bash
# Install from the plugins marketplace
/plugin marketplace add citadelgrad/scott-cc
```

Or browse the marketplace at [https://claudecode.dev/plugins](https://claudecode.dev/plugins) to discover this and other plugins.

## What's Inside

### Development Commands (9)

- `/scott-cc:new-task` - Analyze task complexity and create implementation plan
- `/scott-cc:code-explain` - Generate detailed explanations
- `/scott-cc:code-optimize` - Performance optimization
- `/scott-cc:code-cleanup` - Refactoring and cleanup
- `/scott-cc:lint` - Linting and fixes
- `/scott-cc:docs-generate` - Documentation generation
- `/scott-cc:component-new` - Create React components
- `/scott-cc:page-new` - Create Next.js pages
- `/scott-cc:security-cheatsheet` - Comprehensive security reference

### Specialized AI Agents (8)

- **api-debugger** - Full-stack API debugging with browser integration
- **backend-architect** - Backend systems with data integrity & security
- **deep-research-agent** - Comprehensive research with adaptive strategies
- **emergent-behavior** - Analyze systems for emergent properties
- **frontend-architect** - Performant, accessible UI architecture
- **refactoring-expert** - Systematic refactoring and clean code
- **requirements-analyst** - Transform ideas into concrete specifications
- **system-architect** - Scalable system architecture design

### Skills (4)

- **python-simplifier** - DRY/KISS code quality standards for Python
- **typescript-simplifier** - DRY/KISS code quality standards for TypeScript/JavaScript
- **context7** - Fetch up-to-date documentation for any library
- **context-file-optimizer** - Audit and rewrite AI agent context files (AGENTS.md, CLAUDE.md)

### Hooks

- **ghostty-bell** (`Stop` event) - Ghostty terminal tab indicator when Claude finishes responding
  - Adds bell to the Ghostty tab title (clears on focus)
  - Bounces the dock icon
  - Sends a macOS desktop notification with a brief summary of the work done
  - Requires [Ghostty](https://ghostty.org) terminal (v1.2.0+)

### Specialized Plugins

Install these sub-plugins from the marketplace for additional capabilities:

- **beads-epic-builder** - Plan, build, and swarm beads epics (2 agents, 2 commands)
- **browser-automation** - Browser testing & validation (2 agents, 2 skills)
- **research-tools** - Learning guides, tech stack research, technical writing (3 agents, 1 skill)
- **security-suite** - Security advisory and vulnerability scanning (2 agents)
- **performance-optimization** - Performance engineering and profiling (1 agent)
- **mutation-testing** - Comprehensive mutation testing suite (5 agents, 1 skill)

## Beads Epic Builder

The `beads-epic-builder` plugin provides three ways to work with beads epics:

### 1. Plan an Epic

The **epic-planner** agent guides features from concept to implementation-ready tasks:

```
User describes feature
         |
         v
   Research (adaptive depth)
         |
         v
   Research Approval Gate
         |
         v
   Create PRD Document
         |
         v
   Create SPEC Document
         |
         v
   Document Approval Gate
         |
         v
   Create Beads Epic + Tasks
```

### 2. Build Sequentially: `/build-feature <epic-id>`

The **feature-builder** agent implements tasks one at a time through 6 phases:

```
/build-feature <epic-id> [--resume]
         |
         v
  Phase 1: Epic Setup (verify, test requirements audit)
  Phase 2: Architecture Review (conditional agent spawning)
  Phase 3: Implementation (task-by-task via beads)
  Phase 4: Quality Review (DRY/KISS via simplifier skills)
  Phase 5: Validation (tests, lint, types, security)
  Phase 6: Final Review (commit, close epic)

Each phase writes a checkpoint for --resume support.
```

### 3. Build in Parallel: `/epic-swarm <epic-id>`

Spawns parallel worker agents in isolated git worktrees:

```
/epic-swarm <epic-id> [--max-parallel 3] [--no-review] [--dry-run]
         |
         v
  Phase 1: Load epic, build dependency-aware wave plan
  Phase 2: Execute waves (parallel workers in worktrees)
           - Wave 1: independent tasks run simultaneously
           - Wave 2: tasks depending on Wave 1
           - Wave N: continue until done
           - Merge branches, run tests, close tasks after each wave
  Phase 3: CE code review (architecture, simplicity, security, performance)
  Phase 4: Ship (commit, push)

Checkpointing after every wave survives context compaction.
```

**Key differences from CE's `/ce:work` swarm mode:**
- Workers are explicitly implementers, not researchers
- Beads-native (reads tasks from `bd show`, not a plan file)
- Worktree isolation prevents file conflicts between parallel agents
- Dependency-aware waves respect beads task ordering

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

## Installation

### From Plugins Marketplace (Recommended)

```bash
/plugin marketplace add citadelgrad/scott-cc
```

### Update Existing Installation

```bash
/plugin marketplace update scott-cc
```

### From Local Clone (for development)

```bash
git clone https://github.com/citadelgrad/scott-cc.git
cd scott-cc
/plugin install /path/to/scott-cc
```

### Reference Documentation

- `docs/MEANINGFUL_TESTS.md` - Test quality guidelines (Pytest/Vitest)

## Requirements

- Claude Code CLI
- Works with any project (optimized for Next.js, FastAPI, TypeScript)
- Beads plugin recommended for epic workflows

## License

MIT - Use freely in your projects
