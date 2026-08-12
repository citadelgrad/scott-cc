# PAS 0.9.4 Provider, DOT, Trust, and Runtime Contract

Source: `citadelgrad/pascals-discrete-attractor` stable tag `v0.9.4`, commit
`62ef831`. This reference is mandatory before authoring or running DOT.

## 1. Provider Detection and Generation Boundary

Check relevant CLIs without reading credentials:

```bash
command -v codex && codex --version && codex login status
command -v claude && claude --version && claude auth status --json
command -v gemini && gemini --version
```

- A binary existing is not authentication proof.
- Codex `Logged in using ChatGPT` confirms subscription-backed CLI auth, not tier.
- Claude `loggedIn: true` with OAuth confirms subscription-backed CLI auth.
- Gemini authentication is unverified when only `gemini --version` succeeds.
  Use a documented non-destructive auth probe for that installed release or stop.
- If several runtime providers are authenticated and no preference is established,
  ask before selecting a subscription/billing surface.

PAS 0.9.4 generation is Claude-only: `generate`, `launch` generation, and
`plan --from-prompt` call Claude and expose no provider/model selector. Runtime
nodes separately accept canonical `claude`, `codex`, and `gemini` providers.
Aliases `anthropic`, `openai`, and `google` exist but are less clear.

## 2. Model Selection

Omit graph `model` and node `llm_model` by default. The selected runtime CLI then
uses its configured model. For an explicit Codex model:

```bash
codex debug models
```

Use an exact returned slug. Never pass Claude aliases such as `sonnet` to Codex.
Only set `reasoning_effort` when the selected model catalog supports that value.

Generated DOT commonly contains graph `model="sonnet"`; normalize it and add an
explicit `llm_provider` to every runtime agent node before execution.
For a Codex node, write `llm_provider="codex"` explicitly.

## 3. Strict DOT Contract

Start from `assets/codex-pipeline.dot`.

- Use `digraph`, bare ASCII IDs, and `->`.
- Define exactly one `shape="Mdiamond"` start and one `shape="Msquare"` exit.
- Every agent task needs a prompt, explicit provider, timeout, and least-privilege
  execution environment. `allowed_tools` restricts Claude only in v0.9.4.
- A diamond maps to the conditional handler by shape in v0.9.4;
  `node_type="conditional"` is recommended explicitness, not a validation requirement.
- Quote strings; avoid quoted/numeric-only IDs, HTML labels, ports, and undirected edges.
- Set `loop_restart=true` on a back-edge that must clear completed-node state.

For AI conditionals, use one exact uppercase routing token in:

1. The prompt's required final line.
2. The outgoing edge `label`.
3. `condition="preferred_label=<TOKEN>"`.

For objective handlers, route on outcomes instead:

```dot
quality -> review [label="PASS", condition="outcome=success"]
quality -> fixup [label="FAIL", condition="outcome=fail"]
```

Prefer objective quality gates over an agent reviewing its own work:

```dot
quality [
    shape="box"
    type="quality"
    label="Objective Quality Gate"
    timeout=900s
    quality_checks="git diff --check"
    goal_gate=true
    retry_target="fixup"
]
```

A reviewed, trusted `pas.toml` `[quality]` stage list takes precedence over the
`quality_checks` fallback. Use project tests/linters there. AI review can then
cover semantics that deterministic checks cannot.

## 4. Least Privilege and Generated Artifact Review

- For Claude, set `allowed_tools` to the minimum required surface.
- Codex ignores `allowed_tools`; PAS invokes `codex exec --yolo`.
- Gemini ignores `allowed_tools`; PAS invokes `--approval-mode yolo`.
- Codex and Gemini are invoked in YOLO mode, so prompt text such as “do not edit”
  is guidance, not containment. Run them only in a disposable isolated worktree.
- Keep prompts role-specific anyway: investigators read/search, implementers edit,
  and verification nodes review/test without editing.
- Do not include Git commit/push commands unless the user explicitly authorizes them.
- Generated pipelines may include a required-by-generator commit node. Remove it
  when authorization is absent.
- Inspect `git status` before generation and diff all generated files afterward.
- A failed generation can leave partial files; remove or quarantine them.
- Never run generated DOT merely because `pas validate` accepts its structure.

## 5. Validation and Dry Run

```bash
pas validate pipelines/my-pipeline.dot
pas info pipelines/my-pipeline.dot
pas run pipelines/my-pipeline.dot -w . \
  --logs .pas/logs/my-reviewed-run --dry-run --max-steps 20
```

Validation exit 1 blocks execution; warnings still require review. Dry-run
conditionals produce no provider response, so the engine may warn that no condition
matched and select the first edge. This proves traversal only, not live routing.
Dry-run skips provider CLI calls but may still execute non-LLM handlers, including
quality commands. Review those handlers and use a disposable worktree before dry-run.

`pas launch --dry-run` is not zero-LLM: it still calls Claude during generation
and writes files. Its run phase suppresses provider calls, not all side effects.

## 6. Runtime Bounds and Claude Isolation

Codex and Gemini CLI output reports no per-call dollar cost, so
`--max-budget-usd` cannot enforce their real usage. Require explicit node timeouts,
small `--max-steps`, bounded prompts, least-privilege tools, and an isolated
worktree.

Claude runtime controls exposed by PAS 0.9.4 include:

- `--codergen-claude-settings-mode`
- `--codergen-claude-setting-sources`
- `--codergen-claude-settings`
- `--codergen-claude-tools`
- `--codergen-claude-agents`
- `--codergen-claude-plugin-dir`
- `--codergen-claude-mcp-config`

Modes:

- `subscription-bare`: default; isolates ambient customization while preserving
  normal subscription auth.
- `strict-bare`: strongest isolation, but normal OAuth/keychain auth may not load.
- `inherit`: loads selected user/project/local settings; hooks and other ambient
  behavior may run. Use only deliberately.

CLI flags override `[codergen.claude]` manifest settings for that run. Inspect
current `pas run --help`; these controls are release-sensitive.

## 7. Manifest and Trust

Actual PAS 0.9.4 manifest sections are project, toolchain, quality stages/hooks,
and optional Claude codergen settings. It does not define default run budget,
workdir, or generic model selection.

```bash
pas init --dry-run --non-interactive --workdir .
pas init --non-interactive --workdir .
pas trust list
pas trust add <path> <reviewed-blake3-hash>
pas trust remove <path> <hash>
```

`pas init` targets the nearest Git root, refuses overwrite without `--force`, and
exits 4 outside Git in non-interactive mode unless forced. Review manifests as
executable configuration. A content change requires renewed review/trust.

Environment variables:

| Variable | Purpose |
|---|---|
| `PAS_NON_INTERACTIVE=1` | Suppress interactive prompts |
| `PAS_AGENT=1` | Select agent/non-interactive behavior |
| `PAS_TRUST_THIS=1` | Bypass manifest trust; unsafe outside controlled debugging |
| `XDG_CONFIG_HOME` | Trust-store base directory |
| `OPENAI_API_KEY` | Direct OpenAI adapter |
| `ANTHROPIC_API_KEY` | Direct Anthropic adapter |
| `GOOGLE_API_KEY`, `GEMINI_API_KEY` | Direct Gemini adapter |

## 8. Checkpoint Safety

Default logs are `.pas/logs/<pipeline-stem>-<hash>`, where the hash is derived
from the canonical pipeline path, not file content. Therefore:

- Resume only with unchanged DOT and worktree.
- Editing a pipeline in place does not select a new checkpoint.
- Use a new explicit `--logs` directory after edits or when provenance matters.
- `--fresh` clears the selected checkpoint; confirm scope before using it.
- Directory runs maintain additional cross-file completion state and execute files
  sorted lexically.

## 9. Ordering and Launch Hazard

All directory discovery is sorted lexically. Mixed naming schemes do not put
numbered files first. Use `phase-01`, `phase-02`, etc. consistently.

`launch` passes its output directory to directory-mode `run`, which executes every
`*.dot` there. Generate into a dedicated empty directory so stale pipelines cannot
join the run.
