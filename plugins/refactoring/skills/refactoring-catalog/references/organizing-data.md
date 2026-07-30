# Chapter 9: Organizing Data

Untangling variables and fields that carry more than one meaning, and choosing between value and reference semantics deliberately instead of by accident.

### Split Variable
Give each distinct responsibility a variable holds its own separate variable, instead of reassigning one variable to mean different things over its lifetime.

- **Motivation:** A variable that gets reassigned for a second, unrelated purpose (e.g. one used as an accumulator and then reused as a loop index, or as an input parameter and then a working result) forces the reader to track which "meaning" is live at each point. Splitting restores one-variable-one-purpose.
- **Mechanics:**
  1. Find the declaration of the variable and any point where it is reassigned for a genuinely different purpose (not just an updated value of the same purpose, as in a loop accumulator).
  2. Rename the declaration and all references up to the point of reassignment to a name reflecting its first purpose.
  3. Introduce a new variable, declared at the point of reassignment, for the second purpose; rename its references accordingly.
  4. Run tests after each rename to confirm nothing depended on the shared name.
  5. Repeat if the variable is reused for a third purpose.
- **Inverse/companion:** No direct inverse; it pairs with Extract Variable (creating meaningful names for sub-expressions) and often precedes Extract Function once each variable has a single clear role.
- **Fixes smells:** Mutable Data (a variable reassigned for unrelated purposes is a concentrated form of this smell); also improves Mysterious Name symptoms since a split variable can be named for what it actually holds at each point.

### Rename Field
Change the name of a field in a record, class, or structure to better communicate its purpose, propagating the rename to accessors, constructors, and all call sites.

- **Motivation:** Field names are read far more often than they are written; a name that misleads or under-communicates imposes an ongoing tax on every reader. This is the field-level counterpart to renaming a variable or function.
- **Mechanics:**
  1. If the field is only accessed through encapsulating methods (getters/setters), rename the internal field first and update those methods' bodies; run tests.
  2. Rename the accessor/mutator methods (or introduce new ones and deprecate the old) one at a time, updating call sites incrementally rather than in one large sweep.
  3. If the field is public/exposed directly, prefer first applying Encapsulate Variable/Record so future renames stay internal.
  4. Update any serialization, persistence mapping, or external contract names last, and only if warranted, since these often need independent versioning.
  5. Test after each incremental step, not just at the end.
- **Inverse/companion:** Self-inverse (renaming back undoes it); typically preceded by Encapsulate Record or Encapsulate Variable so the rename is localized behind accessors.
- **Fixes smells:** Mysterious Name (the direct target); also reduces Comments that exist only to explain what a poorly-named field actually means.

### Replace Derived Variable with Query
Remove a variable that stores a value computed from other data, and instead recompute it on demand through a function/query, eliminating the need to keep the stored value in sync.

- **Motivation:** A cached/derived value must be updated everywhere its inputs change; miss one update site and the variable silently goes stale. If recomputation is cheap enough, a query removes the synchronization burden entirely and removes a piece of mutable state from the program.
- **Mechanics:**
  1. Identify all points where the derived variable is updated; confirm they all recompute the same logical value.
  2. Use Extract Function to turn the computation into a query function reading current source data.
  3. Find all reads of the variable and replace each with a call to the new query; test after each replacement.
  4. Once no reads remain, remove the variable's declaration and every update site that assigned to it; test.
  5. If recomputation is expensive, consider caching inside the query itself (with clear invalidation) rather than reverting to a manually-synced field.
- **Inverse/companion:** No formal named inverse in the catalog; the opposite move (introducing a stored/cached field to avoid recomputation) is an ad hoc optimization, not a catalogued refactoring, and should only be reached for after measuring a real performance need.
- **Fixes smells:** Mutable Data (removes a piece of state that must be kept consistent with its source); also addresses Divergent Change/Shotgun Surgery when updates to the derived value were scattered across multiple update sites that all had to change together.

### Change Reference to Value
Convert an object that is treated as a shared reference (identity matters, mutated in place, aliasing observable) into an immutable value object (equality by content, replaced rather than mutated).

- **Motivation:** Reference semantics mean a mutation is visible through every alias to the object, which is easy to reason about only when mutation is tightly controlled. When you want objects to behave like plain data — safely copyable, comparable by contents, usable across threads/boundaries without defensive copying concerns — converting to a value removes the aliasing hazard.
- **Mechanics:**
  1. Check that candidate instances are either already immutable or can be made so; if fields are set after construction, migrate those to constructor arguments first.
  2. Remove any setters/mutators; any "change" becomes constructing a new instance with the updated field(s) and replacing the old reference wherever it is held.
  3. Implement equality (and hash, in languages that need it) based on field values rather than identity.
  4. Update call sites that relied on mutating in place to instead reassign the holding variable/field to a new instance; test after each call site or small batch.
  5. Remove any identity-based comparisons (`==`/reference equality checks) that assumed a single shared instance, replacing with value equality.
- **Inverse/companion:** Direct inverse of Change Value to Reference — the two refactorings undo each other, and choosing between them is a deliberate design decision based on whether shared mutable identity or independent value semantics is wanted for the type.
- **Fixes smells:** Not a clean match to any Chapter 3 smell — this refactoring is primarily about aliasing and identity semantics rather than a smell like duplication or naming. It can incidentally reduce Mutable Data if the resulting value objects are immutable, but that is a side effect, not its defining purpose.

### Change Value to Reference
Convert an object that is treated as an independent, copyable value into a single shared reference, so that all logical uses of "the same" conceptual entity point at one mutable instance.

- **Motivation:** When many parts of a system should be looking at the exact same logical entity (e.g. the one customer record for a given customer ID) but are instead each holding separate copies, updates made through one copy don't show up through another. A shared reference makes "same entity" mean "same object," at the cost of needing controlled, deliberate mutation.
- **Mechanics:**
  1. Decide on a single owning registry/repository/factory responsible for producing and looking up the canonical instance for a given identity (e.g. keyed by ID).
  2. Ensure that registry has one authoritative place to create a new instance, so duplicates aren't accidentally constructed elsewhere.
  3. Replace call sites that construct or copy their own instance with a lookup through the registry/factory; test after each replacement.
  4. Confirm the shared object's mutations are appropriately guarded (e.g. through explicit update methods) since multiple owners now observe the same state.
  5. Remove now-dead independent-copy construction paths once all call sites route through the shared lookup.
- **Inverse/companion:** Direct inverse of Change Reference to Value — the two refactorings undo each other, and the choice between them should be made deliberately per type rather than defaulted.
- **Fixes smells:** Not a clean match to any Chapter 3 smell — like its inverse, this is fundamentally about identity/aliasing semantics rather than duplication, naming, or structural smells. Introducing shared mutable references can, if overused, invite Global Data–style hazards, so apply narrowly and only where "same identity" genuinely needs to mean "same object."
