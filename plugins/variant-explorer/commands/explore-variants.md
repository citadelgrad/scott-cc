---
name: explore-variants
description: Spawn N blind builders in isolated worktrees against a spec + acceptance criteria, then judge the results and produce a ranked shortlist
argument-hint: "[spec or design question, or path to one] [--n N] [--ac <path>]"
allowed-tools: Task, Read, Write, Grep, Glob, Bash
---

# Explore Variants

Human entry point for the variant-explorer plugin's blind-builder panel. This command's only job
is to parse arguments into a spec, an AC source, and N, then hand off to the orchestrator skill —
it does not itself spawn builders, judge variants, or manage worktrees.

## Arguments

$ARGUMENTS

Parse the arguments to extract:

- **Spec**: the design question or feature spec, taken as free text or a file path — whatever
  remains after stripping the flags below. Pass it through unparsed to the orchestrator.
- **`--ac <path>`**: path to existing acceptance criteria, if given. If omitted, the orchestrator
  generates AC itself via the `acceptance-criteria` skill — do not attempt to generate AC here.
- **`--n N`**: requested variant count. Pass the raw value through; the orchestrator owns
  validation (refusing N=1, clamping N>6, defaulting to 3) per
  `skills/explore-variants/SKILL.md`'s Phase 1.

## Action

Invoke the **explore-variants** skill (`skills/explore-variants/SKILL.md`) as the orchestrator,
passing the parsed spec, AC source, and N through. Read `SKILL.md` in full before acting — do not
run the panel from memory of this command file. In particular:

- Phase 1 (input gathering and N validation) — the only place N's boundary behavior is decided
- Phase 2 (blind builder dispatch) — the isolation rules a builder's prompt must never violate
- Phase 3 (failure handling) — how a lost variant is reported without silently shrinking N
- Phase 4 (judge panel) — how the taste axis is included or explicitly omitted based on whether
  `TASTE.md` exists
- Phase 5 (human pick & cleanup) — the harvest prompt that must precede any worktree removal

## Example usage

```
/explore-variants "Add a rate limiter to the API gateway" --n 3
/explore-variants specs/checkout-redesign.md --ac specs/checkout-redesign.ac.md --n 4
/explore-variants "Pick a caching strategy for the search index"
```

- No `--n`: defaults to 3.
- No `--ac`: the orchestrator generates acceptance criteria from the spec before spawning builders.
- `--n 1`: the orchestrator refuses and suggests building directly.
- `--n` above 6: the orchestrator clamps to 6 and reports the clamp.
