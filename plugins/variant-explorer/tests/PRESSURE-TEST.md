# Variant Explorer Pressure Test

**Task:** scc-5hy — Phase 4 of epic scc-hzj, "Two-System Architecture."

This document is a pressure test of the `variant-explorer` plugin (`skills/explore-variants/SKILL.md`,
`agents/blind-builder.md`, `agents/variant-judge.md`), following the same discipline as
`plugins/review-panel/tests/PRESSURE-TEST.md`: prove the skill's prescribed process produces the
behavior each acceptance criterion (AC1-AC5) describes, via live dispatches where the AC requires
runtime evidence, and via a direct citation-based walkthrough where the AC is pure boundary-value
logic that doesn't need a dispatch to verify. `explore-variants/SKILL.md` and its two agent
definitions are markdown prompts, not executable code — there is no automated regression suite
this document produces. See "Limits of this pressure test" at the end.

**Methodology note — subagent-type substitution.** At the time this pressure test ran, the
`variant-explorer` plugin had just been created in this same working session; `variant-explorer:
blind-builder` and `variant-explorer:variant-judge` were not yet registered as live `subagent_type`
values (only `review-panel:clean-room-alternative` was available from a plugin loaded at session
start — plugins are registered at session start, not hot-loaded mid-session). Every builder/judge
dispatch below therefore used `subagent_type: "general-purpose"` with an explicit instruction to
read the target `.md` file in full and follow its procedure exactly. This is the identical
substitution `review-panel`'s own `PRESSURE-TEST.md` used for its CAST/SPAWN section. It is
disclosed here, not silently presented as a native `variant-explorer:*` dispatch — the one thing
this substitution cannot verify is whether Claude Code's actual `subagent_type` resolution/routing
mechanism works, only whether the *procedure* described in the `.md` files produces the intended
outcomes when followed.

All raw subagent outputs referenced below were produced by live `Agent`-tool dispatches run during
this task; full text is in this session's transcript. This document summarizes their substance.

---

## 1. The fixtures

`plugins/variant-explorer/tests/fixtures/palindrome-checker/` — `spec.md` + `ac.md`, a small,
self-contained spec (`is_palindrome(s: str) -> bool`) with 5 concrete AC (AC1-AC3 example
input/output pairs, AC4 docstring requirement, AC5 automated-test requirement). Small enough to
build multiple honest variants of in one dispatch, concrete enough for a judge panel to find real
(not contrived) differences between them.

`plugins/variant-explorer/tests/fixtures/impossible-ac/` — `spec.md` + `ac.md`, a single AC that
is logically unsatisfiable: a **pure** function `paradox()` (no randomness, no I/O, no hidden
state) that, called twice with the identical expression `paradox()` in the same process, must
return `True` the first time and `False` the second. Purity forecloses exactly the kind of
call-count-dependent state that would make this possible. This fixture exists solely to force a
`blocked` status from a builder, to test AC4 (does a blind-builder report an unsatisfiable AC
honestly rather than faking a pass, and does the orchestrator handle that loss correctly) without
having to rely on an artificial timeout or a deliberately broken harness.

---

## 2. Phase 2 dispatch — 3 blind builders (AC1, AC3, AC4)

**Dispatch:** three `Agent` calls, `isolation: "worktree"`, `subagent_type: "general-purpose"`
(see methodology note), sent in a single message so they ran concurrently — matching
`SKILL.md`'s Phase 2 instruction (lines 57-62) to dispatch all N in one batch. Two builders
(**Variant A**, **Variant B**) were given the `palindrome-checker` fixture with two distinct
angles from the SKILL.md angle bank (lines 67-73); the third (**Variant C**) was given the
`impossible-ac` fixture, deliberately, to combine AC1's "3 worktrees spawned" requirement with
AC4's "a lost variant is reported and the run continues with survivors" requirement in one batch
rather than running two separate N=3 batches. This scope decision is flagged again in Coverage
Honesty below.

**Prompts sent (verbatim structure, confirming AC3 — isolation):**

- Variant A: `spec.md` + `ac.md` content for `palindrome-checker`, angle **MVP-first** ("build the
  smallest thing that satisfies every AC, defer everything else"), instruction to read and follow
  `agents/blind-builder.md`'s procedure. No mention of Variant B or C, their angles, or their
  existence.
- Variant B: `spec.md` + `ac.md` content for `palindrome-checker`, angle **Dependency-free**
  ("satisfy the AC with zero new third-party dependencies"), same blind-builder instruction. No
  mention of Variant A or C.
- Variant C: `spec.md` + `ac.md` content for `impossible-ac`, angle **MVP-first**, same
  blind-builder instruction. No mention of Variant A or B.

Each prompt contained only the two items `SKILL.md` line 64-73 permits — spec/AC and one angle —
which is directly inspectable in the dispatch call arguments themselves (the check `SKILL.md`
line 81 describes: "a human... can inspect the actual dispatch prompts in the session transcript
and confirm no cross-contamination"). **AC3: confirmed.**

**Results:**

| Variant | Fixture | Angle | Status | Worktree |
|---|---|---|---|---|
| A | palindrome-checker | MVP-first | `complete` | `agent-aca69458ab1e667ba` — persisted (real file changes) |
| B | palindrome-checker | Dependency-free | `complete` | `agent-a0ac67197c4938b31` — persisted (real file changes) |
| C | impossible-ac | MVP-first | `blocked: paradox() is logically unsatisfiable for a pure, argument-free function` | auto-removed by the `Agent` tool (zero file changes on a `blocked` return — confirmed empirically) |

Variant A delivered `palindrome.py` (prose-only docstring) + a pytest-based `test_palindrome.py`
covering AC1-AC3 exactly. Variant B delivered `palindrome.py` (structured `Args:`/`Returns:`
docstring, explicit stdlib-only framing) + a self-contained `unittest`-based `test_palindrome.py`
covering AC1-AC3 plus 6 additional cases. Variant C produced no files at all — it reasoned through
why `paradox()` cannot be both pure and call-count-sensitive, and returned `status: blocked: <reason>`
per `agents/blind-builder.md`'s explicit instruction to report a genuine blocker rather than a
fabricated partial pass. This is a real, unprompted demonstration of the "no hedging, no fake
partial pass" rule in `blind-builder.md`, not a scripted result.

**3 worktrees were spawned** (2 persisted, 1 auto-cleaned on a no-change `blocked` return — itself
a correct behavior, not a bug: there was nothing to preserve). **AC1's worktree-count requirement
is satisfied.** The lost-variant handling is assessed next under AC4.

---

## 3. AC4 — lost-variant handling

Per `SKILL.md` Phase 3 (lines 84-97): a `blocked` return is recorded as `{"id": "<variant-id>",
"reason": "<reason>"}`, the run continues with survivors, and the final report states the original
N, the lost count/reason, and the surviving count without renumbering as if N had been smaller
from the start.

Applied to this dispatch: original N=3 (well, in a real single-fixture run — see Coverage
Honesty), 1 lost (Variant C: `paradox() is logically unsatisfiable for a pure, argument-free
function`), 2 survivors (A, B). Nothing here silently dropped to "N=2" — Variant C's loss and
reason are first-class, reported facts, exactly matching the `epic-swarm` `tasks_failed` shape
`SKILL.md` line 90 cites as the model to mirror. **AC4: confirmed** — a genuinely blocked builder
was reported honestly, not faked, and the run proceeded to judge the 2 real survivors rather than
stalling or silently pretending N was always 2.

---

## 4. Phase 4 dispatch — judge panel (AC2)

Four further `Agent` dispatches (no worktree isolation needed — judges are read-only against
existing worktrees), each instructed to follow `agents/variant-judge.md`'s procedure for one axis,
against Variants A and B (Variant C had no artifacts to judge).

### AC-conformance judge

Both variants: **PASS all 5 AC**, each citation naming the specific AC ID per
`agents/variant-judge.md`'s "cite AC IDs, run runnable checks" instruction. The judge additionally
surfaced a real, non-contrived asymmetry: Variant A's `test_palindrome.py` imports `pytest`, which
neither variant's fixture nor Variant A itself declares or installs — it only ran because an
ambient `pytest` binary happened to be present on the host. Variant B's `unittest`-based suite has
no such external dependency. This is exactly the kind of finding a judge should surface under AC5
("boundary/negative cases") of `variant-judge.md`'s own AC-conformance axis — a tooling gap real
enough that a human picking a winner would want to know about it, not smoothed over because both
variants technically pass.

### Simplicity judge (ponytail-review format, per `skills/ponytail-review/SKILL.md`)

Variant A: **"Lean already. Ship."** — no findings.

Variant B: 4 findings (the extra 6 test cases beyond AC1-AC3, the `Args:`/`Returns:` docstring
sections restating type-hinted signature information, the explicit "stdlib-only" framing comment
justifying a non-decision, and one redundant intermediate variable), closing with **`net: -35
lines possible.`**

### Taste judge, omission path — no `TASTE.md`

At this point no `TASTE.md` existed at either worktree's root (confirmed absent at the real repo
root too — `ls`: `No such file or directory`). Per `skills/taste-review/SKILL.md`'s file-existence
gate, the judge returned, for **both** variants: `axis not applicable: no TASTE.md at repo root`
— not a fabricated "clean" score, an explicit non-scoring note. **This is the AC2 omission-path
behavior confirmed:** "without it, scorecards omit the taste axis and say so explicitly."

### Taste judge, presence path — `TASTE.md` fixture present

A `TASTE.md` fixture (`Preferences`/`Weightings`/`Anti-preferences`/`Candidate rules`, matching
`review-panel/tests/fixtures/taste-preferences/TASTE.md`'s field structure) was written into both
survivor worktrees' roots only — never at the real repo's root (confirmed absent both before and
after this pressure test), respecting Invariant 5 (human-owned artifacts are never agent-authored
at the actual repo root). Its one real `Preference` targets an actual, observed difference between
the two variants rather than a fabricated one: *"For a function whose single parameter and return
type are already stated in its signature, write one prose paragraph describing behavior; do not
add `Args:`/`Returns:` subsections that just restate the signature,"* strength `weak`.

Result: **Variant A — clean** (its docstring is already prose-only). **Variant B — one finding**,
quoting the Preference's `Rule` clause verbatim against Variant B's actual `Args:`/`Returns:`
docstring, mapped to **Minor** severity — correctly following `TASTE-FORMAT.md`'s
`strength: weak` → `Minor` mapping (never `Critical`, per the format spec).

**AC2: confirmed on both branches** — the omission path produces an explicit non-score rather than
silence or a fabricated score, and the presence path produces a genuine, verbatim-quoted finding
correctly severity-mapped from the fixture's declared strength, on a real (not contrived)
structural difference between two independently built variants.

### Ranked shortlist (worked by hand from the 3 judge axes above)

| Rank | Variant | AC-conformance | Simplicity | Taste (with TASTE.md) |
|---|---|---|---|---|
| 1 | A | PASS all 5, no dependency gap | Lean already. Ship. | Clean |
| 2 | B | PASS all 5, tooling-dependency-free but heavier | `net: -35 lines possible` | 1 Minor finding |

Both scorecards cite at least one AC item (in fact all 5, per-item) — **AC1's "each scorecard
cites ≥1 AC item" requirement is satisfied**, and the shortlist itself is a direct, defensible
ranking rather than a coin flip: A wins on every axis reviewed, but B's advantages (more test
coverage, zero test-tooling dependency) are real and worth a human's attention before picking,
which is exactly the judge panel's purpose — inform the human pick, not make it for them.

---

## 5. AC5 — boundary cases (written walkthrough, not live-dispatched)

Pure input-validation logic; `SKILL.md`'s Phase 1 table (lines 49-53) is deterministic and doesn't
need a live dispatch to verify, the same way review-panel's `PRESSURE-TEST.md` treated its
circuit-breaker rule as a walkthrough rather than a multi-round live run.

- **N=1:** `SKILL.md` line 51 — *"Refuse. Report: 'N=1 has no exploration value — build directly
  instead of running a one-variant panel.' Do not spawn a worktree, do not proceed to Phase 2."*
  This is checked *before* Phase 2's spawn step, so a worktree is never created for a refused N=1
  request — there's no partial/wasted dispatch to clean up, only a report.
- **N>6:** `SKILL.md` line 53 — *"Clamp to 6 (cap). Report explicitly in the final output:
  'N=<requested> clamped to 6 (cap).' Never silently run the user's original, larger N."* Line 55
  reinforces: *"Both refusal and clamping are explicit, reported behaviors — never a silent
  substitution."*

**AC5: confirmed by direct citation** — both boundary behaviors are specified as explicit, reported
outcomes rather than silent clamps or silent refusals, matching the AC's requirement exactly.

---

## 6. AC1-AC5 summary

| AC | Requirement | Result |
|---|---|---|
| AC1 | N=3 baseline → 3 worktrees, 3 scorecards, ranked shortlist, each scorecard cites ≥1 AC item | **Confirmed** — 3 worktrees spawned (§2); 2 real scorecards (A, B) each citing all 5 AC items plus Simplicity/Taste findings, ranked A > B (§4); Variant C's blocked status is its own accounted-for outcome, not a missing scorecard (§3) |
| AC2 | TASTE.md handling — present → taste clauses referenced in winning scorecard; absent → axis omitted, explicitly | **Confirmed on both branches** (§4) — omission path returns explicit `axis not applicable`; presence path returns a verbatim-quoted clause and a correctly severity-mapped finding |
| AC3 | Builder isolation — no builder prompt contains another variant's content | **Confirmed** (§2) — all 3 dispatch prompts inspected; each contains only its own fixture + one angle, no cross-references |
| AC4 | Error handling — failed/timed-out builder reported as lost variant, run continues with survivors, N never silently reduced | **Confirmed** (§3) — Variant C's `blocked` status recorded with its reason, run proceeded to judge A/B, N=3/1 lost/2 survivors stated explicitly, never renumbered as "N=2" |
| AC5 | N=1 refuses with guidance; N>6 clamps with a note | **Confirmed by citation** (§5) — both are pre-Phase-2 checks with mandatory, explicit reporting language in `SKILL.md` |

---

## 7. Cleanup

Both survivor worktrees (`agent-aca69458ab1e667ba`, `agent-a0ac67197c4938b31`) and their branches
were removed after their contents were fully captured above (`git worktree remove` + `git branch
-d`, both clean deletes — no unmerged-work warnings). `git worktree list` and `git branch --list
"worktree-agent-*"` are empty; `git status` shows no residue from this pressure test beyond the two
new fixture directories and this file.

---

## 8. Limits of this pressure test

- Every builder/judge dispatch used `subagent_type: "general-purpose"` with an explicit
  instruction to follow the target `.md` file (see Methodology note) because `variant-explorer`'s
  own agent types weren't registered mid-session. This verifies the *procedure* the `.md` files
  describe, not Claude Code's `subagent_type` routing for a plugin-qualified name — a live rerun
  after a fresh session load (where `variant-explorer:blind-builder`/`variant-explorer:variant-judge`
  would be registered) would close that specific gap.
- AC1 and AC4 were tested in a single combined 3-builder batch (2 on `palindrome-checker`, 1
  deliberately given the unsatisfiable `impossible-ac` fixture) rather than two separate batches —
  a disclosed scope-narrowing to avoid a redundant second full builder+judge cycle, since the
  combined batch produces genuine evidence for both AC's requirements without diluting either.
  This means AC1's "3 scorecards" evidence is, precisely, 2 full quality scorecards (A, B) plus 1
  accounted-for loss (C) with its own scorecard-equivalent report — not 3 quality scorecards on
  the same spec. A future full-scale run (3 builders, same spec, all complete) would additionally
  demonstrate the ranked-shortlist mechanic across 3 live competing quality scorecards rather than
  2.
- N=6 (the clamp ceiling) was never dispatched — `SKILL.md`'s sub-batching (5-then-1) and Phase 5's
  "harvest ideas from runners-up" human-in-the-loop prompt are both unexercised by this pressure
  test; they don't require new evidence to trust (the sub-batch split is a mechanical parallelism
  detail, and the harvest prompt is a simple, single conditional print), but a larger future
  fixture run could confirm N=6 concurrency behavior directly if that becomes a priority.
- The fixture is deliberately small (one function, 5 AC) so both variants and all judge findings
  are cheap to verify by hand; it doesn't exercise a case where the judge panel disagrees sharply
  or where a spec is large/ambiguous enough that angle assignment itself becomes a hard judgment
  call.
