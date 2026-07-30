---
name: refactoring-planner
description: >-
  Use when a file, class, or module has multiple code smells and needs a safe, sequenced cleanup
  plan rather than ad-hoc fixes, or when the user asks to "plan a refactor," "how should I tackle
  this messy file," or "what order should I fix these smells in." Orchestrates code-smells
  (detection) and refactoring-catalog (mechanics) into one prioritized, test-checkpointed sequence
  of small refactoring steps. Not for identifying smells in the first place (use code-smells
  directly) or looking up a single refactoring's mechanics in isolation (use refactoring-catalog).
argument-hint: "[file, class, or module to plan a refactor for]"
allowed-tools: Read, Grep, Glob, Task
metadata:
  category: technique
---

# Refactoring Planner

The orchestrator for this plugin. `code-smells` finds problems; `refactoring-catalog` describes
individual fixes; this skill turns a pile of both into one ordered, safety-first plan a person (or
another agent) can execute step by step without breaking the codebase along the way. The
prioritization heuristic and discipline rules below are original to this skill, informed by the
general principles Fowler's *Refactoring* discusses around when and how to refactor (Ch.1-2) — not
reproduced from the book's text.

## When to Use
- A file/class/module has several code smells and the question is "in what order do I fix these"
- The user asks for a refactoring plan, not just a list of problems
- Before starting a refactoring pass on unfamiliar or long-neglected code
- **Not** for a single isolated smell with one obvious fix — just apply `refactoring-catalog`'s
  entry directly; a plan adds no value when there's nothing to sequence

## The Loop

```
SCOPE       identify the file/class/module boundary for this pass
  ↓
SAFETY NET  confirm tests exist and pass now; if not, that's step 1 of the plan, before anything
              else — refactoring without a passing test suite to catch regressions is not
              refactoring, it's just changing code and hoping
  ↓
DETECT      run code-smells over the scope; collect every TRIGGERED smell with its location
  ↓
CLUSTER     group smells that share a root cause (code-smells already flags likely clusters —
              use those, don't re-derive)
  ↓
PRIORITIZE  order clusters using the heuristic below
  ↓
SEQUENCE    within each cluster, pick specific refactorings from refactoring-catalog and order
              them by dependency (see "Sequencing within a cluster")
  ↓
EMIT PLAN   a numbered list of small steps, each with: refactoring name, location, smell(s) it
              resolves, and a test-checkpoint after it
```

## Prioritization heuristic

Fix in roughly this order — earlier categories make everything after them easier or cheaper, so
doing them first isn't just "importance," it's leverage:

1. **Comprehension blockers first**: Mysterious Name, Comments (the misleading kind), Long
   Function. You can't safely judge or sequence anything else until you can read the code.
2. **Duplication next**: Duplicated Code, Shotgun Surgery. Every duplicate site is a multiplier —
   fixing structure while duplication remains means redoing the fix twice.
3. **Coupling and boundaries**: Feature Envy, Message Chains, Middle Man, Insider Trading,
   Divergent Change. These determine where later structural moves (Extract Class, Move Function)
   should land, so resolve them before committing to a class shape.
4. **Data shape**: Primitive Obsession, Data Clumps, Global Data, Mutable Data, Temporary Field.
   Once boundaries are right, fixing what data looks like is next — it's usually a prerequisite
   for the control-flow and structural work that follows.
5. **Control flow**: Repeated Switches, Loops. Often falls out naturally once step 4's data
   changes are in (e.g. a type code becoming a real type is what makes Replace Conditional with
   Polymorphism possible).
6. **Structural cleanup**: Large Class, Data Class, Refused Bequest, Alternative Classes with
   Different Interfaces. Bigger moves, best done once the smaller ones above have already
   shrunk and clarified what's actually there — attempting these first usually means redoing them.
7. **Cheap anytime wins**: Speculative Generality, Lazy Element. Low-risk deletions/inlines with
   few dependencies on the rest of the plan — safe to interleave wherever convenient, but worth
   doing early since they reduce noise for everything else.

Deviate from this order when a smell is blocking the very next planned step (e.g. you can't Move
Function cleanly while Feature Envy's target is still buried inside a Large Class) — dependency
beats category when the two conflict.

## Sequencing within a cluster

Order individual refactorings by what has to be true before the next one is safe or even
possible:

- Extract before Move: pull the misplaced fragment into its own named function (Extract Function)
  before relocating it (Move Function) — moving something unnamed is harder to review and harder
  to revert if wrong.
- Encapsulate before Replace: Encapsulate Variable / Encapsulate Record before Replace Primitive
  with Object — you need a single choke point to swap the representation behind.
- Split before Replace: Split Loop before Replace Loop with Pipeline if a loop is doing more than
  one job — collapsing straight to a pipeline over a loop with mixed responsibilities usually
  produces a pipeline that's just as tangled.
- Introduce Parameter Object before further calls on the same data clump — later steps get
  simpler once the group is one thing.
- Pull Up before Extract Superclass claims are meaningful — a superclass whose members haven't
  been consolidated up is not yet doing the job the smell needs it to.
- For a smell whose fix has a named inverse in the catalog (Extract/Inline, Pull Up/Push Down,
  Change Reference to Value/Change Value to Reference), pick a direction and commit to it for the
  whole cluster — alternating directions mid-cluster is a sign the plan hasn't settled the
  underlying design question yet.

## Discipline rules (bake these into every emitted plan)

- **One hat at a time.** A refactoring step changes structure with zero observable behavior
  change. If a step is tempting to combine with a feature change or bug fix, split it into two
  commits — refactor first (green), then build the feature on the cleaner code (green again).
- **Small steps, verified each time.** Every step in the emitted plan must be independently
  testable. If a "step" can't be checked in isolation, it's too big — break it down further before
  it goes in the plan.
- **Test after every step, not just at the end.** A red test after a step means revert that one
  step, not push forward hoping the next step fixes it.
- **Commit after every green step.** Small, reversible commits are what make "revert this one
  step" actually cheap when something goes wrong.
- **Prefer the smallest scope that unblocks the actual goal.** A plan triggered by "I need to add
  a feature here" should refactor only what's in the way of that feature (preparatory refactoring)
  — not the whole file. A plan triggered by "this file is a mess and nobody's touched it in years"
  can be broader. Say explicitly, in the emitted plan, which of these two modes you're in.
- **Stop and re-scan after a batch.** Refactoring changes the code's shape; a cluster planned
  against the pre-refactor structure may not match post-refactor reality. Re-run `code-smells` on
  the changed region after finishing a cluster before starting the next one, rather than executing
  the entire original plan blind.

## Output format

Emit the plan as a numbered checklist, one refactoring per line:

```
1. [ ] Extract Function — pull lines 40-58 of `calculateInvoice` into `applyDiscount`
       (fixes: Long Function) — test after
2. [ ] Move Function — relocate `applyDiscount` onto `Discount` (fixes: Feature Envy) — test after
3. [ ] Replace Primitive with Object — turn the `(amount, currency)` pair into `Money`
       (fixes: Primitive Obsession, Data Clumps) — test after
...
```

Group the checklist under its cluster headings so the reader sees both the sequence and the
reasoning, and state up front whether this is a preparatory (scoped-to-the-feature) or standalone
(broad cleanup) pass.

## Limitations
- Use this skill only when the task clearly matches the scope described above.
- Produces a plan, not code — executing each step still means actually applying the named
  refactoring from `refactoring-catalog` and running the real test suite.
- Assumes a test suite exists or is the explicit first step; without one, do not proceed past
  SAFETY NET — a plan built on unverifiable steps is not safe to execute.
- Stop and ask for clarification if the scope is too large to hold in one pass (e.g. an entire
  unfamiliar codebase) — narrow to a file or class first, or use `Task` to fan out `code-smells`
  scans across sub-scopes before merging into one plan.
