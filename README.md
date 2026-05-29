# Scott's Claude Code Setup

Modular Claude Code plugin suite for productive development. The core plugin provides **2 slash commands**, **8 specialized AI agents**, **9 skills**, **2 hooks**, and **3 project templates**. Specialized sub-plugins add beads epic workflows, browser automation, mutation testing, and more.

## Quick Install

```bash
/plugin marketplace add citadelgrad/scott-cc
```

## What's Inside — At a Glance

| Type | Count | Names |
|------|------:|-------|
| Commands | 2 | `security-cheatsheet`, `gha` |
| Agents | 8 | `api-debugger`, `backend-architect`, `deep-research-agent`, `emergent-behavior`, `frontend-architect`, `refactoring-expert`, `requirements-analyst`, `system-architect` |
| Skills | 9 | `init`, `python-simplifier`, `typescript-simplifier`, `context7`, `context-file-optimizer`, `karpathy-guidelines`, `property-based-testing`, `writing-about-engineering`, `writing-skills-excellence` |
| Hooks | 2 | `terminal-bell` (Stop), `toon-post-hook` (PostToolUse) |
| Templates | 3 | `.pre-commit-config.yaml`, `CLAUDE.md`, `AGENTS.md` |
| Sub-plugins | 6 | `beads-epic-builder`, `browser-automation`, `research-tools`, `security-suite`, `performance-optimization`, `mutation-testing` |

---

## Commands (2)

- `/scott-cc:security-cheatsheet` — Comprehensive security reference for common vulnerabilities and mitigations
- `/scott-cc:gha` — Debug failing GitHub Actions runs and audit workflow YAML

## Agents (8)

- **api-debugger** — Full-stack API debugging with browser integration
- **backend-architect** — Backend systems with data integrity & security focus
- **deep-research-agent** — Comprehensive research with adaptive exploration strategies
- **emergent-behavior** — Analyze systems for emergent and non-obvious properties
- **frontend-architect** — Performant, accessible UI architecture
- **refactoring-expert** — Systematic refactoring and clean code principles
- **requirements-analyst** — Transform ambiguous ideas into concrete specifications
- **system-architect** — Scalable system architecture and long-term technical decisions

## Skills (9)

- **init** — Interactive project scaffolding: beads, CLAUDE.md, AGENTS.md symlink, .envrc, Makefile, pre-commit hooks (all optional)
- **python-simplifier** — DRY/KISS code quality review for Python
- **typescript-simplifier** — DRY/KISS code quality review for TypeScript/JavaScript
- **context7** — Fetch up-to-date documentation for any library or framework
- **context-file-optimizer** — Audit and rewrite AI agent context files (AGENTS.md, CLAUDE.md)
- **karpathy-guidelines** — Behavioral guidelines to reduce common LLM coding mistakes
- **property-based-testing** — Property-based testing for serialization, algorithms, and API contracts
- **writing-about-engineering** — First-person engineering writing (blog posts, postmortems, threads)
- **writing-skills-excellence** — Framework for creating and improving agent skills

## Hooks (2)

- **terminal-bell** (`Stop`) — Terminal tab indicator when Claude finishes responding. Sends BEL character for tab/dock notification, desktop notification with a brief summary, and supports Ghostty/iTerm2 (OSC 9) and WezTerm (OSC 777).

- **toon-post-hook** (`PostToolUse`) — Encodes large tool responses to TOON format (a compact alternative to JSON) before they enter the context window. Reduces token consumption on verbose MCP and built-in tool outputs. No-op if `toon` is not installed.

## Templates (3)

Stored in `templates/` — copy to your project or use the `/init` skill to deploy them.

- **`.pre-commit-config.yaml`** — Canonical pre-commit hooks: general hygiene (trailing whitespace, file checks), Python (ruff lint+format, ty type check), TypeScript/JS (biome lint+format), security (gitleaks secret scanning)
- **`CLAUDE.md`** — Global Claude Code instructions template (CLI tool preferences, direnv/Makefile/port conventions, uv-only Python, diagram standards, TLDR MCP usage)
- **`AGENTS.md`** — Global Codex/agent instructions template (project conventions, code style, git workflow)

## Sub-plugins (6)

Install these from the marketplace for additional capabilities:

```bash
/plugin marketplace add citadelgrad/scott-cc/<name>
```

| Plugin | Agents | Commands | Skills | Description |
|--------|-------:|--------:|-------:|-------------|
| `beads-epic-builder` | 2 | 2 | — | Plan, build, and swarm beads epics |
| `browser-automation` | 2 | — | 2 | Browser testing & E2E validation |
| `research-tools` | 3 | — | 1 | Learning guides, tech stack research, technical writing |
| `security-suite` | 2 | — | — | Security advisory and vulnerability scanning |
| `performance-optimization` | 1 | — | — | Performance engineering and profiling |
| `mutation-testing` | 5 | — | 1 | Comprehensive mutation testing suite |

---

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

---

## Code Quality Standards

All code follows these principles (enforced by simplifier skills):

- **DRY** — Remove duplicate code
- **KISS** — Straightforward over clever
- **Thin Handlers** — Business logic in services
- **No Hardcoded Values** — Use config/env
- **No Silent Failures** — Fail fast, specific exceptions
- **Function Size** — ~20 lines max
- **No Premature Abstraction** — Wait for 3+ patterns

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
/plugin install /path/to/scott-cc
```

## Reference Documentation

- `docs/setup-architecture.md` — Full system architecture with C4 diagrams, bootstrap and project-init sequences, configuration reference
- `docs/MEANINGFUL_TESTS.md` — Test quality guidelines (Pytest/Vitest)

## Requirements

- Claude Code CLI
- Works with any project (optimized for Next.js, FastAPI, TypeScript)
- Beads plugin recommended for epic workflows

## License

MIT — Use freely in your projects
