# Outcome Ledger

**Status: schema definition only. No code in this plugin reads or writes this ledger yet, and no
recalibration or scoring-adjustment logic exists anywhere against it — see "Explicitly out of
scope" below.**

review-panel's MERGE stage assigns every surviving finding a confidence anchor fixed at one of five
levels — **0, 25, 50, 75, 100** (see [merge-and-validate.md](merge-and-validate.md) Step 2) — but
today nothing records whether that anchor turned out to match reality: whether a 100-confidence
finding was actually a real, worth-fixing issue, or whether a 25-confidence finding that got
demoted past the evidence gate turned out to matter anyway. The outcome ledger is where that
after-the-fact signal would eventually be recorded, as raw data, for some future recalibration
effort to consume. This document defines the ledger's schema and storage location only.

## Storage location

`plugins/review-panel/outcomes.jsonl` — one JSON object per line (JSONL), append-only by
convention once anything ever writes to it.

The file exists today as an **empty (0-byte) file**, not populated with placeholder rows. Rationale
for that choice: acceptance criteria for this task ask for "the file exists in that format, even if
initially empty or with placeholder entries" — an empty file is the more honest artifact here,
because this plugin has never run an outcome-confirmation step, so there is no real recorded
outcome yet, illustrative or otherwise. A placeholder row risks being mistaken for a real data point
by whatever eventually reads this file, or copy-pasted as a template without its
`"_example": true` marker surviving. An empty file plus this schema doc's own worked example (see
below) documents the shape just as unambiguously without that risk. If a future change wants seed
rows for tooling development, add them then with an explicit `"_example": true` field per the note
in that section.

## Schema

Each line is one JSON object — one row per **outcome confirmation event** for one finding. A single
finding may appear more than once across its lifetime if it is checked at different points (e.g.
once at merge time, again after a later incident) — the ledger is an append-only event log, not a
one-row-per-finding table keyed for update-in-place.

| Field | Type | Required | Meaning |
|---|---|---|---|
| `finding_id` | string | yes | The finding's `id` as emitted in the `mode:agent` JSON contract's `findings[].id` field (e.g. `"f-001"`, see [dual-mode-contract.md](dual-mode-contract.md)) — links this ledger row back to the specific finding it's confirming. This id is only unique within one review-panel run, so `run_id` (below) is required to disambiguate across runs. |
| `run_id` | string | yes | An identifier for the review-panel run the finding came from (e.g. a timestamp, a PR number, or a git SHA of the reviewed head — whatever the invoking context has on hand). Together with `finding_id`, forms the composite key that uniquely identifies the finding being confirmed. |
| `fingerprint` | object | yes | Copy of the finding's fingerprint at merge time, per MERGE Step 1 (see [merge-and-validate.md](merge-and-validate.md)): `{"file": string, "line": integer, "normalized_title": string}`. Carried here (not just referenced by id) so the ledger remains interpretable even if the original run's full findings JSON is no longer available. |
| `seat` | string or array of strings | yes | The contributing seat(s) that originally reported the finding (MERGE's `contributing_seats`, e.g. `"Correctness/Adversarial"` or `["Correctness/Adversarial", "Fresh-Eyes"]`) — preserved for eventual per-seat calibration analysis, not just per-anchor. |
| `confidence_anchor` | integer | yes | The confidence anchor MERGE assigned this finding, one of the five fixed values: `0`, `25`, `50`, `75`, `100`. Must be one of these five — no intermediate values, matching MERGE Step 2's own constraint. |
| `severity` | string | yes | The finding's severity as merged: `"Critical"`, `"Important"`, or `"Minor"`. |
| `validation_tally` | string or null | no | The VALIDATE-stage tally this finding received, if any, in the same `"survives-refuted"` format the JSON contract uses (e.g. `"2-0"`) — see [merge-and-validate.md](merge-and-validate.md)'s Majority-survives-challenge section. `null` if the finding never reached VALIDATE (e.g. it was excluded at confidence 0). |
| `confirmed_outcome` | boolean or null | yes | The later-confirmed ground truth: `true` if the finding was confirmed to be a real, correctly-identified issue; `false` if it was confirmed to be a false positive (the anchor overstated it, or it never actually held up); `null` if outcome confirmation is still pending — this is the expected value for the vast majority of rows for the foreseeable future, since nothing yet writes confirmed outcomes. |
| `confirmed_by` | string or null | no | Who or what confirmed the outcome — e.g. a human reviewer's identifier, `"production-incident"`, `"follow-up-review-panel-run"`. `null` while `confirmed_outcome` is `null`. |
| `confirmed_at` | string (ISO 8601) or null | yes | Timestamp of the outcome confirmation event (not the original finding's timestamp). `null` while `confirmed_outcome` is `null`. |
| `notes` | string or null | no | Free-text context on why the outcome was confirmed as it was — e.g. "fix reverted 3 days later, root cause was actually elsewhere" or "confirmed real via prod incident INC-4821". |
| `_example` | boolean | only on illustrative rows | Present and `true` only on rows meant purely as documentation/seed examples, never as real recorded data. Must never appear (or must be `false`/absent) on a genuine outcome row. No such rows exist in the current `outcomes.jsonl` — see "Storage location" above for why the file is empty rather than seeded. |

### Worked example (illustrative only — not present in `outcomes.jsonl`)

```json
{"finding_id": "f-003", "run_id": "pr-1842", "fingerprint": {"file": "src/orders/checkout.ts", "line": 142, "normalized_title": "missing null check on payment token"}, "seat": ["Correctness/Adversarial", "Fresh-Eyes"], "confidence_anchor": 100, "severity": "Critical", "validation_tally": "2-0", "confirmed_outcome": true, "confirmed_by": "human-reviewer:citadelgrad", "confirmed_at": "2026-08-02T14:03:00Z", "notes": "confirmed in staging before merge", "_example": true}
{"finding_id": "f-007", "run_id": "pr-1842", "fingerprint": {"file": "src/utils/cache.ts", "line": 58, "normalized_title": "possible race condition in cache invalidation"}, "seat": "Fresh-Eyes", "confidence_anchor": 50, "severity": "Important", "validation_tally": "1-0", "confirmed_outcome": null, "confirmed_by": null, "confirmed_at": null, "notes": null, "_example": true}
```

The first row shows a fully-confirmed outcome (a 100-confidence Critical finding that was, in fact,
real). The second shows the pending state every real row starts in: outcome fields present but
null, waiting on some future confirmation event.

## Explicitly out of scope for this schema

This document defines storage and shape only. Deliberately **not** included, and not to be added
under this task:

- Any code path in review-panel (FIX, RE-REVIEW, CONVERGE, or the orchestrator's SKILL.md) that
  writes a row to `outcomes.jsonl` automatically.
- Any tooling that reads `outcomes.jsonl` to compute per-anchor accuracy, adjust future confidence
  assignments, or otherwise feed back into MERGE's Step 2 anchor rules.
- Any schema migration/versioning mechanism — if the schema changes later, that's a follow-up
  concern once a real writer/reader exists.

A future task may build a confirmation-writing mechanism (human-driven, incident-driven, or a
follow-up review-panel run checking prior findings) and, later still, a recalibration pass that
reads accumulated rows to adjust anchor thresholds. Both are out of scope here by design — this
task exists solely so that whenever that work starts, the ledger it needs already has an agreed
shape and location.
