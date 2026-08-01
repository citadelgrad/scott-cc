# Bash Helpers & Detection Logic

Reference commands used throughout the init skill for detecting project state and availability of tools.

## Project State Detection

### Git Repository Check

```bash
ls -d .git/ 2>/dev/null
# Returns: .git/ (exit 0) if repo exists, silent failure (exit 1) if not
```

### Project Type Detection

```bash
ls pyproject.toml package.json tsconfig.json 2>/dev/null
# Returns list of files found; used to determine if Python, Node/TS, or unknown
```

**Logic:**
- If `pyproject.toml` exists → Python project (use Python Makefile)
- If `package.json` or `tsconfig.json` exists → Node/TS project (use Node/TS Makefile)
- Otherwise → Unknown type (use generic Makefile)

### Existing Scaffolding Check

```bash
ls CLAUDE.md AGENTS.md .envrc Makefile .pre-commit-config.yaml foundry.yaml 2>/dev/null
ls -d .beads/ 2>/dev/null
# Returns list of files/dirs found; used to determine what already exists
```

## Tool Availability Checks

### Beads (bd) Availability

```bash
command -v bd >/dev/null 2>&1 || { echo "bd not found — install beads before continuing"; exit 1; }
```

Exits with error message if `bd` is not installed.

### Direnv Availability

```bash
command -v direnv >/dev/null 2>&1 && direnv allow
```

Runs `direnv allow` only if direnv is installed (optional; exits silently if not found).

### Pre-commit Availability

```bash
command -v pre-commit >/dev/null 2>&1 || { echo "pre-commit not found — install with: uv tool install pre-commit"; exit 1; }
```

Exits with error message if pre-commit is not installed.

## Symlink & File State Checks

### AGENTS.md Symlink Verification

```bash
# Check if symlink exists and points to CLAUDE.md
[ -L AGENTS.md ] && [ "$(readlink AGENTS.md)" = "CLAUDE.md" ]
```

Returns exit 0 if AGENTS.md is a valid symlink to CLAUDE.md; exit 1 otherwise.

### File Existence in .gitignore

```bash
# Check if 'CLAUDE.md' is in .gitignore
grep -qxF 'CLAUDE.md' .gitignore 2>/dev/null || echo 'CLAUDE.md' >> .gitignore
```

- `-q` — quiet mode (no output)
- `-x` — match entire line only
- `-F` — treat pattern as literal string (not regex)
- Appends to `.gitignore` if not found; creates file if it doesn't exist

## Finding scott-cc Repository

```bash
SCOTT_CC_DIR=$(fd -HI -t d -g 'scott-cc' ~ 2>/dev/null | grep -E '/scott-cc$' | head -1)
```

- `fd -HI -t d -g 'scott-cc'` — find directories named scott-cc anywhere in home
- `grep -E '/scott-cc$'` — filter for exact matches (ends with scott-cc)
- `head -1` — return first match
- Assumes `fd` is installed (Rust-based alternative to `find`)

Fallback if `fd` not available:
```bash
SCOTT_CC_DIR=$(find ~ -type d -name scott-cc 2>/dev/null | grep -E '/scott-cc$' | head -1)
```

## Pre-commit Chain Detection

```bash
# Check if pre-commit chain already exists in .beads/hooks/pre-commit
grep -q 'pre-commit run' .beads/hooks/pre-commit 2>/dev/null
```

Returns exit 0 if chain is already present; exit 1 if not. Used to make the pre-commit setup idempotent.

## Beads Configuration

```bash
# Set validation rule (idempotent)
bd config set validation.on-create warn
```

## Directory Structure References

**Typical project layout after init:**
```
.git/                            # git repository
.beads/                          # beads issue tracking
.beads/hooks/                    # git hook scripts
.beads/config.yaml               # beads configuration (validation.on-create set here)
.envrc                           # direnv environment (personal, not committed)
.pre-commit-config.yaml          # pre-commit hook definitions
.gitignore                       # git ignore rules (added: CLAUDE.md, AGENTS.md, .envrc)
CLAUDE.md                        # project instructions (personal, not committed)
AGENTS.md                        # symlink to CLAUDE.md
Makefile                         # service targets (up, down, test, lint, etc.)
foundry.yaml                     # scheduling & automation profiles
```
