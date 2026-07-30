# refactoring

A three-skill suite for finding, fixing, and sequencing fixes for code smells, structured around
Martin Fowler's *Refactoring: Improving the Design of Existing Code* (2nd ed., 2018).

| Skill | Role |
|---|---|
| `code-smells` | Diagnostic. Scans code against all 24 named smells from Chapter 3 and points to the refactoring(s) that fix each one. |
| `refactoring-catalog` | Reference. Indexes all ~61 refactorings from Chapters 6-12 — motivation, small-step mechanics, inverse/companion, and which smell(s) each one resolves. |
| `refactoring-planner` | Orchestrator. Turns a pile of detected smells into one prioritized, test-checkpointed sequence of refactoring steps. |

Typical flow: `code-smells` finds what's wrong → `refactoring-planner` decides what order to fix
it in → each step's mechanics come from `refactoring-catalog`.

## Attribution

This plugin's chapter structure, smell names, and refactoring names (Chapter 3's 24 smells;
Chapters 6-12's ~61 refactorings) are taken from the table of contents of Fowler's *Refactoring*
(2nd ed.) — used here as a naming and organizational scheme, the same way a book index is used to
navigate a library, not reproduced as a copy of the book.

**No prose, code examples, or explanatory text from the book itself was available while writing
this plugin** — only chapter/section titles and page numbers (from photographs of the table of
contents). Every description, motivation, mechanics list, smell-to-refactoring cross-reference,
and prioritization heuristic in this plugin's `SKILL.md` and `references/*.md` files is original
writing, drawn from general, widely-published software engineering knowledge of these
industry-standard techniques (the vocabulary — "Extract Function," "Feature Envy," and so on — is
common across many books, talks, and tools, not exclusive to Fowler's text). None of it is a
verbatim or paraphrased reproduction of the book's own text or examples.

Readers who want the book's own explanations, worked examples, and language-specific code samples
should read *Refactoring: Improving the Design of Existing Code*, 2nd edition, by Martin Fowler
(Addison-Wesley, 2018) directly — this plugin is a working reference and planning tool, not a
substitute for it.
