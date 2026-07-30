# Chapter 12: Dealing with Inheritance

Moving members up and down a class hierarchy, and — when inheritance itself is the wrong tool — replacing it with delegation or collapsing it away entirely.

### Pull Up Method
Move a method with identical (or near-identical) implementations in several subclasses up into their shared superclass.

- **Motivation:** Duplicated logic in sibling subclasses has to be found and fixed in every copy; consolidating it in the superclass gives a single place to read and change the behavior.
- **Mechanics:**
  - Compare candidate methods in the sibling subclasses to confirm they are truly equivalent (or make them so first, e.g. via Extract Function/Change Function Declaration for minor differences).
  - If the signatures don't yet match, adjust them so they do.
  - Create a new method in the superclass; copy one subclass's implementation into it.
  - Delete the method from each subclass in turn, testing after each removal.
  - Test the full suite once all duplicates are removed.
- **Inverse/companion:** Push Down Method — its direct inverse.
- **Fixes smells:** Duplicated Code (the classic case: near-identical methods across sibling subclasses).

### Pull Up Field
Move a field declared separately in several subclasses up into their shared superclass.

- **Motivation:** The same field re-declared in multiple subclasses is duplication in the data model, not just the code; consolidating it removes redundant declarations and clears the way for pulling up behavior that uses it.
- **Mechanics:**
  - Verify the field is used similarly across the candidate subclasses.
  - Declare the field in the superclass.
  - Remove the field's declaration from each subclass, one at a time, testing after each.
- **Inverse/companion:** Push Down Field — its direct inverse.
- **Fixes smells:** Duplicated Code (redundant field declarations across sibling subclasses).

### Pull Up Constructor Body
Move common initialization logic from several subclasses' constructors into the shared superclass constructor, invoked via a call to it.

- **Motivation:** Constructors resist ordinary Pull Up Method treatment because of language rules around superclass construction; this refactoring gives duplicated constructor logic the same treatment via an explicit superclass-constructor call.
- **Mechanics:**
  - Define (or locate) a superclass constructor that takes the parameters the common initialization needs.
  - In each subclass constructor, move the shared initialization code so it happens via an explicit call to the superclass constructor, passing the required parameters.
  - Remove the now-duplicated initialization statements from each subclass constructor.
  - Test after adjusting each subclass constructor.
- **Inverse/companion:** Push Down Method (conceptually the reverse direction for constructor-specific logic, since Push Down Constructor Body isn't separately named); closely related to Pull Up Method / Extract Function as a preparatory step.
- **Fixes smells:** Duplicated Code (repeated initialization logic across sibling constructors).

### Push Down Method
Move a method from a superclass down into only the subclass(es) that actually need it.

- **Motivation:** A method relevant to only some subclasses clutters the superclass interface for the rest, and misleads readers into thinking it applies universally.
- **Mechanics:**
  - Confirm the method is genuinely used by only a subset of subclasses (check all call sites and any overrides).
  - Copy the method down into each subclass that needs it.
  - Remove the method from the superclass.
  - Test; if a subclass that shouldn't have the method is somehow calling it, that call site needs to be dealt with first.
- **Inverse/companion:** Pull Up Method — its direct inverse.
- **Fixes smells:** Refused Bequest (a subclass that ignores or overrides away an inherited method is a sign it never belonged at that level).

### Push Down Field
Move a field from a superclass down into only the subclass(es) that actually use it.

- **Motivation:** A field only meaningful to some subclasses is dead weight (and a source of confusion) in the rest; narrowing its scope to where it's used clarifies the model.
- **Mechanics:**
  - Confirm which subclasses actually use the field.
  - Declare the field in each subclass that needs it.
  - Remove the field from the superclass.
  - Test after the move.
- **Inverse/companion:** Pull Up Field — its direct inverse.
- **Fixes smells:** Refused Bequest (a subclass that doesn't use an inherited field signals the field was placed too high).

### Replace Type Code with Subclasses
Replace a field holding a type code (a value that distinguishes categories of an object) with subclasses, one per category, so behavior that varies by type is expressed through polymorphism instead of conditionals.

- **Motivation:** A type-code field paired with conditional logic scattered around the codebase couples every use site to the same set of `if`/`switch` branches; subclasses let each variant own its behavior and let the language's dispatch mechanism replace the conditionals.
- **Mechanics:**
  - Encapsulate the type-code field if it isn't already (Encapsulate Variable/Field).
  - Create a subclass for each value the type code takes.
  - Use Replace Constructor with Factory Function so callers get the right subclass without directly naming it.
  - For each conditional that branches on the type code, use Replace Conditional with Polymorphism to move the corresponding logic into an overriding method on each subclass.
  - Remove the type-code field once all its uses have been replaced by subclass-specific behavior; test after each step.
- **Inverse/companion:** Remove Subclass — roughly its inverse (collapsing subclasses back into a type-code field when the hierarchy has stopped earning its keep).
- **Fixes smells:** Repeated Switches (conditionals on the same type code recurring in multiple places), Primitive Obsession (a raw code/string/enum standing in for what should be a proper type).

### Remove Subclass
Replace a subclass that no longer earns its keep with a field on the (now-sole) superclass holding an equivalent type code.

- **Motivation:** A subclass hierarchy that never grew meaningful variation, or whose variants shrank back down over time, is unnecessary indirection; collapsing it back to data simplifies the model.
- **Mechanics:**
  - Create (or reuse) a type-code field on the superclass to represent what the subclass used to signify.
  - Use Replace Constructor with Factory Function at creation sites so they stop referencing the subclass directly and instead set the type-code field.
  - For each method the subclass overrides, fold its logic into the superclass method as a conditional on the new type-code field.
  - Delete the subclass once nothing references it, testing after each step.
- **Inverse/companion:** Replace Type Code with Subclasses — roughly its inverse.
- **Fixes smells:** Speculative Generality (a subclass hierarchy built for variation that never materialized beyond a couple of trivial cases), Lazy Element (a subclass contributing little beyond its name).

### Extract Superclass
Create a common superclass for two or more classes that share behavior or data, and move the shared elements up into it.

- **Motivation:** Similar classes with overlapping fields and methods duplicate that overlap; a shared superclass consolidates the commonality in one place and leaves each subclass to hold only what's distinct about it.
- **Mechanics:**
  - Define an empty superclass; make the related classes extend/inherit from it.
  - Use Pull Up Field, Pull Up Method, and Pull Up Constructor Body to migrate shared elements into the superclass one at a time.
  - Test after each individual pull-up.
  - Once migration settles, review whether the remaining subclass-specific members still belong there or reveal a further extraction.
- **Inverse/companion:** Collapse Hierarchy (undoes an extraction that turned out not to be worth the added structure); built entirely from Pull Up Method/Field/Constructor Body.
- **Fixes smells:** Duplicated Code (overlapping fields/methods across otherwise-unrelated classes), Alternative Classes with Different Interfaces (a precursor step is often aligning interfaces before extracting the shared superclass).

### Collapse Hierarchy
Merge a superclass and a subclass together when they're no longer meaningfully different, removing a level of the hierarchy.

- **Motivation:** A hierarchy level that has stopped pulling its weight — because the subclass and superclass drifted apart in responsibility from what originally justified the split, or the distinction between them faded — adds indirection without payoff.
- **Mechanics:**
  - Pick which of the two (superclass or subclass) will absorb the other.
  - Use Pull Up Field/Method or Push Down Field/Method to move all members into the surviving class.
  - Update all references to the removed class to point at the survivor.
  - Delete the now-empty class; test after the merge.
- **Inverse/companion:** Extract Superclass (the reverse move: splitting one class's responsibilities back out into a hierarchy).
- **Fixes smells:** Lazy Element (a class contributing too little to justify its own place in the hierarchy), Speculative Generality (structure built ahead of need that never paid off).

### Replace Subclass with Delegate
Replace a subclass with a separate delegate object that the (formerly-superclass, now standalone) class holds a reference to, moving subclass-specific behavior into the delegate.

- **Motivation:** Inheritance is single-purpose and fixes the relationship at construction time, whereas delegation can be swapped at runtime and composed with other delegations; when a subclass is really adding one narrow variation, or when inheritance is being (ab)used for something other than a clean is-a relationship, delegation is more flexible and avoids entangling the subclass with unrelated inherited machinery.
- **Mechanics:**
  - Create an empty delegate class; give the client-facing class a field referencing an instance of it.
  - For each subclass-specific method or field, move it into the delegate using Move Function/Move Field, having the host class forward to the delegate.
  - Redirect construction so the right kind of delegate is created/assigned instead of instantiating the subclass.
  - Remove the subclass once all its behavior has migrated and nothing constructs it directly; test after each move.
- **Inverse/companion:** No direct inverse in this chapter (re-introducing the subclass would mean reversing the same steps); pairs with Replace Superclass with Delegate as the two delegation-based alternatives to inheritance.
- **Fixes smells:** Refused Bequest (a subclass that only wants part of its parent's interface and overrides away or ignores the rest is the textbook signal to swap that inheritance link for delegation).

### Replace Superclass with Delegate
Replace an inheritance relationship with delegation when a subclass only needs part of its superclass's interface, rather than a genuine is-a relationship.

- **Motivation:** Inheriting from a class to reuse a fraction of its behavior drags along the rest of its interface, letting clients call methods that don't make sense for the subclass, or forcing awkward overrides to hide them; delegation lets the class expose only the operations that fit, calling through to the delegate for the reused logic.
- **Mechanics:**
  - Create a field in the (former) subclass that holds an instance of the (former) superclass as a delegate, instead of inheriting from it.
  - For each superclass method the class actually uses, add a forwarding method that delegates the call to the field.
  - Update the class to no longer inherit from the superclass.
  - Redirect any remaining direct references (including polymorphic ones) to go through the delegate/forwarding methods; test after each change.
  - Remove forwarding methods that turn out to be unused.
- **Inverse/companion:** No direct inverse in this chapter; pairs with Replace Subclass with Delegate as the two delegation-based alternatives to inheritance.
- **Fixes smells:** Refused Bequest (a subclass using only a slice of its superclass's interface, overriding or blocking the rest, is the specific signal for this refactoring).
