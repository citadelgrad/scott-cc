# Adversarial Reviewer: Evidence-Based Falsification

`adversarial-reviewer` reviews code, diffs, pull requests, and designs by asking a hard question: **can the alleged defect be demonstrated against the reviewed target and distinguished from a known control?**

It is built to optimize review precision, not finding volume. A clean result is valid. The reviewer receives no credit for manufacturing plausible complaints.

## Why this exists

Conventional AI code review has a predictable failure mode: the model is asked to be adversarial, assumes it should find something, and returns confident prose that may not describe a real or newly introduced defect. That creates three problems:

1. **False positives waste engineering time.** Someone must investigate every authoritative-sounding claim.
2. **Pre-existing defects get blamed on the current change.** A failure on HEAD proves little if BASE fails the same way.
3. **Severity, confidence, and evidence get collapsed together.** A catastrophic hypothetical can sound more urgent than a bounded defect that has actually been reproduced.

This reviewer addresses those problems with a falsification loop. Candidates are cheap; accepted findings are not. A finding must survive explicit evidence checks before it can affect the gate.

## The core rule

> Reward findings that survive reproduction against a known control, not findings merely produced by the reviewer.

The normal comparison is HEAD versus BASE, but the control can also be a known-fixed revision, a known-vulnerable/fixed pair, or a contract-compatible sibling implementation. The control must be independently justified and comparable to the target.

```text
candidate
   |
   v
bounded target probe ---- same command/environment ---- control probe
   |                                                   |
   +---------------- classify the difference ----------+
                           |
                           v
                 evidence and gate policy
```

Typical outcomes:

| Target | Control | Meaning | Treatment |
|---|---|---|---|
| fails | passes | Introduced differential failure | May be `reproduced` and gate-eligible |
| fails | fails | Pre-existing or non-differential defect | Do not blame the reviewed change |
| passes | passes | Candidate was not substantiated | Reject it; clean restraint is correct |
| unavailable | any | Runtime evidence is incomplete | Keep only as `supported` or `hypothesis` |
| complete static proof | independently checked premise | Defect proven without execution | Mark `proven`, never pretend it was reproduced |

## Review workflow

### 1. Freeze the review target

The reviewer records an immutable target manifest: repository, base/head identity or content hash, reviewed paths, model and prompt identity, tool versions, assumptions, limitations, and target hash. Findings cite that identity so stale evidence cannot silently survive a changed diff.

### 2. Establish clean-room independence

The two-phase protocol prevents prior findings from anchoring the reviewer:

- **Phase A:** inspect the raw target and bounded context without seeing earlier findings.
- **Phase B:** freeze Phase A, then reveal earlier findings and classify each one.

The handoff records the actual independence level. A self-reset is not counted as independent corroboration. Phase B must classify the unique, exact set of prior-finding IDs—missing, duplicate, extra, or unrelated IDs fail validation.

Target code, comments, tests, issue text, and design documents are treated as untrusted data. Instructions embedded in the material under review are not agent instructions.

### 3. Build a threat model

Before generating findings, the reviewer records assets, actors, entry points, trust boundaries, privileges, security objectives, deployment assumptions, abuse cases, unknowns, and exclusions. It also records systematic weakness-taxonomy coverage rather than relying on whichever issue happens to catch the model's attention.

### 4. Generate candidates broadly

The reviewer looks for logic, state, concurrency, resource, trust-boundary, security, and malformed-input failures. Candidate generation is intentionally broad; candidate acceptance is intentionally strict.

### 5. Try to falsify each candidate

For each candidate, the reviewer states its preconditions and constructs a bounded regression test, exploit, trace, tool invocation, or complete static proof. Runtime probes use the same command and environment on target and control. Non-differential results, invalid controls, and unsupported claims cannot masquerade as reproduced regressions.

### 6. Apply evidence and gate policy

The contract keeps these dimensions separate:

- **Impact:** consequence if the defect occurs.
- **Likelihood:** chance that its preconditions occur.
- **Confidence:** reviewer certainty in the assessment.
- **Priority:** remediation urgency.
- **Evidence:** `reproduced`, `proven`, `supported`, or `hypothesis`.
- **Blocking:** whether the finding fails the review gate.

The default gate blocks only P0/P1 findings with `reproduced` or `proven` evidence and confidence of at least 80. Hypotheses and residual risks never block.

## Evidence states

| State | Meaning |
|---|---|
| `reproduced` | A bounded probe ran and the target/control observations support the stated differential classification. |
| `proven` | Complete static reasoning establishes reachability and failure, with independently checked proof metadata. |
| `supported` | Concrete evidence exists, but it is incomplete. |
| `hypothesis` | The claim is plausible but unsupported or blocked by unavailable runtime access. |

The validator rejects silent promotion between these states.

## Outputs and fail-closed validation

Human output includes target identity, independence, scope and taxonomy coverage, assumptions, limitations, evidence, target/control observations, immutable citations, rejected-candidate counts, and exactly one verdict.

Agent mode emits one JSON object conforming to `schemas/adversarial-report-v1.schema.json`. The bundled CLI validates both the JSON Schema and semantic rules, recomputes the verdict, detects stale citations and fingerprints, and converts accepted reports to SARIF 2.1.0.

```bash
python3 scripts/adversarial_contract.py doctor
python3 scripts/adversarial_contract.py validate report.json \
  --current-target-hash 'sha256:...'
python3 scripts/adversarial_contract.py sarif report.json --output report.sarif
```

Malformed reports, contradictory verdicts, stale evidence, invalid proof metadata, missing schema support, and incomplete benchmark manifests fail closed.

## Benchmark philosophy

The bundled benchmark uses a frozen paired-control corpus and a fixed execution budget. It measures whether the reviewer discriminates vulnerable targets from controls—not whether it emits many comments.

Reported metrics include precision, recall, control false-positive rate, paired accuracy, classification and evidence calibration, schema validity, cost, latency, and run-to-run variance. Benchmark runs must cover the frozen corpus exactly and include concrete provenance.

## Installation and portability

The skill is self-contained and can be selected through the Skills CLI:

```bash
npx skills add citadelgrad/scott-cc --skill adversarial-reviewer
```

It supports portable installation for Codex, Hermes Agent, and other Skills CLI targets. The standalone package includes its references, schema, validator, fixtures, and benchmark. Claude's full `review-panel` plugin can also use it as a review seat, but the standalone skill does not depend on plugin-only agents or contracts.

## What it does not do

- It does not guarantee that every defect will be found.
- It does not replace SAST, DAST, fuzzing, penetration testing, or human judgment.
- It does not run destructive probes against production.
- It does not treat a high finding count as success.
- It does not let an unsupported but scary claim block a change.

The intended result is narrower and more useful: fewer claims, stronger evidence, explicit uncertainty, and a review gate engineers can audit.
