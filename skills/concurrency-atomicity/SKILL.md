---
name: concurrency-atomicity
description: >-
  Use when a diff, branch, or PR touches threads, async/concurrent code, shared
  mutable state, locks/mutexes/semaphores, check-then-act logic, or multi-step state
  transitions that must be all-or-nothing (payments, inventory, multi-table writes).
  Applies a narrow, four-checkpoint concurrency-correctness review: race
  conditions/shared mutable state, TOCTOU non-atomicity, deadlock/lock-ordering
  violations, and transactional atomicity. Grounded in fetched CWE reference entries
  (CWE-362, CWE-367, CWE-833, CWE-667, CWE-662), not general security review. Also
  runnable directly via /scott-cc:concurrency-atomicity for an explicit standalone
  pass. Not for broad security/hostile-input review (use adversarial-reviewer) or
  general structural, code-health, or per-language idiom review (use thermo-nuclear,
  google-standard, or polyglot-idiom).
license: MIT
metadata:
  category: technique
  triggers: [code-review, concurrency, race-condition, deadlock, atomicity, toctou]
---

# Concurrency & Atomicity Review

This skill applies exactly four bug-class checkpoints, each grounded in a real CWE
reference entry fetched from `https://cwe.mitre.org/`, fetched 2026-07-31:

| Checkpoint | CWE | URL |
|---|---|---|
| Race conditions / shared mutable state | CWE-362 | `https://cwe.mitre.org/data/definitions/362.html` |
| TOCTOU non-atomicity | CWE-367 | `https://cwe.mitre.org/data/definitions/367.html` |
| Deadlock / lock-ordering violations | CWE-833 | `https://cwe.mitre.org/data/definitions/833.html` |
| Improper locking (backs both deadlock and lock-discipline findings) | CWE-667 | `https://cwe.mitre.org/data/definitions/667.html` |
| Transactional atomicity / improper synchronization | CWE-662 | `https://cwe.mitre.org/data/definitions/662.html` |

It is a single-bug-class specialist, not a general reviewer — it does not evaluate
naming, style, structure, or hostile-input handling outside of concurrency correctness.

## How This Differs From adversarial-reviewer, thermo-nuclear, google-standard, and polyglot-idiom

- **adversarial-reviewer** red-teams broadly for bugs, security holes, and
  hostile/malformed input handling across the entire attack surface.
  **concurrency-atomicity** is narrower: it only checks four specific concurrency and
  atomicity bug classes, each tied to a cited CWE entry, and does not evaluate input
  validation, injection, auth, or any other security concern outside of concurrency.
- **thermo-nuclear** applies a structural-simplification doctrine (branch count, file
  size, spaghetti-branching). **google-standard** applies Google's code-health
  approval bar. **polyglot-idiom** applies per-language idiom checklists.
  **concurrency-atomicity** applies none of these lenses — a change can pass every one
  of those three reviews and still contain a race condition, and vice versa.
- Use concurrency-atomicity specifically when the diff touches shared mutable state,
  multi-step check-then-act logic, lock acquisition/release, or multi-step state
  transitions that must be all-or-nothing (e.g. financial transfers, inventory
  decrements, multi-table writes).
- This skill can be invoked automatically by the model, or by another orchestrating
  skill or agent (e.g. review-panel), whenever a diff shows this kind of concurrency
  or atomicity surface area — it is not limited to explicit invocation via its slash
  command, though that remains available for a standalone pass.

## Checkpoints

### 1. Race conditions / shared mutable state (CWE-362)

CWE-362, *Concurrent Execution using Shared Resource with Improper Synchronization
('Race Condition')*: "The product contains a concurrent code sequence that requires
temporary, exclusive access to a shared resource, but a timing window exists in which
the shared resource can be modified by another code sequence operating concurrently."

A race condition violates one of two properties, per the CWE's extended description:

- **Exclusivity** — "the code sequence is given exclusive access to the shared
  resource, i.e., no other code sequence can modify properties of the shared resource
  before the original sequence has completed execution."
- **Atomicity** — "the code sequence is behaviorally atomic, i.e., no other thread or
  process can concurrently execute the same sequence of instructions (or a subset)
  against the same resource."

Flag:

- Shared mutable state (module-level variables, class-level fields, shared caches,
  singletons) read and written by more than one thread/coroutine/process without a
  lock, mutex, semaphore, or atomic primitive guarding the access.
- Read-modify-write sequences on shared counters, balances, or collections (e.g.
  `balance = balance + amount` split across separate read and write statements) that
  are not wrapped in an atomic operation or lock.
- The CWE's own demonstrative example: two concurrent operations both reading a value
  (e.g. an account balance), independently computing a new value, and writing it back —
  the classic lost-update pattern.

### 2. TOCTOU non-atomicity (CWE-367)

CWE-367, *Time-of-check Time-of-use (TOCTOU) Race Condition*: "The product checks the
state of a resource before using that resource, but the resource's state can change
between the check and the use in a way that invalidates the results of the check."

Flag:

- Any `if <check-condition>: <act>` pattern against a resource that another
  thread/process/request can mutate between the check and the act — file existence
  checks before open/write, permission checks before an operation, stock-level checks
  before decrementing inventory, "does this row exist" checks before insert/update.
- Consequences called out by the CWE apply directly: integrity violations (unauthorized
  access or modification of data/files that should be restricted), unlogged actions
  bypassing legitimate channels, and "the product may perform invalid actions when the
  resource is in an unexpected state."
- Per the CWE's cited mitigation, prefer avoiding the check-then-act split entirely —
  use an atomic check-and-act primitive (e.g. `INSERT ... ON CONFLICT`, `compare-and-swap`,
  a filesystem's atomic create-exclusive flag) or acquire the lock *before* the check so
  the checked state cannot change before use.

### 3. Deadlock / lock-ordering violations (CWE-833, CWE-667)

CWE-833, *Deadlock*: "The product contains multiple threads or executable segments that
are waiting for each other to release a necessary lock, resulting in deadlock." Its
common consequence: "Each thread of execution will 'hang' and prevent tasks from
completing. In some cases, CPU consumption may occur if a lock check occurs in a tight
loop." CWE-833 is itself classified as a specific case of CWE-667, *Improper Locking*:
"The product does not properly acquire or release a lock on a resource, leading to
unexpected resource state changes and behaviors" — and CWE-667 notes "inconsistent
locking discipline can lead to deadlock."

Flag:

- Two or more locks acquired in inconsistent order across different code paths (lock
  A-then-B in one function, B-then-A in another) — the canonical deadlock precondition.
- Locks acquired but not released on every exit path, including exception/error paths
  (missing `finally`/`defer`/`using`/context-manager release).
- Nested lock acquisition where the inner lock is held while waiting on a resource
  (I/O, network call, another lock) that could itself require the outer lock.
- Lock-check-in-a-loop patterns (busy-wait/spin patterns) that the CWE notes can turn a
  hang into unbounded CPU consumption.

### 4. Transactional atomicity (CWE-662)

CWE-662, *Improper Synchronization*: "The product utilizes multiple threads, processes,
components, or systems to allow temporary access to a shared resource that can only be
exclusive to one process at a time, but it does not properly synchronize these
actions." Its extended description states directly: "some shared resource operations
cannot be executed atomically; that is, multiple steps must be guaranteed to execute
sequentially, without any interference by other processes" — and improper synchronization
of such multi-step operations "can result in data or memory corruption, denial of
service, etc."

Flag:

- Multi-step state changes (e.g. debit one account then credit another; decrement
  inventory then create an order row; write to two tables) that are not wrapped in a
  single transaction or equivalent atomic unit — a crash, exception, or concurrent
  read between the steps leaves the system in a partially-updated, inconsistent state.
- Partial-write hazards: a multi-field or multi-record update where only some
  fields/records are persisted before a failure, with no rollback or compensating
  action.
- Missing or incorrect transaction boundaries (transaction opened too late, committed
  too early, or spanning a network call/external side effect that cannot itself be
  rolled back).
- Idempotency gaps in retried operations — if a multi-step operation is retried after a
  partial failure, does it re-apply steps that already succeeded?

## Review Process

1. **Resolve the target** — a `base..head` range, branch, PR, or (if none given) the
   current working-tree diff against `HEAD`.
2. **Identify concurrency-relevant surface area**: shared mutable state, multi-threaded
   or multi-process code, async/concurrent code, check-then-act patterns, lock
   acquisition/release, and multi-step state transitions (especially ones touching
   money, inventory, or multiple tables/records).
3. For each candidate, apply the matching checkpoint (1–4 above) and cite the CWE it
   violates.
4. Categorize each finding as **blocking** (a real, reachable race/TOCTOU/deadlock/
   atomicity gap) or **advisory** (theoretically possible but requires an unlikely
   timing window or is already mitigated elsewhere in the stack, e.g. a DB unique
   constraint backstopping an app-level check).
5. Produce the report: findings grouped by checkpoint (with CWE citation per finding),
   and an explicit approve/block verdict.

## What NOT to Do

1. **Don't flag single-threaded, single-process code with no shared state** — none of
   these four checkpoints apply without concurrent or multi-step-interruptible
   execution.
2. **Don't raise a finding without tying it to one of the four checkpoints and its
   CWE** — if a real concurrency bug doesn't map to CWE-362/367/833/667/662, describe
   it as a general finding rather than inventing a fifth checkpoint this skill doesn't
   own.
3. **Don't evaluate anything outside concurrency/atomicity** — naming, style, general
   security (injection, auth, hostile input), and structural design are out of scope;
   defer to `adversarial-reviewer`, `thermo-nuclear`, `google-standard`, or
   `polyglot-idiom` for those.
4. **Don't assume a database's default isolation level fixes an application-level
   race** — many default isolation levels (e.g. Postgres's default READ COMMITTED)
   do not prevent read-modify-write races; verify the actual isolation level and
   locking strategy in use rather than assuming ACID guarantees cover it.

## When to Use

- Runnable directly via `/scott-cc:concurrency-atomicity`, or automatically by the
  model or an orchestrating skill/agent (e.g. review-panel) when a diff's surface area
  warrants this lens.
- Use when a diff touches threads, async/concurrent code, shared caches or singletons,
  file/resource check-then-act logic, explicit locks/mutexes/semaphores, or multi-step
  state transitions that must succeed or fail as a unit (payments, inventory, multi-
  table writes).
- Not the right tool for a diff with no concurrency or multi-step-atomicity surface
  area — use `review-panel`, `thermo-nuclear`, `google-standard`, or `polyglot-idiom`
  instead.

## Limitations

- Covers exactly four checkpoints tied to five CWE entries (CWE-362, CWE-367, CWE-833,
  CWE-667, CWE-662). It is not a general concurrency-theory reviewer and does not cover
  every CWE under the broader "Concurrent Execution" category (CWE-557 family) —
  only the ones listed above.
- Grounded in CWE reference pages fetched 2026-07-31. If MITRE revises these entries,
  this skill will drift until re-synced.
- Static review only — it cannot detect timing-window races that require dynamic
  analysis, stress testing, or a race detector (e.g. Go's `-race`, ThreadSanitizer) to
  confirm. Flag suspected races as findings; recommend dynamic verification rather than
  asserting a race is provably reachable from a diff alone.
- Does not check general security holes or hostile-input handling — use
  `adversarial-reviewer` for that.
- Stop and ask for clarification if the diff, PR, or branch target cannot be resolved
  unambiguously.
