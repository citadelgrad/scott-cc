# MERGE and VALIDATE

Stages 3 and 4. MERGE turns N seats' raw findings into one deduplicated, confidence-scored list.
VALIDATE independently checks each survivor before it's allowed into FIX.

---

## MERGE

**Goal:** take every seat's raw `contracts/reviewer-output.md` output (from SPAWN) and produce one
deduplicated list of findings, each with a confidence score, ready for VALIDATE.

### Artifact boundary

Dispatch one MERGE worker with the paths under `$WORKSPACE/seat-artifacts/`; do not load those raw
reports into the orchestrator. The worker executes Steps 1-5 below, writes the complete result to
`$WORKSPACE/merged-findings.json`, and returns only a bounded manifest containing that path,
finding counts by severity/confidence, rejected count, and coverage gaps. A write failure fails
MERGE rather than returning the findings inline.

### Step 1 — Fingerprint every finding

For every Issue (Critical/Important/Minor) across every seat's output, compute a fingerprint:

```
fingerprint = (file_path, line_bucket, normalized_title)
```

- **file_path**: the file:line reference's file component, exactly as reported.
- **line_bucket**: the reported line number, bucketed with a **±3 line tolerance** — two findings
  whose line numbers are within 3 lines of each other on the same file are treated as the same
  bucket for fingerprint purposes. Different seats reading the same diff will often cite slightly
  different lines for what is clearly the same underlying issue (e.g. one cites the line with the
  bug, another cites the line where the function starts) — a tolerance this size catches that
  without being so wide it collapses genuinely distinct nearby issues.
- **normalized_title**: derive a comparable short title from each finding's stated issue
  (typically the first clause of its "what's wrong" text) and normalize it: lowercase, strip
  punctuation, collapse repeated whitespace to single spaces, trim leading/trailing whitespace.
  Example: `"Missing Null-Check on `user.email`!!"` and `"missing null check on user.email"`
  normalize to the same string (`missing null check on useremail` after punctuation-strip) and are
  treated as title-equivalent for fingerprint purposes.

Two findings with the same fingerprint (same file, line within ±3, normalized titles equal or one
is clearly a substring/paraphrase of the other on manual judgment) are the same underlying finding
reported by multiple seats — merge them into one, retaining links to every seat that reported it.

### Step 2 — Assign confidence anchors

Every merged finding gets a confidence score anchored at one of five fixed levels: **0, 25, 50,
75, 100**. Do not assign arbitrary intermediate values (e.g. "62") — pick the nearest anchor and
justify it. What pushes a finding to each anchor:

- **100** — the finding cites the exact code text at the claimed location (passes the quote-the-
  line gate below) AND at least 2 independent seats reported the same fingerprint AND the
  reasoning is a concrete, mechanically verifiable claim (e.g. "this branch is unreachable because
  X is already checked on line N" — checkable by reading the code).
- **75** — either (a) 2+ independent seats agree AND the quote-the-line gate passes, but the
  reasoning involves some judgment rather than a purely mechanical check, or (b) a single seat's
  finding passes the quote-the-line gate with a concrete, mechanically verifiable claim, but no
  second seat corroborated it (not yet bumped — see the 2+ agreement rule below).
- **50** — a single seat's finding, passes the quote-the-line gate, but the claim itself requires
  contextual/design judgment a reasonable reviewer could disagree with (the same "design smells are
  contextual, not binary" caveat clairvoyance's `workflow-builder.md` applies to structural
  findings generally — see this skill's Design Lineage notes).
- **25** — the finding fails the quote-the-line gate (see below) but is otherwise coherent and
  specific enough to be worth a validator's attention rather than discarding outright.
- **0** — vague, unsupported, or self-contradicting (e.g. a "Critical" severity with reasoning that
  describes a Minor-level concern with no concrete failure mode) — do not pass this finding to
  VALIDATE; drop it from the merged list, but keep a record of it (with which seat produced it) in
  case CONVERGE's progress-measurement needs to see the full history.

### Step 3 — The 2+ agreement bump

If 2 or more independent seats (not the same seat reporting twice, and not one seat's internal
sub-dispatch like an adversarial-reviewer's nested clean-room subagent counting as a second "seat")
report findings that fingerprint-match, bump the resulting merged finding's confidence anchor **up
by exactly one level** from where Step 2's base criteria would otherwise place it (e.g. a finding
that would be 50 on single-seat merits becomes 75 with 2+ agreement; a 75 becomes 100). This
implements the persona-catalog's diversity-of-perspective premise directly: independent
corroboration is signal, and MERGE is where that signal gets counted.

The bump applies only to validated findings. Candidate concerns, residual risks, rejected
candidates, and hypotheses are not findings and cannot supply a corroborating vote or receive a
promotion. `adversarial-reviewer` deliberately permits a clean empty result and never manufactures
a fallback issue merely to populate the list.

**Distinct-lens requirement — agreement alone is not enough.** Two seats agreeing is only real
independent corroboration if they got there via genuinely different review lenses. Two seats that
both effectively ran the same lens (e.g. a live-scan-added security-flavored skill agreeing with
the catalog's own Security seat) converging on the same finding is one perspective confirming
itself, not two — it must not earn the bump.

- **What counts as a "declared lens":** each seat's `Seat` name from
  `reviewers/persona-catalog.md`'s Seat Summary Table (Correctness/Adversarial, Simplicity,
  Structural, Security, Domain-Intent, Fresh-Eyes, Change-Trajectory, Design-Alternatives,
  Test-Design Quality, Data Steward, Taste). This table is the catalog's own lens taxonomy — MERGE
  does not define a second, separate one. A live-scan-added supplementary seat (persona-catalog's
  "SECONDARY enrichment layer") inherits the declared lens of whichever catalog Seat its function
  most closely matches (e.g. a user-installed security linter skill declares the Security lens);
  if its lens doesn't map cleanly to any row in the table, treat it as its own distinct lens rather
  than folding it into an existing one, per the catalog's fail-closed default.
- **Overlapping, and does not qualify for the bump on its own:** two or more contributing seats
  that share the same declared lens (same `Seat` row, or a live-scan seat mapped to the same row).
  Their agreement still merges into one finding (Step 1 fingerprinting is unaffected) and still
  contributes to that finding's `contributing seat(s)` list, but it does not, by itself, satisfy
  the 2+ agreement bump — same-lens agreement is treated as a single corroborating perspective,
  confidence-wise, no matter how many same-lens seats reported it.
- **Distinct, and qualifies:** two or more contributing seats whose declared lenses are different
  rows in the Seat Summary Table (e.g. Structural + Security, or Domain-Intent + Correctness/
  Adversarial). This is the normal case the bump was designed for and needs no special handling
  beyond confirming the lenses actually differ.
- **The mandatory-contrarian exception:** if a fingerprint-matched finding's contributing seats are
  all same-lens (so the rule above would withhold the bump), the bump still applies if
  `Correctness/Adversarial` (`adversarial-reviewer`) — this plugin's always-cast contrarian/
  adversarial seat, per persona-catalog's Core Seats — is itself one of the contributing seats. A
  same-lens pair corroborated by the panel's mandatory adversarial seat has already cleared a
  genuinely independent, hostile-framed check, which is what the distinct-lens requirement exists
  to guarantee; a third seat is not required. This exception cannot itself be satisfied by two
  same-lens seats that both happen not to be Correctness/Adversarial — it requires that specific
  seat's participation, since it is the one seat every CAST always includes regardless of
  diff-specific casting judgment (persona-catalog's Core Seats section), making it the one lens
  every panel run can rely on as a structural check on same-lens groupthink.
- **Practical effect:** when evaluating a fingerprint-matched finding for the bump, first list the
  declared lens of every contributing seat. If 2+ distinct lenses are present, apply the bump. If
  only one lens is represented (however many seats reported it), withhold the bump unless
  Correctness/Adversarial is among the contributors. A finding that fails this check is not
  demoted or dropped — it simply stays at whatever confidence anchor Step 2's base criteria alone
  would assign, same as any single-corroboration finding.

### Step 4 — Quote-the-line evidence gate

Every finding must cite the ACTUAL code text at its claimed file:line as part of its evidence —
not a paraphrase, not "the function doesn't handle nulls" without showing the line in question.
Concretely: cross-reference each finding's cited file:line against the packaged diff (or the
current file content) and confirm the quoted text is verbatim present at that location (allowing
for the ±3 line tolerance in citation drift, same as fingerprinting). This is a targeted check —
read just the few lines around each finding's claimed location (via `Read`/`Grep` on the current
file, or the specific hunk in the packaged diff), not the whole packaged diff. The **MERGE worker**
performs these per-finding reads in its disposable context and writes the results into
`merged-findings.json`; the parent receives only MERGE's bounded manifest and never performs quote
verification itself.

- **Passes the gate**: finding includes a verbatim (or trivially-whitespace-normalized) quote of
  the code it's about, and that quote is actually found at or within 3 lines of the claimed
  location.
- **Fails the gate**: no quote given, quote doesn't match anything near the claimed location, or
  the claimed file:line doesn't exist in the diff/file at all.
- A finding that fails the gate is **demoted**, not deleted outright — cap its confidence anchor
  at 25 regardless of what Step 2 would otherwise assign, and flag it explicitly as
  "evidence-gate-failed" in the merged list. This keeps a potentially-real-but-sloppily-cited
  finding visible to VALIDATE rather than silently erasing it, while still ranking it below
  properly-evidenced findings.

### Step 5 — Emit the merged list

Produce one list of findings, each carrying: fingerprint, confidence anchor (0/25/50/75/100),
contributing seat(s), severity (Critical/Important/Minor, taking the highest severity any
contributing seat assigned if they disagree), the evidence quote, and the original recommendation
text. Findings at confidence 0 are excluded from what VALIDATE receives (per Step 2) but retained
in the run's internal record.

**Sovereignty marker passes through untouched.** A finding carrying `sovereignty: human-required`
(currently emitted by the data-steward seat, see `skills/data-steward/SKILL.md`'s Output Contract)
keeps that marker through fingerprinting and dedup exactly as-is — it is not part of the fingerprint
key `(file_path, line_bucket, normalized_title)` and never influences fingerprint matching. If two
or more seats report fingerprint-matching findings and any one of them carries the marker, the
merged finding keeps it (the marker is a logical OR across contributing seats, not something that
needs unanimous agreement — a single seat correctly identifying a sovereignty boundary is enough).
MERGE must not strip, downgrade, or silently drop this field while deduplicating.

---

## VALIDATE

**Goal:** independently check each surviving merged finding (confidence 25-100) before it's
trusted enough to hand to FIX. No finding reaches FIX without passing through an independent
validator — this is where self-grading (a seat's finding being accepted purely because that seat
said so) is structurally prevented.

### One validator per surviving finding, by default

Dispatch one validator subagent per surviving finding (post-MERGE, post-dedup — NOT one per raw
seat report; a finding two seats agreed on gets one validator, not two). Default: **1 validator**
per finding.

### Bounded validator batches and artifact output

The orchestrator passes `merged-findings.json` by path. A validator subagent may process **at most
5 findings** in one batch, provided it was not an original finder for any finding in that batch.
VALIDATE accepts **at most 25 total validator assignments** and dispatches **at most 5 total
validator batches** for the whole stage, as well as at most **5 concurrent validator subagents**.
Before dispatch, compute assignments after applying the tier's Critical multiplier. If that total
exceeds 25 — even when there are 25 or fewer findings — stop with `finding_scope_too_large` and
require the target to be split; do not truncate, prioritize, under-validate, or silently defer
findings. Critical findings that require multiple
validators must appear in distinct validator batches so each verdict remains independent.

Each validator writes blind restatements, reconciliations, evidence, and verdicts to
`$WORKSPACE/validator-artifacts/<batch-id>.json` and returns only its artifact path and hash. Once
all batches finish, one reducer reads those paths, writes `$WORKSPACE/validated-findings.json`, and
returns **one bounded VALIDATE manifest** of at most 2 KiB with the final path and counts. The
orchestrator never accumulates per-validator finding IDs, verdicts, reasoning, or the full list.

### Escalate to 2-3 validators for CRITICAL findings — tier conditional

**This escalation is itself tier-conditional** (see [lite-mode.md](lite-mode.md), narrowed
guarantee #2 for both tiers):

- **Lite (`--lite`):** no escalation — every surviving finding, Critical or not, gets exactly
  **1 validator**. The confidence-based 3-vs-2 branch below does not apply; it only exists to
  choose between 2 and 3, which is moot once Critical findings are capped at 1 like everything
  else.
- **Medium (`--medium`):** Critical findings get exactly **2 validators**, never 3 — the
  confidence-based branch below (which would otherwise pick 3 for sub-75 confidence) is dropped in
  favor of a flat 2. Non-Critical findings are unaffected: still the 1-validator default, identical
  to full mode.
- **Full (no tier flag, or `--auto` resolved to full):** unchanged from today — any finding whose
  severity is Critical gets **2-3 independent validators**, not 1. This directly implements
  clairvoyance `workflow-builder.md`'s majority-survives-challenge principle (see Design Lineage):
  keep a finding only if a majority of its challengers cannot refute it. For a Critical-severity
  finding — the class most likely to block a merge or trigger a fix that touches sensitive code — a
  single validator's miss is more costly than for a Minor finding, so the extra validation cost is
  justified. Use 3 validators when the finding's confidence anchor is below 75 (more room for the
  finding to be wrong); 2 validators when confidence is 75+ (already well-evidenced, but Critical
  severity still warrants more than one check).

Nothing else about validation narrows: the validator's own procedure (clean-room independence,
never-the-original-finder rule, evidence given to the validator) is identical across all three
tiers — only the *count* of validators dispatched per finding changes. Any run where a Critical
finding received fewer validators than full mode would have used must say so in the Coverage
Honesty disclosure.

### The validator must never be the original finder

Before dispatching, check the fingerprint's contributing-seat list (from MERGE Step 5) and
exclude those seats' identity/context from the validator dispatch — the validator subagent must be
a fresh dispatch, never a continuation of or handoff from the seat(s) that originally reported the
finding. This is the no-self-grading rule: a seat cannot validate its own finding by definition.

### Clean-room/blind independence

Use `../adversarial-reviewer/references/clean-room-protocol.md` for each validator dispatch. Freeze
the raw target and Phase-1 restatement before exposing prior findings; record `process_isolated`,
`prompt_blinded`, or `self_reset`, and never count `self_reset` as independent corroboration. Use
`../adversarial-reviewer/references/control-backed-findings.md` to validate candidates against the
target and a named known control; unsupported hypotheses cannot reach FIX or silently block. The
dispatch happens in two ordered phases within the same validator subagent — **blind restatement
first, original claim second** — because showing the
original finder's title, severity, or rationale before the validator has committed to its own
read is exactly the anchoring bias this procedure exists to prevent (a validator who reads "this
is Critical" before looking at the code tends to go looking for a reason to agree with "Critical"
rather than independently arriving at a severity).

1. **Phase 1 — blind restatement.** Give the validator only: the finding's claimed file:line, and
   the raw code at and around that location (via Read/Grep on the actual files, not a copy-paste
   snippet chosen by the original finder). **Withhold everything else** — the original finder's
   title, its stated issue category (Critical/Important/Minor), its full reasoning chain, its "why
   it matters" prose, and its proposed fix. Instruct the validator to independently examine the
   code at that location and record, before seeing anything else: **what it sees wrong there (if
   anything), the severity it would assign (Critical/Important/Minor/nothing), and its own
   rationale** — in the same title / severity / rationale shape the original finding uses, so the
   two are directly comparable in Phase 2. This restatement is committed (returned as part of the
   validator's output) before Phase 2 begins; the validator does not get to revise it after seeing
   the original claim.
2. **Phase 2 — reveal and reconcile.** Only after the blind restatement is recorded, reveal the
   original finder's title, severity, and rationale (still withholding its proposed fix, which
   remains irrelevant to whether the claim is real). Ask the validator to state whether its
   independent restatement **matches, partially matches, or contradicts** the original finding —
   and to use that comparison, not deference to the original claim, to decide the verdict.
3. **The validator's task**: independently determine whether the claimed issue is real, given only
   the location and the raw code (Phase 1), then reconcile against the original claim (Phase 2).
   Does the code at that location actually exhibit the described problem? Construct the Phase 2
   framing as a challenge, not a confirmation request — ask the validator to try to show the
   finding is WRONG (no bug here, the "issue" is actually handled elsewhere, the input claimed to
   be hostile is actually validated upstream) before concluding it's right. This framing matches
   the challenger framing in Step 4 below and the majority-survives-challenge principle.
4. Each validator returns: its **blind restatement** (title/severity/rationale, Phase 1), its
   **match/partial-match/contradicts** call against the original claim (Phase 2), and a final
   verdict of either **SURVIVES** (the finding is real, as stated or with minor correction) or
   **REFUTED** (the finding does not hold — the validator found a reason the claimed issue isn't
   actually a problem, and states that reason concretely).

### Majority-survives-challenge verdict

- **1-validator findings** (every finding under `--lite`, non-Critical findings in every tier):
  SURVIVES → finding proceeds to FIX. REFUTED → finding is dropped (recorded in the internal
  history, not discarded from the run's audit trail, but not sent to FIX). Record the tally as the
  single-validator shape, e.g. `1-0` (survives) or `0-1` (refuted) — no recount, no second
  validator dispatched regardless of severity.
- **2-validator findings** (Critical severity under `--medium`, and Critical findings at
  confidence 75+ under full mode): the finding proceeds to FIX only on a `2-0` majority. A `1-1`
  split is recorded as a non-majority tally and treated the same as a REFUTED majority — the
  finding is dropped, and **no 3rd tie-breaking validator is dispatched** to resolve it; `--medium`
  never escalates past 2 regardless of how a 2-validator round ties.
- **3-validator findings** (Critical severity below confidence 75, full mode only — never occurs
  under `--lite` or `--medium`, which cap Critical validator counts below 3): the finding proceeds
  to FIX only if a majority return SURVIVES (2 of 3, or 3 of 3). If a majority return REFUTED, the
  finding is dropped. A tie is impossible at 3 validators by construction.
- **Zero surviving findings after MERGE**: VALIDATE dispatches zero validators and emits an empty
  validated list — this is a normal, expected outcome in every tier, not an error condition.

### Output

VALIDATE persists the final validated findings list to `validated-findings.json` — every finding that survived its
challenge(s) — annotated with its confidence anchor, severity, evidence quote, and (for
transparency in the final report) how many validators checked it and the verdict tally. For every
finding, the record includes **both** the validator's blind restatement (title/severity/rationale,
recorded before the original claim was revealed) **and** the original finder's claim
(title/severity/rationale), shown side by side, plus the match/partial-match/contradicts call that
reconciled them — this pair is retained in the audit trail even for SURVIVES findings, not just
disputed ones, so a reader of the final report can see the independent read that produced the
verdict. This artifact path is FIX's input; the list itself does not enter the orchestrator context.

The `sovereignty` marker (see MERGE Step 5) carries through VALIDATE unchanged as well — a
validator judges whether the finding's underlying claim is real (survives/refuted), not whether the
sovereignty marker is warranted; VALIDATE has no authority to add, remove, or reinterpret that
field. A sovereignty-marked finding that is REFUTED is dropped like any other refuted finding (the
marker doesn't grant immunity from validation); one that SURVIVES keeps the marker into FIX, where
[fix-and-rereview.md](fix-and-rereview.md)'s dispatch contract and post-FIX sovereignty guard take
over.
