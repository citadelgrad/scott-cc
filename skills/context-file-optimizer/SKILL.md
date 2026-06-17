---
name: context-file-optimizer
description: Audit and rewrite AGENTS.md, CLAUDE.md, and other AI agent context files to be minimal and effective. This skill should be used when creating, reviewing, or rewriting context files (AGENTS.md, CLAUDE.md, .cursorrules, etc.) to follow research-backed guidelines that improve agent performance and reduce costs. Based on findings from arxiv.org/abs/2602.11988.
---

# Context File Optimizer

Audit and rewrite AI agent context files following research-backed principles. Verbose context files hurt agent performance (-2 to -3%) and increase costs (+20%). Minimal, tooling-focused files improve performance (+4%) with lower overhead.

## Principle Hierarchy

Three layers inform what belongs in a context file:

1. **karpathy-guidelines** (skill) — Foundational behavioral principles: think before coding, simplicity first, surgical changes, goal-driven execution. These govern how an agent acts; they don't need to be restated in every project's CLAUDE.md if the project explicitly uses this skill on a regular basis.
2. **Code quality standards** — Project coding rules (DRY, KISS, thin handlers, no hardcoded values, no silent failures, ~20-line functions, no premature abstraction). These ARE project-specific and belong in CLAUDE.md. **Preserve them — do not cut them as "general advice".**
3. **This skill** — Strips everything else: architecture prose, directory listings, duplicated docs, tutorial content.

## When to Use

- Creating a new AGENTS.md, CLAUDE.md, or similar context file
- Reviewing an existing context file for bloat or ineffectiveness
- Consolidating overlapping context files in a project
- Migrating from auto-generated to human-curated context

## Audit Process

### Step 1: Inventory All Context Files

Locate every file that injects context into agent sessions:

```bash
# Common context file locations
fd -t f "AGENTS.md|CLAUDE.md|\.cursorrules|\.windsurfrules|copilot-instructions" .
```

Read each file. Note total word count and section count. Flag any file over 700 words.

### Step 2: Identify Duplication

Cross-reference content across all context files found. Mark sections that appear in more than one file or that duplicate information already present in README, pyproject.toml, package.json, Dockerfile, or other standard project files.

Common duplication sources:
- Service URLs repeated across multiple context files
- Tool commands duplicated between AGENTS.md and CLAUDE.md
- Architecture descriptions that restate what's in README
- Dockerfile patterns that agents can read from the actual Dockerfiles
- Linter rules that agents can read from config files (pyproject.toml, eslint.config.mjs)

### Step 3: Classify Each Section

For every section in every context file, classify it:

| Classification | Action | Examples |
|---------------|--------|---------|
| **Tooling spec** | KEEP | Required CLI tools, package managers, linter commands |
| **Build/test command** | KEEP | Exact test commands with paths, build commands |
| **Non-obvious gotcha** | KEEP | "Worker caches env vars", "pitchers stored as P not SP/RP" |
| **Operational rule** | KEEP (condense) | "Stop after 2-3 failures", "never use pip" |
| **Code quality standards** | KEEP | DRY, KISS, thin handlers, no silent failures, ~20-line functions — project coding rules belong in CLAUDE.md |
| **Architecture overview** | CUT | System diagrams, component descriptions |
| **Directory listing** | CUT | File tree enumerations, module inventories |
| **Duplicated docs** | CUT | Content from README, config files, or other context files |
| **Tutorial/reference** | MOVE to docs/ | MCP tool guides, pipeline authoring references |
| **Code examples of patterns** | CUT | Agents discover patterns from actual code |
| **Tool installation instructions** | CUT | One-time setup, not per-session |
| **Behavioral guidelines** | CUT (with caution) | Karpathy-style rules — only cut if the project team consistently invokes `/karpathy-guidelines`; keep them if behavioral consistency matters more than token savings |

### Step 4: Rewrite

Apply these rules when rewriting:

**Structure rules:**
- Target ~500-650 words per file (research optimal: ~640)
- Use tables for dense reference data (tool names, commands, URLs)
- Use code blocks for exact commands agents should run
- One-line descriptions over paragraphs
- No prose explanations of architecture — agents explore codebases effectively on their own

**Content rules — what TO include:**
- Required tools with their primary commands
- Exact test/build/lint commands with full paths
- Session workflow (start → work → close checklist)
- Domain-specific gotchas that cause real bugs (not general advice)
- Pointers to detailed docs for complex subsystems (e.g., "see docs/pipelines.md")

**Content rules — what NOT to include:**
- Repository overviews or architecture descriptions
- Directory listings or component enumerations
- Content duplicated in README, config files, or other context files
- Code pattern examples (agents read actual code)
- Installation or one-time setup instructions
- Verbose prose explaining "why" behind conventions

**Multi-file projects:** Assign clear responsibilities to each file:
- AGENTS.md → Tooling commands, session workflow, operational rules
- CLAUDE.md → Conventions that affect how code is written (standards, patterns, domain knowledge)
- Avoid any content appearing in both files

### Step 5: Validate

After rewriting, verify:

1. **Word count** — Each file should be under 700 words
2. **No duplication** — No section appears in more than one context file
3. **No redundancy** — No section restates what's in standard project files
4. **Commands are exact** — Every command can be copy-pasted and run
5. **Displaced content preserved** — Any cut reference material was moved to docs/, not deleted

## Research Reference

Read `references/research-findings.md` for the full experimental data supporting these guidelines, including specific performance numbers and the verbatim conclusion from the paper.
