# Chapter 7: Encapsulation

Drawing and tightening boundaries around data and behavior — turning primitives and records into real objects, and controlling how much of a collaborator's structure leaks through.

### Encapsulate Record
Wrap a raw record/struct (or plain hash/dict-of-fields) behind an object so field access goes through methods instead of direct field references.

- **Motivation:** Direct field access spreads knowledge of the record's shape throughout the codebase; wrapping it lets you change the internal representation, add validation, or add computed fields without touching every call site.
- **Mechanics:**
  1. Encapsulate the variable holding the record itself first (if it isn't already) so all reads/writes go through a single accessor.
  2. Create a class wrapping the record; give it a getter that returns the raw record, and have the accessor return an instance of this class instead.
  3. For each field, add a getter/setter pair to the class; run tests after each field.
  4. Redirect callers one at a time from raw field access to the new getters/setters, testing after each change.
  5. Once all access is through the class, change the internal storage as needed (rename fields, split/merge fields, switch representation) since only the class itself touches the raw shape.
- **Inverse/companion:** Pairs naturally with Encapsulate Variable (from Ch. 6) as a prerequisite step; conceptually mirrors Extract Class when the wrapped record grows real behavior.
- **Fixes smells:** Data Class, Primitive Obsession, Divergent Change, Shotgun Surgery.

### Encapsulate Collection
Hide a collection field behind an interface that returns read-only views (or a defensive copy) and provides explicit add/remove methods, rather than exposing the raw collection for arbitrary mutation.

- **Motivation:** A raw getter that returns the live collection lets any caller add/remove elements behind the owning object's back, silently breaking invariants the owner thinks it controls.
- **Mechanics:**
  1. Add explicit `add`/`remove` methods to the owning class that operate on the underlying collection.
  2. Find every place that mutates the collection through the getter (e.g. `obj.getItems().add(x)`) and redirect it to call `obj.addItem(x)` instead; test after each site.
  3. Change the getter to return a read-only view, an unmodifiable wrapper, or a copy of the collection, not the live reference.
  4. Run tests to confirm no caller still depends on mutating through the getter.
- **Inverse/companion:** A specialization of Encapsulate Record applied specifically to collection-typed fields; often followed by Remove Middle Man if the add/remove methods end up just forwarding trivially.
- **Fixes smells:** Mutable Data, Data Class, Duplicated Code (validation logic scattered at every mutation site collapses into the owning class).

### Replace Primitive with Object
Turn a primitive value (a string, number, etc.) that carries extra meaning or behavior into its own small object.

- **Motivation:** Primitives are dumb — once a value needs validation, formatting, comparison logic, or grows related behavior, keeping it as a bare `int`/`string` scatters that logic wherever the value is used.
- **Mechanics:**
  1. Apply Encapsulate Variable on the field/parameter holding the primitive, if not already encapsulated.
  2. Create a simple value class wrapping the primitive; give it a way to retrieve the raw value.
  3. Change the field's declared type to the new class, updating the constructor to wrap the value; run tests.
  4. Add behavior to the new class incrementally — one method extracted from a call site at a time — testing after each move.
  5. Consider making the new class immutable and adding equality semantics if the value is meant to be compared.
- **Inverse/companion:** No formal inverse; conceptually the opposite would be inlining the object back to a raw value, which is just Inline Class applied to a trivial wrapper.
- **Fixes smells:** Primitive Obsession, Duplicated Code, Data Clumps, Long Parameter List (once several related primitives combine into one object).

### Replace Temp with Query
Replace a local variable that holds the result of an expression with a method (query) that recomputes it, then use the method call wherever the variable was used.

- **Motivation:** Extracting the expression into a named method makes the computation available to other methods without parameter-passing, and is a common enabling step before Extract Function on surrounding code.
- **Mechanics:**
  1. Confirm the variable is calculated once and not reassigned in ways that change its meaning (if it is reassigned, consider Split Variable first).
  2. Extract the assignment's right-hand expression into its own method; make it a pure query with no side effects.
  3. Replace the one reference to the temp with a call to the new method; run tests.
  4. Remove the now-unused temp declaration; run tests again.
- **Inverse/companion:** Enabling step that often precedes Extract Function; the reverse move (turning a query back into a cached temp) is effectively Extract Variable / manual memoization, used only when performance requires it.
- **Fixes smells:** Long Function, Duplicated Code, Feature Envy (once the query moves to the object whose data it uses).

### Extract Class
Split a class that is doing the work of two into two classes, moving the relevant fields and methods to the new class.

- **Motivation:** A class that has grown multiple responsibilities, or a clump of fields/methods that always change together and only sometimes relate to the rest of the class, should be pulled apart so each class has one clear job.
- **Mechanics:**
  1. Decide how to split the class's responsibilities; create a new empty class for the split-off responsibility.
  2. Establish a link from the old class to the new one (or vice versa, whichever is more natural).
  3. Move one field at a time to the new class using Move Field, testing after each move.
  4. Move one method at a time to the new class using Move Function, starting with lower-level methods, testing after each.
  5. Review the resulting interfaces of both classes; rename methods/fields for clarity now that responsibilities are separated.
  6. Decide whether to expose the new class directly or hide it behind the original (Hide Delegate).
- **Inverse/companion:** Inline Class (direct opposite — merges a class back into another).
- **Fixes smells:** Large Class, Divergent Change, Data Clumps, Temporary Field (splitting off fields that are only sometimes used), Primitive Obsession (when the extracted class replaces a cluster of primitives).

### Inline Class
Merge a class into another class when it no longer justifies its own existence, moving all its fields and methods into the absorbing class and removing it.

- **Motivation:** A class that used to earn its keep has been refactored down until it does almost nothing, or two classes' responsibilities have become so entangled that keeping them separate only adds indirection without benefit.
- **Mechanics:**
  1. Declare public methods on the target (absorbing) class that delegate to the class being inlined, for every method callers use.
  2. Redirect all callers to use the target class's delegating methods instead of the source class directly; test after each redirect.
  3. Move fields and methods from the source class into the target class one at a time, using Move Function/Move Field, testing after each move.
  4. Once the source class is empty, remove it.
- **Inverse/companion:** Extract Class (direct opposite — splits one class into two).
- **Fixes smells:** Lazy Element, Speculative Generality (an over-engineered class that never grew the responsibilities it was designed for), Middle Man (if the class being inlined mostly just delegated).

### Hide Delegate
Add a method on a class that forwards to a method on one of its fields (its "delegate"), so callers talk only to the class itself and never see the delegate object.

- **Motivation:** When a client calls `object.getDelegate().someMethod()`, the client is coupled to the delegate's interface too, not just the object's; hiding the delegate keeps that structural knowledge inside the object and shields callers from changes to how the object collaborates internally.
- **Mechanics:**
  1. For each method called on the delegate, create a forwarding method on the server object with the same behavior.
  2. Redirect each client that calls through the delegate to call the new forwarding method on the server instead; test after each redirect.
  3. Once no client accesses the delegate directly, remove (or make private) the accessor that exposed the delegate.
- **Inverse/companion:** Remove Middle Man (direct opposite — undoes this when the forwarding methods pile up and the server becomes a pure pass-through).
- **Fixes smells:** Message Chains (this is the standard fix), Insider Trading (reduces how much internal structure is exposed across the boundary).

### Remove Middle Man
Let clients call a delegate object directly instead of going through forwarding methods on a server object, removing methods that do nothing but pass calls through.

- **Motivation:** Too much hiding of delegates turns the server class into a Middle Man whose interface is mostly forwarding boilerplate that adds indirection without adding value; it's cheaper to expose the delegate and let clients call it directly.
- **Mechanics:**
  1. Add an accessor on the server that returns the delegate object.
  2. For each forwarding method, redirect its callers to go through the accessor and call the delegate directly instead; test after each redirect.
  3. Remove the now-unused forwarding method from the server; test.
  4. Stop once the remaining forwarding methods that do carry real logic (validation, translation, etc.) are left in place — not every delegate call needs removing.
- **Inverse/companion:** Hide Delegate (direct opposite — this is the standard fix when Hide Delegate has been overapplied and produced a Middle Man).
- **Fixes smells:** Middle Man (this is the standard fix), Lazy Element.

### Substitute Algorithm
Replace the body of a method with a clearer or different algorithm that produces the same result.

- **Motivation:** Sometimes the cleanest way to simplify a confusing or inefficient method isn't incremental extraction — it's recognizing a simpler, better-understood way to solve the same problem and swapping the implementation wholesale.
- **Mechanics:**
  1. Make sure the method is well covered by tests before touching it, since this is a wholesale replacement, not a step-by-step transformation.
  2. Prepare the replacement algorithm as a separate, self-contained unit.
  3. Substitute the old algorithm's body with the new one, keeping the method's signature/interface unchanged.
  4. Run tests; if they fail, compare behavior on the failing case directly against the old algorithm to find the discrepancy rather than debugging the new algorithm from scratch.
  5. If the new algorithm is large, break the substitution into smaller comparable pieces to isolate failures faster.
- **Inverse/companion:** No formal inverse; often follows a long series of smaller refactorings once it becomes clear the whole method should just be rewritten. Complements Alternative Classes with Different Interfaces at the class level.
- **Fixes smells:** Alternative Classes with Different Interfaces (when unifying two implementations of the same idea), Comments (replaces a comment-heavy explanation of a convoluted algorithm with a self-evidently simpler one), Loops (when the replacement uses pipeline operations instead).
