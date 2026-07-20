# variant-explorer

> Parallel blind-builder variant exploration with a judged, ranked shortlist

## What's Included

### Commands (1)

- **`/explore-variants`** - Spawn N blind builders in isolated worktrees against a spec +
  acceptance criteria, then judge the results and produce a ranked shortlist.

### Agents (2)

- **blind-builder** - Builds one complete, independent implementation of a spec inside an
  isolated worktree, without seeing any sibling variant.
- **variant-judge** - Scores every surviving variant along one judging axis (AC-conformance,
  taste, or simplicity) and returns a scorecard per variant. Never edits variant code.

### Skills (1)

- **explore-variants** - The orchestrator: gathers input, validates N, spawns blind builders,
  collects results (reporting any lost variants explicitly), runs the judge panel, and hands the
  human a ranked shortlist.

## When to Use

**Install this if you**:
- Want to compare multiple genuinely different implementations before committing, not just
  designs on paper
- Have a spec concrete enough to hand to independent builders with acceptance criteria
- Already use `review-panel` and want its taste/simplicity lenses applied to variant comparison

**Don't install if you**:
- Only need to compare design alternatives, not working code — use `review-panel`'s
  `design-it-twice` skill instead, it's far cheaper
- Have a trivial change or a single well-established implementation pattern

## Common Use Cases

### 1. Comparing implementation approaches for a spec
```
User: /explore-variants "Add a rate limiter to the API gateway" --n 3
explore-variants: spawns 3 blind builders (MVP-first, data-model-first, dependency-free),
  judges the survivors against AC, TASTE.md (if present), and simplicity, and returns a
  ranked shortlist.
```

### 2. Exploring a design question with no prior AC
```
User: /explore-variants "Pick a caching strategy for the search index"
explore-variants: generates acceptance criteria via the acceptance-criteria skill first,
  then proceeds as usual.
```

### 3. Harvesting ideas from a losing variant
```
User: (after reviewing the shortlist) "Yes, harvest ideas from runner-up 2 before cleanup"
explore-variants: reads that worktree, notes the specific idea(s) worth extracting in the
  final report, then removes the non-winning worktrees.
```

## Quick Start

```bash
# Explore 3 variants of a spec with existing acceptance criteria
/explore-variants specs/checkout-redesign.md --ac specs/checkout-redesign.ac.md --n 4

# Explore with default N=3 and auto-generated AC
/explore-variants "Add a rate limiter to the API gateway"
```

## Dependency Direction

Depends on `review-panel`'s `taste-review` and `ponytail-review` skills for two of the judge
panel's three axes. `review-panel` never depends on or special-cases `variant-explorer`, and
never gains worktree-spawning or execution machinery — that stays entirely in this plugin.

## Recommended Combinations

**Full exploration-to-review pipeline**:
- variant-explorer ✅ (build and judge N variants, pick a winner)
- review-panel ✅ (full adversarial review of the winning variant's diff before merge)
