---
name: pas-pipeline
description: >-
  Use when authoring, validating, launching, or resuming PAS DOT pipelines;
  selecting an authenticated Codex, Claude, or Gemini subscription CLI and
  compatible model; capping execution; or generating pipelines from specs.
license: MIT
metadata:
  category: technique
  triggers: [pas, pas-run, pas-launch, pas-generate, dot-pipeline, dot-authoring, ai-pipeline, pipeline-budget, pipeline-resume, model-selection, subscription-detection, spec-to-pipeline, PRD-pipeline]
---

# PAS Pipeline Management

Operates `pas` — the DOT-based AI pipeline runner. Verified against version 0.9.4; inspect current command help rather than assuming flags are unchanged.

**Role in the stack:** PAS is the sole execution engine for AI tasks. Reckoner (the factory layer) wraps PAS — it never invokes Claude directly. Foundry sits above as the platform quality layer. All task execution ultimately calls `pas run` inside a container.

## Prerequisites

- **Required:** `pas` CLI tool (version 0.9.4 or compatible)
  - Verify installation: `pas --version`
  - If not installed, consult your project's setup documentation or contact your platform team
- **Required:** Ability to run shell commands and access `.dot` pipeline files
- **Optional:** `pas.toml` configuration file in project root (auto-created by `pas init` if missing)

## When to Use
- Launching a pipeline from spec/PRD documents (`pas launch`)
- Running or resuming a `.dot` pipeline file (`pas run`)
- Validating a pipeline before execution (`pas validate`)
- Generating `.dot` files from spec documents (`pas generate`)
- Hand-authoring a `.dot` pipeline for Codex, Claude Code, or Gemini
- Detecting which subscription-backed provider CLI and model are actually available
- Debugging a stalled or budget-exceeded pipeline

## Required Reference for DOT Authoring

Before creating or editing a `.dot` file, read `references/provider-and-dot-authoring.md`. It defines provider/auth detection, model selection, PAS's strict DOT subset, and the exact conditional-label contract. Start Codex pipelines from `assets/codex-pipeline.dot`; do not reconstruct the syntax from memory.

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
| Hand-author `.dot` | Read `references/provider-and-dot-authoring.md`, copy the matching asset, then validate |
| Inspect a pipeline | `pas info <file>` |
| Create PRD/spec stubs | `pas plan` |
| Create spec from a prompt | `pas plan --spec --from-prompt` |
| Decompose spec to beads epic | `pas decompose` |
| Scaffold pipeline from epic | `pas scaffold` |
| Initialize `pas.toml` | `pas init` |

---

## Step 2: Detect Provider and Model

Before generating or running agent nodes:

1. Check the candidate CLI's version and authentication status using the commands in `references/provider-and-dot-authoring.md`.
2. If this skill is running in Codex and `codex login status` succeeds, write `llm_provider="codex"` on every agent node.
3. Omit `model` and `llm_model` by default so the authenticated provider uses its configured model.
4. Only pin Codex to a model slug returned by the current `codex debug models` catalog. Never pass Claude aliases such as `sonnet` to Codex.
5. Remember that Hermes Agent is the skill host, not a PAS provider; never emit `llm_provider="hermes"`.

If more than one provider is authenticated and neither the current host nor the user establishes a preference, ask before choosing a subscription surface.

---

## Step 3: Apply Flags

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

**Rule:** Set `--max-budget-usd` for providers that report cost. Codex and Gemini CLI currently report no per-call dollar cost to PAS, so the cap cannot enforce their real spend. For those providers, require `--max-steps`, node timeouts, bounded prompts, and an isolated worktree.

### Working directory

```bash
# Execute tools relative to a specific directory
pas run my-pipeline.dot -w /path/to/project
```

---

## Step 4: Launch vs Run

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

## Step 5: Common Failure Modes

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
- Missing required node attributes (`prompt` on task/conditional nodes, `node_type="conditional"` on explicit conditional nodes)
- Missing or duplicate start/exit nodes (`shape="Mdiamond"` / `shape="Msquare"`)
- Conditional routing tokens that disagree between the prompt, edge `label`, and `preferred_label=<TOKEN>` condition
- Cycles without a termination condition

Node `label` is optional and falls back to the node ID, but explicit labels are strongly recommended for readable logs. Fix the `.dot` file using `references/provider-and-dot-authoring.md` or re-run `pas generate` if it was auto-generated.

### Dry run to test ordering

```bash
pas launch docs/ --dry-run -v
```

Shows which specs were discovered, what `.dot` files would be generated, and the execution order — without any LLM calls.

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Running without execution bounds | Use `--max-budget-usd` where cost is reported; always bound steps and node timeouts |
| Using `--fresh` when you meant to resume | Default behavior resumes from checkpoint; `--fresh` discards all progress |
| Guessing flags for `pas plan` / `pas info` | Run `pas <command> --help` first — flags change across versions |
| Forgetting `--dry-run` for first-time pipeline testing | Always dry-run before committing to LLM calls |
| Writing `model="sonnet"` for Codex nodes | Omit the model or use an exact slug from `codex debug models` |
| Treating Hermes Agent as a PAS provider | Hermes hosts the skill; select an authenticated `codex`, `claude`, or `gemini` CLI |
| Assuming `--max-budget-usd` tracks Codex subscription usage | PAS receives no Codex dollar cost; bound steps, timeouts, scope, and worktree instead |
| Letting conditional labels drift | Use the same exact uppercase token in the prompt, edge `label`, and `preferred_label` condition |
| Manually running pipelines that Reckoner should manage | Use `reck task` for repo-level pipeline execution |

## Step 6: Less-Common Commands

`pas info`, `pas plan`, `pas plan --spec --from-prompt`, `pas decompose`, and `pas scaffold` are not detailed above. Do not guess their flags — run `pas <command> --help` first to confirm current syntax before invoking one of these.

## Step 7: Project Setup

If `pas.toml` doesn't exist in the project root:

```bash
pas init
```

This creates a `pas.toml` with sensible defaults. Edit it to set default budget caps, working directory, and model preferences rather than passing flags every run.

## Limitations
- Use this skill only when the task clearly matches the scope described above.
- Requires `pas` CLI to be installed and accessible in PATH.
- Budget caps are advisory — actual spend depends on model pricing and task complexity.
- Codex and Gemini CLI nodes are uncosted in PAS, so their real usage cannot currently be enforced by `--max-budget-usd`.
- PAS invokes Codex non-interactively with broad execution permissions; use an isolated worktree and review the pipeline before running it.
- Does not manage container orchestration directly; use `reck task` for repo-level pipeline execution.
- Stop and ask for clarification if the pipeline structure, budget constraints, or execution environment are unclear.
