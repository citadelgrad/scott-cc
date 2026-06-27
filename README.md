# Scott's Claude Code Setup

Modular Claude Code plugin suite for productive development. The core plugin provides **4 slash commands**, **8 specialized AI agents**, **17 skills**, **3 hooks**, and **3 project templates**. Specialized sub-plugins add beads epic workflows, browser automation, mutation testing, and more.

## Quick Install

```bash
/plugin marketplace add citadelgrad/scott-cc
```

## At a Glance

| Type | Count | Names |
|------|------:|-------|
| Commands | 4 | `delegate-first`, `gha`, `handoff`, `security-cheatsheet` |
| Agents | 8 | `api-debugger`, `backend-architect`, `deep-research-agent`, `find-emergent-behavior`, `frontend-architect`, `refactoring-expert`, `requirements-analyst`, `system-architect` |
| Skills | 17 | `init`, `acceptance-criteria`, `cli-design`, `delegate-first`, `python-simplifier`, `typescript-simplifier`, `karpathy-guidelines`, `property-based-testing`, `verified-implementation`, `context7`, `context-file-optimizer`, `c4-diagram`, `writing-about-engineering`, `writing-skills-excellence`, `pas-pipeline`, `reck-factory`, `thinking-in-systems` |
| Hooks | 3 | `terminal-bell` (Stop), `toon-post-hook` (PostToolUse), `prefer-modern-tools` (PreToolUse) |
| Templates | 3 | `.pre-commit-config.yaml`, `CLAUDE.md`, `AGENTS.md` |
| Sub-plugins | 6 | `beads-epic-builder`, `browser-automation`, `research-tools`, `security-suite`, `performance-optimization`, `mutation-testing` |

---

## Commands (4)

| Command | Description |
|---------|-------------|
| `/scott-cc:delegate-first` | Keep the main conversation clean by forking implementation work to sub-agents. |
| `/scott-cc:gha` | Debug failing GitHub Actions runs and audit workflow YAML. Fetches logs via `gh` CLI, analyzes errors, suggests fixes. |
| `/scott-cc:handoff` | Generate a compact session handoff with git state, active work, key files, and concrete next actions. |
| `/scott-cc:security-cheatsheet` | Look up OWASP security cheatsheets by topic. Comprehensive security reference for common vulnerabilities and mitigations. |

---

## Agents (8)

### Engineering

| Agent | Description |
|-------|-------------|
| `backend-architect` | Design reliable backend systems with focus on data integrity, security, and fault tolerance. |
| `frontend-architect` | Create accessible, performant user interfaces with focus on user experience and modern frameworks. |
| `system-architect` | Design scalable system architecture with focus on maintainability and long-term technical decisions. |

### Analysis

| Agent | Description |
|-------|-------------|
| `deep-research-agent` | Specialist for comprehensive research with adaptive strategies and intelligent exploration. |
| `requirements-analyst` | Transform ambiguous project ideas into concrete specifications through systematic requirements discovery and structured analysis. |
| `find-emergent-behavior` | Analyze codebases, documents, or systems to identify instances of emergence — behaviors, properties, or functions that arise from component interaction rather than being explicitly hard-coded. |

### Debugging & Quality

| Agent | Description |
|-------|-------------|
| `api-debugger` | Expert debugger for APIs, Python backends, and JavaScript/TypeScript frontends with integrated browser testing via Playwright MCP. |
| `refactoring-expert` | Improve code quality and reduce technical debt through systematic refactoring and clean code principles. |

---

## Skills (17)

### Project Setup

| Skill | Description |
|-------|-------------|
| `init` | Interactive project scaffolding. Detects what already exists, presents a menu, and sets up only what you select: beads (`bd init`), `CLAUDE.md`, `AGENTS.md` symlink, `.envrc`, `Makefile`, and pre-commit hooks. |
| `acceptance-criteria` | Generate testable acceptance criteria before creating beads issues or planning implementation work. |

### Code Quality

| Skill | Description |
|-------|-------------|
| `python-simplifier` | Simplifies and refines Python code for clarity, consistency, and maintainability. Applies KISS principles, Pythonic patterns, and framework best practices. Use when reviewing or refactoring Python code. |
| `typescript-simplifier` | Simplifies and refines TypeScript/JavaScript code for clarity, consistency, and maintainability. Applies KISS principles, modern ES features, and framework best practices. Use when reviewing or refactoring TS/JS code. |
| `cli-design` | Design patterns and conventions for building agent-compatible CLI tools. Covers flag design, output formatting, exit codes, and composability with AI-driven workflows. |
| `delegate-first` | Keep the parent conversation clean by forking noisy implementation, validation, and multi-file work to sub-agents. |
| `karpathy-guidelines` | Behavioral guidelines to reduce common LLM coding mistakes. Helps avoid overcomplication, make surgical changes, surface assumptions, and define verifiable success criteria. |
| `property-based-testing` | Use when implementing serialization/parsing, data transformations, algorithms with mathematical properties, API contracts, or state machines where testing all edge cases is impractical. Describe invariants instead of specific input/output pairs. |
| `verified-implementation` | Require authoritative sources for security-critical, financial, protocol, and production-ready implementation decisions. |

### Documentation & AI Context

| Skill | Description |
|-------|-------------|
| `context7` | Retrieve up-to-date documentation for any software library or framework via the Context7 API. Use instead of relying on potentially outdated training data. |
| `context-file-optimizer` | Audit and rewrite `AGENTS.md`, `CLAUDE.md`, and other AI agent context files to be minimal and effective. Based on research-backed principles: verbose context files hurt performance (−2 to −3%) while minimal, tooling-focused files improve it (+4%). |
| `c4-diagram` | Generate C4 architecture diagrams using standard Mermaid `flowchart` syntax. Covers Context, Container, and Component levels with short labels, companion legend tables, and sequence diagrams for runtime behavior. Never uses the broken C4 Mermaid plugin. |

### Writing

| Skill | Description |
|-------|-------------|
| `writing-about-engineering` | Use when drafting first-person engineering writing — blog posts, short posts/threads, or postmortems. Produces a conversational-but-rigorous, peer-to-peer voice anchored on the Julia Evans / Simon Willison TIL/blog rhythm. |
| `writing-skills-excellence` | Framework for creating, updating, or improving agent skills. Covers structure, frontmatter, when-to-use clauses, and quality principles. |

### Automation & Pipelines

| Skill | Description |
|-------|-------------|
| `pas-pipeline` | Run, validate, and manage PAS (Pascal's Discrete Attractor) DOT-based AI pipelines. Covers `pas launch`, `pas run`, budget/step caps, checkpoint resumption, and common failure modes. |
| `reck-factory` | Manage the Reck software factory — register repos, run AI tasks in containers, schedule background pipelines, and monitor results via Loki/Grafana. |

### Systems Thinking

| Skill | Description |
|-------|-------------|
| `thinking-in-systems` | Apply Donella Meadows' systems thinking framework to map, diagnose, and redesign any system — organizational, technical, ecological, or policy. Covers stocks/flows, feedback loops, system archetypes, leverage points, and concrete intervention recommendations. Use with `--design` to build a new system, or `--focus map/archetypes/leverage` to run a partial analysis. |

---

## Hooks (3)

| Hook | Event | Description |
|------|-------|-------------|
| `terminal-bell` | `Stop` | Terminal tab indicator when Claude finishes responding. Sends a BEL character for tab/dock notification, a desktop notification with a brief summary, and supports Ghostty/iTerm2 (OSC 9) and WezTerm (OSC 777). |
| `toon-post-hook` | `PostToolUse` | Encodes large tool responses to TOON format (a compact alternative to JSON) before they enter the context window. Reduces token consumption on verbose MCP and built-in tool outputs. No-op if `toon` is not installed. |
| `prefer-modern-tools` | `PreToolUse` | Rewrites legacy CLI commands to faster modern equivalents at runtime: `grep`/`egrep` → `rg`, `cat` → `bat --style=plain --paging=never`, `ls` → `lsd`, `ps aux`/`ps -ef` → `procs`. Safe near-drop-ins only — tools with incompatible flag syntax (`fd`, `dust`, `choose`) are excluded and documented in CLAUDE.md for native use. |

---

## Templates (3)

Stored in `templates/` — copy to your project or use the `/init` skill to deploy them.

| Template | Deployed by | Description |
|----------|-------------|-------------|
| `.pre-commit-config.yaml` | `init` skill | Canonical pre-commit hooks: general hygiene (trailing whitespace, file checks), Python (ruff lint+format, ty type check), TypeScript/JS (biome lint+format), security (gitleaks secret scanning). |
| `CLAUDE.md` | `init` skill | Global Claude Code instructions template covering CLI tool preferences, direnv/Makefile/port conventions, uv-only Python, C4 diagram standards, and TLDR MCP usage. |
| `AGENTS.md` | `init` skill (symlink) | Global Codex/agent instructions template. Deployed as a symlink pointing to `CLAUDE.md` so both agents share the same instructions. |

---

## Sub-plugins (6)

Install from the marketplace:

```bash
/plugin marketplace add citadelgrad/scott-cc/<name>
```

### beads-epic-builder

Plan, build, and swarm beads epics — sequential and parallel execution with CE code review.

**Agents (2)**

| Agent | Description |
|-------|-------------|
| `epic-planner` | Plan complete features from initial concept through implementation-ready beads tasks. Orchestrates research, documentation, and task breakdown with approval gates. |
| `feature-builder` | Orchestrate complete feature development from epic to deployment. Manages architecture review, implementation, quality gates, and validation using beads for task tracking. |

**Commands (2)**

| Command | Description |
|---------|-------------|
| `/build-feature <epic-id>` | Build a complete feature from a beads epic with sequential architecture review, implementation, and validation. Supports `--resume` for interrupted runs. |
| `/epic-swarm <epic-id>` | Build all tasks in a beads epic using parallel worker agents in isolated git worktrees, with CE code review after. Options: `--max-parallel 3`, `--no-review`, `--dry-run`. |

---

### browser-automation

Browser testing and validation with E2E test generation and UI validation.

**Agents (2)**

| Agent | Description |
|-------|-------------|
| `browser-validator` | Validate UI implementations using browser automation with Playwright MCP tools for real-time verification and test generation. |
| `e2e-runner` | End-to-end testing specialist using browser-use AI automation. Handles authenticated flows with secure credential injection, supports persistent browser profiles for 2FA, and generates Python test scripts. |

**Skills (2)**

| Skill | Description |
|-------|-------------|
| `browser-use` | Automate browser interactions for web testing, form filling, screenshots, and data extraction. |
| `browser-use-e2e` | Generate and run E2E tests using browser-use AI automation. Handles credentials securely via `.env.test` with domain-prefixed variables. |

---

### research-tools

Learning guides, tech stack research, and technical writing assistance.

**Agents (3)**

| Agent | Description |
|-------|-------------|
| `learning-guide` | Teach programming concepts and explain code with focus on understanding through progressive learning and practical examples. |
| `tech-stack-researcher` | Guide technology choices, architecture decisions, and implementation approaches when planning new features or functionality. Invoked proactively during planning discussions before implementation begins. |
| `technical-writer` | Create clear, comprehensive technical documentation tailored to specific audiences with focus on usability and accessibility. |

**Skills (1)**

| Skill | Description |
|-------|-------------|
| `humanizer` | Remove AI writing patterns to make generated text sound more natural and human, based on WikiProject AI Cleanup guidelines. |

---

### security-suite

Security advisory and vulnerability scanning.

**Agents (2)**

| Agent | Description |
|-------|-------------|
| `security-advisor` | Answer security questions, review architecture for vulnerabilities, and provide tailored guidance by searching OWASP cheatsheets. |
| `security-engineer` | Identify security vulnerabilities and ensure compliance with security standards and best practices. |

---

### performance-optimization

Performance engineering with bottleneck analysis and profiling.

**Agents (1)**

| Agent | Description |
|-------|-------------|
| `performance-engineer` | Optimize system performance through measurement-driven analysis and bottleneck elimination. |

---

### mutation-testing

Comprehensive mutation testing with zombie test detection and automated refactoring.

**Agents (5)**

| Agent | Description |
|-------|-------------|
| `test-quality-reviewer` | Orchestrate comprehensive mutation testing workflow for test quality analysis using semantic code mutations and parallel test execution. |
| `test-saboteur` | Create semantic code mutations — applies realistic bugs to verify whether test suites catch them. |
| `test-executor` | Execute test suites against mutated code and collect detailed results for mutation testing analysis. |
| `test-auditor` | Analyze mutation testing results to calculate mutation score and identify zombie tests, redundant tests, and quality issues. |
| `test-refactor-specialist` | Consolidate redundant tests and generate improved test suites based on mutation testing analysis. |

**Skills (1)**

| Skill | Description |
|-------|-------------|
| `mutation-test` | Run comprehensive mutation testing to audit test quality, find zombie tests, and propose refactoring. |

---

## Setup Architecture

This plugin is one layer of a three-layer setup system:

| Layer | What | How |
|-------|------|-----|
| 1 — Machine | Ansible `ai-tools` role | `./bootstrap.sh` in macOS-config — clones this repo, symlinks skills into Hermes/Codex, installs tools, deploys security configs |
| 2 — Plugin | This repo (`scott-cc`) | `/plugin marketplace add citadelgrad/scott-cc` in Claude Code |
| 3 — Project | `/init` skill | Run per-project to scaffold `CLAUDE.md`, `AGENTS.md`, `.envrc`, `Makefile`, pre-commit hooks |

Full bootstrap instructions and Ansible configuration: **[citadelgrad/macOS-config](https://github.com/citadelgrad/macOS-config)**

See `docs/setup-architecture.md` for context and init sequence diagrams.

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

## Requirements

- Claude Code CLI
- Works with any project (optimized for Next.js, FastAPI, TypeScript)
- Beads plugin recommended for epic workflows

## License

MIT — Use freely in your projects
