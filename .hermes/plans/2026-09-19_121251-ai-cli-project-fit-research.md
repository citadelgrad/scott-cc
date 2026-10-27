# Plan: Research Vercel Labs `ai-cli` for project and coding-harness use

## Goal

Produce a source-grounded recommendation artifact showing where `vercel-labs/ai-cli` is useful, redundant, or unsafe across this repository's agent tooling and coding harnesses.

## Current context / assumptions

- Target repository: `https://github.com/vercel-labs/ai-cli`.
- Research the latest stable release, currently `v0.5.1` (released 2026-09-17), rather than `main`; record the resolved tag commit before making claims.
- The active workspace is `scott-cc`, a portable skills and Claude Code plugin repository. Relevant local surfaces already identified:
  - `agents/deep-research-agent.md` — the requested adversarial research agent contract.
  - `skills/pas-pipeline/SKILL.md` — bounded multi-provider coding pipeline guidance.
  - `skills/beads/scripts/hermes_discovery_harness.py` — model-backed skill-routing evaluation harness.
  - `evaluation/beads-skill/harness/README.md` — deterministic paired-evaluation boundary.
  - `plugins/research-tools/agents/tech-stack-researcher.md` — existing technology-recommendation agent.
  - `docs/setup-architecture.md` — Claude Code, Hermes, Codex, and portable-skill integration layers.
- The checkout already contains unrelated modified and untracked files. Research must not edit, stage, clean, or reformat them.
- The requested durable artifact will be `docs/research/ai-cli-project-fit.md`. Temporary source inspection belongs under `${TMPDIR:-/tmp}/ai-cli-research`, not in the repository.
- No production integration, global npm install, credential creation, billable generation, or modification of an active Hermes/Claude profile is authorized by this plan.
- Honcho memory is unavailable in this session because `honcho.json` has no user peer; the implementer must ground project-specific claims in repository evidence rather than presumed memory.

## Architecture / proposed approach

Run one bounded deep-research subagent using the methodology in `agents/deep-research-agent.md`, but give it three explicit evidence lanes: upstream stable source, local harness integration points, and adversarial alternatives/counter-evidence. The parent agent then independently verifies every material recommendation against upstream code or current local files and writes a single decision-oriented artifact; raw notes are disposable and are not treated as evidence.

The default recommendation threshold is intentionally high: adopt `ai-cli` only where its shell-native typed evaluation, live model discovery, or media pipeline removes real custom glue. Do not recommend it merely as another `git diff | LLM` wrapper, and never place probabilistic evaluation in charge of deterministic release, security, or correctness gates.

## Step-by-step tasks

### 1. Freeze the working context and artifact scope

Read only; do not create branches or worktrees for this documentation-only investigation.

```bash
pwd
git status --short
git branch --show-current
git rev-parse HEAD
```

Expected output:

- `pwd` is the `scott-cc` repository root.
- The branch is `feature/hermes-beads-v1` unless the user has moved it since this plan was written.
- `git status --short` may show pre-existing changes. Save the output in the research agent's private notes and do not alter those paths.

Read the local contracts that define the comparison surface:

```bash
bat --style=plain --paging=never \
  agents/deep-research-agent.md \
  skills/pas-pipeline/SKILL.md \
  evaluation/beads-skill/harness/README.md \
  docs/setup-architecture.md
```

Expected result: all four files are readable; the researcher can distinguish research behavior, pipeline behavior, evaluator boundaries, and installation layers.

### 2. Resolve and inspect the upstream stable source

Use a disposable clone and resolve the release tag to an immutable commit.

```bash
research_dir="${TMPDIR:-/tmp}/ai-cli-research"
test ! -e "$research_dir" || {
  printf 'Refusing to reuse existing path: %s\n' "$research_dir" >&2
  exit 1
}
git clone --filter=blob:none --no-checkout https://github.com/vercel-labs/ai-cli.git "$research_dir"
git -C "$research_dir" fetch --tags --force
git -C "$research_dir" checkout --detach v0.5.1
git -C "$research_dir" describe --tags --exact-match
git -C "$research_dir" rev-parse HEAD
```

Expected output:

- `git describe` prints exactly `v0.5.1`.
- `git rev-parse HEAD` prints one 40-character lowercase commit SHA; record it in the artifact.
- Failure to resolve `v0.5.1` is a blocker. Do not silently substitute `main` or a prerelease.

Inspect documentation, package metadata, CLI entry points, command definitions, environment reads, and tests:

```bash
bat --style=plain --paging=never \
  "$research_dir/README.md" \
  "$research_dir/CHANGELOG.md" \
  "$research_dir/package.json" \
  "$research_dir/skills/ai-cli/SKILL.md"
rg -n "evaluate|filter|rank|pick|models|--json|process\\.env|AI_CLI_|API_KEY|exitCode|process\\.exit" \
  "$research_dir/packages" "$research_dir/skills" "$research_dir/README.md"
```

Expected result: evidence locations exist for command behavior, machine-readable output, environment variables, failure/partial-failure exit codes, and evaluation semantics. Record file paths and line numbers, not just README prose.

### 3. Launch the requested deep-research agent

Use the available subagent/delegation tool, not an improvised inline summary. The child is read-only except for private temporary notes and must return findings to the parent; it must not write the final repository artifact.

Use this complete prompt as the delegated goal:

```text
Research vercel-labs/ai-cli v0.5.1 for practical adoption in the scott-cc agent-skills repository and its coding/evaluation harnesses.

Upstream source is checked out read-only at ${TMPDIR:-/tmp}/ai-cli-research. The active project is scott-cc. Read these local files: agents/deep-research-agent.md, skills/pas-pipeline/SKILL.md, skills/beads/scripts/hermes_discovery_harness.py, evaluation/beads-skill/harness/README.md, plugins/research-tools/agents/tech-stack-researcher.md, docs/setup-architecture.md, and README.md.

Apply the R2 falsification loop from agents/deep-research-agent.md. Investigate:
1. Exact stable-version capabilities, commands, config/env vars, output contracts, exit codes, model/provider behavior, Node/runtime requirements, and license from source and tests.
2. Concrete integration candidates: typed semantic evaluation, triage/filter/rank/pick flows if they still exist in v0.5.1 source, live model discovery, multi-model comparison, media/documentation generation, and an installable portable ai-cli skill.
3. Fit with existing scott-cc surfaces: PAS pipelines, Beads/Hermes discovery evaluation, review-panel or triage workflows, research tooling, and shell-native agent workflows.
4. Duplication and conflict with existing provider CLIs, Hermes model routing, PAS, direct AI SDK/provider APIs, and deterministic Python evaluators.
5. Security, privacy, reliability, reproducibility, cost, lock-in, credential, prompt-injection, non-determinism, and CI failure-mode risks.
6. The smallest reversible experiments that could validate the top use cases without global installation, profile mutation, production access, or unbounded spend.

Source priority: tagged source/tests > recent merged PRs/issues > official docs > 2025-2026 practitioner material. Skip Stack Overflow and pre-2025 tutorials. Separate sourced fact from inference. For every material recommendation, name the strongest alternative, counter-evidence, a discriminating test, verdict (SUPPORTED/WEAKENED/REJECTED/UNRESOLVED), and confidence.

Return concise markdown containing: immutable upstream identity, capability table, local fit matrix, top 3 experiments, rejected uses, risk controls, falsification ledger, and linked sources with file:line references or URLs. Do not edit repository files, install packages globally, use credentials, invoke paid models, or claim that commands were live-tested unless they actually were.
```

Expected subagent result:

- Names the tag and immutable commit.
- Distinguishes `ai evaluate`'s exit status from application thresholds.
- Separates deterministic gates from probabilistic advisory signals.
- Includes at least three supported or weakened candidate uses, at least three rejected/low-value uses, and a complete falsification ledger.
- Provides verifiable source locations for each material capability claim.

If delegation fails, report the failure as a blocker. Do not silently replace the requested deep-research agent with a shallow parent-only answer.

### 4. Run independent local-fit and alternative checks

After the subagent returns, verify its proposed integration points in the current checkout:

```bash
rg -n "experimental_evaluate|semantic|judge|score|rank|filter|model discovery|AI_GATEWAY|OPENAI_API_KEY" \
  agents skills plugins evaluation docs README.md
rg -n "deterministic|release-blocking|scoring authority|fail-closed|threshold|provider|model" \
  evaluation/beads-skill skills/beads skills/pas-pipeline
```

Expected result:

- Existing deterministic scoring authority remains in Python harnesses.
- Existing provider/pipeline boundaries are visible and can be compared rather than guessed.
- Any claim that `ai-cli` fills a gap cites the exact local gap; overlap is labeled as overlap.

Review recent upstream activity without treating popularity as technical evidence:

```bash
gh release view v0.5.1 -R vercel-labs/ai-cli --json tagName,publishedAt,url
gh pr list -R vercel-labs/ai-cli --state merged --limit 30 \
  --json number,title,mergedAt,url
gh issue list -R vercel-labs/ai-cli --state open --limit 30 \
  --json number,title,labels,url
```

Expected result: valid JSON from each command. If GitHub authentication or network access is unavailable, disclose the gap in the artifact; source-code evidence remains primary.

Explicitly compare these alternatives for every recommended use:

1. Keep the current deterministic Python implementation.
2. Call an existing provider CLI or API directly.
3. Use PAS for orchestration and provider selection.
4. Use Hermes/Codex/Claude-native model invocation.
5. Use `ai-cli` as a narrow shell adapter.

A recommendation without this comparison is incomplete.

### 5. Design three bounded, reversible experiments

Do not execute paid model calls during research. Specify each experiment in the artifact with input fixture, exact command shape, expected machine-readable output, success metric, budget cap, and rollback.

The candidate experiments should be:

1. **Advisory triage scoring** — feed a frozen set of public, non-sensitive issue records to `ai evaluate`; compare classifications with human labels. The semantic result may annotate or prioritize, but must not close issues or pass/fail releases.
2. **Model-catalog adapter** — snapshot `ai models --json` and test whether it reduces hard-coded model metadata in a non-production discovery/reporting flow. Cache the snapshot so CI does not depend on live Gateway availability.
3. **Portable skill usability** — install the upstream `skills/ai-cli/SKILL.md` into a disposable agent home and test whether an agent chooses safe `-o`/`--json` patterns without exposing binary stdout or credentials.

For each experiment, include explicit pass/fail criteria. Suggested minimum criteria:

- zero secret or private-input exposure;
- deterministic fixture identity and retained raw JSON result hashes;
- fixed request count, timeout, and dollar ceiling before any live run;
- no authority over deterministic correctness/security/release gates;
- measurable improvement over the named alternative (less glue, better calibration, or better agent behavior).

Reject the experiment if its only benefit is stylistic convenience.

### 6. Write the durable research artifact

Create `docs/research/ai-cli-project-fit.md` with this exact structure:

```markdown
# Vercel Labs ai-cli: Project and Coding-Harness Fit

## Executive recommendation
## Scope and immutable source identity
## Methodology and evidence hierarchy
## Capability map
## Current scott-cc overlap
## Project and harness fit matrix
## Recommended experiments
### 1. Advisory triage scoring
### 2. Model-catalog adapter
### 3. Portable skill usability
## Rejected or deferred uses
## Security, privacy, cost, and reliability controls
## Adoption decision tree
## Falsification ledger
## Open questions
## Sources
```

Requirements:

- Lead with a crisp `ADOPT NARROWLY`, `DEFER`, or `REJECT` verdict and one paragraph of rationale.
- Include the upstream tag, commit, release date, license, runtime requirement, and date researched.
- Use a fit matrix with columns: `Surface`, `Candidate use`, `Existing alternative`, `Expected gain`, `Risk`, `Recommendation`, `Validation`.
- Clearly label facts, inferences, and untested hypotheses.
- Cite tagged source as GitHub permalinks containing the resolved commit SHA whenever possible.
- Include at least five source-code/test citations, all material recent PR/issue citations, and the upstream skill/README links.
- Include the deep-research agent's falsification ledger format exactly: claim/recommendation, strongest counter-evidence sought, discriminating test, verdict, confidence.
- Do not include credentials, full environment dumps, private prompts, generated secrets, or unsupported claims about projects not evidenced in the repository.
- Keep the artifact decision-oriented; target roughly 1,500-3,000 words rather than dumping research notes.

### 7. Validate the artifact and working-tree isolation

Run deterministic documentation checks:

```bash
test -s docs/research/ai-cli-project-fit.md
rg -n '^## (Executive recommendation|Scope and immutable source identity|Methodology and evidence hierarchy|Capability map|Current scott-cc overlap|Project and harness fit matrix|Recommended experiments|Rejected or deferred uses|Security, privacy, cost, and reliability controls|Adoption decision tree|Falsification ledger|Open questions|Sources)$' \
  docs/research/ai-cli-project-fit.md
rg -n 'v0\.5\.1|SUPPORTED|WEAKENED|REJECTED|UNRESOLVED|https://github\.com/vercel-labs/ai-cli/(blob|commit|pull|issues)' \
  docs/research/ai-cli-project-fit.md
git diff --check -- docs/research/ai-cli-project-fit.md
git status --short
```

Expected output:

- `test -s` exits `0`.
- The first `rg` prints every required second-level heading exactly once.
- The second `rg` finds the stable version, falsification verdicts, and immutable/reviewable GitHub sources.
- `git diff --check` exits `0` with no output.
- Relative to the baseline from task 1, the only newly introduced repository change is `docs/research/ai-cli-project-fit.md`.

Perform a manual citation audit:

- Open every source URL.
- Confirm every tagged-source permalink uses the recorded commit SHA.
- Confirm each recommendation has an alternative, risk, and discriminating test.
- Confirm no semantic model is proposed as the sole correctness, security, or release authority.

### 8. Clean temporary research state and report

Remove only the disposable clone created in task 2, after confirming its exact path:

```bash
test "$research_dir" = "${TMPDIR:-/tmp}/ai-cli-research"
rm -rf -- "$research_dir"
test ! -e "$research_dir"
```

Expected result: both `test` commands exit `0`; no repository path is removed.

Do not commit by default: the user requested research and an artifact, not a Git commit, and the checkout contains unrelated work. If the user separately authorizes a commit, stage only the artifact and verify the staged diff before committing:

```bash
git add -- docs/research/ai-cli-project-fit.md
git diff --cached --check
git diff --cached --name-only
```

Expected output: the staged-name list contains exactly `docs/research/ai-cli-project-fit.md`.

## Tests / validation

This is a research/documentation task, so a Red → Green code TDD cycle and `uv run pytest` are not applicable unless implementation work is subsequently authorized. The validation contract is instead:

1. **Red:** before writing, `test -e docs/research/ai-cli-project-fit.md` should be false unless an existing artifact is deliberately being revised.
2. **Green:** after writing, `test -s`, required-heading searches, source/verdict searches, and `git diff --check` all pass.
3. **Review:** independently open citations and challenge every material recommendation through the falsification ledger.
4. **Isolation:** compare final `git status --short` with the recorded baseline and verify no pre-existing path was altered.
5. **Optional implementation follow-up:** if the artifact recommends an experiment, create a separate implementation plan with fixture-first TDD; do not smuggle code into this research task.

## Risks, tradeoffs, and open questions

- **Probabilistic authority creep:** `ai evaluate` can look typed and machine-readable while remaining model judgment. Keep it advisory unless calibrated against a frozen corpus and paired with deterministic policy.
- **Exit-code trap:** valid false/uncertain evaluations exit `0`; callers must apply explicit thresholds (for example with `jq -e`) instead of treating process success as a positive judgment.
- **Reproducibility:** live model catalogs, provider routing, and hosted model behavior can change without a CLI release. Record model IDs, provider metadata, input hashes, timestamps, and output hashes for experiments.
- **Credential and data exposure:** AI Gateway or provider-specific keys create another secret-bearing path, and piped repository data may leave the machine. Only public/sanitized fixtures are allowed until a separate data-handling review approves more.
- **Cost opacity:** shell composability makes repeated or parallel model calls easy. Any live experiment needs fixed request counts, concurrency, timeout, and an incremental-spend ceiling approved before execution.
- **Dependency/runtime burden:** adopting a Node 22+ global CLI in otherwise Python/portable harnesses may worsen portability. Prefer disposable execution or an optional adapter over a mandatory global dependency.
- **Overlap:** `ai text` duplicates existing model-capable agents and provider CLIs; convenience alone is not enough to add another abstraction.
- **Gateway/vendor coupling:** AI Gateway simplifies model access but introduces a hosted control-plane dependency. Compare direct provider keys and existing subscription CLIs for each use case.
- **Upstream churn:** `ai-cli` is young and changed substantially between recent releases. Pin the tag/version and verify commands from source before automating them.
- **Project breadth:** this workspace proves fit for `scott-cc` and its included harnesses. Claims about unrelated private projects remain hypotheses until their repositories and data policies are inspected.
- **Open decision after research:** whether the best next step is no adoption, a portable `ai-cli` skill, or one isolated advisory evaluator experiment. The artifact must choose one and explain what evidence would change the decision.
