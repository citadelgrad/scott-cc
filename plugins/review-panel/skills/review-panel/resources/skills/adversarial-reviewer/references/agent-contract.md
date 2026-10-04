# Agent Contract

Agent mode emits one JSON object conforming to [`../schemas/adversarial-report-v1.schema.json`](../schemas/adversarial-report-v1.schema.json). Version 1.x is additive only; a breaking field or semantic change requires 2.0.0.

The validator requires Python `jsonschema>=4.26` and fails closed when the dependency or bundled schema is unavailable. Install it with the environment's package manager before invoking `validate` or `sarif`.

## Outcomes and verdicts

The validator recomputes the verdict after filtering/suppression. Never trust a precomputed verdict.

| Outcome / surviving findings | Verdict |
|---|---|
| malformed input, unreadable target, validator/tool failure | `error` with diagnostics |
| intentionally not run | `skipped` |
| frozen target has no diff | `empty_diff` |
| no findings | `ready` |
| findings, none blocking | `ready_with_fixes` |
| one or more blocking findings | `not_ready` |

`hypothesis` findings and residual risks cannot block. The default gate blocks P0/P1 findings only when evidence is `reproduced` or `proven` and confidence is at least 80. Projects may tighten this policy, but may not silently promote hypotheses.

## Fail-closed gate

```sh
python3 "$SKILL_ROOT/scripts/adversarial_contract.py" validate "$REPORT" || exit 2
verdict=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["verdict"])' "$REPORT") || exit 2
case "$verdict" in
  ready|ready_with_fixes|skipped|empty_diff) ;;
  not_ready) exit 1 ;;
  error) exit 2 ;;
  *) exit 2 ;;
esac
```

Do not use a `jq` expression whose missing or unknown value falls through to success. `error` means infrastructure failure, not a clean review.

## Citation and provenance

The run manifest identifies repository, base/head or content identity, reviewed paths, model, prompt hash/version, tools, assumptions, limitations, and target hash. Every finding cites that immutable hash:

- current code: commit, path, start/end line;
- deleted code: base commit, diff side, hunk and line;
- prose/design: document hash, section or line range;
- cross-file claim: primary citation plus ordered related locations/data-flow path.

Validate with `--current-target-hash`; a mismatch is stale evidence, not reviewer disagreement.

## Dimensions

Keep these independent: impact, exploit/failure likelihood, reviewer confidence, remediation priority, evidence status, and blocking decision. A catastrophic but unsupported claim is not a reproduced P0. A bounded, highly reproducible defect can still deserve prompt remediation.

SARIF export is deterministic:

```sh
python3 "$SKILL_ROOT/scripts/adversarial_contract.py" sarif report.json --output report.sarif
```

It preserves stable rule IDs, semantic fingerprints, priority-derived levels, source/code-flow locations, CWE/help metadata, evidence classification, and suppression state. This is an adversarial-reviewer schema, not alleged field-for-field review-panel parity.
