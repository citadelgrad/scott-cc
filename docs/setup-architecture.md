# Setup Architecture

## Overview

Scott's AI coding environment uses a three-layer setup system. Layer 1 (Ansible) runs once per machine via `bootstrap.sh` and installs all tools, configures security guardrails, and symlinks skills into Hermes and Codex. Layer 2 (scott-cc plugin) is installed manually in Claude Code via the plugin marketplace and provides skills, agents, and commands. Layer 3 (the `init` skill) is run per-project to scaffold CLAUDE.md, AGENTS.md, .envrc, Makefile, and pre-commit hooks interactively.

## System Diagram (C4 Context)

```mermaid
flowchart TB
    classDef person fill:#08427b,color:#fff,stroke:#052e56
    classDef system fill:#1168bd,color:#fff,stroke:#0b4884
    classDef external fill:#999,color:#fff,stroke:#6b6b6b

    scott([Scott]):::person
    setup[AI Tools Setup]:::system
    github[GitHub\ncitadelgrad/scott-cc]:::external
    brew[Homebrew]:::external
    pypi[PyPI / npm]:::external

    scott -->|runs bootstrap.sh| setup
    scott -->|runs /init| setup
    setup -->|clones| github
    setup -->|installs tools| brew
    setup -->|blocks new packages| pypi
```

| Node | Description |
|------|-------------|
| Scott | Developer running the setup |
| AI Tools Setup | Ansible ai-tools role + scott-cc plugin + init skill |
| GitHub citadelgrad/scott-cc | Plugin source, skill definitions, templates |
| Homebrew | Installs pre-commit, ruff, biome |
| PyPI / npm | Package registries — age-restricted to block supply chain attacks |

## Component Diagram (C4 Container)

```mermaid
flowchart TB
    classDef ansible fill:#c7522a,color:#fff,stroke:#8f3a1e
    classDef plugin fill:#1168bd,color:#fff,stroke:#0b4884
    classDef config fill:#555,color:#fff,stroke:#333
    classDef tool fill:#2d6a4f,color:#fff,stroke:#1b4332

    subgraph macOS ["macOS-config (Ansible)"]
        role[ai-tools role]:::ansible
        templates_a[role templates]:::ansible
    end

    subgraph scottcc ["scott-cc (Plugin)"]
        skills[skills/]:::plugin
        templates_s[templates/]:::plugin
        init[init skill]:::plugin
    end

    subgraph configs ["~/.config / dotfiles"]
        claude[~/.claude/]:::config
        hermes[~/.hermes/skills/]:::config
        codex[~/.codex/skills/]:::config
        npm[~/.npmrc]:::config
        uv[~/.config/uv/uv.toml]:::config
        pip[~/.config/pip/pip.conf]:::config
        dcgcfg[~/.config/dcg/]:::config
        gitignore[~/.gitignore_global]:::config
    end

    subgraph tools ["AI Coding Tools"]
        cc[Claude Code]:::tool
        herm[Hermes]:::tool
        cox[Codex]:::tool
    end

    role -->|clones| scottcc
    role -->|symlinks skills| hermes
    role -->|symlinks skills| codex
    role -->|deploys| npm
    role -->|deploys| uv
    role -->|deploys| pip
    role -->|deploys| dcgcfg
    role -->|deploys| gitignore
    templates_s -->|/init copies| claude
    skills -->|loaded by| cc
    skills -->|loaded by| herm
    skills -->|loaded by| cox
```

| Component | Description |
|-----------|-------------|
| ai-tools role | Ansible role in macOS-config; runs once per machine |
| role templates | Ansible-managed config templates (npmrc, uv.toml, pip.conf, etc.) |
| skills/ | Skill definitions shared across Claude Code, Hermes, Codex |
| templates/ | Reusable project templates (CLAUDE.md, AGENTS.md, .pre-commit-config.yaml) |
| init skill | Interactive project scaffolding skill |
| ~/.claude/ | Claude Code config dir — CLAUDE.md lives here at global level |
| ~/.hermes/skills/ | Hermes skill directory — populated via symlinks from scott-cc |
| ~/.codex/skills/ | Codex skill directory — populated via symlinks from scott-cc |

## Bootstrap Sequence

What happens when you run `./bootstrap.sh` on a new Mac:

```mermaid
sequenceDiagram
    participant U as You
    participant B as bootstrap.sh
    participant A as Ansible
    participant GH as GitHub
    participant HB as Homebrew

    U->>B: ./bootstrap.sh
    B->>HB: install ansible (if missing)
    B->>A: ansible-playbook local.yml
    A->>A: homebrew role (brew update)
    A->>A: python role
    A->>A: common role (CLI tools, apps)
    A->>A: zsh role
    A->>GH: git clone citadelgrad/scott-cc
    A->>HB: install pre-commit, ruff, biome
    A->>A: install uv, ty, dcg
    A->>A: symlink skills → Hermes, Codex
    A->>A: deploy npmrc, uv.toml, pip.conf
    A->>A: configure git globals
    A->>A: deploy .gitignore_global
    A->>A: configure direnv fish hook
    A->>A: configure dcg in Hermes
    A-->>U: machine ready
```

## Project Init Sequence

What happens when you run `/init` in a new project:

```mermaid
sequenceDiagram
    participant U as You
    participant C as Claude Code
    participant S as init skill
    participant FS as filesystem

    U->>C: /init
    C->>S: load skill
    S->>FS: detect existing files
    S-->>U: show component menu\n(✓ exists / ○ available)
    U->>S: select components
    S->>FS: bd init (if selected)
    S->>FS: copy CLAUDE.md template (if selected)
    S->>FS: ln -sf CLAUDE.md AGENTS.md (if selected)
    S->>FS: create .envrc + direnv allow (if selected)
    S->>FS: create Makefile (if selected)
    S->>FS: copy .pre-commit-config.yaml (if selected)
    S->>FS: pre-commit install (if selected)
    S-->>U: report what was set up
```

## Command Guard Flow

What happens when Claude Code or Hermes runs a shell command:

```mermaid
sequenceDiagram
    participant A as AI Agent
    participant DCG as dcg (hook)
    participant SH as Shell

    A->>DCG: PreToolUse: bash command
    DCG->>DCG: scan against rule packs
    alt safe command
        DCG-->>A: allow (exit 0)
        A->>SH: execute command
    else destructive pattern matched
        DCG-->>A: block + explain reason
        Note over A: command never runs
    end
```

`dcg` (destructive command guard) is a Rust binary installed by Ansible. It runs as a PreToolUse hook in Claude Code, Hermes, and Codex, intercepting shell commands before execution and blocking patterns like `rm -rf /`, force-pushes to main, credential-touching commands, etc.

## How to Bootstrap a New Mac

1. Clone macOS-config:
   ```bash
   git clone https://github.com/citadelgrad/macOS-config.git && cd macOS-config
   ```
2. Run bootstrap (takes 10–20 min, installs everything):
   ```bash
   ./bootstrap.sh
   ```
3. Install the scott-cc plugin in Claude Code:
   ```
   /plugin marketplace add citadelgrad/scott-cc
   ```
4. Done — skills are available in Claude Code, Hermes, and Codex automatically.

## How to Set Up a New Project

1. `cd` into your project directory.
2. Run `/init` in Claude Code (or invoke the init skill in Hermes).
3. Select which components you want from the menu.
4. Done — the skill handles everything and reports what was created.

## Keeping Things Up to Date

| What | How | When |
|------|-----|-------|
| scott-cc skills | `cd ~/projects/oss/scott-cc && git pull` | When you want new/updated skills |
| Claude Code plugin | `/plugin update scott-cc` | Independent of skills — updates agents/commands |
| dcg | `dcg update` | Automatically done by Ansible on next run |
| pre-commit hooks | `pre-commit autoupdate` in each project | When hook versions go stale |
| Full machine re-sync | `cd ~/path/to/macOS-config && ansible-playbook local.yml -K` | After OS upgrade or new machine |

## Configuration Reference

| File | Purpose | Managed by |
|------|---------|------------|
| `~/.npmrc` | Blocks npm packages < 3 days old | Ansible ai-tools role |
| `~/.config/uv/uv.toml` | Blocks Python packages < 3 days old | Ansible ai-tools role |
| `~/.config/pip/pip.conf` | Blocks pip packages < 3 days old | Ansible ai-tools role |
| `~/.gitignore_global` | Global git ignores (.DS_Store, .env, etc.) | Ansible ai-tools role |
| `~/.config/dcg/config.toml` | dcg rule packs (which commands to guard) | Ansible ai-tools role |
| `~/.hermes/skills/` | Skills available in Hermes | Ansible (symlinks to scott-cc) |
| `~/.codex/skills/` | Skills available in Codex | Ansible (symlinks to scott-cc) |
| `~/.claude/CLAUDE.md` | Global Claude Code instructions | Manual (template in scott-cc/templates/) |
| `~/.codex/AGENTS.md` | Global Codex instructions | Manual (template in scott-cc/templates/) |
| `~/projects/oss/scott-cc/` | Plugin source + skill definitions | `git pull` to update |
| `.pre-commit-config.yaml` | Per-project commit hooks | Copied by `/init` skill |
