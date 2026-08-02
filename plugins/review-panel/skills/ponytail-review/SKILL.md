---
name: ponytail-review
description: "Use when the user says \"review for over-engineering\", \"what can we\
  \ delete\", \"is this over-engineered\", or \"simplify review\". Code review focused\
  \ exclusively on over-engineering \u2014 finds what to delete: reinvented standard\
  \ library, unneeded dependencies, speculative abstractions, dead flexibility. One\
  \ line per finding: location, what to cut, what replaces it."
metadata:
  category: discipline
  triggers:
  - ponytail-pattern
  - architecture-review
  - design
---

## When to Use
- Reviewing diffs or PRs for over-engineering and unnecessary complexity
- Finding what to delete: reinvented stdlib, unneeded dependencies, speculative abstractions
- The user says "review for over-engineering", "what can we delete", or "simplify review"
- Getting a concise one-line-per-finding report focused on making code shorter

Review diffs for unnecessary complexity. One line per finding: location, what
to cut, what replaces it. The diff's best outcome is getting shorter.

## Format

`L<line>: <tag> <what>. <replacement>.`, or `<file>:L<line>: ...` for
multi-file diffs.

Tags:

- `delete:` dead code, unused flexibility, speculative feature. Replacement: nothing.
- `stdlib:` hand-rolled thing the standard library ships. Name the function.
- `native:` dependency or code doing what the platform already does. Name the feature.
- `yagni:` abstraction with one implementation, config nobody sets, layer with one caller.
- `shrink:` same logic, fewer lines. Show the shorter form.

## Examples

❌ "This EmailValidator class might be more complex than necessary, have you
considered whether all these validation rules are needed at this stage?"

✅ `L12-38: stdlib: 27-line validator class. "@" in email, 1 line, real validation is the confirmation mail.`

✅ `L4: native: moment.js imported for one format call. Intl.DateTimeFormat, 0 deps.`

✅ `repo.py:L88: yagni: AbstractRepository with one implementation. Inline it until a second one exists.`

✅ `L52-71: delete: retry wrapper around an idempotent local call. Nothing replaces it.`

✅ `L30-44: shrink: manual loop builds dict. dict(zip(keys, values)), 1 line.`

## Scoring

End with the only metric that matters: `net: -<N> lines possible.`

If there is nothing to cut, say `Lean already. Ship.` and stop.

## Boundaries

Scope: over-engineering and complexity only. Correctness bugs, security holes,
and performance are explicitly out of scope. Route them to a normal review
pass, not this one. A single smoke test or `assert`-based
self-check is the ponytail minimum, not bloat, never flag it for deletion.
Does not apply the fixes, only lists them.
"stop ponytail-review" or "normal mode": revert to verbose review style.

## Limitations
- Use this skill only when the task clearly matches the scope described above.
- Lists findings only — does not apply fixes.
- Focused exclusively on over-engineering; does not review for correctness, security, or performance.
- Self-check code (tests, assertions) is the ponytail minimum — never flag it for deletion.
- Stop and ask for clarification if the diff scope, review criteria, or deletion boundaries are unclear.
