# Frozen Paired-Control Benchmark

The optimization loop has one mutable artifact (the skill prompt/references), one frozen corpus (`../benchmark/corpus.json`), and one fixed budget recorded in that corpus. Corpus changes require a new corpus version and a new baseline; never quietly edit fixtures while optimizing the prompt.

Every positive has a named control. The broader maintained corpus should cover representative CWEs, non-security bugs, clean patches, pre-existing defects, interprocedural cases, context pressure, empty/binary/generated/vendor diffs, unreachable and test-only paths, misleading comments, target-data prompt injection, prior-finding anchoring, severity vignettes, schema failures, and unavailable tools. This portable offline seed includes the seven method examples and is deliberately deterministic; it is the contract regression floor, not a claim of model-quality generalization.

Run:

```sh
python3 ../scripts/adversarial_contract.py evaluate baseline-results.json --corpus corpus.json
```

The report includes precision, recall, F1, false-positive rate on clean/patched controls, paired accuracy, introduced/pre-existing classification accuracy, evidence and severity calibration, citation accuracy, schema validity, cost, tokens, latency, and run-to-run variance. The score rewards precision, recall, paired discrimination, and control restraint. Finding count is diagnostic only and has no positive coefficient. `noisy-results.json` is a regression control proving extra control false positives lower the score despite more findings.

A live baseline must preserve the exact run manifest: corpus/skill hashes, model/tool versions, token/tool/time/cost ceilings, seed/repeat count, environment, and limitations. Deduplicate related fixtures and record provenance plus temporal cutoff to expose contamination risk.

Research basis and implications:

- [PrimeVul](https://arxiv.org/abs/2410.04048): realistic paired vulnerable/patched examples.
- [CVE-Bench](https://arxiv.org/abs/2503.17332): isolated, executable exploit evidence.
- [Agentic Benchmark Checklist](https://arxiv.org/abs/2507.02825): benchmark defects can overstate capability.
- [OpenSSF CVE Benchmark](https://github.com/ossf-cve-benchmark/ossf-cve-benchmark): score both vulnerable and patched revisions.
- [2025 CWE Top 25](https://cwe.mitre.org/top25/archive/2025/2025_cwe_top25.html): risk-driven weakness coverage, not a finding quota.
