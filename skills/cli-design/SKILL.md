---
name: cli-design
description: Design or audit CLI tools for agent compatibility. Covers stdout/stderr separation, --json flag, exit codes, NDJSON streaming, TOON format, composability, and idempotency. Use when building a new CLI or reviewing an existing one for LLM/agent use.
license: MIT
tags: [cli, agents, llm, design, tooling]
sources:
  - https://clig.dev/
  - https://developer.hashicorp.com/terraform/internals/machine-readable-ui
  - https://toonformat.dev/cli/
  - https://github.com/toon-format/toon
---

# CLI Design for Agents

Design or audit a CLI tool so that AI agents can invoke it reliably, parse its
output without brittle text scraping, and compose it into pipelines.

Use this skill when:
- Designing a new CLI from scratch
- Auditing an existing CLI for agent/LLM compatibility
- Adding machine-readable output to an existing tool

---

## Step 1: Understand the Scope

Ask (or infer from context):

1. **New or existing CLI?** New → design mode. Existing → audit mode.
2. **Language/runtime?** (Python, Node, Go, Rust, shell…)
3. **Primary consumer?** Human-first with agent support, or agent-first?
4. **Streaming output?** Long-running commands (builds, deploys, watches) need NDJSON.
5. **TOON interest?** If LLM token efficiency is a priority, mention TOON as an option.

---

## Step 2: Audit Against the Core Checklist

Run through each item. For existing CLIs, check the source. For new CLIs, use
this as the design spec.

### ✦ stdout / stderr separation (HIGH — verified 3-0)

> **Rule:** Primary output and all machine-readable data → stdout.
> Logs, warnings, errors, status messages → stderr.

Why it matters: when a command is piped (`cmd | jq`), stderr is shown to the
user while stdout flows to the next program. Mixing them breaks parsers.

```bash
# Good
echo '{"status":"ok"}' >&1   # data to stdout
echo "Processing..." >&2     # status to stderr

# Bad — breaks piping
echo "Processing..."         # status to stdout pollutes parsers
echo '{"status":"ok"}'
```

Check: does the CLI ever write log lines, progress, or warnings to stdout?
If yes, flag as a defect.

---

### ✦ --json flag (HIGH — verified 3-0)

> **Rule:** Expose `--json` (or `--output json`) that switches output to
> structured JSON. Keep human-readable output as the default.

Adopted by: GitHub CLI (`gh`), AWS CLI, npm, yarn, pnpm, eslint.

```bash
# Human default
$ my-tool list
item-a  active
item-b  inactive

# Machine mode
$ my-tool list --json
[{"name":"item-a","status":"active"},{"name":"item-b","status":"inactive"}]
```

Design rules for `--json` output:
- Output a single JSON object or array on stdout
- No trailing commentary, no progress lines (those stay on stderr)
- Schema should be stable — breaking changes require a version bump
- Pipe-friendly: `my-tool list --json | jq '.[].name'` must work

Do NOT auto-detect TTY to switch formats. The `--json` flag must be explicit.
(TTY auto-detection was refuted as a best practice — use explicit flags.)

---

### ✦ Exit codes (HIGH — verified 2-1)

> **Rule:** Exit 0 on success, non-zero on any failure.

This is the mechanism scripts and agents use to detect failure. An agent that
calls `subprocess.run()` checks `returncode`, not stdout content.

```python
# Good — agent can check exit code
result = subprocess.run(["my-tool", "deploy"], capture_output=True)
if result.returncode != 0:
    raise DeployError(result.stderr.decode())
```

Common conventions:
- `0` — success
- `1` — general error (safe default for all failures)
- `2` — misuse / bad arguments (some tools)

For **partial success** (some items succeeded, some failed): encode per-item
status in structured output (`--json`), and still exit non-zero if any item
failed. Let the agent parse which items failed from structured output.

---

### ✦ NDJSON for streaming (HIGH — verified, Terraform canonical example)

For long-running commands (builds, deploys, watches), use **NDJSON**
(newline-delimited JSON): one JSON object per line to stdout.

Terraform's `terraform apply -json` is the canonical implementation:

```jsonl
{"@level":"info","@message":"Initializing...","@module":"terraform","@timestamp":"2026-06-17T10:00:00Z","type":"log"}
{"@level":"info","@message":"Plan: 3 to add","@module":"terraform.ui","@timestamp":"2026-06-17T10:00:01Z","type":"planned_changes","changes":{"add":3,"change":0,"remove":0}}
```

Standard NDJSON message fields (adopt these):

| Field | Type | Notes |
|---|---|---|
| `@level` | string | `debug`, `info`, `warn`, `error` |
| `@message` | string | Human-readable summary |
| `@module` | string | Component that emitted this |
| `@timestamp` | string | RFC3339 (`2026-06-17T10:00:00Z`) |
| `type` | string | Machine-readable event type |

Schema versioning rules (semver):
- **Minor bump** — new fields added (backward-compatible)
- **Major bump** — fields removed or renamed (breaking)
- Consumers must ignore unknown fields to stay forward-compatible

```bash
# Agent consuming NDJSON
my-tool build --json 2>/dev/null | while IFS= read -r line; do
  echo "$line" | jq -r 'select(.type == "error") | .["@message"]'
done
```

---

### ✦ Composability (Unix pipeline design)

> **Rule:** Accept input from stdin when it makes sense. Output to stdout.
> Support piping as a first-class workflow.

```bash
# Composable pipeline
cat items.json | my-tool process --json | jq '.results[]'

# File or stdin interchangeably
my-tool process input.json       # file arg
my-tool process < input.json     # stdin
cat input.json | my-tool process # pipe
```

Design checklist:
- [ ] Reads stdin if no file argument provided (or `-` as explicit stdin)
- [ ] No mandatory interactive prompts in the happy path
- [ ] No color codes in `--json` output (color is for TTY humans)
- [ ] `--no-color` / `NO_COLOR` env var respected for human output

For non-interactive / agent invocation, destructive operations should either:
- Require an explicit `--yes` / `--force` flag (preferred)
- Or check for TTY and fail with a clear error message naming the bypass flag

---

### ✦ Idempotency

> **Rule:** Running the same command twice should produce the same result.
> Agents retry on failure — a non-idempotent CLI causes double-creates.

Design patterns:
- `--force` to overwrite if already exists (don't error on re-run)
- Or return success silently when the desired state is already true
- Document which commands are idempotent in help text

```bash
# Idempotent — safe to retry
$ my-tool create-bucket my-bucket
Created: my-bucket
$ my-tool create-bucket my-bucket
Already exists: my-bucket (no change)  # exit 0, not exit 1
```

---

## Step 3: TOON — Optional LLM Token Optimization

[TOON](https://toonformat.dev) (`@toon-format/cli`) is a tabular encoding
for JSON arrays that uses explicit count/field headers and CSV-style rows.
Designed to improve LLM parsing reliability by giving models a clear schema.

**When to consider it:** You're passing large arrays of uniform objects to an
LLM and token count matters.

**When to skip it:** Standard tooling (`jq`, curl, etc.) doesn't understand
TOON. Use JSON as your primary interchange format; TOON is an LLM-layer
optimization only.

### TOON encoding format

```
# JSON
[{"name":"alice","role":"admin"},{"name":"bob","role":"user"}]

# TOON
users[2]{name,role}:
alice,admin
bob,user
```

Syntax: `arrayName[N]{field1,field2,...}:` followed by N CSV rows.
The explicit `[N]` count and `{fields}` header give models a schema to follow.

### TOON CLI usage

```bash
# Install
npm install -g @toon-format/cli

# Encode JSON → TOON (pipe)
cat data.json | npx @toon-format/cli

# Decode TOON → JSON
cat data.toon | npx @toon-format/cli --decode

# Auto-detected by file extension
npx @toon-format/cli -o output.toon input.json   # .json → encode
npx @toon-format/cli -o output.json input.toon   # .toon → decode

# Estimate token savings (self-reported, use as a guide)
npx @toon-format/cli --stats < data.json
```

Flags:
- `-e` / `--encode` — explicit encode
- `-d` / `--decode` — explicit decode
- `-o` / `--output <file>` — write to file (default: stdout)
- `--stats` — print token count comparison

> **Caveat:** TOON token-saving percentages are self-reported. The tool's
> `--stats` flag shows an estimate; treat it as a guide, not a guarantee.
> TOON is young — validate independently before relying on it for production
> LLM pipelines.

---

## Step 4: Deliver the Audit / Design

### For an existing CLI (audit mode)

Present a table:

```
CLI Agent Compatibility Audit
──────────────────────────────────────────────────
✓  stdout/stderr separated
✗  --json flag missing           → add --json to list/show subcommands
✓  exit codes correct
○  no NDJSON for build command   → consider for long-running ops
✗  list command writes progress to stdout → move to stderr
○  create not idempotent         → add --force or silent-success on re-run
──────────────────────────────────────────────────
Critical (break agent parsing): 2
Recommended: 2
Optional: 1
```

Follow up with concrete diffs or pseudocode for each `✗` item.

### For a new CLI (design mode)

Output a checklist contract the implementation must satisfy:

```
CLI Design Contract
──────────────────────────────────────────────────
[ ] All data to stdout, all status/errors to stderr
[ ] --json flag on every subcommand that produces output
[ ] Exit 0 on success, 1 on failure (document partial-success behavior)
[ ] NDJSON for <list long-running commands>
[ ] Reads stdin when no file arg given
[ ] --yes / --force for destructive operations (no TTY prompting)
[ ] --no-color respected; NO_COLOR env var honored
[ ] Idempotent: re-running succeeds if state already matches
──────────────────────────────────────────────────
```

Then propose the JSON schema for `--json` output before any code is written.

---

## Quick Reference: Standard Flag Names

From clig.dev and ecosystem conventions:

| Flag | Purpose |
|---|---|
| `--json` | Structured JSON output |
| `--output <format>` | Multi-format: `json`, `text`, `table` |
| `--no-color` | Disable ANSI color codes |
| `--quiet` / `-q` | Suppress informational output |
| `--verbose` / `-v` | More output (goes to stderr) |
| `--yes` / `-y` | Skip confirmation prompts |
| `--force` / `-f` | Overwrite / proceed despite warnings |
| `--dry-run` | Show what would happen without doing it |

---

## Ponytail note

The minimum viable agent-compatible CLI is three things:
1. stdout = data, stderr = noise
2. `--json` flag
3. Exit code reflects success/failure

Everything else (NDJSON, TOON, idempotency, schema versioning) adds value as
the tool's agent usage grows. Ship the three-thing version first.
