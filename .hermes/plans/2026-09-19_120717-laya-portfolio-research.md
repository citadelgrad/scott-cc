# Laya portfolio-fit investigation plan

## Goal

Determine whether Laya offers a defensible advantage in Scott's existing projects or a genuinely useful new product, and recommend one bounded experiment—or a documented no-go—with evidence, alternatives, and explicit decision gates.

## Scope and execution boundary

This is a plan for a research investigation, not authorization to integrate Laya, train a model, download weights, deploy a service, modify Hermes, export customer data, or incur API/GPU charges. The planning turn only inspects public sources and local documentation and writes this file. Future execution produces research documents; implementation and empirical benchmarking require a subsequent experiment plan.

Do not turn research into a framework-building exercise. No generic decision-service platform, dashboard, model registry, or cross-project SDK. Do not manufacture a use case merely because the model exists. A no-go is a successful outcome.

Code implementation tasks, hence red/green/refactor cycles, are intentionally absent from this investigation. Any proposed implementation must receive its own exact-file TDD plan after its repository, input contract, dataset, and acceptance thresholds have been verified. Do not pretend a research checklist tests model quality.

## Current context and assumptions

### Verified during planning

- Active workspace: `/Volumes/qwiizlab/projects/oss/scott-cc`, branch `feature/hermes-beads-v1`. This is the portable skill/plugin repository, not a product backend. It has pre-existing tracked and untracked changes; do not stage, reset, clean, or edit them.
- Requested upstream: https://github.com/NandhaKishorM/laya.
- Latest release observed: `v0.3.3`, published `2026-09-19T09:28:56Z`; resolved commit `3152a82b974b775002da90f0f45ae7ca52140dc4`. Use this immutable baseline; record newer releases separately rather than silently changing versions.
- Upstream `pyproject.toml:5-34`: Python package, beta classifier, Apache-2.0 declaration, dependencies on PyTorch, Transformers, safetensors, Hugging Face Hub, and NumPy. Dependency lower bounds are not a tested lockfile.
- Upstream `laya/__init__.py:3-23`: public `load`, `Agent`, `Router`, and workflow presets. It emits `choice`, ordinal `score`, and boolean-probability `noul`; it does not generate summaries or explanations.
- Upstream `laya/agent.py:99-128,337-346`: public load API has no `revision` argument. Future reproducibility needs separately pinned local model snapshots, not `laya.load(..., revision=...)`.
- Upstream `laya/agent.py:155-211,264-278`: CUDA/MPS selection and CPU fallback exist; requested device does not prove actual execution device or performance.
- Upstream `laya/common.py:49-86`: question/options consume sequence budget; option descriptions and state are truncated. Encoder architectural capacity is not equivalent to the deployed decision model's effective context.
- Upstream `laya/router.py:35-47,144-163`: default model locations are subfolders in a bundled Hub repository; standalone repositories are another option. Default resident-cache size is one. Automatic workflow detection is off.
- Current upstream README explicitly calls Laya a base to specialize; it reports weak base-checkpoint typed-decision results and confident non-English failures on the English model. These are author-reported results, not independently reproduced measurements.
- The README advertises GPU latency and self-hosting economics; neither establishes latency or total cost on Scott's Mac or production hosts. Structured outputs prevent malformed generation, not incorrect decisions.

### Local portfolio anchors

These are starting points, not proof that their README still matches runtime behavior:

| Project | Verified source | Initial opportunity | Main objection |
|---|---|---|---|
| Hermes Fast Jev Compaction | `/Volumes/qwiizlab/projects/hermes-fast-jev-compaction/README.md:3-5,40-60`; `engine.py:20-31` | Local classification alternative to existing Jev decisions | Current state/request budgets are 25,000/30,000 tokens; Laya advertises much shorter contexts. A direct swap is not credible. |
| Field Guide | `/Volumes/qwiizlab/projects/field-guide/README.md:1-29` | Query intent, answerability/relevance prefilter, advisory guardrail scoring | Must beat current classifier and preserve answer quality; security must not depend on this classifier. |
| NixonNote | `/Volumes/qwiizlab/projects/nixon-note/README.md:1-18,45` | Private fixed-taxonomy note classification | Cannot replace summarization or arbitrary new tag generation; a Python model runtime adds friction to Rust/local-first operation. |
| Rosco candidate checkout | `/Volumes/qwiizlab/projects/SMB-AI-Search-Monitor/smb-ai-search-monitor/README.md:1-10,23` | Classify already-retrieved answer snippets by brand mention/context | README names an MVP; verify active Rosco ownership and current pipeline before assuming this is canonical. |
| GMP / Meal Mentor | `/Volumes/qwiizlab/projects/gmp/README.md:1-9,44-65` | Advisory support-intent triage | No autonomous refunds, medical/nutrition claims, allergen decisions, or account changes. Data availability unverified. |
| Foundry | `/Volumes/qwiizlab/projects/foundry/README.md:1-3,53-64` | Failure-log categorization and reviewer suggestions | Deterministic gates remain authoritative; model must not declare a failed gate passed. |
| Zeno | `/Volumes/qwiizlab/projects/zeno/CONTEXT.md:3-25` | Match bounded activity evidence to a goal for review | Never auto-complete goals; goals, not tasks, are its domain objects. |

Field Guide broad source search returned `Operation not permitted`; `/Volumes/qwiizlab/projects/field-guide/src` does not exist. Do not invent `src` paths or interpret access failure as absent functionality. Zeno has `CONTEXT.md`, not a root `README.md`. These discovery limits must be resolved or reported.

Honcho peer memory is unavailable in this session. Supplied persistent project notes are useful hypotheses, but current source and explicit user instructions win when they disagree. In particular, deployment descriptions in older READMEs must not drive infrastructure changes.

## Architecture / proposed approach

Run a source-first capability audit and a portfolio workflow audit in parallel, then join them in a decision matrix grounded in actual bounded classification needs. Rank by user value, labeled-data availability, error consequences, context fit, and measured-or-testable advantage over rules, a conventional classifier, and the existing model. Keep any eventual experiment offline and advisory, with deterministic validation and abstention outside Laya; recommend adoption only after held-out evaluation, not from upstream benchmark claims.

## Deliverables and evidence rules

Future research outputs live under `docs/research/laya/` in scott-cc:

- `00-sources.md`: release/commit, source register, access dates, local git revisions and dirty-state caveats.
- `01-capabilities.md`: API, model provenance, license, context, loading, calibration, deployment and failure behavior.
- `02-portfolio-fit.md`: source-backed opportunity cards for the seven existing projects above.
- `03-alternatives.md`: rules, conventional classification, current provider, and appropriate small local model comparisons.
- `04-new-projects.md`: three new-product hypotheses, each with a real user workflow and rejection criteria.
- `05-experiment-spec.md`: one selected experiment specification, or explicit no-go conditions if none qualifies.
- `06-decision.md`: ranked shortlist, recommendation, blockers, dissent, and next authorized action.

Every consequential assertion gets an immutable upstream URL or local `absolute/path:line` plus revision. Mark it `verified-source`, `author-reported`, `hypothesis`, or `unknown`. Runtime behavior inferred from code is not a measured result. Missing evidence stays missing; no invented accuracy, traffic, pricing, labels, or market demand. Do not copy secrets or private conversations into the documents.

## Step-by-step research tasks

Each numbered unit is a 2–5 minute focused pass. Where repetition is specified, execute one pass per named file/project; the overall investigation is not a five-minute task. Dependencies are explicit. Read-only command examples below may be run during research; creation of deliverable documents starts only after execution is authorized.

### 1. Establish a reproducible baseline

Dependency: none. Output: `docs/research/laya/00-sources.md`.

Run from `/Volumes/qwiizlab/projects/oss/scott-cc`:

```sh
pwd
git branch --show-current
git status --short
git rev-parse HEAD
```

Expected: the stated workspace, a branch name, current modifications, and a full commit SHA. Record changes from the planning snapshot rather than treating them as errors. Read `AGENTS.md`, `CLAUDE.md`, `README.md`, and `pyproject.toml` with file tools; do not run tests or package synchronization merely to investigate documentation.

Verify the upstream pin with this complete read-only command:

```sh
python3 - <<'PY'
import json
import urllib.request
base = 'https://api.github.com/repos/NandhaKishorM/laya/'
for endpoint in ('releases/latest', 'commits/v0.3.3'):
    with urllib.request.urlopen(base + endpoint, timeout=30) as response:
        value = json.load(response)
    print(json.dumps({key: value.get(key) for key in
                     ('tag_name', 'published_at', 'sha')}, sort_keys=True))
PY
```

Expected: release metadata and commit `3152a82b974b775002da90f0f45ae7ca52140dc4`. A newer latest release is a finding; a changed v0.3.3 commit is a provenance blocker. An HTTP error is an access blocker, not evidence of project abandonment.

Acceptance: baseline identifies source, retrieval date, full SHA, and local dirty-state status. Unblocks tasks 2–8.

### 2. Audit the public inference contract

Output: `docs/research/laya/01-capabilities.md`, API and context sections.

Read these exact pinned sources, one focused pass each:

- `https://raw.githubusercontent.com/NandhaKishorM/laya/3152a82b974b775002da90f0f45ae7ca52140dc4/laya/agent.py`
- Same prefix plus `laya/common.py`.
- Same prefix plus `laya/router.py`.
- Same prefix plus `laya/presets.py` and `laya/lang.py`.

For each, record symbols and line ranges for accepted inputs, output keys, confidence calculation, probability normalization, calibration temperatures, per-question batching, option limits, state truncation, routing precedence, and errors. Distinguish routing between Laya checkpoints from the `router_questions()` preset that predicts a downstream model choice.

Acceptance: the document can answer what is discarded when a long conversation enters the model, how confidence is computed, and whether unsupported/empty input raises, defaults, or silently truncates. Any unresolved answer is an explicit blocker, not guessed behavior.

### 3. Audit reproducibility, supply chain, and model rights

Output: `docs/research/laya/01-capabilities.md`, provenance/runtime sections.

Read pinned `pyproject.toml`, `setup.py`, `LICENSE`, and `laya/agent.py`; inspect Hugging Face model cards and file manifests for `convaiinnovations/laya`, `convaiinnovations/laya-multilingual`, and `convaiinnovations/laya-typed-decisions`, one model per pass. Record immutable Hub revision, weight size, bundled/subfolder relationships, encoder and tokenizer dependencies, code license versus weight/base-model/data license, and any remote-code requirement.

Specifically inspect `_fix_tokenizer_config`, `build_model`, and tokenizer/encoder fallback loading before declaring snapshots read-only or fully offline. Safetensors does not eliminate dependency or model-provenance risk. Explain how all required files could be pinned locally without an unsupported `revision` parameter on `laya.load`.

Acceptance: every artifact has a known provenance or an explicit unresolved license/reproducibility blocker. Do not download model weights or install dependencies in this task.

### 4. Audit the strength of the evidence

Output: `docs/research/laya/01-capabilities.md`, evidence limitations section.

Read pinned `README.md`, `BENCHMARKS.md`, `tests/test_criteria.py`, `tests/test_router.py`, `tests/test_local_e2e.py`, and `notebooks/laya_finetune_typed_decisions_2xT4_kaggle.ipynb`, one file/pass. Inspect notebook code and stored output as text; do not execute it.

Trace reported results to data split, teacher, training corpus, calibration set, hardware, timing boundary, baseline, and metric definition. Flag benchmark-specific fine-tuning, teacher agreement versus human truth, language-dependent overconfidence, and any inconsistent numbers. The current README references a benchmark notebook not present in the v0.3.3 tree inspected during planning; resolve version/history mismatch before claiming reproducibility.

Acceptance: each headline accuracy/latency/calibration claim is linked to a reproducible artifact or labeled author-reported and not independently reproducible from inspected files. Tiny hand-picked E2E examples are smoke checks, not deployment evidence.

### 5. Check maintenance and independent evidence

Output: `docs/research/laya/00-sources.md` and maturity section in `01-capabilities.md`.

Read https://github.com/NandhaKishorM/laya/issues, https://github.com/NandhaKishorM/laya/pulls, and https://github.com/NandhaKishorM/laya/releases. Search the exact project name/owner plus `2026`, `calibration`, `benchmark`, and `failure`. Prioritize source, independent reproductions, and substantive issue reports, not reposted release announcements.

Record release cadence, test/CI coverage, API churn, bus-factor concerns, and whether independent reproductions exist. Investigate history-rewrite provenance only as it affects pinning; do not retrieve accidentally committed sensitive material.

Acceptance: absence of independent evidence is stated plainly. No quota of links, issues, or gotchas may be satisfied by fabrication.

### 6. Map the closest existing fit: Jev compaction

Output: compaction card in `docs/research/laya/02-portfolio-fit.md`.

Read exact local paths, one per pass:

- `/Volumes/qwiizlab/projects/hermes-fast-jev-compaction/engine.py`
- `/Volumes/qwiizlab/projects/hermes-fast-jev-compaction/sidecar.mjs` (verify existence first)
- `/Volumes/qwiizlab/projects/hermes-fast-jev-compaction/tests/test_plugin.py`
- `/Volumes/qwiizlab/projects/hermes-fast-jev-compaction/tests/test_sidecar_contract.py`

Trace the request builder, Jev response parser, decision application, timeout fallback, and invariant tests. Record how original user/system/developer/assistant messages and complete tool-call/result pairs are protected. Identify whether bounded per-tool-result classification is possible without losing the long-range goal and dependency evidence necessary to keep relevant content.

Acceptance: explicitly compare (a) current Jev path, (b) deterministic recency/size pruning, and (c) Laya per-item decisions. Reject a drop-in replacement if its context cannot represent the existing decision problem. Do not delete or compact any real session history.

### 7. Map the other portfolio candidates

Output: remaining six cards in `docs/research/laya/02-portfolio-fit.md`.

Perform a separate discovery pass and a separate call-path pass for each of Field Guide, NixonNote, Rosco, GMP, Foundry, and Zeno. Start at the exact documentation paths in the portfolio table. Use bounded file searches inside each verified root to locate actual classification/model calls and their tests, then read definitions and callers with file tools. For Rosco also start at `/Volumes/qwiizlab/projects/SMB-AI-Search-Monitor/smb-ai-search-monitor/experiments/brand-matching/README.md`; verify it exists before relying on it.

Do not assume directory layouts. Store newly discovered exact code/test paths and revision in the card. Retry Field Guide's denied broad search with a root-level filename listing and narrow accessible directories; if still blocked, mark the integration unknown instead of requesting elevated access or guessing.

Each card must contain:

1. Real user and recurring decision, with a concrete input example containing no private data.
2. Existing function/caller/test paths and current decision maker.
3. Proposed fixed labels or boolean; an `unknown/abstain` handling policy outside the model.
4. Input lengths, language mix, traffic, and label availability—observed or explicitly unknown.
5. False-positive/false-negative consequences and fallback behavior.
6. Why rules or the current model may be better.
7. Smallest offline experiment and the condition that would kill it.

Acceptance: no card earns high confidence from a README alone. No deployment details are adopted from stale documents. No project repository is modified.

### 8. Identify genuinely new product opportunities

Output: `docs/research/laya/04-new-projects.md`.

Write one 2–5 minute concept pass for each hypothesis:

- Private multilingual intake inbox: classify incoming support messages into a reviewed queue without sending message bodies to a hosted classifier.
- Local workflow-review queue: categorize failures/events from existing tools and prioritize human review without granting execution or closure authority.
- Domain-specific document intake sorter: route short documents/snippets into a fixed taxonomy with visible evidence and manual correction.

These are seeds, not conclusions. For each specify one actual target user, input source, frequency, correction workflow, why existing tools are inadequate, labeled-data path, buyer/user evidence to collect, and maintenance burden. Check overlap with Rosco, NixonNote, Foundry, and Zeno; prefer an existing-project feature if it solves the same problem.

Acceptance: each concept has a concrete before/after workflow and a falsifiable rejection condition. Generic "AI decision API" wrappers and unsupported market-size claims are rejected.

### 9. Compare alternatives and real economics

Dependencies: 2–8. Output: `docs/research/laya/03-alternatives.md`.

Use one comparison pass per finalist, at most three finalists. Compare deterministic rules, TF-IDF plus logistic regression, the current project provider/model, and Laya. Include an embedding-based classifier only when an embedding pipeline already exists or the task genuinely justifies it. For compaction, Jev and deterministic retention are mandatory baselines.

Record quality evidence, calibration needs, context capacity, language fit, cold/warm latency, memory, labeling effort, operational burden, and maintenance maturity. Obtain current provider prices from primary pricing pages; do not make paid calls. If traffic or machine utilization is unknown, supply a formula with variables, not a fabricated monthly saving. Self-hosting is not free; include idle capacity, amortized training/calibration, and fallback calls.

Acceptance: each finalist has a simpler baseline and an explicit hypothesis for why Laya might outperform it. Distinguish measured figures, vendor figures, and proposed measurements.

### 10. Rank opportunities without fake precision

Dependencies: 6–9. Output: initial `docs/research/laya/06-decision.md`.

Rank as `investigate first`, `conditional`, or `reject/defer`; do not invent decimal fit scores. Mandatory gates are bounded context fit, obtainable lawful labels, reversible advisory behavior, and an advantage worth testing against the baseline. Unknown labels or unresolved context mismatch prevent an adoption recommendation.

Initial hypothesis, subject to evidence: NixonNote fixed-taxonomy organization and Field Guide query classification may be safer initial experiments than compaction; compaction is the most direct Jev comparison but has a substantial context/information-loss risk. Rosco snippet classification is promising only if simple brand matching is demonstrably insufficient.

Acceptance: one leading experiment or an explicit no-go; explain rejected alternatives and the evidence that could reverse the ranking.

### 11. Specify the experiment without building it

Dependencies: 10. Output: `docs/research/laya/05-experiment-spec.md`.

Use three separate passes: data protocol, evaluation protocol, operational protocol. Name the selected project's verified function/test files from its card. Specify a future isolated experiment workspace; do not add PyTorch to scott-cc or a product's dependencies.

Data protocol:

- Define exact label rubric, annotation authority, consent/redaction, and data retention.
- Split by source entity/thread/document before any chunking or augmentation; keep near-duplicates and translations within the same split.
- Separate training, calibration/threshold selection, and untouched test sets; temporal holdout where applicable.
- Record per-class and per-language support. Synthetic cases test mechanics and edge conditions, not real-world accuracy.
- Pick sample size from the required error bound; if labels are insufficient, classify the work as feasibility-only, never an adoption verdict.

Evaluation protocol:

- Compare majority-class baseline, simple rules/classifier, current implementation, base Laya, and optionally fine-tuned Laya as distinct arms.
- Report macro-F1, per-class precision/recall, confusion matrices, Brier score and reliability plots; include ordinal MAE only for an ordinal task. ECE needs explicit binning and sample counts.
- Sweep abstention thresholds on calibration data only; freeze them before test evaluation. Report coverage versus selective error and confidence intervals, including critical slices.
- Measure raw and calibrated probabilities separately. Do not transfer the README's example threshold of 0.85 as a policy.
- Compare the actual complete input pipeline, including context reduction; an LLM-generated summary before Laya counts toward cost and latency.
- Define task-specific downstream success: note corrections, retrieval/answer quality, or replayed task success for compaction—not just classifier agreement.

Operational protocol:

- Pin package, dependency lock, encoder/tokenizer/weight revisions, prompts/rubrics, split hashes, and seed.
- Measure requested and actual device; separate download/load/warm inference; synchronize accelerator timing; report p50/p95, memory, batch size, option count, and tokens.
- Include empty input, oversized state, huge rubrics, unsupported language, code-switching, missing checkpoint, load error, timeout, OOM/CPU fallback, and invalid probability/output cases.
- Fail safely: preserve content for compaction; keep current behavior or request review elsewhere. No new external action permissions.
- Set proposed pass/fail thresholds before execution based on current baseline and error cost. If business tolerances cannot be inferred, ask the user here rather than inventing them.

Acceptance: the experiment specifies data, baselines, measurable success and kill criteria, hardware/resource cap, and approval boundary. No model execution is claimed. If fine-tuning is necessary but labels/budget are absent, recommend deferral rather than unconditional implementation.

### 12. Adversarially review and publish the recommendation

Dependencies: 1–11. Output: final `docs/research/laya/06-decision.md`.

Perform four short review passes, documenting findings and resolutions in this file:

1. Provenance: could any current capability be an unverified README assertion or wrong-version source?
2. Integration: does context fit and do exact callers/invariants support the proposed workflow?
3. Evaluation: is there leakage, unsupported calibration, missing baseline, or an unmeasured downstream harm?
4. Simplicity: would rules, the current model, or doing nothing be better?

If a review requires structural changes, revise the affected document and repeat that review. Do not claim independent model review unless it actually occurred. Read-only research subagents may help after execution is authorized; their claims require parent verification.

Final recommendation format: one-paragraph verdict; ranked existing-project shortlist; three new-product concepts with dispositions; one experiment or no-go; required data/hardware/budget; unresolved questions; source links. Explicitly distinguish investigation complete from deployment readiness.

## Tests / validation

This phase validates research artifacts, not product code. No test suite, linter autofix, installation, service startup, model download, or commit runs in the planning turn.

After future research documents are written, run this read-only completeness check from scott-cc:

```sh
python3 - <<'PY'
from pathlib import Path
root = Path('docs/research/laya')
files = ('00-sources.md', '01-capabilities.md', '02-portfolio-fit.md',
         '03-alternatives.md', '04-new-projects.md',
         '05-experiment-spec.md', '06-decision.md')
for name in files:
    path = root / name
    assert path.is_file(), f'MISSING: {path}'
    assert path.read_text().strip(), f'EMPTY: {path}'
print('PASS: seven nonempty research documents')
PY
git diff --check -- docs/research/laya
```

Expected: `PASS: seven nonempty research documents`; tracked diff check exits zero with no output. The latter does not validate untracked files; manually inspect new documents too. Completeness is not correctness: verify every consequential source citation and each task's acceptance criterion, and reconcile every unknown with the verdict.

For subsequent code experiments, require an exact-file TDD plan: failing boundary/unit test, run to confirm intended failure, minimal implementation, green test, real-model E2E on approved data, then project-specific gates. Run `uv run pytest` and `uv run ruff check --fix` on modified Python paths under that later authorization. Mocks can exercise errors, but cannot substantiate accuracy or performance.

Frequent commits apply only if later explicitly authorized: separate source audit, portfolio/alternatives, and final experiment/decision documents. Stage only `docs/research/laya/`; never `git add .` in this dirty workspace. No commits or pushes are authorized by this plan. Do not create Beads during plan mode; if execution requires tracked work, load the Beads and acceptance-criteria skills and create dependency-linked tasks after approval.

## Risks, tradeoffs, and open questions

- Early maturity and release churn: pin source and artifacts; newer versions require a recorded comparison.
- Short context: likely decisive for Jev compaction and long documents. Raising encoder context is not a validated solution; chunking changes the decision problem.
- Miscalibration and language routing: confidently wrong predictions can bypass naive confidence gates. Domain/language-specific held-out testing and abstention are mandatory.
- Model/runtime overhead: Python/PyTorch may outweigh savings in a Rust app or low-volume workflow. Prefer existing infrastructure; no shared service until demand is proven.
- Data scarcity and leakage: teacher labels and fine-tuning-set benchmarks do not establish real user value. Lack of lawful representative labels can end the investigation.
- Security: classifier outputs are advisory, never access control, permission to run tools, proof a prompt is safe, or authority to delete history.
- Licensing: code license is not sufficient evidence for all weights, base models, or training data.
- Privacy: inspect code before data; do not upload notes, support messages, session logs, or customer responses to public tools or hosted teachers without approval.
- Portfolio ownership: verify the Rosco checkout and Field Guide source access; use local sources to resolve stale memory/document conflicts.
- Unknown current volumes, correction rates, and inference costs: collect only the measurements necessary to rank the finalists; do not undertake a portfolio-wide observability project.
- Approval questions are deferred until evidence makes them consequential: Which candidate has usable labels? Is a checkpoint download acceptable? What local RAM/accelerator budget is safe? Is any incremental paid inference/training allowed? What critical error rate is tolerable?

## Planning completion record

This plan is grounded in read-only inspection of upstream v0.3.3 source, release metadata, and local project documentation plus the compaction engine definition. No models were run, benchmarks reproduced, private data exported, project files edited, services started, or external records changed. Deep research, independent verification, and empirical validation remain future work; the plan does not imply an adoption recommendation.
