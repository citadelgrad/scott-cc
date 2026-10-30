---
name: pas-pipeline
description: >-
  Use when authoring, validating, generating, launching, or resuming PAS DOT
  pipelines; selecting an authenticated subscription CLI; or bounding execution.
license: MIT
metadata:
  category: technique
  triggers: [pas, pas-run, pas-launch, pas-generate, dot-pipeline, pipeline-budget, pipeline-resume, model-selection, subscription-detection]
---

# PAS Pipeline Management

Operates PAS CLI, the DOT-based AI pipeline runner. Verified against PAS 0.11.1,
stable tag `v0.11.1`, commit `b82172d` (released 2026-10-13). Run `pas --version`
first: 0.11.0 lacks pi, `stop`, `kill`, `answer`, `monitor`, and the `--plan` and
`--json` flags marked below. Run current command help before relying on flags
from this skill.

## Required References

Before creating, changing, generating, or running DOT, read
`references/provider-and-dot-authoring.md`. It contains the provider boundary,
strict DOT contract, trust model, Claude isolation controls, and checkpoint rules.
Start Codex pipelines from `assets/codex-pipeline.dot`.

## Choose the Operation

| Goal | Command |
|---|---|
| Run or resume DOT | `pas run <pipeline>` |
| Discard checkpoint and restart | `pas run <pipeline> --fresh` |
| Machine-readable run start | `pas run <pipeline> --json` (first stdout line has `run_id`, `run_dir`) |
| List Runs and status | `pas runs [--active] [--json]` |
| Stop after current stage (resumable) | `pas stop <run-id>` |
| End a Run now (checkpoint kept) | `pas kill <run-id> [--grace 10s]` |
| Answer a waiting Human Gate | `pas answer <run-id> <question-id> <choice>` |
| Local web UI for Runs (127.0.0.1:7777) | `pas monitor [--port N] [--open]` |
| Validate / inspect | `pas validate [--json] <file>` / `pas info <file>` |
| Generate from specs or a Plan | `pas generate <docs-dir>` / `pas generate --plan <file>...` |
| End-to-end generation and execution | `pas launch <docs-dir>` |
| Create PRD/spec template | `pas plan --prd` / `pas plan --spec` |
| Create spec with Claude | `pas plan --spec --from-prompt "Describe the required change" -o docs/change-spec.md` |
| Decompose to Beads / scaffold | `pas decompose <spec>` or `--plan <file>...` / `pas scaffold <epic-id> [--json]` |
| Preview project manifest | `pas init --dry-run --non-interactive --workdir .` |

Run `pas <command> --help` before using less-common flags.

## Provider Boundary

PAS 0.11.1 has two separate provider surfaces:

- `pas generate`, `pas launch` generation, and `pas plan --from-prompt` use
  Claude CLI; generation is Claude-only and exposes no provider/model flag.
- Runtime agent nodes select `claude`, `codex`, `gemini`, or `pi` with
  `llm_provider`. There is no implicit Claude fallback: every provider-consuming
  node must name its provider or `pas validate` blocks with `provider_required`.
- A `pi` node also requires `llm_model` as `provider/model-id[:thinking]`
  (for example `openai/gpt-5.5`). `llm_provider="openai"` selects Codex, not pi.
  Needs pi 1.0 or later; PAS runs `pi --version` and `pi auth check` first.

Provider detection does not configure generated DOT. Before execution, inspect
every generated graph/node provider, graph `model`, node `llm_model`, timeout,
tool surface, and commit/push behavior. In particular, generated pipelines may
contain an automatic Git commit node; remove it unless Git mutation was explicitly
authorized.

For hand-authored Codex nodes, omit `model` and `llm_model` by default. If a model
must be pinned, use an exact slug from `codex debug models`. Hermes Agent hosts the
skill but is not a PAS provider; never emit `llm_provider="hermes"`.

## Safe Workflow

Do not use `pas launch` when provider, model, permissions, or generated DOT need
human review. Use this staged path instead:

1. Record `git status`; use an isolated worktree.
2. Generate into a dedicated empty output directory.
3. Inspect every new/changed DOT file and remove partial output after failures.
4. Reject unexpected providers/models, destructive commands, and
   unauthorized commit/push nodes.
5. Run `pas validate` and review warnings.
6. Run `pas info` and confirm nodes, edges, start, exit, and loops.
7. Run a bounded traversal dry run after reviewing non-LLM handlers.
8. Run live only after all previous checks pass.

In short: generate → review → validate → info → bounded dry-run → live run.

```bash
pas generate docs/ -o .pas/generated/reviewed
pas validate .pas/generated/reviewed/phase-01.dot
pas info .pas/generated/reviewed/phase-01.dot
pas run .pas/generated/reviewed/phase-01.dot -w . \
  --logs .pas/logs/reviewed-phase-01 --dry-run --max-steps 20
pas run .pas/generated/reviewed/phase-01.dot -w . \
  --logs .pas/logs/reviewed-phase-01 --max-steps 50
```

`pas launch --dry-run` still calls Claude during generation and writes generated
files. During execution, dry-run skips provider CLI calls but may still execute
non-LLM handlers such as objective quality commands. It is not a zero-side-effect
preview: inspect every tool/quality/human handler first and use a disposable
worktree.

## Bounds and Isolation

- Always set `--max-steps`; the default is 200, which is too loose for small jobs.
- Set `--max-budget-usd` for providers that report cost.
- Codex and Gemini report no per-call dollar cost to PAS, so their nodes count as
  `$0`; bound them with steps, node timeouts, narrow prompts, tools, and worktree.
- Every work/conditional node should have an explicit timeout.
- Restrict Claude and pi nodes with `allowed_tools` (pi maps it to `--tools`).
  PAS 0.11.1 rejects `allowed_tools` and node `max_budget_usd` on Codex and Gemini
  nodes at compile time, and invokes both in YOLO mode, so prompts are not a
  security boundary; contain those providers with a disposable isolated worktree
  and review.
- Do not set `reasoning_effort`, `fidelity`, `auto_status`, `allow_partial`, or
  `thread_id`; PAS rejects them with `unsupported_execution_capability`. Parallel
  nodes with several outgoing edges and fan-in nodes are rejected too.
- `max_budget_usd` is enforced for Claude and pi only (pi: process group stopped
  when summed cost exceeds the limit; one message can overshoot).
- Prefer objective quality nodes (`type="quality"`) backed by reviewed,
  trusted `pas.toml` hooks. AI semantic review may follow, but should not be the
  only completion gate.
- For Claude, default to `subscription-bare`; use `inherit` only when ambient
  hooks/settings are explicitly intended. See the required reference.
- Named skills (`--codergen-skill`, `[codergen] skills`) load only on pi nodes and
  Claude `inherit`/`strict-bare`. Elsewhere PAS warns `CODERGEN_SKILLS_NOT_LOADED`.

## Ordering and Generated Directories

Spec files and directory-mode DOT files are sorted lexically. There is no
“numbered files first” rule. Prefix every file consistently with zero-padded
numbers when order matters.

`pas launch` generates files and then runs every `*.dot` in its output directory,
including stale files. Always use a dedicated empty output directory rather than
reusing a shared `pipelines/` directory.

## Concurrency, Run Control, and Exit Codes

Each `pas run` gets a Run ID, a Run folder under its logs folder, and an entry in
the Run Index (`$PAS_STATE_DIR/runs.jsonl`). Two locks apply:

- Pipeline lock: a second `pas run` of the same pipeline exits 5.
- Worktree lock: a run of another pipeline in the same git worktree exits 6. Use a
  separate worktree. `--allow-shared-workdir` overrides only this lock; use it only
  for a nested inner `pas run`.

Exit codes for `pas run`: 0 success or stop request honored, 1 pipeline failure,
2 untrusted `pas.toml`, 5 pipeline locked, 6 worktree locked.

`pas stop` ends a Run between stages; `pas kill` ends it now. Both keep the
checkpoint, so rerunning the same `pas run` command resumes. `pas runs` reports
`running`, `completed`, `failed`, `stopped`, `crashed` (no heartbeat for about 2
minutes), or `missing`. `pas answer` exits 7 when the question is already answered.

## Checkpoints

`pas run` resumes automatically. Default checkpoint identity is path-based, not content-based:
editing a DOT in place can resume stale state. Resume only when the
DOT and worktree are unchanged. After editing or moving the pipeline, use a new
`--logs` directory or deliberately use `--fresh` after confirming which progress
will be discarded.

## `pas.toml` and Trust

`pas init` is explicit; it does not auto-create a manifest. It targets the nearest
Git root, refuses overwrite without `--force`, and exits 4 in non-interactive mode
outside Git unless deliberately forced. PAS 0.11.1 supports project/toolchain,
ordered quality stages/hooks, Claude codergen isolation config, and per-run
resources (`[codergen] skills`, `[codergen.pi]` extensions and prompt templates)—not
run-level budget, workdir, or generic model defaults. A pi extension named in
`pas.toml` is covered by the trust hash; changing it needs renewed trust.

Treat repository `pas.toml` as executable configuration because quality hooks run
commands. Inspect it before trust:

```bash
pas trust list
pas trust add <path-to-pas.toml> <reviewed-blake3-hash>
pas trust remove <path-to-pas.toml> <hash>
```

Never casually use `PAS_TRUST_THIS=1`; it bypasses manifest verification.

## Failure Diagnosis

| Symptom | Action |
|---|---|
| Validation error | Fix all errors; inspect warnings too |
| Conditional misroutes | Align exact prompt token, edge label, and `preferred_label` condition |
| Max steps reached | Inspect the loop with `pas info`; do not blindly raise the limit |
| Budget reached | Resume only with unchanged DOT/worktree; then adjust deliberately |
| Untrusted manifest | Review `pas.toml`, calculate/obtain its verified BLAKE3 hash, then add trust |
| Generated provider/model wrong | Edit and revalidate DOT; `pas generate` has no runtime-provider selector |
| Exit 5 or 6 from `pas run` | Another Run holds the pipeline or worktree lock; find it with `pas runs --active`, then `pas stop` it or use another worktree |
| `provider_required` | Add explicit `llm_provider` (and `llm_model` for pi) to the named node |
| `unsupported_execution_capability` | Remove the rejected attribute; see Bounds and Isolation |
| pi readiness check fails | Run `pi --version` and `pi auth check --model <model> --json`; fix auth before the Run |
| Gemini CLI merely exists | Authentication remains unverified; do not infer auth from `gemini --version` |

## Citadelgrad Stack Convention

Within the citadelgrad stack, Reckoner is the factory layer and should normally
own repository-level execution through `reck task`; Foundry supplies platform
quality controls. This is an organizational convention, not PAS CLI behavior.

## Done When

- Provider authentication and generation/runtime boundaries are explicit.
- Generated DOT was reviewed, not merely validated.
- Objective quality checks and least-privilege tools are present.
- Every node and whole-pipeline execution are bounded.
- Validation, info, and bounded dry-run passed.
- Live execution used an isolated worktree and explicit logs.
