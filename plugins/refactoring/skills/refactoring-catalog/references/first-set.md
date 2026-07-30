# Chapter 6: A First Set of Refactorings

The foundational, most-used refactorings — extracting and naming things, changing signatures safely, and the two "combine" moves that seed later structural refactorings.

### Extract Function
Take a fragment of code and turn it into its own function, named for what it does rather than how it does it.

- **Motivation:** Separates intention from implementation; short, well-named functions document themselves and are easier to reuse, override, and test in isolation.
- **Mechanics:**
  - Create a new function named for the fragment's intent (the "what," not the "how").
  - Copy the extracted code into the new function.
  - Scan for variables the fragment uses that are local to the source; pass them in as parameters (or return them if the fragment assigns to them).
  - Replace the original fragment with a call to the new function.
  - Test.
- **Inverse/companion:** Inline Function.
- **Fixes smells:** Long Function, Duplicated Code, Comments (a comment explaining a block often signals the block should be its own named function).

### Inline Function
Replace a function call with the function's body when the function's name adds no more clarity than its implementation.

- **Motivation:** Indirection is only valuable when it pays for itself; when a function body is as clear as its name, or when too many tiny functions obscure control flow, collapsing them back helps readability.
- **Mechanics:**
  - Check the function isn't polymorphic (overridden or overriding) — inlining those is unsafe.
  - Find all call sites.
  - Replace each call site with the function's body, adjusting for parameters passed at each call.
  - Test after each replacement.
  - Remove the function definition once all callers are inlined.
- **Inverse/companion:** Extract Function.
- **Fixes smells:** Lazy Element, Middle Man (an indirection layer that no longer earns its keep).

### Extract Variable
Give a name to an expression (or part of one) by assigning it to a variable, then use that variable in place of the expression.

- **Motivation:** Complex or repeated expressions are hard to scan and easy to get wrong when duplicated; naming a sub-expression documents its meaning and gives a single place to fix or reuse it.
- **Mechanics:**
  - Confirm the expression has no side effects that would change behavior if evaluated once and cached in a variable.
  - Declare a new immutable variable; set it to a copy of the expression you want to name.
  - Replace the original expression with the new variable.
  - Test.
  - Repeat for other occurrences of the same expression if applicable.
- **Inverse/companion:** Inline Variable.
- **Fixes smells:** Comments (a comment explaining an expression is a cue to name it instead), Duplicated Code.

### Inline Variable
Replace references to a variable with the expression it was set to, then remove the variable.

- **Motivation:** When the variable's name adds nothing beyond the expression itself, and the expression is short and clear enough to read directly, the extra name is just noise; also useful as a step before other refactorings (e.g., before Inline Function or Extract Function).
- **Mechanics:**
  - Confirm the right-hand side expression is free of side effects (or that it's evaluated exactly once either way).
  - Find all references to the variable.
  - Replace each reference with the expression.
  - Test after each replacement.
  - Remove the variable declaration.
- **Inverse/companion:** Extract Variable.
- **Fixes smells:** Middle Man (a named alias that adds an unnecessary layer of indirection); rarely needed on its own — more often a supporting move for other refactorings.

### Change Function Declaration
Modify a function's name and/or its parameter list to better communicate its purpose.

- **Motivation:** A function's name and signature are the primary interface contract for its callers; a poor name or an awkward parameter list forces callers (and readers) to work harder than they should.
- **Mechanics:**
  - For a simple rename with few callers: change the declaration and all call sites together, then test.
  - For riskier or wider-reaching changes, use the migration approach: keep the old declaration in place but have it delegate to a new one; migrate callers to the new declaration one at a time, testing after each; remove the old declaration once all callers are migrated.
  - When adding a parameter, give it a sensible default or derive it inside the function first, then migrate call sites incrementally.
  - Test after every incremental step, not just at the end.
- **Inverse/companion:** None distinct — it is its own inverse (renaming back, or reverting a parameter change, is the same refactoring applied in reverse); pairs naturally with Rename Variable and Introduce Parameter Object.
- **Fixes smells:** Mysterious Name, Long Parameter List.

### Encapsulate Variable
Wrap access to a variable (especially widely shared or mutable data) behind a getter/setter function pair, and route all access through them.

- **Motivation:** Data that's referenced or updated from many places is hard to change safely; funneling access through functions creates a single point of control for validation, logging, change-tracking, or a later change in storage/representation.
- **Mechanics:**
  - Create getter and setter functions that wrap access to the variable.
  - Find all references to the variable and replace reads with the getter and writes with the setter.
  - Restrict the variable's visibility/scope as much as the language allows.
  - Test after each batch of replacements.
  - If the data is a structure/record, consider whether callers mutate its internals directly (encapsulating the reference alone isn't enough if its contents remain freely mutable — encapsulate the fields too, or return copies).
- **Inverse/companion:** None strict; conceptually pairs with Encapsulate Collection (a related, more specialized move not in this chapter's list) and often precedes Rename Variable or Split Variable.
- **Fixes smells:** Global Data, Mutable Data.

### Rename Variable
Change a variable's name to better reveal its purpose.

- **Motivation:** Variables are used and re-read constantly; a name that clearly signals intent pays for itself many times over, especially for variables with wide scope where the cost of a bad name compounds.
- **Mechanics:**
  - For a variable with wide scope, consider Encapsulate Variable first so all access goes through one place.
  - Find every reference to the variable.
  - Rename each reference consistently.
  - Test after the change (or incrementally, if scope is wide enough to make a single pass risky).
- **Inverse/companion:** None distinct — it is its own inverse; closely related to Change Function Declaration (renaming parameters).
- **Fixes smells:** Mysterious Name.

### Introduce Parameter Object
Replace a group of parameters that habitually travel together with a single object that holds them all.

- **Motivation:** Groups of data that repeatedly appear together as parameters are a sign they belong together conceptually; bundling them shortens signatures, clarifies relationships, and gives the group a place to grow shared behavior later.
- **Mechanics:**
  - If no suitable structure exists yet, create one to hold the group of data.
  - Use Change Function Declaration to add the new structure as a parameter to the target function.
  - Adjust call sites to pass the new structure, initially still passing the old individual parameters through unused or ignored.
  - Update the function body to reference fields on the new structure instead of the individual parameters.
  - Remove the now-unused individual parameters from the declaration, testing after each removal.
- **Inverse/companion:** None strict inverse; conceptually the reverse move is decomposing a parameter object back into individual parameters (rarely named separately since it's just repeated field access + Change Function Declaration).
- **Fixes smells:** Data Clumps, Long Parameter List, Primitive Obsession.

### Combine Functions into Class
Group a set of functions (and the data they operate on) into a class, exposing the functions as methods that share that data.

- **Motivation:** When several functions repeatedly operate on the same underlying data, packaging them together as a class makes that relationship explicit, shortens each function's parameter list (data becomes shared instance state), and gives client code a single, coherent object to work with.
- **Mechanics:**
  - Apply Encapsulate Record (or equivalent) to the shared data record used by the functions, if not already encapsulated.
  - Choose one function; move it into the new class using Move Function, adjusting it to use the class's fields directly instead of parameters.
  - Move each remaining related function into the class the same way, one at a time, testing after each.
  - Look for logic in client code that could instead be expressed as a call to one of the new methods; replace it with Extract Function plus Move Function as needed.
- **Inverse/companion:** Combine Functions into Transform (an alternative structural response to the same underlying situation — class-with-shared-state vs. derived-fields-on-a-record); companion moves are Move Function and Encapsulate Record.
- **Fixes smells:** This is more of a follow-on structural move than a direct smell-fix; it's typically applied after noticing Feature Envy or Data Clumps across a group of related functions, and it helps guard against Shotgun Surgery for future changes to that group.

### Combine Functions into Transform
Gather a set of derived values, computed from the same source data, into a single transform step that produces an enriched copy of that data.

- **Motivation:** Useful for read-heavy, largely-immutable source data (e.g., data flowing through a pipeline) where multiple derived fields are recalculated in various places; centralizing the derivation avoids repeating (and risking divergence in) that logic wherever the data is used.
- **Mechanics:**
  - Create a transform function that takes the source data and returns a copy of it (never mutate the original).
  - Pick one piece of derived data computed from the source; move that calculation into the transform, adding it as a new field on the output copy.
  - Replace call sites that compute that value with a read of the new field.
  - Repeat for each remaining derived value, one at a time, testing after each.
- **Inverse/companion:** Combine Functions into Class (the mutable/object-oriented alternative for the same problem); prefer Transform when the data is immutable or read-only, Class when the data legitimately changes over time.
- **Fixes smells:** Duplicated Code (repeated derivation logic scattered across call sites); also a follow-on structural move rather than a direct fix for a single specific smell.

### Split Phase
Divide a block of code that handles two or more distinct concerns into separate sequential phases, passing an intermediate result between them.

- **Motivation:** Code that does several different things in a single pass (e.g., parsing input, then calculating with it) is harder to understand and modify than the same logic separated into clear, sequential stages, each of which can be understood, tested, and changed on its own.
- **Mechanics:**
  - Extract the second phase's logic into its own function first, using Extract Function, so it operates only on data structured the way it needs.
  - Introduce an intermediate data structure that will carry the output of the first phase into the second.
  - Extract the first phase's logic into its own function, having it populate the intermediate structure and pass it to the second phase.
  - Test after each extraction.
- **Inverse/companion:** Inline Function (to collapse the phases back if the separation turns out not to be worth it); closely paired with Extract Function and Move Function.
- **Fixes smells:** Divergent Change (splitting phases so each one changes for one reason only), Long Function.
