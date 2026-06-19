---
name: pas-pipeline
description: Run, validate, and manage PAS (Pascal's Discrete Attractor) DOT-based AI pipelines. Use when launching a pipeline end-to-end, resuming interrupted runs, capping spend, or generating pipelines from spec/PRD files.
license: MIT
tags: [pas, pipeline, ai-workflows, automation]
---

# PAS Pipeline Management

Operates `pas` — the DOT-based AI pipeline runner. Version: 0.7.2.

Use this skill when:
- Launching a pipeline from spec/PRD documents (`pas launch`)
- Running or resuming a `.dot` pipeline file (`pas run`)
- Validating a pipeline before execution (`pas validate`)
- Generating `.dot` files from spec documents (`pas generate`)
- Debugging a stalled or budget-exceeded pipeline

---

## Step 1: Identify the Operation

Ask or infer from context which command applies:

| Goal | Command |
|---|---|
| End-to-end from docs | `pas launch <docs-dir>` |
| Run existing pipeline | `pas run <pipeline>` |
| Resume interrupted run | `pas run <pipeline>` (resumes automatically) |
| Fresh start (discard checkpoints) | `pas run <pipeline> --fresh` |
| Validate only | `pas validate <file>` |
| Generate `.dot` from specs | `pas generate <docs-dir>` |
| Inspect a pipeline | `pas info <file>` |
| Create PRD/spec stubs | `pas plan` |
| Decompose spec to beads epic | `pas decompose` |
| Scaffold pipeline from epic | `pas scaffold` |
| Initialize `pas.toml` | `pas init` |

---

## Step 2: Apply Flags

Always review these flags before running — they prevent runaway spend and enable safe testing.

### Budget and safety flags

```bash
# Cap total LLM spend (recommended for any non-trivial pipeline)
pas run my-pipeline.dot --max-budget-usd 5.00

# Abort after N node executions (default: 200)
pas run my-pipeline.dot --max-steps 50

# Dry run — no LLM calls, validates graph traversal only
pas run my-pipeline.dot --dry-run

# Verbose logging for debugging
pas run my-pipeline.dot -v
```

**Rule:** Always set `--max-budget-usd` for any pipeline running against production LLM endpoints.

### Working directory

```bash
# Execute tools relative to a specific directory
pas run my-pipeline.dot -w /path/to/project
```

---

## Step 3: Launch vs Run

### `pas launch` — end-to-end from documents

```bash
pas launch <docs-dir>
```

What it does in order:
1. Discovers `*-spec.md` and `*-prd.md` files in `<docs-dir>`
2. Calls `pas generate` to produce `.dot` files
3. Validates each generated pipeline
4. Runs them in discovery order

**Ordering:** Name spec files with zero-padded numeric prefixes to control execution order:
```
phase-01-auth-spec.md
phase-02-api-spec.md
phase-03-ui-spec.md
```
Files without a numeric prefix run after numbered ones, in alphabetical order.

**PRD pairing:** A `*-prd.md` alongside a `*-spec.md` is optional but recommended. PRDs provide product context that improves generated pipeline quality:
```
auth-prd.md      ← paired with →   auth-spec.md
```

### `pas run` — direct pipeline execution

```bash
pas run my-pipeline.dot
pas run pipelines/              # runs all .dot files in directory
```

**Checkpoint behavior:** `pas run` automatically resumes from the last successful checkpoint. If a run was interrupted (crash, budget exceeded, timeout), re-running the same command picks up where it left off. Use `--fresh` to discard all checkpoints and start over.

---

## Step 4: Common Failure Modes

### Budget exceeded mid-run

```
Error: budget cap reached ($5.00)
```

The pipeline checkpointed at the last successful node. Increase the cap and re-run — it resumes:

```bash
pas run my-pipeline.dot --max-budget-usd 10.00
```

### Max steps hit

```
Error: max steps reached (200)
```

Either increase `--max-steps` or investigate why the pipeline is taking more steps than expected (`pas info` to inspect the graph).

### Validation failures

```bash
pas validate my-pipeline.dot
```

Common issues:
- Unreachable nodes (disconnected subgraph)
- Missing required node attributes (`label`, `type`)
- Cycles without a termination condition

Fix the `.dot` file directly or re-run `pas generate` if it was auto-generated.

### Dry run to test ordering

```bash
pas launch docs/ --dry-run -v
```

Shows which specs were discovered, what `.dot` files would be generated, and the execution order — without any LLM calls.

---

## Step 5: Project Setup

If `pas.toml` doesn't exist in the project root:

```bash
pas init
```

This creates a `pas.toml` with sensible defaults. Edit it to set default budget caps, working directory, and model preferences rather than passing flags every run.
