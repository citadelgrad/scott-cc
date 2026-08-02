---
name: ponytail-audit
description: "Use when the user says \"audit this codebase\", \"audit for over-engineering\"\
  , \"what can I delete from this repo\", or \"find bloat\". Whole-repo audit for\
  \ over-engineering \u2014 like ponytail-review but scans the entire codebase instead\
  \ of a diff, producing a ranked list of what to delete, simplify, or replace with\
  \ stdlib/native equivalents."
metadata:
  category: discipline
  triggers:
  - ponytail-pattern
  - code-review
  - architecture
---

## When to Use
- Auditing an entire codebase for over-engineering and bloat
- Finding what to delete, simplify, or replace with stdlib/native equivalents
- Running a repo-wide scan (vs. ponytail-review which operates on diffs)
- Ranking findings by biggest cut first

ponytail-review, repo-wide. Scan the whole tree instead of a diff. Rank
findings biggest cut first.

## Tags

Same as ponytail-review:

- `delete:` dead code, unused flexibility, speculative feature. Replacement: nothing.
- `stdlib:` hand-rolled thing the standard library ships. Name the function.
- `native:` dependency or code doing what the platform already does. Name the feature.
- `yagni:` abstraction with one implementation, config nobody sets, layer with one caller.
- `shrink:` same logic, fewer lines. Show the shorter form.

## Hunt

Deps the stdlib or platform already ships, single-implementation interfaces,
factories with one product, wrappers that only delegate, files exporting one
thing, dead flags and config, hand-rolled stdlib.

## Output

One line per finding, ranked: `<tag> <what to cut>. <replacement>. [path]`.
End with `net: -<N> lines, -<M> deps possible.` Nothing to cut: `Lean already. Ship.`

## Boundaries

Scope: over-engineering and complexity only. Correctness bugs, security holes,
and performance are explicitly out of scope. Route them to a normal review
pass. Lists findings, applies nothing. One-shot.
"stop ponytail-audit" or "normal mode" to revert.

## Limitations
- Use this skill only when the task clearly matches the scope described above.
- Lists findings only — does not apply fixes.
- Correctness, security, and performance are explicitly out of scope; route those to other lenses.
- One-shot scan; does not track changes over time.
- Stop and ask for clarification if the audit scope, codebase boundaries, or severity threshold is unclear.
