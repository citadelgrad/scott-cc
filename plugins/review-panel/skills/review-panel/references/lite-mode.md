# Narrowed Review Tiers: `--lite` / `--medium` / `--auto`

Covers both narrowed tiers in this one file (SPEC Architecture invariant 1 — no parallel
`skills/review-panel-lite/` or `-medium/` directory, no per-flag file split). `--auto` is a
pre-CAST *resolver* over these same two tiers plus full, not a fourth tier of its own; its
resolution mechanism (decision table, signal definitions) lives in this file's own
"Auto resolution" section, below.

## Flag contract

- `--lite`, `--medium`, `--auto`: presence-only flags, no `=value` form. Pairwise mutually
  exclusive with each other — at most one may be present per invocation; two or more together is a
  hard error raised before CAST runs, naming the conflicting flags.
- Each is independently composable with `--mode=agent`: order does not matter, and all four flags
  (`--lite`/`--medium`/`--auto`/`--mode=agent`) may appear in any combination/order and parse to
  the same internal state.
- Selected once at invocation and held constant for the whole run, exactly like `--mode=agent`
  (SPEC Architecture invariant 6) — a run never switches tiers mid-loop.
- Full parsing/rejection detail (malformed `=false` attempts, the exclusivity check, `tier_source`
  assignment) lives in `SKILL.md`'s Setup step 1 — this file states the contract's shape, that file
  owns enforcing it.

## Narrowed guarantees, per tier

The canonical per-dimension behavior table is the SPEC's "Narrowing tiers" table
(`docs/plans/2026-07-18-review-panel-lite/review-panel-lite-spec.md`) — this section restates it as
prose guarantee strings for citation elsewhere (the human report and the `mode:agent` JSON's
`narrowed_guarantees` array both quote these verbatim; do not paraphrase a new wording at either
call site).

**Lite (`--lite`):**

1. SPAWN restricted to the Adversarial seat plus any seat forced in by fail-closed cast-when
   criteria — see [cast-and-spawn.md](cast-and-spawn.md).
2. VALIDATE capped at one validator per finding, flat, with no Critical escalation — see
   [merge-and-validate.md](merge-and-validate.md).
3. RE-REVIEW's regression re-cast limited to Adversarial (if it was the fixing seat) plus the
   fixed fail-closed seats — see [fix-and-rereview.md](fix-and-rereview.md).
4. CONVERGE capped at 1 total iteration — see [converge-and-pipeline.md](converge-and-pipeline.md).

**Medium (`--medium`):**

1. SPAWN restricted to Adversarial, Simplicity, and Structural, plus any seat forced in by
   fail-closed cast-when criteria — see [cast-and-spawn.md](cast-and-spawn.md).
2. VALIDATE capped at one validator per finding, with up to 2 for Critical findings — see
   [merge-and-validate.md](merge-and-validate.md).
3. RE-REVIEW's regression re-cast limited to whichever of {Adversarial, Simplicity, Structural}
   was the fixing seat, plus the fixed fail-closed seats — see
   [fix-and-rereview.md](fix-and-rereview.md).
4. CONVERGE capped at 2 total iterations — see [converge-and-pipeline.md](converge-and-pipeline.md).

Both tiers skip CAST Step 4 (live-scan enrichment) entirely — see
[cast-and-spawn.md](cast-and-spawn.md). Neither tier ever returns `circuit_broken`; both use the
new `capped` status (see `dual-mode-contract.md`) for the "hit the iteration cap with residual
findings" terminal case. Full mode (no tier flag, and `--auto` resolved to full) is unaffected by
any of the above — its guarantees are unchanged and its `narrowed_guarantees` value is always `[]`.

## Auto resolution

`--auto` defers tier selection to a resolver that runs once, in `SKILL.md`'s Setup (step 6, after
the diff is packaged and its stat summary captured, before CAST) — using only cheap, pre-CAST
signals computed from the diff's file list and added/removed line counts. It never reads live-scan
results and never reads file content beyond path matching; either would require work CAST itself is
responsible for, and would defeat the point of a cheap pre-CAST resolver.

### Signals

Three signals, computed once per run from the stat summary `SKILL.md` Setup step 4 (or its step 5
fallback) already captured:

- **`files_changed`**: count of distinct files touched by the diff.
- **`lines_changed`**: total added + deleted lines across every touched file.
- **`sensitive_path_match`**: `true` if any touched file's path matches the sensitive-path criteria
  `reviewers/persona-catalog.md` defines under the Security entry's "Path-identifiable subset (for
  cheap, pre-CAST signals)" and the Data Steward entry's own "Path-identifiable subset" note —
  cited from there verbatim, never redefined here (Architecture invariant 2 — no second, competing
  notion of "sensitive path" exists in this plugin; `persona-catalog.md` is the single source of
  truth for both path lists). In short: auth/crypto/secrets-handling/dependency-supply-chain paths,
  plus migration/schema paths — see those two entries for the exact patterns. `sensitive_path_match`
  is a path-matching check only, never a content-reading one; the content-only cast-when categories
  each entry excludes from its own path list ("input validation at a trust boundary" and
  "deserialization" for Security; ORM/model and serialization changes with no recognizable path for
  Data Steward) are intentionally excluded from this signal — see "Why this is still safe" below.

### Decision table (fixed for v1 — PRD OQ5, D18)

Evaluated top-to-bottom; the first matching row wins:

1. `sensitive_path_match` is `true` → resolve to **full**, regardless of `files_changed`/
   `lines_changed`. This check runs first and short-circuits the size-based bands below — `--auto`
   is never less safe than a human manually picking a tier for the same diff.
2. `files_changed <= 3` AND `lines_changed <= 200` → resolve to **lite**.
3. `files_changed <= 15` AND `lines_changed <= 1000` → resolve to **medium**.
4. Otherwise → resolve to **full**.

Boundary values resolve to the cheaper tier: a diff at exactly 3 files/200 lines is lite, not
medium; a diff at exactly 15 files/1000 lines is medium, not full. One signal over either boundary
(4 files, or 201 lines; 16 files, or 1001 lines) moves to the next tier up.

These thresholds are fixed constants for v1, resolved 2026-07-19 (PRD OQ5). Validated against this
repo's own history: a check across the last 49 non-merge commits (`git show --numstat`) using the
original tighter proposal (`<=40`/`<=300` lines) produced a balanced 17/19/13 lite/medium/full
split, confirming the mechanism itself wasn't degenerate. The human reviewing this SPEC then chose
to widen both line ceilings — to `<=200` for lite and `<=1000` for medium — to bias the default
toward the faster tiers and reserve full for genuinely large diffs; re-tallied against the same 49
commits this produces roughly a 51%/41%/8% lite/medium/full split. File-count ceilings (`<=3` lite,
`<=15` medium) are unchanged from the original proposal. Per-repo tuning (e.g. via `foundry.yaml`)
is out of scope, per the PRD's Future direction section.

### Why this is still safe

`sensitive_path_match`'s path-only scope (excluding the content-only triggers each seat's Cast-when
also covers — see below) only affects *which tier `--auto` picks*, never whether a fail-closed
seat gets cast once CAST actually runs. Both Security and Data Steward have cast-when criteria
that are decidable from CAST Steps 1-3 alone, with no dependency on Step 4/live-scan (see
`persona-catalog.md`'s Security and Data Steward entries) — so a content-only trigger
`sensitive_path_match` didn't catch (e.g. input validation at a trust boundary or deserialization
for Security; an ORM/model definition or serialization-format change with no recognizable
migration/schema path for Data Steward) may still resolve `--auto` to `lite` or `medium`, but
either seat is still forced into that tier's SPAWN dispatch by CAST's own fail-closed criteria —
coverage is never silently dropped for either seat, only the *tier* (and therefore
VALIDATE/RE-REVIEW/CONVERGE's cost envelope) is not maximally conservative for that one narrow
case. This is a deliberate cost/precision tradeoff for a cheap pre-CAST resolver: `--auto` may
pick a cheaper tier than a human would for a diff with a subtle content-only trigger, but it never
drops the specialist seat itself — see `persona-catalog.md`'s Security and Data Steward "Path-
identifiable subset" notes for the exact boundary of what `sensitive_path_match` can and can't
approximate from paths alone.

### Applying the result

Once resolved, `tier` is set to the concrete value the decision table produced, and the run
proceeds exactly as if that tier's flag had been passed explicitly — every later stage
(CAST/SPAWN/VALIDATE/RE-REVIEW/CONVERGE) reads `tier`, never `tier_source`, so no stage needs its
own `--auto`-specific branch (Architecture invariant 1). `tier_source` stays `"auto"` for the rest
of the run regardless of which concrete tier it resolved to — `tier_source` records *how* the tier
was chosen, `tier` records *what* was chosen, and the two are independent fields for exactly this
reason (see `dual-mode-contract.md`).

### Disclosure

`auto_signals` — `files_changed`, `lines_changed`, `sensitive_path_match`, the exact values the
resolver used — is emitted as a top-level `mode:agent` JSON field whenever `tier_source` is
`"auto"` (see `dual-mode-contract.md`). In human-interactive mode, the same three values back a
one-line disclosure appended to the report: inside the existing "## Narrowed Run" block when
`--auto` resolves to lite or medium, or as a new unheaded single line in that block's position when
`--auto` resolves to full (see `dual-mode-contract.md`'s report template) — either way, an `--auto`
run is never mistakable for an explicit-flag run by omission (PRD Goal 6).

## The sovereignty guard is untouched

Per SPEC Architecture invariant 3: the post-FIX integrity check and its `escalated` terminal status
(documented in `dual-mode-contract.md`, produced along the FIX/RE-REVIEW/CONVERGE path) apply
identically regardless of tier. No narrowed-tier conditional exists anywhere inside that guard's
code path, in this file or any other. This is the file most likely to be read by someone deciding
whether a narrowed tier is safe for a given diff class, so it states this plainly: **narrowing the
review scope never narrows the sovereignty guard** — a `--lite` or `--medium` run is exactly as
protected against an unauthorized sovereignty-relevant change as a full run is.

That guard's own implementation — the Data Steward seat and its fail-closed escalation path — is
present in this plugin's `reviewers/persona-catalog.md` (see its "Data Steward" entry) and is,
like Security, a Steps-1-3-decidable, fail-closed-forced seat: it is never excluded from
`--lite`/`--medium` SPAWN dispatch (see `cast-and-spawn.md`'s "Seat set: full vs. narrowed tiers").
Narrowing the review scope narrows *which other seats* SPAWN dispatches; it never narrows Data
Steward's cast-when, its sovereignty-marker mechanism, or CONVERGE's `escalated` terminal status
for a sovereignty-marked finding.

## What this file does not cover

- Per-stage mechanics (how CAST/SPAWN/VALIDATE/RE-REVIEW/CONVERGE actually execute): cited above,
  never restated here — see [design-lineage.md](design-lineage.md) for this plugin's citation
  convention.
