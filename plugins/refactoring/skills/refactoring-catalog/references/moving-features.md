# Chapter 8: Moving Features

Relocating behavior and data to where they're actually used — across functions, across objects, and within a function body — plus cleaning up loops and dead code along the way.

### Move Function
Relocate a function to the class, module, or file where it is most used or most conceptually at home.

- **Motivation:** A function that spends most of its time reading data or calling other functions on a different object than the one it lives on is in the wrong place; moving it closer to that data reduces coupling and clarifies responsibility.
- **Mechanics:**
  1. Check all sub-functions and references the function uses in its current context; move or replicate anything it depends on that isn't already visible in the target location.
  2. Declare the function in the target location, adjusting parameters as needed to supply what it can no longer reach implicitly.
  3. Have the old function body delegate to the new one (or replace all callers to point at the new location), and test.
  4. Once all callers reference the new location, remove the old function; test again.
  5. Consider whether the moved function should now be renamed to fit its new home.
- **Inverse/companion:** Itself is symmetric (moving back is the same refactoring in reverse); closely paired with Move Field when behavior and data travel together.
- **Fixes smells:** Feature Envy, Divergent Change, Shotgun Surgery, Insider Trading, Large Class.

### Move Field
Relocate a field's declaration from one class/record to another where it is more heavily used or more logically owned.

- **Motivation:** When code on another object constantly reaches into a field, or a class changes for reasons unrelated to that field, the field's home no longer matches its usage; moving it aligns data ownership with data use.
- **Mechanics:**
  1. Encapsulate the field first if it isn't already accessed through a getter/setter.
  2. Create the equivalent field on the target class, along with accessors.
  3. Change the source getter/setter to delegate to the target's field; test.
  4. Update each caller to use the new location directly (or leave the delegating accessor in place if callers are numerous); test after each swap.
  5. Remove the old field once nothing references it directly; test.
- **Inverse/companion:** Itself is symmetric; frequently done alongside Move Function when a field and the code that uses it belong together.
- **Fixes smells:** Feature Envy, Data Clumps, Divergent Change, Shotgun Surgery, Insider Trading, Temporary Field.

### Move Statements into Function
Pull statements that always accompany a call to a function into the function body itself.

- **Motivation:** When every caller repeats the same lines immediately before or after invoking a function, that duplication belongs inside the function, reducing repetition and the risk callers drift apart.
- **Mechanics:**
  1. Confirm the statements to be moved appear identically (or can be made to) at every call site.
  2. If only some call sites share the statements, use Slide Statements first to bring them adjacent to the call.
  3. Move the statements into the start or end of the function body, adjusting for one call site; test.
  4. Remove the now-redundant statements from each other call site one at a time, testing after each.
- **Inverse/companion:** Move Statements to Callers.
- **Fixes smells:** Duplicated Code, Long Function.

### Move Statements to Callers
Push statements out of a shared function and into each of its callers when the behavior is no longer uniformly needed.

- **Motivation:** When a function's responsibilities begin to diverge across callers — some need extra behavior, others don't — keeping it all inside the function causes conditional complexity or unwanted side effects for some callers; moving the varying part out restores a single clear responsibility.
- **Mechanics:**
  1. For simple cases, copy the statements to be extracted into each caller, immediately after the call; test after each copy.
  2. Remove the statements from the function body; test.
  3. Consider whether follow-up inlining (Inline Function) is warranted if the function is now trivial, or whether an extraction point (a parameter, or Extract Function on the remaining logic) is needed for callers that still want the old combined behavior.
  4. For many callers or risky changes, do the move behind a temporary duplicated function so old and new callers can be migrated one at a time.
- **Inverse/companion:** Move Statements into Function.
- **Fixes smells:** Divergent Change, Long Function.

### Replace Inline Code with Function Call
Replace a fragment of inline logic with a call to an existing function that already does the same thing.

- **Motivation:** Duplicated inline logic that duplicates a named function's behavior should be replaced by calling that function, so intent is named once and future changes only need to happen in one place.
- **Mechanics:**
  1. Identify the inline code and the existing function that reproduces its behavior.
  2. Replace the inline code with a call to the function, passing whatever arguments are needed to match behavior exactly.
  3. Test.
- **Inverse/companion:** Roughly the inverse of Inline Function (which turns a function call back into its inline body).
- **Fixes smells:** Duplicated Code.

### Slide Statements
Reorder statements within a function (or across nearby scopes) so that related code sits together.

- **Motivation:** Statements that operate on the same data or concept but are scattered through a function are harder to read and harder to extract; sliding them adjacent to each other prepares the ground for further refactoring such as Extract Function.
- **Mechanics:**
  1. Identify the statement(s) to move and the target location.
  2. Check for interference: confirm nothing between the current position and the target reads or writes data the sliding statements depend on, and vice versa.
  3. Move the statements in one small step; test.
  4. If moving across a structural boundary (e.g., into or out of a conditional or loop), take extra care and consider smaller intermediate moves.
- **Inverse/companion:** Symmetric — sliding is its own inverse (slide back to undo); often a precursor step used inside Extract Function, Split Loop, and Move Statements into/to Function.
- **Fixes smells:** Duplicated Code (setup for removing it), Long Function.

### Split Loop
Separate a loop that does two or more distinct things into multiple single-purpose loops.

- **Motivation:** A loop accumulating more than one result at once is doing more than one job, making each part harder to understand, reuse, or extract in isolation; running the loop twice for two purposes clarifies each and enables independent refactoring (e.g., Extract Function or Replace Loop with Pipeline) on each.
- **Mechanics:**
  1. Duplicate the loop so the same iteration appears twice in sequence.
  2. Remove the statements belonging to the "other" purpose from each copy, leaving each loop doing exactly one thing; test after each removal.
  3. Consider applying Extract Function to each resulting loop.
- **Inverse/companion:** No formal named inverse; conceptually the opposite of manually fusing two loops together (which is generally discouraged in favor of clarity over the perceived performance gain).
- **Fixes smells:** Loops, Long Function.

### Replace Loop with Pipeline
Rewrite a loop as a chain of collection pipeline operations (e.g., filter/map/reduce equivalents).

- **Motivation:** Pipeline operations name the operation being performed (filtering, transforming, combining) rather than the mechanics of iteration, making the intent easier to read at a glance once you're familiar with pipeline vocabulary.
- **Mechanics:**
  1. Identify the collection being iterated and the loop variable.
  2. Convert the loop body's logic, step by step, into an equivalent pipeline operation (e.g., a conditional-then-collect becomes a filter; a transform-then-collect becomes a map), replacing one small piece at a time.
  3. Test after each conversion step.
  4. Delete the original loop once the pipeline fully replaces its behavior.
- **Inverse/companion:** No formal named inverse; the reverse transformation (pipeline back to explicit loop) is occasionally done when pipeline chains become hard to follow or debug.
- **Fixes smells:** Loops.

### Remove Dead Code
Delete code that is no longer executed or referenced by anything live.

- **Motivation:** Unreachable or unused code adds reading and maintenance burden and creates false signals about what the system does; since version control preserves history, it can always be recovered later if truly needed.
- **Mechanics:**
  1. Confirm the code is genuinely dead — not reachable through any live path, reflection, or dynamic dispatch.
  2. If a feature toggle or flag makes the code path unreachable, remove the flag and its branches too.
  3. Delete the code outright rather than commenting it out.
  4. Test to confirm nothing depended on it.
  5. Rely on version control history (not commented-out code) as the safety net for recovering it later.
- **Inverse/companion:** None — this is a one-directional cleanup with no meaningful companion refactoring.
- **Fixes smells:** No direct Ch.3 smell mapping — Fowler treats dead code removal as a general hygiene and simplicity practice rather than a remedy for a specific named smell, though it can incidentally reduce the visual noise associated with Comments left to explain now-unused code.
