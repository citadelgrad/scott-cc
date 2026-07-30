---
name: refactoring-catalog
description: >-
  Use when you need the concrete mechanics for a named refactoring (e.g. "how do I do Extract
  Function safely", "what's the inverse of Inline Class"), when picking which refactoring resolves
  a smell found by code-smells, or when the user asks for a refactoring's steps, motivation, or
  inverse. Indexes all ~61 refactorings from Chapters 6-12 of Fowler's "Refactoring" (2nd ed.),
  each with motivation, small-step mechanics, its inverse/companion, and the code smell(s) it
  fixes. Not for identifying which smells are present in code (use code-smells) or for sequencing
  a multi-step cleanup across several smells (use refactoring-planner).
argument-hint: "[refactoring name, or a smell name to find refactorings that fix it]"
allowed-tools: Read, Grep
metadata:
  category: reference
---

# Refactoring Catalog (Fowler, Ch.6-12)

A reference index, not a tutorial. This catalog's chapter grouping and refactoring names are
Martin Fowler's, from *Refactoring: Improving the Design of Existing Code* (2nd ed.). The
motivation/mechanics/cross-reference text in each `references/` file is written fresh for this
skill from general refactoring knowledge — it is not reproduced from the book.

**Read references one at a time, just-in-time.** Each chapter file is self-contained; open only
the one containing the refactoring(s) you need right now, not the whole catalog at once.

## When to Use
- You know (or `code-smells` told you) which refactoring to apply, and need its actual mechanics
- Looking up a refactoring's inverse or companion move before deciding which direction to go
- Confirming which smell(s) a refactoring is a recognized fix for
- The user names a refactoring by name and asks "how do I do this" or "what does this do"

## Index

| Chapter | File | Refactorings |
|---|---|---|
| 6. A First Set of Refactorings | `references/first-set.md` | Extract Function, Inline Function, Extract Variable, Inline Variable, Change Function Declaration, Encapsulate Variable, Rename Variable, Introduce Parameter Object, Combine Functions into Class, Combine Functions into Transform, Split Phase |
| 7. Encapsulation | `references/encapsulation.md` | Encapsulate Record, Encapsulate Collection, Replace Primitive with Object, Replace Temp with Query, Extract Class, Inline Class, Hide Delegate, Remove Middle Man, Substitute Algorithm |
| 8. Moving Features | `references/moving-features.md` | Move Function, Move Field, Move Statements into Function, Move Statements to Callers, Replace Inline Code with Function Call, Slide Statements, Split Loop, Replace Loop with Pipeline, Remove Dead Code |
| 9. Organizing Data | `references/organizing-data.md` | Split Variable, Rename Field, Replace Derived Variable with Query, Change Reference to Value, Change Value to Reference |
| 10. Simplifying Conditional Logic | `references/conditional-logic.md` | Decompose Conditional, Consolidate Conditional Expression, Replace Nested Conditional with Guard Clauses, Replace Conditional with Polymorphism, Introduce Special Case, Introduce Assertion |
| 11. Refactoring APIs | `references/apis.md` | Separate Query from Modifier, Parameterize Function, Remove Flag Argument, Preserve Whole Object, Replace Parameter with Query, Replace Query with Parameter, Remove Setting Method, Replace Constructor with Factory Function, Replace Function with Command, Replace Command with Function |
| 12. Dealing with Inheritance | `references/inheritance.md` | Pull Up Method, Pull Up Field, Pull Up Constructor Body, Push Down Method, Push Down Field, Replace Type Code with Subclasses, Remove Subclass, Extract Superclass, Collapse Hierarchy, Replace Subclass with Delegate, Replace Superclass with Delegate |

Each entry in every chapter file follows the same shape: one-line description, **Motivation**,
**Mechanics** (small, individually-testable steps — never a step you can't verify before moving
to the next), **Inverse/companion**, and **Fixes smells** (cross-referenced by exact name to
`code-smells`).

## How to Use This

1. **Know the name already?** Grep the file list above for which chapter file has it, open just
   that file, jump to the `### <Name>` heading.
2. **Have a smell instead of a name?** `code-smells` already names candidate refactorings per
   smell — go straight to the chapter file(s) those candidates live in. (Don't re-derive the
   mapping here; it's already done there.)
3. **Deciding between a refactoring and its inverse?** Every entry names its inverse/companion
   explicitly — check both before picking a direction. Refactoring is reversible by design: if a
   move turns out to be wrong, its inverse gets you back.
4. **Applying it:** follow the Mechanics steps as written — in order, one at a time, running tests
   after each step. Skipping steps or batching several together is exactly the discipline Fowler's
   "small steps" principle exists to prevent; it's what turns a safe mechanical transformation
   back into risky manual surgery.

## Limitations
- Use this skill only when the task clearly matches the scope described above.
- This is a lookup reference, not an executor — it describes mechanics, it does not run them for
  you or edit code on your behalf.
- The chapter/name/order structure follows the book; the explanatory prose is independently
  authored and may not match the book's own wording or examples.
- Stop and ask for clarification if the target refactoring's name doesn't match anything indexed
  here — check for a naming variant before assuming it's missing.
