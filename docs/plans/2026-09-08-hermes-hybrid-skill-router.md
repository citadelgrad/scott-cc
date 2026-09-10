# Hermes hybrid skill router: algorithm, receipts, and benchmark contract

Status: accepted local design for upstream implementation
Upstream context: `NousResearch/hermes-agent#13944`
Tracking issue: `scc-9cx`
Upstream source reviewed: `NousResearch/hermes-agent@0e9fc2cc152b4a4d9fd736f107412ace2a0c2555`

## Decision

Replace the model-visible, all-skills description index as the primary router with a pre-model hybrid router:

1. deterministic routing for explicit invocations and applicable authoritative repository policy;
2. bounded lexical retrieval, optionally fused with local embeddings, for implicit intent;
3. one classifier call only for a small ambiguous candidate set;
4. no skill when evidence is below the reject floor;
5. an allowlist-built, content-free receipt for every decision; and
6. a declared legacy compatibility lane for skills that have no v1 routing metadata.

The router selects skills before the main model turn. Selected skill bodies remain behind the existing `skill_view`/progressive-disclosure boundary. Hermes may preload a selected body only through the existing guarded loader and the ordinary context budget; routing metadata never substitutes for skill instructions.

This removes inventory-size-dependent prose from the system prompt. The cached system prompt contains only a constant routing protocol. A bounded route packet with selected identities and any guarded skill load is attached after that static prefix for the current turn. Per-turn routing must not rebuild `agent._cached_system_prompt` or move dynamic bytes into the provider's stable prompt-cache prefix.

## Evidence and constraints

The current upstream checkout shows the relevant seams:

- `agent/skill_utils.py` sets `SKILL_PROMPT_DESC_LIMIT = 60` and renders long descriptions as the first 57 characters plus `...`.
- `agent/prompt_builder.py::build_skills_system_prompt` scans all visible skills and renders each name plus that truncated description into the system prompt.
- `tools/skills_tool.py::skills_list` exposes name and description; `skill_view` is the full-content boundary.
- The existing prompt snapshot and LRU cache optimize rebuilding the same all-skills prompt, but do not change its O(inventory) token cost.
- Project-local skills currently precede profile and external skills. Name collision and platform/environment eligibility behavior must be retained.

The Beads discovery experiment establishes why description tuning is not an adequate router. The 57-character route reached 75/75 positive observations but only 29/60 negative-restraint observations. Their one-sided 95% Wilson lower bounds are approximately 96.5% and 38.0%, respectively. Longer descriptions were rejected because they move routing cost into every main-model request and still do not create a deterministic policy boundary.

The existing frozen benchmark contract supplies useful invariants: 75 positive and 60 negative observations, three fresh-session repeats per variant, per-family macro metrics, one-sided 95% Wilson bounds, no pooling across model/provider/Hermes/harness strata, and no retained private prompt text.

## Non-goals

- Do not infer that a tracker skill applies merely because a repository contains that tracker.
- Do not grant third-party skill metadata authority over repository policy.
- Do not send private skill bodies to an embedding provider or classifier.
- Do not persist raw user prompts, classifier rationales, or matched metadata phrases in receipts.
- Do not maintain a private Hermes fork. Implementation lands as isolated upstream modules and migration documentation.

## Metadata contract

Routing metadata lives under `metadata.hermes.routing`. Absence means legacy compatibility. Presence means strict v1 validation; a malformed declaration is never partially accepted.

The normative structural contract is
[`docs/schemas/hermes-skill-routing-v1.schema.json`](../schemas/hermes-skill-routing-v1.schema.json).
The field table and YAML below explain the contract but do not replace that schema.

Structural schema validation is necessary but not sufficient. The canonical upstream validator must perform this fail-closed sequence:

1. reject a routing block larger than 8,192 UTF-8 bytes before constructing registry records;
2. parse with a bounded safe YAML loader that rejects duplicate keys, aliases, custom tags, excessive nesting, and non-scalar surprises;
3. validate the parsed value against the structural schema;
4. normalize only for comparison, then reject duplicate normalized aliases, intent IDs, hard-route IDs, capabilities, and terms;
5. reject aliases that collide with canonical or qualified names, slash commands, or another accepted alias;
6. reject unknown capability, context-predicate, policy-key, and operation vocabulary entries;
7. reject regex/glob/instruction syntax, hard-route aliases not declared by the skill, and policy keys not present in the versioned catalog; and
8. apply source trust and existing eligibility checks before adding any automatic route.

Any failure quarantines the whole routing block from automatic use. The validator returns a typed error code only. It never includes rejected source text in a receipt or falls back to that skill's prose. JSON Schema alone cannot enforce UTF-8 byte counts, normalized property uniqueness, catalog membership, cross-record collisions, or source trust; upstream tests must exercise the canonical semantic validator as well as the schema.

```yaml
metadata:
  hermes:
    routing:
      schema_version: hermes.skill-routing.v1
      aliases: [beads, bd]
      capabilities: [issue_tracking, durable_work, dag_coordination]
      positive_intents:
        - id: tracked_work_lifecycle
          terms: [claim issue, close issue, next ready work]
          capabilities: [issue_tracking, durable_work]
          required_context: [repository]
      negative_intents:
        - id: unrelated_small_request
          terms: [one-off calculation, prose rewrite]
          effect: suppress
      conflicts: [profile/alternative-tracker]
      priority: 20
      hard_routes:
        - id: explicit_beads_alias
          kind: explicit_invocation
          aliases: [beads, bd]
        - id: repo_issue_tracker
          kind: repository_policy_key
          policy_key: issue_tracker
```

### Strict schema

| Field | Contract |
|---|---|
| `schema_version` | Required exact enum `hermes.skill-routing.v1`. Unknown versions are not auto-routable. |
| `aliases` | 0–16 unique, NFKC-stable aliases; 1–64 characters; no control characters, path separators, or invocation punctuation. |
| `capabilities` | 1–32 identifiers from a versioned Hermes capability vocabulary. Unknown capabilities are rejected, not silently ignored. |
| `positive_intents` | 1–32 entries. Each has a stable identifier, 1–16 bounded terms, optional capabilities, and optional required-context predicates. Terms are data, never instructions or regular expressions. |
| `negative_intents` | 0–32 entries with the same bounded data shape plus required `effect: suppress|penalize`. A match cannot force another skill. `suppress` is accepted only for an exact normalized phrase match; retrieval/classifier semantic matches use a bounded penalty. |
| `conflicts` | 0–16 exact qualified skill identities. Conflict affects automatic multi-load only; it does not create a route. |
| `priority` | Integer from -100 to 100. Used only after evidence class and score; it cannot outrank a stronger route class or a negative veto. Default 0. |
| `hard_routes` | 0–16 entries of the two closed kinds shown above. `explicit_invocation` only declares aliases. `repository_policy_key` only declares an addressable key; the skill cannot assert that the policy is active. |
| `required_context` | Closed predicates such as `repository`, `git_repository`, `changed_files`, `url_present`, or `named_artifact`. They filter eligibility and must be computed by Hermes, not supplied by the skill. |

Additional properties fail validation. All arrays and strings have byte and item limits. Duplicate IDs, aliases, capabilities, or normalized terms fail validation. Regexes, glob patterns, free-form classifier instructions, weights, executable hooks, file paths, and URLs are forbidden from v1 metadata.

### Trust and compatibility

Metadata trust and skill-content trust are separate:

| Source | Automatic metadata use | Hard-route authority |
|---|---|---|
| Bundled/upstream skill | Yes after schema validation | Explicit aliases; repository-policy keys only when invoked by trusted policy |
| Profile-local skill | Yes after schema validation | Explicit aliases only; no self-activated policy |
| Trusted project skill | Yes after schema validation | Explicit aliases; policy keys only when an authoritative project rule names the qualified skill |
| Attested hub/org/plugin skill with current content hash and accepted scan | Retrieval after validation | Only a hash-bound user or signed organization policy may activate it |
| Configured external/community/plugin skill without accepted attestation | Structured metadata is inactive; existing name plus 57-character description may participate only through the legacy lane | None |
| Missing v1 metadata | Legacy compatibility candidate | Exact canonical-name invocation remains deterministic |
| Declared but invalid metadata, or a source that fails quarantine | Excluded from all automatic routing | None; diagnostics expose an error code, not rejected content |

An invalid metadata block does not corrupt the registry or fall back to interpreting its prose. Exact canonical-name invocation can still load the skill through the existing guarded loader, with `metadata_status=invalid` in the receipt. Aliases from invalid metadata do not resolve. A structurally valid but unattested external block is different: none of its structured fields participate, and the underlying skill remains only on the unchanged legacy name/57-character compatibility path with `metadata_status=untrusted`. Trust comes from installation provenance and the current content hash; a skill cannot declare its own trust.

Authoritative policy comes only from `<git-root>/.hermes/skill-routes.yaml` under a root already accepted by Hermes's trusted-project mechanism. Natural-language text in `AGENTS.md`, `CLAUDE.md`, or a skill body is not parsed into a hard route. The policy file validates against
[`docs/schemas/hermes-project-skill-routes-v1.schema.json`](../schemas/hermes-project-skill-routes-v1.schema.json).
A policy rule must name a qualified skill and at least one operation predicate. Repository presence alone is not a predicate.

Example policy shape:

```yaml
schema_version: hermes.project-skill-routes.v1
rules:
  - id: tracked_work_mutation
    policy_key: issue_tracker
    when:
      operation_any: [create_issue, claim_issue, update_issue, close_issue]
    require: [project/beads]
  - id: tracker_read_only
    policy_key: issue_tracker
    when:
      operation_any: [list_ready_work, inspect_issue, inspect_blockers]
    require: [project/beads]
```

The project loader supplies source provenance and trust. Before schema parsing, it enforces a 32,768-byte UTF-8 limit and rejects duplicate keys, aliases, custom tags, and excessive nesting. After structural validation, it rejects duplicate normalized rule IDs, unknown operation or policy-key vocabulary entries, unresolved or ambiguous skill identities, and rules whose required skills do not all declare the same `policy_key` in valid routing metadata. One bad rule rejects the whole policy file. Untrusted, malformed, or ambiguous policy is ignored for hard routing and reported by code. The policy file is part of the protected project-instruction surface and follows the same trust and write-approval rules as the existing `.hermes` project tree.

Policy and receipt identities are always source-qualified. V1 uses `project/<skill>`, `profile/<skill>`, `bundled/<skill>`, and `org|external|plugin/<source-id>/<skill>`. Bare names remain valid only for explicit user invocation, where existing collision handling can ask for qualification. They are invalid in policy records, conflicts, classifier candidate IDs, and persisted receipts.

## Algorithm

### Inputs

- current user turn plus a bounded intent frame from the immediately preceding turn;
- explicit session attachments (`--skills`, cron skill attachment, slash invocation, API field);
- trusted repository-policy rules and Hermes-computed context predicates;
- eligible registry snapshot, source precedence, platform/toolset availability, and disabled set;
- frozen router configuration and optional local embedding model identity.

Do not route over full conversation history. The bounded intent frame contains at most the current request and one unresolved referent summary produced by the main runtime, with a fixed byte cap.

### Registry compilation

1. Scan with existing precedence: trusted project, profile, then external/plugin.
2. Apply existing disabled, quarantine, platform, environment, tool, and collision checks. Derive source trust and attestation from host-owned installation provenance plus the current content hash. A skill cannot influence this state.
3. Strictly validate v1 metadata. Mark absent metadata `legacy`; mark invalid metadata `invalid` with an enum error. Mark a valid block from an unattested external source `untrusted`, ignore every structured field, and place only its canonical name and first 57 description characters in the legacy index. A source that fails quarantine is excluded entirely. Never render legacy records into the main-model prompt.
4. Build an exact canonical-name/qualified-name index and validated alias index.
5. Build BM25 fields from names, aliases, capabilities, and positive intent terms. Keep negative terms in a separate index. Build a separate bounded legacy index over canonical names and first-57-character descriptions. Query both indexes on every non-deterministic route. A clear structured acceptance outranks legacy, but a marginal structured hit cannot suppress a strong legacy candidate.
6. Optionally build local embeddings from the same routing fields. Never embed a skill body, linked file, secret, path, or arbitrary frontmatter.
7. Bind the snapshot to `registry_digest`, `policy_digest`, platform/toolset digest, router config digest, and embedding model digest.

### Request normalization

Normalize matching text with Unicode NFKC, case-folding, punctuation-to-boundary conversion, and conservative tokenization. Preserve the original explicit identifier exactly for lookup and error handling; normalization never “repairs” a malformed token. After successful resolution, receipts contain only the source-qualified registry identity, never the original bare invocation text.

Derive operation predicates using deterministic syntax/host signals where possible. A repository-policy predicate must match an operation, not a topic noun. If operation extraction is uncertain, that policy rule is not a hard route and its named skill joins the retrieval candidates instead.

### Decision procedure

```text
route(request, registry, policy, budgets):
  eligible, denials = apply_safety_and_availability_gates(registry)

  pinned = validated_session_attachments(request)
  explicit = exact_invocation_matches(request, canonical_names, aliases)
  policy_required = applicable_authoritative_rules(request.operation, policy)

  hard = stable_union(pinned, explicit, policy_required)
  if hard has unresolved collision or forbidden conflict:
      return NEEDS_CLARIFICATION with receipt
  if hard is not empty:
      return SELECT(hard, route_class=highest_precedence(hard)) with receipt

  lexical = bm25(valid_metadata_records, request.intent_frame, limit=LEXICAL_K)
  vector = local_vector_search(valid_metadata_records, request.intent_frame, limit=VECTOR_K) if enabled
  structured = reciprocal_rank_fuse(lexical, vector, union_limit=CANDIDATE_K)
  structured = apply_required_context_filters(structured)
  structured = apply_negative_intent_penalties_and_conflicts(structured)
  legacy = bm25(legacy_records, request.intent_frame, limit=LEGACY_K)

  if structured.top clears ACCEPT_FLOOR and ACCEPT_MARGIN and no conflict:
      return SELECT(bounded_compatible_prefix(structured)) with receipt

  legacy_eligible = legacy candidates clearing LEGACY_REJECT_FLOOR
  if structured has no candidate clearing REJECT_FLOOR and legacy.top clears
     LEGACY_ACCEPT_FLOOR and LEGACY_ACCEPT_MARGIN:
      return SELECT(legacy.top, route_class=legacy) with receipt

  ambiguous = bounded_union(
      structured candidates clearing REJECT_FLOOR,
      legacy_eligible,
      limit=CLASSIFIER_K,
      max_legacy=1,
  )
  if ambiguous is empty:
      return NO_SKILL with receipt

  verdict = classify_from_ids_and_sanitized_routing_fields(request, ambiguous)
  if classifier unavailable, late, malformed, or below CLASSIFIER_FLOOR:
      if legacy.top independently clears LEGACY_ACCEPT_FLOOR and LEGACY_ACCEPT_MARGIN
         and no structured negative veto or declared conflict applies:
          return SELECT(legacy.top, route_class=legacy) with receipt
      return NO_SKILL (or NEEDS_CLARIFICATION for an explicit conflict) with receipt
  return SELECT(verdict.skills bounded by MAX_AUTO_LOAD) with receipt
```

### Retrieval scoring

Use deterministic BM25 as the mandatory baseline. An embedding lane is optional and local by default. Fuse independent rankings with reciprocal-rank fusion rather than averaging incomparable raw scores:

`RRF(skill) = sum(source_weight / (60 + rank_source(skill)))`

Then apply only bounded, declared modifiers:

- exact capability match: positive bounded boost;
- satisfied required context: eligibility, not an unbounded boost;
- exact normalized phrase match on a `suppress` negative intent: suppress; every approximate or classifier-level negative match: bounded penalty;
- source/author priority: tie-break after score class;
- declared conflict: prevent automatic co-load and create ambiguity when scores are close.

All scores in receipts are integer millionths after normalization. Freeze weights and thresholds before hidden/sealed evaluation. Do not tune against sealed failures.

### Ambiguity definition

The classifier is allowed only if at least one candidate clears `REJECT_FLOOR` and one of these is true:

- top score is below `ACCEPT_FLOOR`;
- top-two margin is below `ACCEPT_MARGIN`;
- candidates have a declared conflict;
- applicable policy named a skill but operation extraction was uncertain.

A request below the reject floor is “no evidence,” not ambiguity, and makes no classifier call. A high-confidence retrieval hit makes no classifier call. This is the restraint and cost boundary.

The classifier sees only: bounded request intent text, candidate qualified identities, capabilities, positive/negative intent IDs, and required-context booleans. It never sees skill bodies, linked files, arbitrary metadata, absolute paths, environment values, or repository file content. It must return constrained JSON with candidate IDs, `select|none|clarify`, and integer confidence. Free-form rationale is disabled.

The classifier must not expand the request's provider trust boundary. V1 uses either a local classifier or a classifier on the already selected main-model provider under explicit configuration. It must not silently send request text to a second provider. Every classifier call is a first-class session usage event charged to the existing API-call, token, rate-limit, and monetary-cost counters. The route is refused before the call if provider pricing is unknown, the incremental cost cannot be bounded, or any session, spend, or rate limit would be exceeded. Disabling model-backed routing leaves deterministic and lexical routing usable.

### Turn integration and cache stability

Routing runs in `agent/turn_context.py` after the current user content and trusted project context are resolved but before API messages are finalized. Its output is a typed, bounded route packet. The packet is inserted as a synthetic runtime message after the cached static system prompt and before the current user turn, using the same guarded skill-loading boundary as explicit skill invocation.

The route packet is persisted with the user turn's durable identity so retry and resume reuse the same decision. A changed registry, policy, router configuration, or trust digest makes that packet stale and requires a new decision with a new receipt. Compression preserves the selected skill identity and receipt reference, not private routing text. No routing stage mutates the cached system prompt.

### Multi-skill selection

- `MAX_AUTO_LOAD = 3`.
- Deterministic requirements are unioned unless a deny/conflict makes the set invalid.
- Retrieval may select more than one only when each clears `MULTI_ACCEPT_FLOOR`, capabilities are complementary, and no conflict exists.
- Classifier output can only choose from its supplied candidate IDs.
- Stable order is route class, descending score, priority, qualified identity.
- The ordinary skill-body/context budget is enforced after routing. If a selected body cannot fit, retain the selection but mark `load_state=deferred_budget`; give the main model the exact selected name so it can call `skill_view` deliberately. Never silently truncate routing metadata into instructions.

## Precedence table

Lower row number wins. Rows at the same level are stable-unioned, not last-writer-wins.

| Level | Route/effect | Trigger | Can auto-load? | Failure behavior |
|---:|---|---|---|---|
| 0 | Safety/availability deny | disabled, quarantined, incompatible platform/toolset, invalid namespace, unresolved collision | No | Deny candidate; explicit collision asks for qualification |
| 1 | Runtime attachment | validated `--skills`, cron attachment, slash/API structured field | Yes | Unknown identity fails that attachment loudly |
| 2 | Explicit user invocation | exact canonical/qualified name or validated alias in invocation grammar | Yes | Alias collision asks for canonical qualification |
| 3 | Authoritative repository policy | trusted rule **and** matching operation predicate | Yes | Invalid/uncertain rule cannot hard-route |
| 4 | High-confidence retrieval | score and margin clear frozen thresholds | Yes, bounded | Negative veto/conflict demotes to ambiguity or none |
| 5 | Ambiguity classifier | only the defined gray/conflict cases, candidate IDs only | Yes, bounded | Timeout/malformed/low confidence => none or clarify |
| 6 | Legacy compatibility | metadata absent, or valid metadata from an unattested external source whose structured fields were ignored; bounded local retrieval over canonical name plus the first 57 description characters | At most one | Queried beside structured retrieval so it cannot be starved; never enters the all-skills prompt or outranks a clear level 4–5 decision |
| 7 | No route | no eligible evidence | No | Main model proceeds without a skill |

Repository policy cannot override an explicit disable/quarantine. Explicit user invocation does not bypass platform incompatibility. A policy-required and explicitly requested skill normally coexist; a declared conflict returns clarification rather than silently picking one.

## Budget model

These are proposed v1 ceilings, not measurements. Benchmarks must report actual distributions and may tighten them before freeze.

```json
{
  "schema_version": "hermes.skill-router-budget.v1",
  "inventory": {"max_skills": 10000, "max_routing_metadata_bytes_per_skill": 8192},
  "request": {"max_intent_bytes": 8192, "max_context_predicates": 32},
  "retrieval": {"lexical_k": 8, "vector_k": 8, "candidate_union_k": 12},
  "classification": {
    "candidate_k": 5,
    "max_calls": 1,
    "max_input_tokens": 768,
    "max_output_tokens": 96,
    "deadline_ms": 2000,
    "max_incremental_cost_usd_micros": 10000
  },
  "selection": {"max_auto_load": 3},
  "latency_slo_ms": {
    "deterministic_p95": 10,
    "retrieval_without_classifier_p95": 75,
    "router_overhead_without_classifier_p99": 150
  },
  "cache": {
    "query_entries_per_session": 256,
    "query_ttl_seconds": 300,
    "classifier_entries_per_session": 64,
    "classifier_ttl_seconds": 300
  },
  "receipt": {"max_bytes": 16384, "max_candidates": 12}
}
```

Budget accounting is stage-specific:

- `routing_prompt_tokens`: classifier input/output only; deterministic and retrieval routes are zero-model-token decisions.
- `routing_cost_usd_micros`: classifier cost charged through the ordinary session usage ledger; local zero-cost classifiers report zero.
- `routing_api_calls`: remote classifier request count, limited to zero or one. Local classification reports zero.
- `routing_rate_limit_requests`, `routing_rate_limit_input_tokens`, and `routing_rate_limit_output_tokens`: exact classifier debit charged to the provider limiter. Local classification reports zero.
- `system_prompt_inventory_tokens`: must be zero in hybrid mode except a constant protocol block and selected identities.
- `selected_skill_tokens`: reported separately because they are useful work, not router inventory overhead.
- `latency_ms`: registry lookup, deterministic match, lexical, vector, classifier, and total.
- `cache`: registry/index/query/classifier hit or miss, never cached raw values.

Semantic receipt validation requires the per-classifier API-call, token, rate-limit, and cost values to equal their aggregate routing-budget values. A cache miss that calls a remote classifier reports one API call, one rate-limit request, actual input/output token debits, and actual cost. A classifier cache hit reports zero current-turn API calls, rate-limit debits, input/output tokens, and cost while retaining `cache_hit=true`, provider/model identity, and the cached typed verdict. A local classifier also reports zero API calls, rate-limit debits, and monetary cost. Any mismatch rejects the detailed receipt before persistence.

The local contract suite proves only the structural receipt shape, required fields, and bounds. Cross-field equality and local-versus-remote accounting require the semantic receipt validator and executable tests in implementation issue `scc-8a7`; this design does not claim that those runtime tests have run.

Timeouts fail toward restraint: deterministic results survive an optional retrieval failure; implicit routes become `none` when required evidence is unavailable. They never fall through to “load every plausible skill.”

### Cache contract

- Registry/index cache key: registry digest + policy digest + platform/toolset + router config + tokenizer/embedding model identity.
- Invalidation: content digest from metadata-bearing files and authoritative policy, not only directory mtime. Build a new immutable snapshot and atomically swap it.
- Query cache key: session-keyed HMAC of normalized bounded intent + context predicate digest + registry/config digests. Do not persist the prompt or a plain unsalted hash.
- Classifier cache: session-local exact-key cache including candidate order, classifier model/version, thresholds, and all preceding digests.
- No cache is shared across profiles, users, trust domains, or model strata.
- Metadata invalidation must make stale query/classifier entries unreachable by key.
- Disk snapshots, if retained, use profile permissions and contain routing metadata only, never user requests.

## Sanitized routing receipt

Receipts are constructed from an allowlist of typed fields. They are not logs scrubbed after the fact. No field accepts free-form model rationale or source text.

The normative receipt contract is
[`docs/schemas/hermes-skill-routing-receipt-v1.schema.json`](../schemas/hermes-skill-routing-receipt-v1.schema.json).
The standalone schema is the only receipt-shape authority. Implementations and tests must resolve it directly; the design does not duplicate a review copy that can drift. The `classifier` field is always present and is explicitly `null` when no classifier was used.

### What receipts never contain

- raw or excerpted user prompts;
- matched positive/negative phrases (only stable intent/rule IDs);
- skill descriptions, bodies, linked files, generated embeddings, or classifier rationale;
- environment values, secrets, tokens, credentials, absolute paths, repository filenames, or tool output;
- unsalted prompt hashes;
- exception messages or arbitrary provider responses.

Diagnostics default to in-memory/session scope. Persisted diagnostics require explicit configuration, profile-local permissions, a bounded TTL, and the same schema. A `request_ref` is a session-keyed HMAC and is not stable across sessions.

## Failure modes

| Failure | Required behavior | Receipt evidence |
|---|---|---|
| Invalid v1 metadata | Quarantine from automatic routing; do not parse prose as fallback | `metadata_status=invalid`, `METADATA_INVALID` |
| Valid metadata from unattested external source | Ignore all structured fields; permit only the existing bounded legacy record | `metadata_status=untrusted`, `METADATA_UNTRUSTED` |
| Source fails quarantine | Exclude the skill from structured and legacy routing | typed source-quarantine metric; no rejected content |
| Non-authoritative hard-route declaration from an otherwise attested source | Ignore hard route; retrieval may still use validated data according to source policy | no hard-route evidence ID |
| Name/alias collision | Require qualified canonical identity; never first-match | `clarify`, `EXPLICIT_COLLISION` |
| Repository merely contains tracker files | No hard route without matching authoritative operation rule | policy stage absent or candidate below floor |
| Policy parse/provenance failure | Disable policy hard routes; continue deterministic explicit route and retrieval | `POLICY_INVALID` |
| Required context unavailable | Filter candidate rather than assume context | `context_missing` |
| Lexical and vector disagree | Classifier only if one candidate clears reject floor; otherwise none | route class `classifier` or `none` |
| Embedding backend unavailable | Continue lexical-only; never make an undeclared remote call | vector latency absent from internal metrics; stable receipt outcome |
| Classifier timeout/malformed output | No implicit selection; clarify only for an explicit conflict | `CLASSIFIER_TIMEOUT`/`CLASSIFIER_INVALID` |
| Cache stale after metadata edit | Digest mismatch makes old entry unreachable; atomically rebuild | `registry=rebuilt` |
| Candidate/result exceeds top-k | Deterministically cut at configured bound | `budget_cut`, bounded counts |
| Selected body exceeds context budget | Keep route identity, defer body loading | `load_state=deferred_budget` |
| Classifier tries unknown ID | Reject entire classifier verdict | `CLASSIFIER_INVALID` |
| Receipt sanitizer encounters unknown/free text | Drop receipt write and emit minimal in-memory error counter; never serialize raw value | error metric, not raw exception |
| Legacy description false positive | Legacy lane can select at most one and cannot outrank v1 evidence | route class `legacy`; benchmark restraint regression |
| Marginal structured hit plus strong legacy hit | Admit both to the bounded ambiguity set; classifier failure may use only the independently high-confidence legacy fallback | candidate evidence and route class `classifier` or `legacy` |
| All retrieval infrastructure fails | Explicit/policy results remain valid; otherwise no skill | `none` with typed stage error metrics |

## Benchmark and evaluation contract

### Treatments

Run at least these immutable treatments:

1. `legacy_57`: pinned upstream behavior with name plus first 57 description characters in the model-visible index;
2. `hybrid_lexical`: deterministic routes plus lexical retrieval, classifier disabled;
3. `hybrid_full`: deterministic routes, lexical plus configured local embeddings, classifier only under the ambiguity predicate.

If remote embeddings are ever proposed, evaluate them as a separate opt-in treatment; do not fold them into `hybrid_full`.

Primary release comparison is paired `hybrid_full` versus `legacy_57`. `hybrid_lexical` is an ablation that proves whether the classifier or embeddings add value.

### Frozen identity

Each report and pair receipt binds:

- corpus envelope and split hashes;
- router source commit and router-config digest;
- routing metadata registry digest;
- authoritative policy digest;
- legacy implementation commit;
- Hermes commit, harness hash/schema, provider, model, tokenizer, embedding model, classifier model;
- toolset/platform and body-loading budget;
- treatment, variant, repeat, and seed;
- pristine pre-state digest.

Different identities are separate strata and are never pooled. Changing a threshold, prompt, metadata, policy, model, or router implementation requires a new stratum.

### Matrix and isolation

- Reuse the frozen 45-variant family design: 25 positive variants and 20 negative-restraint variants.
- Execute at least three fresh isolated sessions per variant per treatment: 75 positive and 60 negative observations per treatment.
- Keep public, hidden, and sealed splits. Candidate authors never read hidden/sealed prompt text.
- Pair treatments on variant, repeat, seed, model, tools, pre-state, and budgets; randomize within-pair treatment order.
- Use fresh homes, isolated request/query/classifier caches, and an exact candidate registry snapshot for every pair. A separate warm-cache performance phase may intentionally reuse caches but must not contribute behavioral outcomes.
- Pass private prompts through stdin or an equivalent non-argv channel. Retain only hashes, typed outcomes, and sanitized receipts. Delete per-scenario homes.
- Execution/infrastructure errors are `unknown`, not routing failures. Report and rerun them within a frozen cap; zero execution errors is the release gate.

### Outcome definitions

For each observation:

- positive success: the expected skill identity is selected by the router and reaches the guarded load boundary;
- negative-restraint success: the prohibited/unrelated skill is not selected or loaded;
- deterministic success: expected route class and matched rule ID are exact;
- classifier discipline success: classifier call count is 0 except when the frozen ambiguity predicate evaluates true, and never exceeds 1;
- receipt success: receipt validates, contains the exact candidate/selected identities, and passes leak canaries;
- budget success: all top-k/token/latency/cache counters are present and configured hard ceilings are respected.

A main model independently calling `skill_view` outside the router does not retroactively make a missed router observation pass. Record router selection and guarded body load as distinct events.

### Metrics

Report separately for every stratum and treatment:

- positive recall: raw successes/observations, micro rate, unweighted route-family macro, overall and per-family one-sided 95% Wilson lower bounds;
- negative restraint: the same metrics, with success meaning non-selection;
- deterministic-route accuracy and policy overreach count;
- classifier invocation rate overall and by ambiguity status; calls on non-ambiguous cases are a hard violation;
- no-route accuracy;
- top-k overflow, conflict/clarification, invalid metadata, and fallback counts;
- cold and warm latency median/p95/p99/worst for deterministic, lexical, vector, classifier, and total;
- routing input/output tokens, incremental classifier cost, session API-call/rate-limit consumption, all-skills system-prompt tokens, selected-body tokens, and total prompt delta versus legacy;
- registry/query/classifier cache hit rates and invalidation correctness;
- receipt validation, secret/private-content canary disclosures, and receipt bytes;
- paired absolute lift and paired discordant counts versus legacy.

Macro is the unweighted mean of exact family rates, not the mean of rounded percentages. Wilson uses a one-sided 95% bound (`z = 1.6448536269514722`) and raw counts. Round only for presentation.

### Release gates

The initial gate should preserve the frozen discovery standard and add architectural hard gates:

- positive macro >= 95%;
- negative-restraint macro >= 95%;
- overall positive and negative one-sided 95% Wilson lower bounds >= 85%;
- each family has >= 5 variants and each variant >= 3 fresh repeats;
- 100% deterministic explicit and applicable-policy route accuracy;
- zero repository-presence-only policy routes;
- zero classifier calls outside the frozen ambiguity predicate and <= 1 call per observation;
- zero top-k, token, selection-count, or receipt-size hard-budget violations;
- zero secret, private skill content, private prompt text, path, or canary disclosure;
- zero execution errors and complete matrix identity;
- hybrid all-skills system-prompt inventory tokens = 0;
- hybrid positive macro is non-inferior to legacy by no more than 1 percentage point, and hybrid negative-restraint macro is strictly better than legacy;
- p95 retrieval-only router overhead <= 75 ms on the declared benchmark host; classifier latency is reported separately and must meet its 2000 ms deadline.

The observed 29/60 legacy restraint is a comparator, not a relaxed hybrid gate. At 60/60 and 57/60, the one-sided Wilson lower bounds are approximately 95.7% and 88.1%; the 85% Wilson gate is therefore attainable without requiring a mathematically impossible 100% observed rate.

### Required tests

Unit tests:

- structural schema acceptance/rejection, unknown fields/version, and array/string bounds;
- canonical semantic validation for byte budgets, duplicate YAML keys/aliases/tags, normalized ID collisions, vocabulary membership, cross-record alias collisions, and source trust;
- source trust matrix and invalid-metadata quarantine;
- canonical/qualified name and alias invocation grammar;
- deterministic precedence, stable union, collision, conflict, disable/platform/tool gates;
- authoritative policy requires both provenance and operation predicate;
- negative restraint and required-context filtering;
- lexical ranking, RRF, tie-break stability, top-k and max-load bounds;
- ambiguity predicate truth table and proof that classifier is skipped outside it;
- constrained classifier output, unknown IDs, timeout, malformed response, low confidence;
- classifier usage integration with session API-call, token, rate-limit, and cost budgets, including unknown-pricing refusal;
- content-digest invalidation and profile/session cache isolation;
- receipt schema, typed allowlist construction, proof that schema validation alone is not treated as sanitization, size bound, HMAC rotation, and leak canaries;
- absent-metadata legacy route, invalid-metadata non-fallback, unattested-external legacy-only behavior, quarantine exclusion, and legacy rank ceiling.
- mixed structured/legacy cases proving a marginal structured hit cannot starve an independently strong legacy route.

Integration tests:

- upstream `build_skills_system_prompt` no longer emits all descriptions in hybrid mode;
- explicit CLI/API/cron skill attachment routes without a classifier;
- project policy routes only matching operations and does not route an unrelated request;
- selected skill reaches the existing guarded `skill_view` loader and usage accounting;
- metadata edit atomically changes registry digest and invalidates query/classifier caches;
- classifier receives only the approved bounded payload;
- diagnostics round-trip the exact sanitized receipt and no source content.

Property/fuzz tests:

- arbitrary Unicode and malformed YAML cannot create an alias/hard route or escape receipt patterns;
- output candidate and selection counts never exceed frozen bounds;
- classifier cannot select an ID outside its candidates;
- receipt serialization never includes seeded secret/prompt/body/path canaries;
- equivalent normalized requests produce deterministic lexical ranks within one registry/config identity.

Model-backed evaluation:

- execute the repeated paired matrix above;
- compute macro and Wilson metrics with the same shared implementation as the current harness;
- publish sanitized aggregate reports and pair receipts only;
- keep hidden/sealed prompt material with the benchmark custodian.

## Upstream implementation seams

Suggested modules and minimal integration points:

- `agent/skill_routing_schema.py`: strict metadata and policy types/validation;
- `agent/skill_registry.py`: immutable digest-bound routing snapshot and indexes;
- `agent/skill_router.py`: precedence, retrieval, ambiguity predicate, and selection;
- `agent/skill_routing_receipt.py`: allowlist schema construction and diagnostics;
- `agent/prompt_builder.py`: hybrid-mode constant protocol only; retain the legacy flag during migration;
- `agent/turn_context.py`: route after current-turn normalization and attach the dynamic route packet without rebuilding the cached system prompt;
- `agent/skill_utils.py`: parse routing metadata without changing exact-name resolution;
- `tools/skills_tool.py`: optional sanitized route diagnostics, still keeping full content behind `skill_view`;
- `hermes_cli/config.py`: `skills.router.mode = legacy|hybrid`, frozen budgets, local embedding opt-in;
- existing skill-management invalidation hook: clear/rebuild registry and routing caches after writes.
- trusted project-context loading: validate `<git-root>/.hermes/skill-routes.yaml` and bind its provenance and digest without interpreting natural-language context files.

Ship behind `skills.router.mode=hybrid` as an opt-in first, run the paired benchmark, then make hybrid default after gates pass. Keep `legacy` for one deprecation window and remove only after metadata migration telemetry shows acceptable coverage. The compatibility path is a migration lane, not the permanent primary router.

Migration tooling should:

1. lint v1 metadata without reading or exporting body content;
2. generate a skeleton from existing name/category/description only for author review, never auto-activate it;
3. report missing, valid, invalid, and legacy counts;
4. explain trust effects and hard-route limitations;
5. preserve exact-name loading for every existing eligible, non-quarantined skill; safety and source-quarantine denials still win.

## Rejected alternatives

| Alternative | Why rejected |
|---|---|
| Keep tuning the first 57 characters | The experiment already shows excellent recall and poor restraint. One tiny prose prefix cannot faithfully encode positive scope, exclusions, conflicts, policy, and prerequisites. |
| Raise the description limit or inject full metadata for every skill | Preserves O(inventory) prompt/token growth, harms prompt-cache stability, and makes every request pay for irrelevant skills. |
| Classifier over the full inventory on every request | O(inventory) token cost, added latency/provider dependency, privacy exposure, nondeterministic explicit routes, and weak restraint under outages. |
| Embedding-only router | Exact names and authoritative policy should not be approximate; vector thresholds drift by model/version and negatives/conflicts remain awkward. |
| Lexical-only router as the final design | It is the mandatory cheap baseline but cannot reliably resolve paraphrases or close semantic conflicts; the bounded classifier gray lane is justified. |
| Remote embeddings by default | Sends request/metadata-derived text outside the local trust boundary and creates an availability/cost dependency. Local-only is the safe default. |
| Let skills declare self-activating hard routes | Untrusted content could force itself into unrelated turns. Metadata may declare addressable keys, but only trusted runtime attachments or authoritative policy activate them. |
| Treat repository tracker presence as policy | Recreates the observed restraint failure: arithmetic, rewriting, or other unrelated work would load the tracker skill. Operation predicates are required. |
| Fall back from invalid v1 metadata to the same skill's prose | Converts malformed metadata into a permissive route and defeats fail-closed validation. Legacy compatibility is limited to absent metadata and valid-but-unattested external metadata whose structured fields are ignored. |
| Store prompt hashes in receipts | Plain hashes of short/private prompts are dictionary-testable. Use session-keyed HMAC references and short retention. |
| Store classifier rationale for observability | Rationale can quote prompts, metadata, paths, or secrets. Typed IDs, scores, verdicts, and error codes provide sufficient auditability. |
| Silently truncate selected skill bodies | Can remove safety-critical instructions. Defer the body load under the existing progressive-disclosure boundary and report `deferred_budget`. |

## Acceptance mapping

- Structured metadata: strict closed v1 schema, source trust matrix, invalid declaration quarantine.
- Deterministic routes: precedence levels 1–3, operation-scoped policy, exact receipts.
- Implicit/ambiguous intent: bounded BM25/local-vector candidates and explicit classifier gray lane.
- Auditable decision: typed content-free receipt and leak-canary contract.
- Scale/compatibility: O(selected) prompt shape, top-k/token/latency/cache budgets, and the absent-or-unattested metadata legacy lane.
- Upstream delivery: named upstream modules, feature flag, tests, migration tooling, no fork dependency.
