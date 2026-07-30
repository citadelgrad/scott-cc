# Chapter 10: Simplifying Conditional Logic

Making branching logic legible — naming its pieces, flattening nested paths, and replacing type-check switches with polymorphism or explicit special-case objects.

### Decompose Conditional
Extract the condition, the then-branch, and the else-branch each into their own well-named function.

- **Motivation:** A conditional with dense boolean logic or multi-line branches forces the reader to parse "what" before they can see "why"; extracting each part lets names carry the intent instead.
- **Mechanics:**
  1. Extract the condition expression into a function named for what it checks, not how.
  2. Run tests.
  3. Extract the then-branch into a function named for what it does.
  4. Run tests.
  5. Extract the else-branch (if any) into a function.
  6. Run tests.
- **Inverse/companion:** Inline Function (to undo); often paired with Consolidate Conditional Expression when several conditions guard the same branch.
- **Fixes smells:** Long Function, Comments (a comment explaining a condition or branch becomes unnecessary once it is named).

### Consolidate Conditional Expression
Combine a series of conditionals that use different tests but lead to the same action into a single condition, extracted to a well-named function.

- **Motivation:** Sequential checks that all funnel into the same result are really one logical test in disguise; merging them clarifies that they are one decision, not several.
- **Mechanics:**
  1. Confirm the checks are truly independent (no side effects that matter) and all produce the same result.
  2. Combine the conditions using and/or into a single expression, replacing the sequence of separate ifs.
  3. Run tests.
  4. Extract the combined condition into a function named for the decision it represents.
  5. Run tests.
- **Inverse/companion:** Decompose Conditional (works in the opposite direction on a single complex condition); Split Phase is unrelated but often follows once the logic is clear.
- **Fixes smells:** Long Function, Duplicated Code (the repeated shape of "check, then same action" across branches).

### Replace Nested Conditional with Guard Clauses
Replace deeply nested if/else structures with early-return guard clauses for the exceptional or edge cases, leaving the main logic unindented at the top level.

- **Motivation:** Nested conditionals imply that all branches are equally normal; guard clauses signal "this case is unusual, handle it and get out," making the dominant, expected path easy to find.
- **Mechanics:**
  1. Pick the outermost or simplest condition that represents an edge case; invert it into an early return (or throw) at the top of the function.
  2. Run tests.
  3. Repeat for each remaining edge case, one guard at a time.
  4. Run tests after each guard is introduced.
  5. Once only the main-path logic remains, remove any now-unneeded else blocks.
- **Inverse/companion:** Consolidate Conditional Expression (if several guards check related conditions, consider merging them); inverse move would be re-nesting, which is rarely useful.
- **Fixes smells:** Long Function (deep nesting inflates apparent complexity), Duplicated Code (repeated cleanup/return logic scattered through nested branches).

### Replace Conditional with Polymorphism
Move each branch of a conditional that switches on an object's type or state into an overriding method on a corresponding subclass (or strategy/state object), letting method dispatch replace the explicit branching.

- **Motivation:** When the same type-based conditional recurs across a codebase, or a conditional is expected to grow more branches over time, polymorphism lets each case live in one place and lets new cases be added without touching existing code.
- **Mechanics:**
  1. Ensure a class hierarchy (or strategy/state objects) exists with one subclass per branch of the conditional; create it if missing, using Extract Class / factory as needed.
  2. Pick one branch; create or use the corresponding subclass method and move that branch's logic into it as an override.
  3. Run tests.
  4. Repeat one branch/subclass at a time, running tests after each move.
  5. Once all branches are moved, remove the original conditional and make the caller invoke the polymorphic method directly.
  6. Run tests.
- **Inverse/companion:** Replace Type Code with Subclasses (often a prerequisite); the inverse — collapsing polymorphism back into a conditional — is rarely named but is a legitimate simplification when the hierarchy has only one real variant left.
- **Fixes smells:** Repeated Switches (the same type-check switch/conditional appearing at multiple call sites), Duplicated Code, Shotgun Surgery (adding a new case previously meant editing every switch).

### Introduce Special Case
Replace repeated checks for a special value (such as null, "unknown," or a sentinel) with a special-case object that responds to the same interface with sensible default behavior.

- **Motivation:** When many call sites independently check for and handle an absent or special value, the logic for "what to do in the special case" is duplicated; a special-case object centralizes that behavior behind the normal interface.
- **Mechanics:**
  1. Add a method or property on the containing object that reports whether it is the special case, if one does not exist.
  2. Create a special-case object (or shared constant/singleton) implementing the same interface as the normal object, encoding the default behavior.
  3. Find a call site that checks for the special value; replace its check with use of the special-case object instead, so the check disappears from that call site.
  4. Run tests.
  5. Repeat for each remaining call site, one at a time.
  6. Once all checks are replaced, remove the now-unused raw special-value handling.
- **Inverse/companion:** Introduce Assertion (for cases that should never legitimately occur, versus special cases that are expected); this is a specific application of Replace Conditional with Polymorphism where one "type" is the special case.
- **Fixes smells:** Duplicated Code (repeated null/missing-value checks scattered across the code), Shotgun Surgery (a new special-case rule previously required touching every check site).

### Introduce Assertion
Add an explicit assertion that states an assumption the code depends on but does not otherwise document, making the precondition visible and failing loudly if violated.

- **Motivation:** Some code only behaves correctly under an assumption that is nowhere stated; making that assumption an assertion documents it for readers and turns a silent wrong-behavior bug into a loud, immediate failure.
- **Mechanics:**
  1. Identify the implicit assumption the surrounding code relies on.
  2. Add an assertion expressing that assumption at the point it is relied upon.
  3. Run tests to confirm the assertion holds under current behavior and doesn't fire spuriously.
- **Inverse/companion:** Introduce Special Case (assertions guard conditions that should never happen; special cases handle conditions that legitimately can happen).
- **Fixes smells:** Does not map cleanly to a specific Ch.3 smell — it is primarily a documentation and safety-net move rather than a remedy for a structural smell, though it can substitute for a Comment explaining an assumption.
