# FIX and RE-REVIEW

Stages 5 and 6. FIX applies every validated finding in one coordinated pass. RE-REVIEW checks the
result for both regressions and domain-intent coherence before CONVERGE decides whether to loop.

---

## FIX

**Goal:** resolve every validated finding from VALIDATE's output in one coordinated editing pass.

### ONE fixer, the WHOLE list — not one fixer per finding

Dispatch exactly **one** fixer subagent (via `Task`, with `Read`, `Edit`, `Write`, `Bash` — this
is the only stage in the loop where a subagent gets mutation tools) and give it the **entire**
validated findings list from VALIDATE in a single dispatch prompt. Do not dispatch N fixers for N
findings, and do not dispatch fixers serially one-finding-at-a-time either.

**Why one fixer, not N:**
- **Shared context prevents redundant/conflicting fixes.** Two findings that both trace back to
  the same root cause (e.g. a missing null-check pattern repeated at three call sites, each
  flagged as a separate finding by different seats) get fixed once, correctly, by a fixer that can
  see all three findings together and recognize the shared cause — not three times independently,
  possibly with three slightly different fixes that don't agree with each other.
- **Batching and prioritization.** A single fixer with the whole list can order its edits
  sensibly (e.g. fix the type/schema change a Domain-Intent finding calls for before fixing the
  call sites an Adversarial finding flagged, since the call-site fixes depend on the new type
  shape existing) — an outcome not achievable if N independent fixers each grab one finding
  without visibility into the others.
- **Avoids edit collisions.** N fixers editing the same file concurrently (or in an uncoordinated
  order) risk clobbering each other's changes or producing a file that doesn't compile because two
  fixes were made against two different intermediate states of the same function. One fixer
  editing serially through its own prioritized plan has no such race.
- **Matches the plan's explicit design decision** (COPY MANIFEST, superpowers section): "one
  fixer, whole findings list" is lifted deliberately from superpowers' subagent-driven-development
  pattern for exactly these reasons — see [design-lineage.md](design-lineage.md).

### Fixer dispatch contract

Give the fixer:
1. The full validated findings list (fingerprint, severity, confidence, evidence quote, original
   recommendation, contributing seats) — the complete VALIDATE output, not a filtered subset.
2. The packaged diff and read/write access to the actual codebase files (not just the diff text —
   it needs to make real edits).
3. Explicit instruction to fix Critical findings first, then Important, then Minor, and to note in
   its own return report any finding it could NOT fix (with a reason: ambiguous requirement,
   requires a decision the fixer isn't positioned to make, conflicts with another finding's fix)
   rather than silently skipping it.
4. Explicit instruction to batch/consolidate related fixes rather than treating each finding as an
   isolated edit — e.g. if 3 findings all stem from the same missing validation layer, add that
   layer once and note which findings it resolves.

### Output

The fixer returns: a list of {finding → fix applied, or fix skipped + reason}, plus a summary of
what changed. This becomes RE-REVIEW's context for what to check, and CONVERGE's raw material for
measuring progress (see [converge-and-pipeline.md](converge-and-pipeline.md)).

---

## RE-REVIEW

**Goal:** after FIX, check the result along two independent axes before deciding whether the loop
can stop: (a) did the fixes introduce regressions, and (b) does the fixed code still cohere with
documented domain intent.

### Re-package the diff first

Before re-reviewing, re-run `scripts/review-package` against the new `HEAD` (the fixer's
committed changes, or current working-tree state if uncommitted) per SKILL.md's Setup section.
RE-REVIEW always operates on a freshly packaged diff reflecting FIX's actual output — never the
pre-fix diff, and never a stale package from an earlier loop iteration.

### Axis (a) — Regression check

Re-run a subset of the panel against the new diff, focused on catching regressions FIX itself
introduced:
- Always re-cast **Correctness/Adversarial** (`adversarial-reviewer`) — fixes are exactly the kind
  of hand-written change most likely to introduce a new bug, and this seat's entire purpose is
  finding exactly that.
- Re-cast any other seat whose prior-round finding was in the fixed set, scoped to just the files
  that finding's fix touched — confirm the fix actually resolved what it claimed to, not just that
  something changed at that location.
- Re-cast **Fresh-Eyes** if the fix touched a broad enough surface that a truly independent
  first-read of the new diff is warranted (judgment call — a one-line fix to a single validated
  finding likely doesn't need it; a fix that restructured a type or workflow across multiple files
  does).
- This is a smaller re-cast than a full CAST-stage run — CAST's full judgment-based casting only
  runs again if CONVERGE decides to loop back to SPAWN for a genuinely new full round (see
  [converge-and-pipeline.md](converge-and-pipeline.md) for the loop-back decision between SPAWN
  and MERGE).

### Axis (b) — Coherence vs. domain intent

Check whether the fixed code still matches documented domain decisions, wiring into
`domain-modeling`'s `CONTEXT-AND-ADR.md` mechanism:

1. Check whether a `CONTEXT.md` (or `CONTEXT-MAP.md` + per-context files) exists at the repo root
   or wherever `formats/CONTEXT-FORMAT.md`'s detection rule specifies. If none exists, this axis
   has nothing to check against yet — note that in the report and move on; do not treat "no
   CONTEXT.md" as a coherence failure.
2. If it exists, read the glossary entries relevant to the files FIX touched. For each fixed
   location, ask: does the post-fix code still use domain terms consistently with their
   `CONTEXT.md` definitions? A fix that, say, renames a variable from `fulfillment` to `shipping`
   to resolve an unrelated naming complaint would introduce exactly the kind of term-drift
   `CONTEXT.md` exists to prevent — catch that here.
3. Cast (or re-cast) the **Domain-Intent** seat (`domain-modeling`) specifically for this axis
   when the fixed files include type/schema/workflow code that a `CONTEXT.md` entry documents a
   decision for — this is the same cast-when trigger the persona-catalog already defines for
   Domain-Intent, applied now against the post-fix diff instead of the pre-fix one.
4. A coherence finding here (post-fix code diverges from a documented domain decision) is treated
   as a new finding for the next MERGE pass if CONVERGE decides to loop — it did not exist before
   FIX ran, so it wasn't and couldn't have been validated in the prior VALIDATE pass.

### Output

RE-REVIEW emits: a clean/dirty verdict per axis, any new findings surfaced (regressions or
coherence drift), and — critically — the finding counts and severities needed for CONVERGE's
progress measurement. Pass this directly into CONVERGE; do not summarize it away, since CONVERGE's
3-strikes circuit-breaker depends on comparing round-over-round counts precisely.
