# Control-Backed Findings

Reward a reviewer for findings that survive reproduction against a known control—not for producing findings. Raw finding count receives zero positive reward. A clean empty result is valid.

```text
candidate -> target probe -> control probe -> classify -> evidence policy -> gate
                 |               |
                 + same bounded probe/environment +
```

A candidate is an attack claim. A probe is a bounded test, exploit, trace, tool invocation, or complete static proof. The reviewed target is the immutable artifact under review. A known control has expected behavior established independently: preferably a paired fixed/vulnerable fixture, then the base SHA, a known-good sibling, or a minimal invariant fixture. Never choose a control merely because it makes the claim look differential.

## Decision table

| Target | Control | Classification | Gate/reward |
|---|---|---|---|
| fail | pass | introduced differential; `reproduced` | eligible under policy; reward |
| fail | fail | pre-existing/non-differential or invalid control | do not blame patch; no differential reward |
| pass | pass | rejected candidate | no finding; reward clean restraint |
| unavailable | any | `supported`/`hypothesis` with limitation | never reproduced; hypothesis cannot block |
| complete static proof | independently checked premise | `proven` | eligible under policy, not called reproduced |

Record preconditions, target/control identity, exact probe/command, environment, expected and observed result, exit code, and artifact references. Run only in isolated, bounded environments. Refuse production targets, destructive payloads, uncontrolled network access, or secrets without explicit authorization.

## Seven worked examples

1. Introduced null-token regression. Input omits `payment.token`; the regression test fails on HEAD and passes on BASE. Classify `introduced_regression`, evidence `reproduced`, P1/high, block under the default policy, positive reward.
2. Pre-existing null-token defect. The same test fails on HEAD and BASE. Classify `pre_existing_defect`; do not attribute it to the patch or grant differential reward. It may be reported separately for triage but does not make the reviewed patch causally responsible.
3. Rejected SQL-injection hypothesis. The attempted payload cannot reach the sink and both target and control reject it. Remove it from findings; increment rejected-candidate diagnostics; clean restraint is preferable to noise.
4. Vulnerable/fixed pair. A bounded exploit succeeds only on the independently known vulnerable fixture and fails on the patched fixture. This is a benchmark true positive and receives discrimination reward.
5. Missing credentials. The service probe cannot run because credentials are unavailable. Preserve a supported concern or hypothesis plus limitation; do not label it reproduced and do not block silently.
6. Known-good sibling. No useful base revision exists. Run the same malformed-input probe against an independently maintained sibling with the same contract; target fails and sibling passes. Reproduced if environment parity is established.
7. Bad control. Target fails, but the proposed control uses different dependencies/configuration. Classify `invalid_control`; the result is inconclusive until a comparable control exists. No differential reward and no reproduced label.

## Copyable human finding

```text
P1 — introduced regression — reproduced — blocking
Preconditions: payment.token omitted.
Target HEAD: `pytest -q test_null_token.py` -> exit 1, null dereference.
Control BASE: same command/environment -> exit 0.
Citation: HEAD:path:line plus immutable target hash.
```

Schema-valid examples for introduced, pre-existing, rejected, and residual cases live in `tests/fixtures/`. Validate them with:

```sh
python3 scripts/adversarial_contract.py validate tests/fixtures/introduced-regression.json
```

## Troubleshooting

- Flaky/nondeterministic probe: repeat within the fixed budget, record variance, and downgrade rather than cherry-picking.
- Stale SHA/hash: stop and report stale evidence; rerun against the new target.
- Unavailable tool/service: disclose limitation and use `supported`/`hypothesis`.
- Invalid control: fix parity or classify inconclusive.
- Safety refusal: record the refused operation and retain only the evidence level actually established.

Research basis: [PrimeVul](https://arxiv.org/abs/2410.04048) motivates realistic vulnerable/patched pairs; [CVE-Bench](https://arxiv.org/abs/2503.17332) motivates sandboxed exploit evaluation; the [Agentic Benchmark Checklist](https://arxiv.org/abs/2507.02825) motivates benchmark-validity controls; [OpenSSF CVE Benchmark](https://github.com/ossf-cve-benchmark/ossf-cve-benchmark) emphasizes vulnerable and patched revisions; and the [2025 CWE Top 25](https://cwe.mitre.org/top25/archive/2025/2025_cwe_top25.html) informs taxonomy coverage.
