---
name: property-based-testing
description: Use when implementing serialization/parsing, data transformations, algorithms with mathematical properties, API contracts, or state machines where testing all edge cases is impractical — especially when you can describe invariants rather than specific input/output pairs.
---

# Property-Based Testing

## Overview

Instead of testing specific examples, describe **properties that must always hold** and let the framework generate hundreds of random inputs to find counterexamples. Think in invariants, not examples.

PBT complements example-based tests — it doesn't replace them. Use both.

## Property Taxonomy

| Property | Description | Signature |
|----------|-------------|-----------|
| **Round-trip** | Encode then decode returns original | `decode(encode(x)) == x` |
| **Invariant** | Property always holds regardless of input | `len(sort(xs)) == len(xs)` |
| **Idempotence** | Applying twice equals applying once | `f(f(x)) == f(x)` |
| **Commutativity** | Order doesn't matter | `f(a, b) == f(b, a)` |
| **Associativity** | Grouping doesn't matter | `f(f(a,b),c) == f(a,f(b,c))` |
| **Oracle** | Compare fast impl against trusted slow impl | `fast_sort(xs) == reference_sort(xs)` |
| **Metamorphic** | Known input transformation → known output change | `sort(xs + [min]) starts with min` |

## Where It Shines

- **Parsing & serialization** — JSON, CSV, Protobuf, custom formats (round-trip is natural)
- **Data transformation pipelines** — normalization, canonicalization, ETL logic
- **Algorithms** — sort stability, search correctness, graph traversal properties
- **API contracts** — Pydantic model validation, request/response schemas
- **State machines** — any sequence of valid transitions preserves invariants

## Where It Struggles

- UI rendering (hard to express as properties)
- Side-effectful code without good mocks
- Properties you haven't thought of (PBT only finds bugs you have a property for)
- Performance-sensitive hot paths (generates many inputs by default)

## Quick Reference by Language

| Language | Library | Install |
|----------|---------|---------|
| Python | `hypothesis` | `uv add hypothesis` |
| TypeScript/JS | `fast-check` | `npm add -D fast-check` |
| Rust | `proptest` | `cargo add proptest --dev` |
| Go | `rapid` | `go get pgregory.net/rapid` |
| Java/Scala | `jqwik` / `ScalaCheck` | Maven/sbt |

## Examples

`examples.py` in this directory contains **two runnable Hypothesis tests per property type** (14 tests total). Copy and adapt them as a starting point.

```
pytest skills/property-based-testing/examples.py  # requires: uv add hypothesis pytest
```

## Hypothesis (Python) Example

```python
from hypothesis import given, settings, assume
from hypothesis import strategies as st
from myapp.models import UserSchema
import json

# Round-trip: serialize → deserialize returns original
@given(st.builds(UserSchema, name=st.text(min_size=1), age=st.integers(18, 120)))
def test_user_schema_round_trip(user):
    serialized = user.model_dump_json()
    restored = UserSchema.model_validate_json(serialized)
    assert restored == user

# Idempotence: normalizing twice = normalizing once
@given(st.text())
def test_normalize_idempotent(s):
    assert normalize(normalize(s)) == normalize(s)

# Invariant: sort preserves length and elements
@given(st.lists(st.integers()))
def test_sort_invariants(xs):
    result = my_sort(xs)
    assert len(result) == len(xs)           # length preserved
    assert sorted(result) == sorted(xs)    # same elements
    assert all(result[i] <= result[i+1]    # ordered
               for i in range(len(result)-1))

# Metamorphic: adding the minimum value produces a known first element
@given(st.lists(st.integers(), min_size=1))
def test_sort_metamorphic(xs):
    minimum = min(xs)
    result = my_sort(xs)
    assert result[0] == minimum

# Oracle: compare new fast implementation against trusted reference
@given(st.lists(st.integers()))
def test_fast_sort_matches_reference(xs):
    assert fast_sort(xs) == sorted(xs)
```

## fast-check (TypeScript) Example

```typescript
import fc from 'fast-check';

// Round-trip for a custom serializer
test('serialize/parse round-trip', () => {
  fc.assert(
    fc.property(fc.record({ id: fc.uuid(), value: fc.string() }), (record) => {
      expect(parse(serialize(record))).toEqual(record);
    })
  );
});

// Commutativity: merge order doesn't matter for non-conflicting keys
test('merge is commutative for disjoint objects', () => {
  fc.assert(
    fc.property(
      fc.record({ a: fc.integer() }),
      fc.record({ b: fc.integer() }),
      (left, right) => {
        expect(merge(left, right)).toEqual(merge(right, left));
      }
    )
  );
});
```

## Thinking in Properties Checklist

Before writing any data transformation or algorithm, ask:

- [ ] Does encode/decode round-trip? (`decode(encode(x)) == x`)
- [ ] Does applying this twice give the same result? (idempotence)
- [ ] What size invariants hold? (lengths, counts, set membership)
- [ ] Does order of inputs matter? Could it be commutative?
- [ ] Can I compare this against a slower trusted implementation? (oracle)
- [ ] What transformation of the input produces a predictable output change? (metamorphic)

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Writing properties that only hold for your examples | Use `assume()` to filter, not constrain strategies |
| Generating too-large inputs causing timeouts | Use `max_size` on collections; add `@settings(max_examples=50)` |
| Forgetting to shrink: hard to debug failures | Hypothesis shrinks automatically; fast-check uses `fc.property` |
| Testing implementation details, not behavior | Properties should describe what, not how |
| Abandoning PBT when first property is hard | Start with round-trip — it's almost always expressible |

## Starting Point Recipe

1. **Find the round-trip** — if you serialize/transform data, this is free
2. **List invariants** — what must always be true about the output's shape/size/type?
3. **Check idempotence** — normalization, formatting, and cleanup functions almost always have this
4. **Add an oracle** — if you're optimizing an existing implementation, diff against it
5. **Look for metamorphic relations** — "if I change input X, output changes predictably by Y"
