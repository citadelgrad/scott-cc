# SkillRanker / TypeSafe evaluation and Hermes skill-router decision plan

## Goal

Produce an evidence-backed decision artifact that rejects SkillRanker as a Hermes dependency, preserves Hermes's deterministic hybrid-router architecture, and specifies a legally cleared, opt-in, Hermes-native Jev ambiguity experiment only if TypeSafe's terms are amended in writing.

## Current context / assumptions

### Executive decision

- Do **not** replace the proposed Hermes hybrid router with SkillRanker.
- Do **not** vendor, execute, benchmark, distribute, or shell out to SkillRanker without explicit written permission from Jeffrey Emanuel. Its license explicitly withholds rights from OpenAI, Anthropic, and people or entities acting for their benefit, and defines restricted use to include analysis, execution, testing, benchmarking, and incorporation.
- Do **not** integrate the current TypeSafe API into a third-party Hermes product or publish TypeSafe benchmark results under the current public terms. The terms limit access to evaluation, prohibit providing a product or service to third parties, prohibit developing a similar or competing product, and prohibit publishing benchmarks or performance information.
- The user's TypeSafe key solves authentication only. It does not override either license or the TypeSafe service terms, and its presence must never activate routing automatically.
- Preserve the existing Hermes proposal: exact invocation and trusted policy first; local BM25 plus optional local embeddings; at most five sanitized classifier candidates; at most one classifier call only for a frozen ambiguity predicate; at most three compatible skills; fail closed; content-free receipts.
- Incorporate **ideas**, not SkillRanker code: opaque provider handles, exact response-set validation, layered abstention, explicit `abstain` versus `unavailable` versus `error`, bounded input/output contracts, model-identity pinning, option-order robustness tests, and capability discovery.
- If permissions are obtained and a private benchmark shows material benefit, implement Jev directly against TypeSafe's documented API as an optional classifier backend behind Hermes's existing `SkillRouterAdapter`. Do not adopt SkillRanker's two-call wide-ranking pipeline.

### Repository state

The active repository is `/Volumes/qwiizlab/projects/oss/scott-cc` on branch `feature/hermes-beads-v1`. It contains an accepted design and schemas, not a router runtime:

- `docs/plans/2026-09-08-hermes-hybrid-skill-router.md`
- `docs/schemas/hermes-skill-routing-v1.schema.json`
- `docs/schemas/hermes-project-skill-routes-v1.schema.json`
- `docs/schemas/hermes-skill-routing-receipt-v1.schema.json`
- `scripts/tests/test_hermes_hybrid_skill_router_contract.py`

The runtime implementation belongs upstream in `NousResearch/hermes-agent`. This repository should hold the research artifact, architecture decision, contract changes, skill metadata migrations, and evaluation design.

The workspace was already dirty before this planning session. The implementer must preserve unrelated changes and may commit only files named by this plan.

### What the two systems actually are

| Concern | Proposed Hermes hybrid router | SkillRanker at reviewed commits |
|---|---|---|
| Product role | Native pre-turn router and guarded skill loader | Standalone Rust advisory CLI/library |
| Deterministic routing | Attachments, exact ID/alias, trusted operation-scoped project policy | Explicit skill references |
| Retrieval | Mandatory local BM25, optional local vectors, RRF | Wide Jev Choice; local retrieval mainly when roster exceeds Jev's 254-option limit |
| Remote/model calls | Zero normally; at most one on true ambiguity | Normally two TypeSafe requests: wide rank/need gate, then detailed rerank |
| Remote candidate count | At most five | Up to 254 wide; up to 32 rerank |
| Content disclosure | Sanitized intent packet and approved metadata only | Recent context, summaries, and shortlisted skill-body excerpts |
| Selection | Zero to three complementary, non-conflicting skills | Ranked list; normal suggestion flow chooses at most one |
| Repository policy | Trusted policy file and deterministic operation predicates | No equivalent authority model |
| Feedback/calibration | First-class design requirement | Advertised/planned; not implemented at reviewed commit |
| Hooks | Native Hermes turn integration is proposed | Claude hook capability was marked planned and hook-mode requests were rejected |
| Failure behavior | Preserve deterministic routes; otherwise no skill or clarification | Structured abstain/unavailable/error, but fresh implicit ranking depends on Jev |
| Platform/packaging | Python/Hermes-native target | Rust 2024, Rust 1.95, pinned nightly, unpublished crate, git dependencies, degraded non-Linux persistence |

### Ideal use cases

SkillRanker is a reasonable fit for:

- a standalone, TypeSafe-first agent where users explicitly consent to sending recent context and skill excerpts;
- manual or shadow advisory ranking over a large skill roster;
- research into wide semantic ranking, near-miss rejection, option-order stability, and candidate-level abstention;
- a single-skill recommendation flow where two provider calls are acceptable.

The Hermes hybrid router is the better fit for:

- default skill routing inside Hermes;
- exact skill requests and operation-scoped repository policy;
- privacy-sensitive work where skill bodies, paths, repository content, and raw prompts must not leave the trust boundary;
- offline and degraded-provider operation;
- multi-skill composition with conflicts and a hard maximum of three;
- auditable, content-free routing receipts and calibrated long-term feedback.

A Hermes-native Jev backend is potentially useful only for:

- the bounded ambiguity lane after deterministic routing and local retrieval;
- private, synthetic, or explicitly consented evaluation;
- independent per-candidate suitability checks in the same single request;
- model-assisted discrimination among two to five genuinely plausible candidates.

It should not be used for:

- exact or policy routes;
- ranking the entire skill inventory on every turn;
- sending full skill bodies or arbitrary frontmatter;
- silently switching providers when a key happens to exist;
- replacing local retrieval, eligibility, conflict checks, budgets, receipts, or calibration.

### Evidence pinned for the artifact

The implementer must cite immutable snapshots, not `main`:

- Local accepted design commit: `8d72f8ab74591a47fedd538f84c6d247dd3b138c`.
- SkillRanker detailed implementation review: `876b37bfa58ec67eb44ba81488c92795b17ea014`.
- SkillRanker decision/license review: `93423348dd098e143c6b048e4409fd012fc48582`.
- SkillRanker `main` moved again to `e575852ab1411a630d5da83936489ed9de32a919` by 2026-09-19 12:15 PDT. That rapid drift is itself a maturity concern; do not silently substitute it for the reviewed snapshots.
- TypeSafe Terms of Service, last updated 2025-11-19: <https://typesafe.ai/terms>.
- TypeSafe privacy policy: <https://typesafe.ai/privacy>.
- Current model documentation observed 2026-09-19: `jev-1.13.0`, `$0.042` per million input tokens, 250,000 tokens/second, 1,200 requests/minute; aliases move and limits can change: <https://docs.typesafe.ai/models.md>.
- TypeSafe skill-suggestion cookbook: <https://docs.typesafe.ai/cookbooks/skill_suggestion.md>.

The TypeSafe cookbook reports a useful but non-equivalent result: on 488 requests and a 182-skill Hermes roster, its two-call single-skill suggestion reduced wrong loads from 16.8% to 7.3% and needless loads from 9.8% to 4.0%. The report must label this as vendor-published evidence using synthetic prompts generated from skill instructions, not proof that SkillRanker beats the proposed Hermes router.

## Architecture / proposed approach

Keep Hermes's router architecture and provider boundary intact. First publish a source-pinned research/decision report and a small accepted-design addendum; then stop at a legal gate. Only after written authorization should a separate implementation plan define a clean-room, one-request Jev adapter that consumes Hermes's existing sanitized ambiguity packet and returns only supplied opaque IDs, while Hermes retains all deterministic policy, compatibility, abstention, accounting, and receipt logic.

The research artifact is the immediate deliverable. SkillRanker remains a design reference or, after permission, a black-box shadow comparator; it is never the production routing engine.

## Step-by-step tasks

### Phase 1 — establish a clean evidence baseline

#### Task 1.1 — create and claim a Beads research issue

Files changed: none.

1. Read the repository workflow:

   ```bash
   bd prime
   ```

   Expected: command help describing claim, update, close, and session-close behavior.

2. Load the `acceptance-criteria` skill and generate acceptance criteria covering:
   - source-pinned factual comparison;
   - explicit license and TypeSafe-terms gates;
   - an unambiguous recommendation;
   - ideal and rejected use cases;
   - a phased Jev experiment with privacy, quality, latency, cost, and model-drift gates;
   - no secret disclosure;
   - no execution or benchmarking of SkillRanker/TypeSafe before written permission.

3. Create and claim the issue:

   ```bash
   bd create --title "Evaluate SkillRanker and TypeSafe for Hermes skill routing" --type task --priority 1 --acceptance '<paste generated acceptance criteria>'
   bd update <new-id> --claim
   ```

   Expected: one new issue ID, then status `in_progress` assigned to the current actor.

4. Commit only tracker state if the repository's active Beads profile requires it:

   ```bash
   git status --short
   ```

   Expected: the pre-existing dirty files plus Beads state; no source or document changes yet.

#### Task 1.2 — capture immutable source identities

Files changed:

- `docs/research/skillranker-typesafe-hermes-evaluation.md` (new)

1. Create the report with these sections only: `Decision`, `Scope and method`, `Pinned evidence`, `System comparison`, `Use cases`, `Options`, `Legal and privacy gates`, `Evaluation design`, `Recommendation`, `Sources`.
2. Record the exact local commit and both reviewed SkillRanker commits. Record the latest observed `main` only as drift evidence.
3. Use immutable GitHub blob URLs containing a commit hash for all SkillRanker code citations.
4. Do not quote or reproduce substantial SkillRanker source. Record behavior, symbol/path references, and short contract fragments only.
5. Verify every SkillRanker URL contains a 40-character commit:

   ```bash
   rg -n 'github\.com/Dicklesworthstone/skillranker/(blob|tree)/main' docs/research/skillranker-typesafe-hermes-evaluation.md
   ```

   Expected: no output and exit code 1.

6. Verify required identities appear:

   ```bash
   rg -n '8d72f8ab74591a47fedd538f84c6d247dd3b138c|876b37bfa58ec67eb44ba81488c92795b17ea014|93423348dd098e143c6b048e4409fd012fc48582' docs/research/skillranker-typesafe-hermes-evaluation.md
   ```

   Expected: all three hashes are present.

7. Commit:

   ```bash
   git add docs/research/skillranker-typesafe-hermes-evaluation.md
   git commit -m "docs(research): pin skill router comparison sources"
   ```

   Expected: one commit containing only the new report skeleton.

### Phase 2 — write the comprehensive comparison artifact

#### Task 2.1 — document the local Hermes baseline

File changed:

- `docs/research/skillranker-typesafe-hermes-evaluation.md`

Add a factual implementation-status section stating:

- the local repository has an accepted design, three schemas, and structural tests;
- it does not have a runtime router;
- runtime implementation belongs upstream in `NousResearch/hermes-agent`;
- exact invocation, trusted policy, local retrieval, bounded ambiguity classification, multi-skill compatibility, and content-free receipts are non-negotiable contracts;
- the old 57-character index remains a benchmark treatment and legacy fallback, not the target architecture.

Cite these local paths:

- `docs/plans/2026-09-08-hermes-hybrid-skill-router.md`
- `docs/schemas/hermes-skill-routing-v1.schema.json`
- `docs/schemas/hermes-project-skill-routes-v1.schema.json`
- `docs/schemas/hermes-skill-routing-receipt-v1.schema.json`
- `scripts/tests/test_hermes_hybrid_skill_router_contract.py`

Verify:

```bash
rg -n 'design-only|runtime|at most five|at most three|content-free|57-character' docs/research/skillranker-typesafe-hermes-evaluation.md
```

Expected: each concept has at least one explicit statement.

Commit:

```bash
git add docs/research/skillranker-typesafe-hermes-evaluation.md
git commit -m "docs(research): establish Hermes router baseline"
```

#### Task 2.2 — document SkillRanker's real implemented pipeline

File changed:

- `docs/research/skillranker-typesafe-hermes-evaluation.md`

Describe the implemented pipeline at commit `876b37...`:

1. discover and validate roster;
2. resolve explicit requests without network access;
3. normalize context;
4. locally reduce only when the roster exceeds the provider limit;
5. make a wide Jev request with one need Noul and one Choice distribution;
6. abstain below the need gate;
7. read shortlisted full skill bodies;
8. make a second Jev request with one candidate-versus-`NONE` Choice per candidate;
9. apply fit, eligibility, exclusions, scoring, and top-K;
10. emit a discriminated result.

Cite exact immutable links for:

- `src/cli.rs`
- `src/pipeline.rs`
- `src/jev/codec.rs`
- `src/jev/wide.rs`
- `src/jev/rerank.rs`
- `src/scoring.rs`
- `src/output.rs`
- `src/capabilities.rs`
- `src/privacy/profiles.rs`
- `src/effects.rs`
- `src/config.rs`
- `Cargo.toml`
- `rust-toolchain.toml`

State the reviewed defaults: 254 Choice options; shortlist 8; final top-K 5; need gate 0.30; fit threshold 0.30; recent context 5 messages. Label final softmax weights as relative ranking weights, not calibrated probabilities.

Verify:

```bash
rg -n '254|shortlist.*8|top-K.*5|0\.30|five.*messages|not calibrated' docs/research/skillranker-typesafe-hermes-evaluation.md
```

Expected: every reviewed bound is explicit.

Commit:

```bash
git add docs/research/skillranker-typesafe-hermes-evaluation.md
git commit -m "docs(research): document SkillRanker implementation"
```

#### Task 2.3 — distinguish implemented features from marketing/plans

File changed:

- `docs/research/skillranker-typesafe-hermes-evaluation.md`

Add a maturity table with evidence:

- implemented: `decide`, `scan`, `list`, `show`, `capabilities`;
- planned at reviewed commit: feedback import/export, calibration, rank command, and Claude hook adapters;
- no stable tags or releases during research;
- crate version `0.1.0`, `publish = false`, Rust 1.95, pinned nightly, direct Git dependencies;
- non-Linux persistence/cache degradation;
- no visible CI workflow at the reviewed commit;
- `main` changed multiple times during the research window.

Do not call planned behavior implemented because it appears in a README.

Verify:

```bash
rg -n 'implemented|planned|0\.1\.0|publish = false|Rust 1\.95|nightly|non-Linux|no tags|no releases|main.*changed' docs/research/skillranker-typesafe-hermes-evaluation.md
```

Expected: all maturity caveats appear.

Commit:

```bash
git add docs/research/skillranker-typesafe-hermes-evaluation.md
git commit -m "docs(research): assess SkillRanker maturity"
```

#### Task 2.4 — write the ideal-use-case analysis

File changed:

- `docs/research/skillranker-typesafe-hermes-evaluation.md`

Add three explicit lists:

- `Good SkillRanker fits` — standalone TypeSafe-first advisory routing, explicit disclosure consent, manual/shadow analysis, single-skill selection.
- `Good Hermes hybrid-router fits` — deterministic/project policy, local-first privacy, degraded-provider operation, 0–3 complementary skills, auditable receipts.
- `Good Jev ambiguity-backend fits` — only 2–5 sanitized candidates after local retrieval, one request, opt-in, private benchmark first.

Add a `Bad fits` list rejecting broad-inventory per-turn ranking, full-body disclosure, exact/policy routes through a model, and key-presence auto-enablement.

Verify:

```bash
rg -n '^### (Good SkillRanker fits|Good Hermes hybrid-router fits|Good Jev ambiguity-backend fits|Bad fits)' docs/research/skillranker-typesafe-hermes-evaluation.md
```

Expected: exactly four headings.

Commit:

```bash
git add docs/research/skillranker-typesafe-hermes-evaluation.md
git commit -m "docs(research): map router use cases"
```

#### Task 2.5 — compare all integration options adversarially

File changed:

- `docs/research/skillranker-typesafe-hermes-evaluation.md`

Score these options in a matrix: full replacement, required subprocess adapter, vendored Rust library, optional shadow comparator, native Jev ambiguity backend, and ideas-only adoption.

For each option assess:

- architecture compatibility;
- deterministic/policy preservation;
- disclosure surface;
- provider trust;
- calls and latency;
- multi-skill behavior;
- calibration;
- installation/platform burden;
- license/terms status;
- verdict.

Required verdicts:

- full replacement: no;
- required subprocess: no;
- vendored library: no;
- optional shadow comparator: blocked pending permission, research-only if approved;
- native Jev backend: preferred experiment only after written TypeSafe permission;
- ideas-only adoption: yes now, limited to independently expressed contracts.

Verify:

```bash
rg -n 'Full replacement|subprocess|Vendored|shadow comparator|native Jev|ideas-only' docs/research/skillranker-typesafe-hermes-evaluation.md
```

Expected: all six options appear in the matrix and prose.

Commit:

```bash
git add docs/research/skillranker-typesafe-hermes-evaluation.md
git commit -m "docs(research): decide skill router integration options"
```

### Phase 3 — legal, privacy, and provider-boundary gates

#### Task 3.1 — add a non-lawyer legal blocker summary

File changed:

- `docs/research/skillranker-typesafe-hermes-evaluation.md`

Add a prominent note: this is an engineering risk assessment, not legal advice.

Quote only the minimum necessary phrases and link to full sources. State:

- SkillRanker's rider names OpenAI and Anthropic as restricted parties and includes analysis, testing, benchmarking, execution, and incorporation in its definition of use.
- TypeSafe's public terms allow evaluation only, disallow third-party products/services, similar/competing product development, and benchmark publication.
- No implementer should run SkillRanker or TypeSafe experiments based only on possession of the API key.
- Written authorization must identify the user/entity, intended private evaluation, possible Hermes integration, benchmark publication rights, retention/security terms, and whether an OpenAI-hosted coding agent may perform the work.

Do not speculate that the license or terms are unenforceable. Do not advise evasion or clean-room implementation until TypeSafe's service terms are resolved.

Verify:

```bash
rg -n 'not legal advice|written (permission|authorization)|third-party|benchmark|API key' docs/research/skillranker-typesafe-hermes-evaluation.md
```

Expected: the disclaimer and all blockers are explicit.

Commit:

```bash
git add docs/research/skillranker-typesafe-hermes-evaluation.md
git commit -m "docs(research): record router legal gates"
```

#### Task 3.2 — document privacy and retention implications

File changed:

- `docs/research/skillranker-typesafe-hermes-evaluation.md`

Compare:

- SkillRanker standard profile sends recent normalized conversation state, summaries, and shortlisted body excerpts;
- Hermes permits only bounded intent text, opaque candidate IDs, approved capabilities/intent IDs, and context booleans;
- TypeSafe says it does not train/fine-tune on input but may process, store, analyze, improve services, use service providers, and retain personal data as reasonably necessary;
- this is not a zero-retention guarantee.

State that synthetic prompts are mandatory before a documented retention amendment or privacy approval. Prohibit prompt, secret, repository-content, absolute-path, skill-body, and tool-output canaries from crossing the provider boundary.

Verify:

```bash
rg -n 'zero-retention|synthetic|skill bod|absolute path|tool output|service provider|retain' docs/research/skillranker-typesafe-hermes-evaluation.md
```

Expected: privacy claims and exclusions appear.

Commit:

```bash
git add docs/research/skillranker-typesafe-hermes-evaluation.md
git commit -m "docs(research): define TypeSafe privacy boundary"
```

### Phase 4 — incorporate safe design lessons into the accepted architecture

#### Task 4.1 — add a source-independent design addendum

Files changed:

- `docs/plans/2026-09-08-hermes-hybrid-skill-router.md`
- `docs/research/skillranker-typesafe-hermes-evaluation.md`

Append a short `External classifier and design-donor decision` section to the accepted plan. It must state:

1. SkillRanker is not a dependency, vendored component, or default subprocess.
2. External classifier providers are disabled by default and cannot activate from credential presence.
3. A provider-facing request uses locally bound opaque candidate handles.
4. Responses must contain exactly the requested question IDs and option IDs; unknown, missing, duplicate, out-of-range, or non-normalized values invalidate the entire classifier result.
5. Provider/model identity must be versioned and recorded; moving aliases cannot share calibration strata.
6. Classifier outcomes distinguish `selected`, `abstain`, `unavailable`, and `error` internally while preserving the existing content-free receipt policy.
7. Global need, candidate fit, score/margin, eligibility, and conflict checks are separate abstention layers.
8. Provider scores are uncalibrated until validated against Hermes outcome data.
9. No external provider can receive skill bodies, arbitrary descriptions, paths, files, secrets, tool output, or raw repository content.
10. Legal and provider-terms clearance is a prerequisite, not a deployment checklist item.

Do not copy SkillRanker wording or implementation. Express the principles against Hermes's own contracts.

Verify:

```bash
rg -n 'External classifier and design-donor decision|opaque|exactly the requested|moving aliases|uncalibrated|disabled by default|Legal' docs/plans/2026-09-08-hermes-hybrid-skill-router.md
```

Expected: every new invariant is discoverable.

Run the existing contract test before committing:

```bash
uv run pytest scripts/tests/test_hermes_hybrid_skill_router_contract.py -q
```

Expected: all existing contract tests pass.

Commit:

```bash
git add docs/plans/2026-09-08-hermes-hybrid-skill-router.md docs/research/skillranker-typesafe-hermes-evaluation.md
git commit -m "docs(hermes): constrain external skill classifiers"
```

#### Task 4.2 — decide whether schemas need a follow-up issue

Files changed: Beads state only unless no follow-up is needed.

Review `docs/schemas/hermes-skill-routing-receipt-v1.schema.json` against the addendum. Do not add provider names, rationale, prompts, candidate text, or exception bodies to the content-free receipt.

Create a follow-up bead only if one of these cannot be represented safely:

- route outcome class;
- versioned provider/model stratum;
- classifier unavailable/error accounting;
- exact request/API/token/cost accounting.

If needed, first load `acceptance-criteria`, then create the issue:

```bash
bd create --title "Version Hermes routing receipt for classifier strata" --type task --priority 2 --acceptance '<generated acceptance criteria>'
```

Expected: either a single justified issue ID or a report note saying the existing schema already covers the requirement. No speculative schema churn.

### Phase 5 — specify the permission-gated Jev experiment

#### Task 5.1 — write explicit go/no-go prerequisites

File changed:

- `docs/research/skillranker-typesafe-hermes-evaluation.md`

Add a checklist that blocks all live calls until written authorization covers:

- the intended user/entity;
- private evaluation;
- integration into Hermes for third-party users;
- public or private benchmark reporting;
- model/version availability and support expectations;
- retention, deletion, service providers, and security;
- use by OpenAI- or Anthropic-hosted coding agents where applicable;
- SkillRanker execution/benchmarking separately from direct TypeSafe API use.

The plan must say `NO-GO` if any required permission remains ambiguous.

Verify:

```bash
rg -n 'NO-GO|private evaluation|third-party users|benchmark reporting|retention|OpenAI|Anthropic' docs/research/skillranker-typesafe-hermes-evaluation.md
```

Expected: all permission dimensions appear.

Commit:

```bash
git add docs/research/skillranker-typesafe-hermes-evaluation.md
git commit -m "docs(research): gate Jev router experiments"
```

#### Task 5.2 — specify, but do not implement, the native adapter contract

Files changed:

- `docs/research/skillranker-typesafe-hermes-evaluation.md`

Describe the future upstream implementation seams exactly as proposed by the accepted design:

- `agent/skill_routing_schema.py`
- `agent/skill_registry.py`
- `agent/skill_router.py`
- `agent/skill_routing_receipt.py`
- `agent/skill_utils.py`
- `agent/prompt_builder.py`
- `agent/turn_context.py`
- `tools/skills_tool.py`
- `hermes_cli/config.py`

State that a later implementation plan must first pin and inspect the upstream Hermes commit. It must not invent APIs against paths that may have changed.

Freeze this adapter behavior:

- input: one already-sanitized ambiguity packet with 2–5 opaque candidate handles;
- request: one pinned Jev model request containing one Choice over supplied handles plus `none`/`clarify`, and one Noul per candidate for independent fit;
- output: supplied handle(s), fit values, answer confidence, returned versioned model ID, usage, and typed availability/error status;
- caller-owned behavior: deterministic routes, local retrieval, thresholding, conflict checks, 0–3 selection, budgets, receipts, and fail-closed fallback;
- prohibited payloads: full skill bodies, linked files, arbitrary descriptions/frontmatter, absolute paths, repository content, secrets, raw tool output, and provider rationale;
- maximum: one request, one HTTP attempt unless the global provider ledger authorizes a bounded retry, and a total deadline no greater than 2,000 ms;
- model: pin `jev-1.13.0` for a stratum; reject or segregate a different returned model identity.

Do not include production code in this report. Implementation is forbidden until Phase 5.1 is satisfied and upstream archaeology produces a separate code plan.

Verify:

```bash
rg -n '2–5|one Choice|one Noul|0–3|2,000 ms|jev-1\.13\.0|returned model|prohibited payload' docs/research/skillranker-typesafe-hermes-evaluation.md
```

Expected: all contract bounds appear.

Commit:

```bash
git add docs/research/skillranker-typesafe-hermes-evaluation.md
git commit -m "docs(research): specify gated Jev adapter contract"
```

#### Task 5.3 — specify the private comparison matrix

File changed:

- `docs/research/skillranker-typesafe-hermes-evaluation.md`

Define these treatments:

1. `legacy_57`
2. `hybrid_lexical`
3. `hybrid_full_local`
4. `hybrid_jev_ambiguity` — permission-gated
5. `skillranker_shadow` — separately permission-gated and never allowed to affect selection

Keep the current benchmark discipline: 25 positive and 20 negative prompt families, three isolated repeats, public/hidden/sealed splits, matched identities/budgets, and no pooling across changed models, providers, question text, candidate schemas, thresholds, or commits.

Add cases for:

- exact and trusted-policy routes with zero provider calls;
- 0-, 1-, 2-, and 3-skill expected sets;
- a fourth plausible skill testing the maximum-three boundary;
- complementary and conflicting skills;
- near misses and repository-presence-only negatives;
- candidate-order permutation, opaque-handle renaming, irrelevant decoys, and duplicate-looking skills;
- Unicode normalization and multilingual requests;
- 401, 429, 529, timeout, malformed response, incomplete option sets, and model-identity drift;
- secret, prompt, skill-body, path, repository-name, and tool-output canaries.

Report these metrics:

- family-macro positive recall and negative restraint;
- exact selected-set precision, recall, and F1;
- unnecessary second/third-skill rate;
- candidate recall before classification;
- classifier invocation rate inside and outside the frozen ambiguity predicate;
- no-route accuracy and false-abstention rate;
- Brier score and reliability bins for candidate fit;
- option-order and opaque-ID instability;
- p50/p95/p99 retrieval, provider, and total latency;
- attempts, input tokens, known cost, unknown usage, and retry counts;
- payload bytes and disclosure-canary violations.

Hard gates:

- 100% exact and policy route accuracy;
- zero provider calls outside true ambiguity;
- zero prohibited disclosures or receipt-content violations;
- at most one provider request per ambiguous turn;
- positive-family macro rate at least 95% and one-sided 95% Wilson lower bound at least 85%;
- negative-family macro restraint at least 95% and one-sided 95% Wilson lower bound at least 85%;
- non-inferior positive recall within one percentage point of `hybrid_full_local`;
- strictly better ambiguous-case quality at an equal provider-call budget;
- p95 classifier duration at most 2,000 ms;
- zero infrastructure errors in the frozen final run.

The report must say no public TypeSafe or SkillRanker results may be published without written permission.

Verify:

```bash
rg -n 'legacy_57|hybrid_lexical|hybrid_full_local|hybrid_jev_ambiguity|skillranker_shadow|Brier|p50/p95/p99|Wilson|one percentage point|written permission' docs/research/skillranker-typesafe-hermes-evaluation.md
```

Expected: all treatments, metrics, and gates appear.

Commit:

```bash
git add docs/research/skillranker-typesafe-hermes-evaluation.md
git commit -m "docs(research): define skill router comparison gates"
```

### Phase 6 — review and close

#### Task 6.1 — adversarially review the report

Files changed:

- `docs/research/skillranker-typesafe-hermes-evaluation.md` only if corrections are required.

Load and apply `adversarial-reviewer` and `comments-docs`. Check specifically for:

- marketing claims presented as independent results;
- confusion between SkillRanker and the TypeSafe cookbook;
- claims based on `main` rather than pinned commits;
- “no training” incorrectly rewritten as “no retention”;
- API-key possession treated as permission;
- provider confidence treated as outcome calibration;
- planned features described as implemented;
- a recommendation that silently weakens deterministic routes or privacy;
- copied SkillRanker implementation detail beyond what is needed for interoperability analysis.

Resolve all P0/P1 findings. Record lower-severity unresolved questions in the report's `Open questions` section.

Verify:

```bash
rg -n 'vendor-published|not.*zero-retention|uncalibrated|planned|written permission|pinned' docs/research/skillranker-typesafe-hermes-evaluation.md
```

Expected: all major caveats remain explicit after editing.

Commit corrections, if any:

```bash
git add docs/research/skillranker-typesafe-hermes-evaluation.md
git commit -m "docs(research): harden skill router recommendation"
```

#### Task 6.2 — run repository quality gates

Files changed: none.

1. Run the required tests:

   ```bash
   uv run pytest
   ```

   Expected: full suite passes with zero failures.

2. Run Ruff on modified Python tracking paths. If this implementation changed no Python files, run it on the existing router contract test to satisfy the repository gate without rewriting unrelated code:

   ```bash
   uv run ruff check --fix scripts/tests/test_hermes_hybrid_skill_router_contract.py
   ```

   Expected: `All checks passed!` and no unrelated file changes.

3. Check Markdown links with the repository's existing link checker if one exists. Discover it without installing a new tool:

   ```bash
   rg -n 'markdown.*link|lychee|markdown-link-check' Makefile pyproject.toml .github scripts
   ```

   Expected: use the discovered command if present; otherwise manually request headers for only the cited public URLs and record that no repository link checker exists.

4. Verify no secret was written:

   ```bash
   rg -n 'TYPESAFE_API_KEY\s*=|Bearer [A-Za-z0-9_-]+' docs/research docs/plans
   ```

   Expected: no credential values. Documentation may mention the environment variable name only.

5. Inspect the exact diff:

   ```bash
   git diff --check
   git status --short
   git diff -- docs/research/skillranker-typesafe-hermes-evaluation.md docs/plans/2026-09-08-hermes-hybrid-skill-router.md
   ```

   Expected: no whitespace errors; only planned files plus pre-existing unrelated workspace changes.

#### Task 6.3 — close the Beads issue and hand off

Files changed: Beads state only.

1. Confirm every acceptance criterion against the report and test output.
2. Create follow-up issues for unresolved legal authorization and, only after it clears, upstream Hermes archaeology and the native Jev experiment.
3. Close the research issue:

   ```bash
   bd close <issue-id>
   ```

   Expected: issue status `closed`.

4. Follow the active Beads profile for commit/push behavior. Do not stage unrelated dirty files.
5. Final handoff must state:
   - report path;
   - recommendation: ideas yes, dependency no, direct Jev experiment only after written permission;
   - exact tests and results;
   - issue status;
   - whether commits/push occurred;
   - legal/provider blockers still open.

## Tests / validation

This task is documentation and architecture work; it must not make live TypeSafe calls or execute SkillRanker. TDD applies only if a schema or code change becomes necessary. The default plan deliberately avoids such changes under YAGNI.

Required validation:

```bash
uv run pytest scripts/tests/test_hermes_hybrid_skill_router_contract.py -q
uv run pytest
uv run ruff check --fix scripts/tests/test_hermes_hybrid_skill_router_contract.py
git diff --check
rg -n 'TYPESAFE_API_KEY\s*=|Bearer [A-Za-z0-9_-]+' docs/research docs/plans
```

Expected:

- router contract tests pass;
- the full suite passes;
- Ruff prints `All checks passed!`;
- `git diff --check` is silent;
- secret scan finds no values;
- no live provider traffic, TypeSafe charges, or SkillRanker execution occurs.

If Task 4.2 proves a schema change is necessary, use this TDD cycle instead of editing the schema directly:

1. Add one failing case to `scripts/tests/test_hermes_hybrid_skill_router_contract.py` for the exact missing structural invariant.
2. Run:

   ```bash
   uv run pytest scripts/tests/test_hermes_hybrid_skill_router_contract.py -q
   ```

   Expected: one new failure naming the missing field or invalid shape.

3. Make the minimal versioned schema change. Do not silently alter v1 semantics; add v2 if compatibility would break.
4. Rerun the focused test; expected: pass.
5. Run full `uv run pytest`; expected: zero failures.
6. Run `uv run ruff check --fix scripts/tests/test_hermes_hybrid_skill_router_contract.py`; expected: `All checks passed!`.
7. Commit test and schema together.

A future Jev adapter implementation requires a separate TDD plan after permission and upstream archaeology. Its minimum test order is: pure request-builder failure, response-validator failure, mocked transport failure matrix, accounting/receipt tests, then a permission-gated synthetic live smoke test. Never begin with a live provider call.

## Risks, tradeoffs, and open questions

### Risks

- **License risk:** SkillRanker's rider is unusually broad and directly relevant to the current OpenAI-hosted agent context. Treat this as a hard blocker, not a warning label.
- **Service-terms risk:** TypeSafe's current preview terms conflict with shipping a third-party Hermes integration and publishing benchmarks. A key is not permission.
- **Research contamination:** Because the rider defines analysis broadly, the final report should contain only the minimum independently stated interoperability facts and immutable citations; counsel or the author should clarify permitted use before any deeper execution-based work.
- **Provider privacy:** “No training” is weaker than zero retention. TypeSafe may process, store, analyze, improve services, use service providers, and retain input.
- **Architecture regression:** Adopting SkillRanker's wide two-call flow would undo Hermes's local-first retrieval, bounded ambiguity lane, provider boundary, multi-skill semantics, and latency budget.
- **Maturity:** SkillRanker was changing during this research, has no stable release, and had implemented/planned discrepancies. `main` is not a reproducible dependency.
- **Calibration:** Jev confidence and SkillRanker softmax rank weights are not probabilities that a skill will improve the user outcome.
- **Benchmark bias:** TypeSafe's published prompts were generated from skill instructions and are easier than real user requests. The vendor result is promising, not dispositive.
- **Operational coupling:** A required Rust binary plus nightly/toolchain/git dependencies is an unnecessary packaging and platform burden for Hermes.
- **Over-design:** Adding provider fields or schemas before permission would create dead architecture. Keep the immediate changes to the report and accepted-design constraints.

### Tradeoffs

- A broad Jev ranking pass may recover semantically relevant skills that BM25 misses, but it exposes more metadata, costs two round trips in SkillRanker's normal flow, and weakens local determinism.
- A one-request Jev ambiguity backend gives less context than SkillRanker's reranker, but it preserves privacy and tests the only place where a semantic model should add value.
- Ideas-only adoption yields defensive contracts immediately with no runtime dependency, but it cannot establish whether Jev improves actual selection quality.
- Private shadow evaluation minimizes production risk, but current terms still require clarification and prevent public reporting.
- Pinning `jev-1.13.0` improves reproducibility but delays automatic model improvements; promotion should be explicit and benchmarked as a new stratum.

### Open questions

1. Will Jeffrey Emanuel provide written permission covering this user, this OpenAI-hosted agent, private execution/benchmarking, and any optional interoperability work?
2. Will TypeSafe amend its terms to allow a third-party Hermes integration and private/public benchmark reporting?
3. What retention/deletion/security commitments can TypeSafe provide beyond the public privacy policy?
4. Is TypeSafe willing to provide a stable versioned model and production support contract rather than preview-only access?
5. After permission, does a single-request, five-candidate Jev ambiguity lane materially beat `hybrid_full_local` at equal provider-call and latency budgets?
6. Can candidate IDs plus approved capabilities/intent IDs provide enough semantic signal without descriptions or skill bodies?
7. Does Hermes need a receipt-schema revision for provider/model strata, or can those remain in a separate private evaluation envelope?
8. Which exact upstream Hermes commit and modules should a future implementation target? Resolve this through repository archaeology before writing code.
9. Should SkillRanker ever be tested as a black box, or is the native Jev comparator sufficient and legally simpler?

## Final recommendation to carry forward

Incorporate the **defensive design patterns** now. Do not incorporate SkillRanker itself. Seek written permission before any execution or benchmark. If permission arrives, evaluate a clean, one-request, opt-in Jev backend only in Hermes's existing ambiguity lane; promote it only if it passes the frozen privacy, deterministic-routing, quality, calibration, latency, cost, and model-drift gates above.
