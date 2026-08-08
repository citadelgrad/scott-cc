# DEV-13 Orchestration Contract Validation

Date: 2026-07-31
Scope: repository-local Tier A orchestration skills
Disposition: source contracts fixed and verified; no commit or push performed

## Scope discovery

For this audit, **Tier A** means a skill whose primary procedure dispatches agents or sequences
multiple downstream skills/commands. This is distinct from `writing-skills-excellence`'s Tier 1
(a simple, usually single-file skill architecture). The repository-local Tier A set is:

1. `review-panel` — multi-seat agent/skill review orchestrator.
2. `design-review` — eleven-lens skill funnel used as one review-panel seat.
3. `explore-variants` — blind builders plus a three-axis judge panel.
4. `mutation-test` — entry skill for the five-agent mutation-testing workflow.
5. `triage-spine` — detector → beads → PAS → review-panel pipeline.
6. `delegate-first` — adapter around Claude Code's fork-agent/runtime worktree contract.

`diagnose` is a one-of-many router, `plan-security-review` is a standalone review procedure, and
`pas-pipeline` / `reck-factory` are CLI reference skills. They are dependencies or adjacent
routers, not Tier A orchestrators themselves.

## Baseline

The pre-change baseline was captured with:

```bash
find plugins/mutation-testing -maxdepth 3 -type f -print | sort
rg -n 'allowed-tools|subagent_type|tests_run|test_results|test_outcomes' \
  plugins/mutation-testing/skills plugins/mutation-testing/agents
claude plugin details mutation-testing@scott-cc
```

Observed failures:

- **FAIL — missing command:** the plugin documented `/mutation-test` throughout its skill and
  README but had no `commands/mutation-test.md`. Claude's component inventory reported one skill
  and five agents, with no command entry.
- **FAIL — wrong namespace:** six dispatch references used `scott-cc:test-*`; the installed
  component inventory exposes these agents under the `mutation-testing` plugin.
- **FAIL — executor schema mismatch:** the orchestrator requested flat `tests_run`, `passed`, and
  `failed` fields, while `test-executor` promised nested `test_results`.
- **FAIL — impossible zombie classification:** `test-auditor` attempted to derive every test name
  from executor results, but the executor returned only counts and failures, not per-test
  outcomes. A test that passed and a test that did not run were indistinguishable.
- **FAIL — missing auditor context:** the auditor procedure reads the test file to detect
  over-mocking, but its caller did not pass `source_file` or `test_file`.
- **FAIL — invalid-mutation scoring ambiguity:** ERROR/INVALID_MUTATION results had no explicit
  denominator rule and could be miscounted as survived mutants.

## Reference matrix

| Orchestrator | Dependency | Resolution / contract | Verdict |
|---|---|---|---|
| review-panel | `/review-panel` | `plugins/review-panel/commands/review-panel.md` | PASS |
| review-panel | Stage references | `cast-and-spawn.md`, `merge-and-validate.md`, `fix-and-rereview.md`, `converge-and-pipeline.md`, `dual-mode-contract.md`, `design-lineage.md`, `lite-mode.md` under `plugins/review-panel/skills/review-panel/references/` | PASS |
| review-panel | Shared seat output | `plugins/review-panel/contracts/reviewer-output.md` | PASS |
| review-panel | Packaging/workspace helpers | `plugins/review-panel/scripts/review-package`, `plugins/review-panel/scripts/workspace` | PASS |
| review-panel | Core/risk skills | `adversarial-reviewer`, `ponytail-review`, `ponytail-audit`, `design-review`, `domain-modeling`, `code-evolution`, `design-it-twice`, `tdd`, `data-steward`, `taste-review`, and four `mental-models-*` skills under `plugins/review-panel/skills/` | PASS |
| review-panel | Fresh-eyes agent | `plugins/review-panel/agents/clean-room-alternative.md` → `review-panel:clean-room-alternative` | PASS |
| review-panel | Security agent | `plugins/security-suite/agents/security-engineer.md` → `security-suite:security-engineer`; catalog explicitly specifies adversarial fallback + coverage-honesty when the plugin is unavailable | PASS (soft runtime dependency) |
| design-review | Eleven lenses | `complexity-recognition`, `module-boundaries`, `deep-modules`, `abstraction-quality`, `information-hiding`, `general-vs-special`, `pull-complexity-down`, `error-design`, `naming-obviousness`, `comments-docs`, `red-flags` under `plugins/review-panel/skills/` | PASS |
| explore-variants | `/explore-variants` | `plugins/variant-explorer/commands/explore-variants.md` | PASS |
| explore-variants | Builders/judges | `blind-builder.md` and `variant-judge.md` → `variant-explorer:blind-builder` / `variant-explorer:variant-judge` | PASS |
| explore-variants | Acceptance criteria | `skills/acceptance-criteria/SKILL.md` → root plugin skill | PASS |
| explore-variants | Taste/simplicity axes | `plugins/review-panel/skills/taste-review/SKILL.md` and `ponytail-review/SKILL.md` → `review-panel:*` | PASS |
| mutation-test | `/mutation-test` | `plugins/mutation-testing/commands/mutation-test.md` | PASS (added) |
| mutation-test | Entry agent | `plugins/mutation-testing/agents/test-quality-reviewer.md` → `mutation-testing:test-quality-reviewer` | PASS (fixed) |
| mutation-test | Downstream agents | `test-saboteur`, `test-executor`, `test-auditor`, `test-refactor-specialist` under `plugins/mutation-testing/agents/` → `mutation-testing:*` | PASS (fixed) |
| mutation-test | Executor → auditor result | Canonical fields: `mutation_id`, `worktree`, `status`, `test_results`, `test_outcomes`, `failures`, `execution_time_seconds`, `test_command`, `exit_code` | PASS (aligned) |
| mutation-test | Auditor input/output | Caller supplies `source_file` + `test_file`; output separates `mutations_total`, `mutations_evaluated`, and `execution_gaps` | PASS (fixed) |
| triage-spine | Detector skills/registry | `plugins/triage/skills/detectors/{lib-upgrades,prod-errors}/SKILL.md`; `triage-spine/references/detector-registry.md` | PASS |
| triage-spine | Beads + AC | `bd` 1.1.0 and `skills/acceptance-criteria/SKILL.md` | PASS (external CLI + internal skill) |
| triage-spine | Fix engine | `skills/pas-pipeline/SKILL.md`; installed `pas` 0.8.0 | PASS |
| triage-spine | Gate | `/review-panel <branch> --mode=agent`; JSON shape from `dual-mode-contract.md`; `claude` 2.1.212 + `jq` 1.8.2 | PASS |
| triage-spine | Foundry wiring | `plugins/triage/docs/foundry-recipes.md` | PASS |
| delegate-first | Skill/command | `skills/delegate-first/SKILL.md`, `commands/delegate-first.md` | PASS |
| delegate-first | Runtime | Claude Code `Agent({subagent_type: "fork", description, prompt})`; v2.1.212 installed; structured return is explicitly *not* assumed and worktree state must be independently verified | PASS (external runtime contract) |

The automated gate expands these grouped rows to 61 concrete components, verifies every local
Markdown reference, validates each component's frontmatter name, rejects stale
`scott-cc:test-*` names, checks the mutation payload fields on caller and callees, and checks the
external CLI surface (`bd`, `claude`, `git`, `jq`, `pas`).

## Changed paths and verdicts

| Path | Change | Verdict |
|---|---|---|
| `plugins/mutation-testing/commands/mutation-test.md` | Added the documented slash-command entry point and complete request contract | PASS |
| `plugins/mutation-testing/skills/mutation-test/SKILL.md` | Corrected entry-agent namespace | PASS |
| `plugins/mutation-testing/agents/test-quality-reviewer.md` | Corrected four downstream namespaces; aligned executor schema; passed auditor context; defined execution-gap denominator behavior | PASS |
| `plugins/mutation-testing/agents/test-executor.md` | Added canonical `status` and per-test `test_outcomes`; corrected example namespace | PASS |
| `plugins/mutation-testing/agents/test-auditor.md` | Consumes canonical results; distinguishes unevaluated tests; reports reduced sample size and null score on zero executable mutations | PASS |
| `plugins/mutation-testing/tests/fixtures/contract-handoff.json` | Added a complete simulated request → saboteur → executor → auditor → refactor handoff, including INVALID_MUTATION | PASS |
| `scripts/verify_orchestration_contracts.py` | Added repository-wide Tier A component/reference/payload gate | PASS |
| `scripts/tests/test_verify_orchestration_contracts.py` | Added reference and handoff regression tests | PASS |

## Post-change dry run and verification

Deterministic end-to-end handoff simulation:

```bash
uv run pytest scripts/tests/test_verify_orchestration_contracts.py -q
```

Result: `4 passed`. The dry-run fixture proves:

- all five plugin-qualified agent names resolve to declared files;
- the executor's nested result reaches the auditor without translation;
- `source_file` and `test_file` survive the caller/callee boundary;
- one COMPLETED caught mutation and one INVALID_MUTATION produce
  `mutations_total=2`, `mutations_evaluated=1`, `mutation_score=1.0`, and one execution gap;
- the refactor specialist receives the auditor's evaluated sample size.

Component/reference gate:

```bash
uv run python scripts/verify_orchestration_contracts.py
```

Result: `OK: 61 orchestration components resolve; mutation payload schemas and external CLI
surface agree`.

Claude manifest validation:

```bash
for p in plugins/review-panel plugins/variant-explorer plugins/mutation-testing \
  plugins/triage plugins/security-suite; do
  claude plugin validate --strict "$p"
done
```

Result: all five plugins passed strict manifest validation.

Repository-required gates:

```bash
uv run ruff check --fix scripts/verify_orchestration_contracts.py \
  scripts/tests/test_verify_orchestration_contracts.py
uv run python scripts/verify_plugin.py
uv run pytest
```

Results: Ruff `All checks passed`; plugin verifier `OK`; pytest `95 passed in 5.12s`.

An additional live no-tools invocation was attempted with:

```bash
claude -p --plugin-dir plugins/mutation-testing \
  --agent mutation-testing:test-quality-reviewer --allowed-tools "" \
  "Contract dry run only ..."
```

The CLI returned `Not logged in · Please run /login` before model execution. This is an honest
environment limitation, not a source-contract failure; the deterministic handoff fixture is the
recorded dry run for the changed orchestrator. Re-running the same no-tools prompt after Claude
login is the remaining optional live-runtime check.

## Remaining risks

- The locally installed `review-panel@scott-cc` cache reported 0.2.1 while this worktree and
  marketplace declare 0.3.0. Source references resolve against the 0.3.0 worktree; installed-cache
  behavior requires the normal reinstall/restart before an end-user live run.
- `security-suite` is not enabled in the current Claude plugin list. `review-panel` already has an
  explicit fail-closed fallback and coverage-honesty contract for that soft dependency.
- No commit, push, plugin reinstall, login, or destructive worktree operation was performed.
