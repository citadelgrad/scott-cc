# MERGE and VALIDATE

Stages 3 and 4. MERGE turns N seats' raw findings into one deduplicated, confidence-scored list.
VALIDATE independently checks each survivor before it's allowed into FIX.

---

## MERGE

**Goal:** take every seat's raw `contracts/reviewer-output.md` output (from SPAWN) and produce one
deduplicated list of findings, each with a confidence score, ready for VALIDATE.

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

### Step 4 — Quote-the-line evidence gate

Every finding must cite the ACTUAL code text at its claimed file:line as part of its evidence —
not a paraphrase, not "the function doesn't handle nulls" without showing the line in question.
Concretely: cross-reference each finding's cited file:line against the packaged diff (or the
current file content) and confirm the quoted text is verbatim present at that location (allowing
for the ±3 line tolerance in citation drift, same as fingerprinting). This is a targeted check —
read just the few lines around each finding's claimed location (via `Read`/`Grep` on the current
file, or the specific hunk in the packaged diff), not the whole packaged diff. MERGE runs in the
orchestrator's own context, which per SKILL.md's Setup step 4 must never hold the diff's full
content — a small per-finding read stays well within that budget across even a long findings list,
which is what makes this check compatible with that discipline.

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

Reuse the blind-subagent pattern from `agents/clean-room-alternative.md` (the same pattern
`adversarial-reviewer` uses internally — see its "Independence via clean-room-alternative"
section) for each validator dispatch:

1. Give the validator: the finding's claimed file:line, its stated issue category
   (Critical/Important/Minor), and the raw code at and around that location (via Read/Grep on the
   actual files, not a copy-paste snippet chosen by the original finder).
2. **Withhold**: the original finder's full reasoning chain, its "why it matters" prose, and its
   proposed fix. The validator sees the finding's *claim* (what's wrong, at what location) and the
   *raw code* — not the finder's argument for why the claim is true. This is deliberate: a
   validator handed the finder's full reasoning tends to rubber-stamp it rather than
   independently re-derive whether the claim holds.
3. **The validator's task**: independently determine whether the claimed issue is real, given only
   the location and the raw code. Does the code at that location actually exhibit the described
   problem? Construct the validator's prompt as a challenge, not a confirmation request — ask it
   to try to show the finding is WRONG (no bug here, the "issue" is actually handled elsewhere,
   the input claimed to be hostile is actually validated upstream) before concluding it's right.
   This framing matches the challenger framing in Step 4 below and in the pipeline-not-barrier
   reference's majority-survives-challenge principle.
4. Each validator returns: **SURVIVES** (the finding is real, as stated or with minor correction)
   or **REFUTED** (the finding does not hold — the validator found a reason the claimed issue
   isn't actually a problem, and states that reason concretely).

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

VALIDATE emits the final validated findings list — every finding that survived its
challenge(s) — annotated with its confidence anchor, severity, evidence quote, and (for
transparency in the final report) how many validators checked it and the verdict tally. This list
is FIX's entire input.

The `sovereignty` marker (see MERGE Step 5) carries through VALIDATE unchanged as well — a
validator judges whether the finding's underlying claim is real (survives/refuted), not whether the
sovereignty marker is warranted; VALIDATE has no authority to add, remove, or reinterpret that
field. A sovereignty-marked finding that is REFUTED is dropped like any other refuted finding (the
marker doesn't grant immunity from validation); one that SURVIVES keeps the marker into FIX, where
[fix-and-rereview.md](fix-and-rereview.md)'s dispatch contract and post-FIX sovereignty guard take
over.
