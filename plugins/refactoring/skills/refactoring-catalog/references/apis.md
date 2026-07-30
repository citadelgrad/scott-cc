# Chapter 11: Refactoring APIs

Cleaning up the contracts between callers and the functions/objects they call — parameter shape, side-effect visibility, and construction.

### Separate Query from Modifier
Split a function that both returns a value and produces a side effect into two functions: a pure query and a pure modifier.

- **Motivation:** Callers can't safely call a function purely for its return value if it might also mutate state; splitting lets the query be called anywhere, any number of times, with no risk, and makes the modifier's effect explicit at the call site.
- **Mechanics:**
  - Copy the function into a new query function; strip any side-effecting code from the copy so it only computes and returns the value.
  - In the original (now the modifier), replace the value computation with a call to the new query, and drop its return value.
  - At each call site, replace uses that only need the return value with a call to the query; replace uses that need the side effect with the modifier, adding a query call alongside it if the value is also needed there.
  - Test after migrating each call site.
  - Remove the return value from the modifier once no caller relies on it.
- **Inverse/companion:** No strict named inverse; undone informally by re-merging the two functions back together. Often a precursor step before other refactorings that need a clean, callable-anywhere query.
- **Fixes smells:** Primarily API hygiene — enforcing command-query separation — rather than a remedy for a specific named smell; loosely relates to Mysterious Name when a getter-sounding function hides a mutation.

### Parameterize Function
Combine several functions whose bodies are nearly identical except for one or more embedded literal values, by extracting the differing value into a parameter.

- **Motivation:** When near-duplicate functions differ only by a hardcoded value, a single parameterized function removes the duplication and gives one place to fix logic that would otherwise need to be changed in several spots.
- **Mechanics:**
  - Choose one of the near-duplicate functions to keep as the base.
  - Add a parameter to it representing the value that varies across the duplicates.
  - Replace each call to a duplicate function with a call to the kept function, passing the appropriate literal as the new argument.
  - Test after migrating each call site.
  - Delete the now-unused duplicate functions.
- **Inverse/companion:** No single named inverse; splitting the function back into separate variants per value is the informal reverse. Related to Replace Conditional with Polymorphism when the varying behavior is more than a simple literal.
- **Fixes smells:** Duplicated Code, Alternative Classes with Different Interfaces (near-identical functions differing only by an embedded literal).

### Remove Flag Argument
Replace a boolean or enum-like parameter that selects between two code paths with two separate, explicitly named functions.

- **Motivation:** A flag argument forces callers to know and pass the correct magic value, and hides which behavior actually executes behind a conditional inside the function; explicit functions make the choice visible and safe at the call site.
- **Mechanics:**
  - Create one explicit new function for each value the flag can take.
  - Implement each new function either by calling the original with the corresponding literal flag value, or by extracting the relevant branch's logic directly into it.
  - At each call site, determine which flag value is passed and replace the call with the matching explicit function.
  - Test after migrating each call site.
  - Once all callers are migrated, remove the flag parameter and its internal conditional from the original function (or delete it if fully replaced).
- **Inverse/companion:** No formally named inverse; combining the explicit variants back into one flagged function is the rough reverse, similar in spirit to Parameterize Function.
- **Fixes smells:** Long Parameter List, Alternative Classes with Different Interfaces (the flag effectively bolts two different interfaces into one function), Repeated Switches (when the same flag is checked via conditional in multiple places).

### Preserve Whole Object
Instead of extracting several individual values from an object and passing them separately, pass the whole object itself.

- **Motivation:** Pulling several fields out of an object to pass individually produces a parameter list that shifts whenever the object's shape changes, and obscures the fact that the values are related; passing the object keeps that relationship visible and the signature stable.
- **Mechanics:**
  - Add a new parameter to the target function for the whole object.
  - Inside the function, replace uses of the individual value parameters with reads from the object.
  - Update each call site to pass the whole object instead of the extracted fields.
  - Remove the now-unused individual parameters, testing after each call site is updated.
- **Inverse/companion:** No direct named inverse; pairs naturally with Replace Parameter with Query, which can shrink the parameter list further by having the function derive the object itself.
- **Fixes smells:** Long Parameter List, Data Clumps (the set of extracted fields traveling together is itself the clump this refactoring resolves).

### Replace Parameter with Query
Remove a parameter whose value the function can compute or look up itself, instead of requiring every caller to compute and pass it.

- **Motivation:** A parameter that callers can only supply by first calling another function pushes unnecessary work and coupling onto every caller; if the callee can derive the value itself, the signature shrinks and the derivation logic stops being duplicated across call sites.
- **Mechanics:**
  - At call sites, use Extract Variable to isolate the expression that currently computes the parameter's value, if it isn't already isolated.
  - Inside the target function, replace references to the parameter with a call to the query that derives the same value.
  - Remove the parameter from the function's declaration and from every call site.
  - Test after each call site is updated.
- **Inverse/companion:** Direct inverse of Replace Query with Parameter.
- **Fixes smells:** Long Parameter List; avoid when it would introduce unwanted coupling to Global Data or context the function shouldn't know about — that situation calls for Replace Query with Parameter instead.

### Replace Query with Parameter
Remove a function's internal reference to global or otherwise hard-to-control state by turning that value into a parameter the caller must supply.

- **Motivation:** When a function reaches into global or ambient data to compute a value, it becomes hard to test and hard to reuse in a different context; moving that value to a parameter makes the dependency explicit and puts the caller in control of it.
- **Mechanics:**
  - At each call site, use Extract Variable to isolate the expression that will become the new argument, if not already isolated.
  - Add a new parameter to the target function for the value.
  - Replace the internal query or global reference inside the function with the new parameter.
  - Update every call site to pass the appropriate value, testing after each.
  - Remove the internal query if nothing else still depends on it.
- **Inverse/companion:** Direct inverse of Replace Parameter with Query.
- **Fixes smells:** Global Data (removes a function's hidden dependence on it), Divergent Change (a function that has to change whenever the external data source it queries changes).

### Remove Setting Method
Eliminate a setter for a field that is truly only ever set once, typically at construction, and never varies afterward.

- **Motivation:** An available setter implies a field is meant to change over the object's lifetime; if it is in fact only ever set once, removing the setter closes off unwanted mutation and makes the field's real immutability explicit in the API.
- **Mechanics:**
  - Confirm the field is only ever set from a constructor or equivalent initialization path, never reassigned afterward.
  - Change the constructor to accept and set the field directly, if it doesn't already.
  - Find and migrate every external caller of the setter to pass the value through construction instead.
  - Remove the setter method.
  - Test after each caller is migrated.
- **Inverse/companion:** No direct named inverse; reintroducing a setter is simply adding back mutability, not a named refactoring. Often paired with Change Function Declaration when adjusting the constructor's parameters, or Preserve Whole Object if several such fields exist.
- **Fixes smells:** Mutable Data, Long Parameter List (when consolidating removed setters pushes the constructor toward a parameter object).

### Replace Constructor with Factory Function
Replace direct calls to a constructor with calls to a factory function that returns the object.

- **Motivation:** Constructors in many languages are constrained — fixed name, cannot return a subtype or a cached/pooled instance, limited control over how construction proceeds; a factory function is free to choose the concrete implementation, reuse instances, or run more elaborate setup logic.
- **Mechanics:**
  - Create the factory function; have its body simply delegate to the existing constructor to start.
  - Find each call site that invokes the constructor directly and replace it with a call to the factory function.
  - Test after migrating each call site.
  - Once all external callers use the factory, restrict the constructor's visibility if the language allows, forcing future construction through the factory.
  - Move any construction logic that doesn't belong in the constructor itself (environment-dependent setup, subtype selection, caching) into the factory function.
- **Inverse/companion:** No direct named inverse in this chapter; informally undone by inlining the factory back to direct construction.
- **Fixes smells:** Primarily construction/API hygiene rather than a remedy for a specific named smell, though it can relieve pressure on a Large Class whose constructor has accumulated conditional logic for selecting between subtypes.

### Replace Function with Command
Turn a function into its own standalone object (a command), moving the function's logic into a method on that object and promoting its parameters and locals to fields.

- **Motivation:** A complex function benefits from the extra room an object provides — parameters and intermediate values become fields reachable by private helper methods, and the function gains space to be decomposed without cluttering its own signature; objects also make behaviors like deferred execution, undo, or logging easier to add later.
- **Mechanics:**
  - Create an empty class named for the function's purpose.
  - Give it a constructor that takes the function's original parameters and stores them as fields.
  - Move the function's body into a method on the new class (commonly named execute or run), replacing references to the old parameters with references to the fields.
  - Update call sites to construct the command object and invoke its execution method.
  - Test after the migration.
  - As a follow-on, extract pieces of the now-roomier execution method into private helper methods on the command, since they can freely access the fields.
- **Inverse/companion:** Direct inverse of Replace Command with Function.
- **Fixes smells:** Long Function (gives a large function room to be broken into private helper methods on an object), Long Parameter List (parameters become fields set once at construction).

### Replace Command with Function
Collapse a command object back into a plain function when the extra machinery of an object is no longer earning its keep.

- **Motivation:** If a command class was created for a function that turned out simpler than expected (or has since been simplified), the constructor, fields, and execution method around it are needless ceremony for what is now a straightforward function call.
- **Mechanics:**
  - Confirm the command's single execution method doesn't need the object's extra facilities — no other methods, no retained state across calls, no deferred or repeated invocation.
  - Use Inline Function and Inline Variable as needed to fold any helper methods and fields back into the body of the execution method.
  - Turn the command's constructor parameters into the plain function's parameters.
  - Replace each call site that constructs the command and calls its execute method with a single direct function call.
  - Remove the command class once all callers are migrated, testing after each step.
- **Inverse/companion:** Direct inverse of Replace Function with Command.
- **Fixes smells:** Speculative Generality (an object built for flexibility or complexity that never materialized), Middle Man (the command class adds a layer that does little beyond forwarding to its own execute method).
