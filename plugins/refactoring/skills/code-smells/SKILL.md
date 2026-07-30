---
name: code-smells
description: >-
  Use when reviewing code for maintainability problems, deciding whether something needs
  refactoring, or when the user asks for a "code smell" check. Scans code against all 24 named
  smells from Martin Fowler's "Refactoring" (2nd ed.) Chapter 3 and maps each one to the specific
  refactoring(s) that resolve it. Not for looking up a refactoring's own mechanics (use
  refactoring-catalog) or for turning a pile of smells into a sequenced cleanup plan (use
  refactoring-planner).
argument-hint: "[file or directory]"
allowed-tools: Read, Grep, Glob
metadata:
  category: discipline
---

# Code Smells (Fowler, Ch.3)

A code smell is a surface signal, not a proven defect — it means "look closer here," not "this is
definitely wrong." When invoked with `$ARGUMENTS`, read the target file or directory and check it
against every smell below. For each: CLEAR, TRIGGERED, or N/A, with a file:line and the specific
refactoring(s) from `refactoring-catalog` that would resolve it.

These 24 names and groupings are Martin Fowler's, from *Refactoring: Improving the Design of
Existing Code* (2nd ed.), Chapter 3. The descriptions, signals, and smell-to-refactoring mappings
below are written fresh for this skill, not reproduced from the book's text.

## When to Use
- Reviewing a PR, file, or module for maintainability problems
- Deciding whether code is "bad enough" to justify a refactoring pass
- The user asks for a code smell check, or references Fowler/"bad smells in code" by name
- Before handing a smell inventory to `refactoring-planner` for sequencing

## Naming & Documentation

### 1. Mysterious Name
A function, variable, class, or module whose name gives no useful clue what it does or holds.
- **Signals:** you have to open the definition (or ask someone) before you can safely call
  something; names like `data`, `handle`, `process`, `mgr`, `util2`
- **Fix:** Rename Variable, Change Function Declaration

### 2. Comments
Not a ban on comments — a comment used as a deodorant for code that should instead be made clear
on its own.
- **Signals:** a comment explaining *what* a block does (rather than *why*); a comment that would
  become unnecessary if the block were extracted and named; a comment that's drifted out of sync
  with the code beneath it
- **Fix:** Extract Function, Extract Variable, Rename Variable, Introduce Assertion (for the rare
  comment that's really a documented invariant worth keeping)

## Bloaters

### 3. Long Function
A function that has grown past the point where its name and shape communicate what it does; you
can no longer hold its whole behavior in your head at once.
- **Signals:** scrolling to see the whole function; deep nesting; needing comments to mark
  sections; hard to name in one phrase
- **Fix:** Extract Function, Decompose Conditional, Replace Loop with Pipeline, Split Loop,
  Replace Conditional with Polymorphism, Replace Function with Command

### 4. Long Parameter List
A function whose signature requires the caller to know and supply more values than they should
have to think about together.
- **Signals:** 4+ parameters; several parameters that always travel together; boolean or code
  parameters that switch behavior
- **Fix:** Introduce Parameter Object, Preserve Whole Object, Remove Flag Argument, Combine
  Functions into Class

### 5. Large Class
A class trying to do — and know — too much.
- **Signals:** many fields that aren't all used by every method; low cohesion between groups of
  members; class hard to describe without "and"
- **Fix:** Extract Class, Extract Superclass, Replace Type Code with Subclasses

### 6. Data Clumps
The same small group of values (a start/end pair, a street/city/zip trio) shows up together,
again and again, as separate parameters or fields instead of one thing.
- **Signals:** the same 2-3 parameters recur across many signatures; deleting one field of the
  group without the others would be a bug
- **Fix:** Extract Class, Introduce Parameter Object, Preserve Whole Object

## Duplication & Change Friction

### 7. Duplicated Code
The same code structure appears in more than one place.
- **Signals:** copy-pasted blocks with minor variable renames; two functions in sibling classes
  that are nearly identical; a bug fix that has to be applied in more than one file
- **Fix:** Extract Function, Pull Up Method, Substitute Algorithm, Combine Functions into Class

### 8. Divergent Change
One module gets modified in different, unrelated ways for different reasons — a sign it's
carrying more than one responsibility.
- **Signals:** commit history shows the same file touched for "billing changes" one week and
  "reporting changes" the next, with no overlap between those diffs
- **Fix:** Extract Class, Split Phase, Move Function

### 9. Shotgun Surgery
The opposite failure mode of Divergent Change: one kind of change requires many small edits
scattered across many modules.
- **Signals:** a single conceptual change (e.g. "add a field to Order") touches ten files; easy
  to forget one of the edit sites
- **Fix:** Move Function, Move Field, Inline Class, Combine Functions into Class

## Coupling Between Elements

### 10. Feature Envy
A function that spends more time reaching into another object's data than it does using its own.
- **Signals:** a function calls three+ getters on the same foreign object; the function would be
  shorter and simpler if it just lived on that other object instead
- **Fix:** Move Function, Extract Function (to pull out just the envious part before moving it)

### 11. Message Chains
Code that walks `a.getB().getC().getD()` — a caller navigating through a sequence of intermediate
objects to reach the one it actually wants.
- **Signals:** long dotted call chains; caller depends on the exact internal structure of a
  navigation path, not just the final value
- **Fix:** Hide Delegate, Extract Function (to name the traversal once)

### 12. Middle Man
A class whose methods mostly just forward to another object, adding no behavior of its own — the
overcorrection of hiding a delegate too aggressively.
- **Signals:** most of a class's methods are one-line delegations; callers could talk to the real
  object directly with no loss of encapsulation
- **Fix:** Remove Middle Man, Inline Function, Replace Superclass with Delegate

### 13. Insider Trading
Two modules cooperate so much, and know so much about each other's internals, that they're really
one thing pretending to be two.
- **Signals:** private-feeling details shared across a module boundary; the two modules change in
  lockstep even though nothing declares the dependency
- **Fix:** Move Function, Move Field, Hide Delegate, Extract Class (to make the shared concept
  explicit instead of implicit)

## Data & State

### 14. Global Data
Data reachable and mutable from anywhere in the program, with no way to trace who's touching it.
- **Signals:** module-level mutable variables, singletons with public setters, environment-wide
  config objects mutated at runtime
- **Fix:** Encapsulate Variable

### 15. Mutable Data
A value that changes underneath code that's still holding a reference to it, producing bugs where
an update in one place breaks something in an apparently unrelated place.
- **Signals:** a setter whose caller can't easily tell who else reads the value; changing an
  update elsewhere and getting an unexplained failure
- **Fix:** Split Variable, Separate Query from Modifier, Change Reference to Value, Remove Setting
  Method, Replace Derived Variable with Query

### 16. Primitive Obsession
Using raw primitives (strings, numbers, tuples/arrays) to represent domain concepts that deserve
their own type — money, a phone number, a date range, a coordinate.
- **Signals:** a string that's always validated the same way everywhere it's used; a group of
  primitives that always travel together; formatting/parsing logic duplicated at every call site
- **Fix:** Replace Primitive with Object, Replace Type Code with Subclasses, Introduce Parameter
  Object

### 17. Repeated Switches
The same `switch`/`if-else` chain over the same condition (often a type code) reappears in
multiple places in the code.
- **Signals:** the same set of `case` branches, or the same enum comparison, copy-pasted or
  reimplemented at several call sites; adding a new case means hunting down every occurrence
- **Fix:** Replace Conditional with Polymorphism

### 18. Temporary Field
An instance variable that's only set and meaningful in certain circumstances — nonsense the rest
of the time.
- **Signals:** a field that's `null`/unset outside one specific call path; conditionals elsewhere
  checking "has this field been set yet" before using it
- **Fix:** Extract Class (to move the field and its dependent behavior into its own object),
  Introduce Special Case (Null Object) for the "not set" state

## Control Flow

### 19. Loops
A loop written the traditional way (explicit iteration, accumulator variable) where a pipeline of
filter/map/reduce-style operations would say the same thing more directly.
- **Signals:** loop body that's really "keep some, transform each, combine into one" but expressed
  as manual iteration with mutable accumulators
- **Fix:** Replace Loop with Pipeline, Split Loop (first, if the loop is doing more than one job)

## Dispensables

### 20. Lazy Element
A function, class, or module that no longer earns the indirection it costs — a wrapper thinner
than the concept it was meant to clarify.
- **Signals:** a class with one trivial method; a function that just calls another function with
  the same arguments; an abstraction layer nobody has needed a second implementation of
- **Fix:** Inline Function, Inline Class, Collapse Hierarchy

### 21. Speculative Generality
Machinery built "in case we need it later" — parameters, hook methods, abstract classes,
configuration options — that nothing in the current codebase actually uses.
- **Signals:** an interface with exactly one implementation and no concrete plan for a second;
  a parameter that every caller passes the same value for; a strategy/plugin point with one
  strategy
- **Fix:** Remove Subclass, Inline Function, Inline Class, Change Function Declaration (to drop
  the unused parameter)

### 22. Alternative Classes with Different Interfaces
Two classes do the same job but expose it through differently-named or differently-shaped methods
— duplication hidden by inconsistent naming.
- **Signals:** two classes could be used interchangeably by callers if only their method names or
  signatures lined up; a caller has an `if (typeA) ... else ...` purely to bridge the naming gap
- **Fix:** Change Function Declaration (to align the two interfaces), Move Function, Extract
  Superclass

### 23. Data Class
A class that's nothing but fields plus getters/setters — all data, no behavior — so the logic
that should live with that data ends up scattered among its callers instead.
- **Signals:** class has no method that does more than read or write a field; behavior that
  clearly belongs to this data lives in three different calling classes instead
- **Fix:** Move Function (to pull behavior in from callers), Encapsulate Collection, Remove
  Setting Method (for fields that shouldn't be externally mutable)

### 24. Refused Bequest
A subclass that inherits from a superclass but only wants part of its interface, ignoring or
overriding the rest to throw/no-op — a sign the inheritance relationship itself is wrong.
- **Signals:** subclass overrides a parent method to do nothing or throw "not supported"; subclass
  never calls several of the methods it inherited
- **Fix:** Replace Subclass with Delegate, Replace Superclass with Delegate, Push Down Method,
  Push Down Field

## Review Process

1. **Identify scope**: file, module, class, or PR diff.
2. **Scan every smell above**: CLEAR, TRIGGERED, or N/A. For each triggered smell: exact
   location, a one-line reason it's triggered (not just the name), and the fix refactoring(s).
3. **Watch for compound smells**: several triggered smells often share one root cause (e.g. Long
   Function + Repeated Switches + Feature Envy together usually point at a class that grew around
   a type code that wants to be polymorphism). Note the cluster, not just the individual smells.
4. **Hand off**: a list of triggered smells with candidate refactorings is the direct input
   `refactoring-planner` needs to build a sequenced, test-checkpointed cleanup plan — don't
   re-derive the smell list there.

## Limitations
- Use this skill only when the task clearly matches the scope described above.
- A smell is a signal, not a diagnosis — a triggered smell may still be the right tradeoff given
  constraints (deadline, code slated for deletion, generated code). Say so rather than insisting
  on a fix.
- Does not fix code or produce a refactoring sequence; that's `refactoring-planner`'s job.
- Stop and ask for clarification if the review scope is unclear, or if a "smell" is actually a
  deliberate, documented design tradeoff you can't evaluate without more context.
