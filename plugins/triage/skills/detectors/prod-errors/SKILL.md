---
name: prod-errors
description: Consumes a log/Sentry-shaped production error source and emits one normalized triage item per distinct error, carrying the stack trace verbatim in the evidence field, per the triage-spine's Triage Item Contract. Use when pointed at a log source or Sentry export, or when asked to triage a production error.
argument-hint: "[log line/file path, or Sentry issue export]"
allowed-tools: Read, Grep, Glob, Bash
---

# Prod-Errors Detector

A **detector**, not a fixer: this skill's only job is to turn a log-shaped production error into a
normalized item for `triage-spine`. It never files a bead, never reproduces the issue, and never
produces a fix itself — those are `triage-spine`'s Phases 3–5, downstream of this detector's
output (`skills/triage-spine/SKILL.md`'s registered `source: prod-errors`).

**Integration is a config detail, not a dependency.** Whether the input arrives as a raw log
tail, a file of log lines, or a Sentry issue export is irrelevant to this skill's contract — all
three reduce to the same "log line with a stack trace" shape below. This skill does not require a
live Sentry API integration to function.

## When to Apply

- Pointed at a log source (file, tail, or pasted excerpt) containing one or more error entries
- Given a Sentry-shaped issue export (title, stack trace, occurrence count)
- A human asks to triage a specific production error
- Not for reviewing code changes that might introduce new errors (that's `review-panel`'s job on a
  diff) — this detector looks at errors that have already occurred

## How to Detect

1. **Read the log source.** Accept a file path, a directory of log files, or inline pasted log
   text. Do not summarize from memory — read the actual content.
2. **Identify distinct errors.** Group log entries into distinct errors by stack trace shape (same
   exception type + same top frame), not by raw line count — repeated occurrences of the same
   underlying error are one triage item, not one per occurrence. Note the occurrence count in
   `evidence` when available.
3. **Extract the stack trace verbatim.** The full trace (or the longest available excerpt) must be
   captured character-for-character into `evidence` — this is what lets `triage-spine`'s Phase 4
   reproduce the exact code path, and what lets a human verify the finding without re-fetching logs.
4. **Map to affected paths.** Use the stack trace's file:line frames that belong to this repo
   (skip vendor/dependency frames) to populate `affected-paths`.
5. **Emit one Triage Item Contract entry per distinct error:**

```json
{
  "source": "prod-errors",
  "severity": "Critical",
  "evidence": "TypeError: Cannot read properties of null (reading 'token')\n  at processPayment (src/orders/checkout.ts:142:19)\n  at async handleCheckout (src/orders/checkout.ts:88:5)\n  — 47 occurrences in the last 24h",
  "affected-paths": ["src/orders/checkout.ts"],
  "suggested-loop": "guard payment.token before dereferencing .value in processPayment; add a regression test covering the null-token path"
}
```

- `severity`: `Critical` for an error on a critical user-facing path (payments, auth, data loss) or
  with high occurrence volume; `Important` for a real error with lower volume or a non-critical
  path; `Minor` for a low-volume, low-impact error (e.g. a benign edge case already degrading
  gracefully).
- `evidence`: the verbatim stack trace plus occurrence count/window if the log source provides one
  — never paraphrase the trace into prose.
- `affected-paths`: repo file paths from the trace's in-repo frames only.
- `suggested-loop`: the concrete fix direction implied by the trace, one line.

## Output Contract

Hand the full list of Triage Item Contract entries to `triage-spine` for Phase 1 intake. If the
log source contains zero distinct errors in the scanned window, report that plainly
(`prod-errors: clean, 0 distinct errors found`) rather than emitting nothing — `triage-spine`'s
Phase 2 zero-findings boundary depends on this detector saying so explicitly.

## Foundry note

This detector is designed to be schedulable as a periodic Foundry check pointed at a log source
(see `../../../docs/foundry-recipes.md`). It does not create or modify any `foundry.yaml` file
itself, nor does it establish a live Sentry integration — both are config/wiring concerns external
to this skill.
