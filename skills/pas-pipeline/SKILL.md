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

Operates PAS CLI, the DOT-based AI pipeline runner. Verified against PAS 0.9.4,
stable tag `v0.9.4`, commit `62ef831` on 2026-08-12. Run current command help
before relying on flags from this skill.

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
| Validate / inspect | `pas validate <file>` / `pas info <file>` |
| Generate from specs | `pas generate <docs-dir>` |
| End-to-end generation and execution | `pas launch <docs-dir>` |
| Create PRD/spec template | `pas plan --prd` / `pas plan --spec` |
| Create spec with Claude | `pas plan --spec --from-prompt "Describe the required change" -o docs/change-spec.md` |
| Decompose to Beads / scaffold | `pas decompose <spec>` / `pas scaffold <epic-id>` |
| Preview project manifest | `pas init --dry-run --non-interactive --workdir .` |

Run `pas <command> --help` before using less-common flags.

## Provider Boundary

PAS 0.9.4 has two separate provider surfaces:

- `pas generate`, `pas launch` generation, and `pas plan --from-prompt` use
  Claude CLI; generation is Claude-only and exposes no provider/model flag.
- Runtime agent nodes can select `claude`, `codex`, or `gemini` with
  `llm_provider`.

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
- Restrict Claude nodes with `allowed_tools`. PAS 0.9.4 ignores that attribute for
  Codex and Gemini and invokes both in YOLO mode, so prompts are not a security
  boundary; contain those providers with a disposable isolated worktree and review.
- Prefer objective quality nodes (`type="quality"`) backed by reviewed,
  trusted `pas.toml` hooks. AI semantic review may follow, but should not be the
  only completion gate.
- For Claude, default to `subscription-bare`; use `inherit` only when ambient
  hooks/settings are explicitly intended. See the required reference.

## Ordering and Generated Directories

Spec files and directory-mode DOT files are sorted lexically. There is no
“numbered files first” rule. Prefix every file consistently with zero-padded
numbers when order matters.

`pas launch` generates files and then runs every `*.dot` in its output directory,
including stale files. Always use a dedicated empty output directory rather than
reusing a shared `pipelines/` directory.

## Checkpoints

`pas run` resumes automatically. Default checkpoint identity is path-based, not content-based:
editing a DOT in place can resume stale state. Resume only when the
DOT and worktree are unchanged. After editing or moving the pipeline, use a new
`--logs` directory or deliberately use `--fresh` after confirming which progress
will be discarded.

## `pas.toml` and Trust

`pas init` is explicit; it does not auto-create a manifest. It targets the nearest
Git root, refuses overwrite without `--force`, and exits 4 in non-interactive mode
outside Git unless deliberately forced. PAS 0.9.4 supports project/toolchain,
ordered quality stages/hooks, and Claude codergen isolation config—not run-level
budget, workdir, or generic model defaults.

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
