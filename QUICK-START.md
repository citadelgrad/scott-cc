# Quick Start

## Install

```bash
/plugin marketplace add citadelgrad/scott-cc
```

## What You Get

**Core Plugin (scott-cc)**
- 9 slash commands (new-task, code-cleanup, code-optimize, code-explain, lint, docs-generate, component-new, page-new, security-cheatsheet)
- 8 AI agents (api-debugger, backend-architect, deep-research-agent, emergent-behavior, frontend-architect, refactoring-expert, requirements-analyst, system-architect)
- 4 skills (python-simplifier, typescript-simplifier, context7, context-file-optimizer)

**Sub-Plugins**
- beads-epic-builder - Plan, build, and swarm beads epics (2 agents, 2 commands)
- browser-automation - Browser testing & validation (2 agents, 2 skills)
- research-tools - Learning guides, tech stack research (3 agents, 1 skill)
- security-suite - Security advisory and scanning (2 agents)
- performance-optimization - Performance engineering (1 agent)
- mutation-testing - Mutation testing suite (5 agents, 1 skill)

## Usage

```bash
# Plan a feature into a beads epic
# Just describe what you want to build - epic-planner agent activates automatically

# Build an epic sequentially
/build-feature <epic-id>

# Build an epic with parallel workers
/epic-swarm <epic-id>

# Code quality
/python-simplifier
/typescript-simplifier
```

## Links

- GitHub: https://github.com/citadelgrad/scott-cc
- README: Full documentation
- PUBLISHING.md: How to publish updates
