"""
Two runnable Hypothesis tests per property type.
Run with: pytest examples.py  (requires: uv add hypothesis pytest)
"""

import base64
import bisect
import json

from hypothesis import given  # ty: ignore[unresolved-import]
from hypothesis import strategies as st  # ty: ignore[unresolved-import]


# ---------------------------------------------------------------------------
# Helpers under test (minimal implementations so the file runs standalone)
# ---------------------------------------------------------------------------


def dedup(xs: list) -> list:
    seen: set = set()
    out = []
    for x in xs:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def linear_search(xs: list, target) -> int:
    for i, x in enumerate(xs):
        if x == target:
            return i
    return -1


def binary_search(xs: list, target) -> int:
    """Requires xs to be sorted."""
    i = bisect.bisect_left(xs, target)
    return i if i < len(xs) and xs[i] == target else -1


def custom_max(xs: list):
    result = xs[0]
    for x in xs[1:]:
        if x > result:
            result = x
    return result


# ---------------------------------------------------------------------------
# 1. ROUND-TRIP  —  decode(encode(x)) == x
# ---------------------------------------------------------------------------


@given(st.dictionaries(st.text(), st.one_of(st.integers(), st.text(), st.booleans())))
def test_json_round_trip(data):
    """JSON serialise then deserialise returns the original dict."""
    assert json.loads(json.dumps(data)) == data


@given(st.binary())
def test_base64_round_trip(data):
    """Base-64 encode then decode returns the original bytes."""
    assert base64.b64decode(base64.b64encode(data)) == data


# ---------------------------------------------------------------------------
# 2. INVARIANT  —  a property that always holds on the output
# ---------------------------------------------------------------------------


@given(st.lists(st.integers()), st.integers())
def test_filter_produces_subset(xs, threshold):
    """Every element that survives a filter was in the original list."""
    result = [x for x in xs if x > threshold]
    assert all(x in xs for x in result)
    assert all(x > threshold for x in result)


@given(st.lists(st.integers()))
def test_dedup_produces_unique_elements(xs):
    """After deduplication every element is unique and came from the input."""
    result = dedup(xs)
    assert len(result) == len(set(result))  # no duplicates
    assert all(x in xs for x in result)  # no invented elements
    assert set(result) == set(xs)  # no elements dropped


# ---------------------------------------------------------------------------
# 3. IDEMPOTENCE  —  f(f(x)) == f(x)
# ---------------------------------------------------------------------------


@given(st.text())
def test_strip_idempotent(s):
    """Stripping whitespace twice is the same as stripping once."""
    assert s.strip().strip() == s.strip()


@given(st.lists(st.integers()))
def test_sorted_idempotent(xs):
    """Sorting an already-sorted list changes nothing."""
    once = sorted(xs)
    assert sorted(once) == once


# ---------------------------------------------------------------------------
# 4. COMMUTATIVITY  —  f(a, b) == f(b, a)
# ---------------------------------------------------------------------------


@given(st.integers(), st.integers())
def test_addition_commutative(a, b):
    """Integer addition: a + b == b + a."""
    assert a + b == b + a


@given(st.lists(st.integers()), st.lists(st.integers()))
def test_set_union_commutative(a, b):
    """Set union: A | B == B | A."""
    assert set(a) | set(b) == set(b) | set(a)


# ---------------------------------------------------------------------------
# 5. ASSOCIATIVITY  —  f(f(a, b), c) == f(a, f(b, c))
# ---------------------------------------------------------------------------


@given(st.integers(), st.integers(), st.integers())
def test_addition_associative(a, b, c):
    """(a + b) + c == a + (b + c)."""
    assert (a + b) + c == a + (b + c)


@given(st.lists(st.integers()), st.lists(st.integers()), st.lists(st.integers()))
def test_list_concat_associative(a, b, c):
    """List concatenation: (a + b) + c == a + (b + c)."""
    assert (a + b) + c == a + (b + c)


# ---------------------------------------------------------------------------
# 6. ORACLE  —  new_impl(x) == trusted_reference(x)
# ---------------------------------------------------------------------------


@given(
    st.lists(st.integers(), min_size=1).flatmap(
        lambda xs: st.tuples(st.just(sorted(xs)), st.sampled_from(xs))
    )
)
def test_binary_search_matches_linear_search(args):
    """Binary search on a sorted list finds the same index as linear search."""
    sorted_xs, target = args
    assert binary_search(sorted_xs, target) == linear_search(sorted_xs, target)


@given(st.lists(st.integers(), min_size=1))
def test_custom_max_matches_builtin(xs):
    """Custom max implementation agrees with Python's built-in max."""
    assert custom_max(xs) == max(xs)


# ---------------------------------------------------------------------------
# 7. METAMORPHIC  —  transform input → predictable change in output
# ---------------------------------------------------------------------------


@given(st.lists(st.integers(), min_size=1), st.integers())
def test_sort_with_new_maximum_ends_last(xs, extra):
    """Appending a value larger than all existing elements puts it last."""
    new_max = max(xs) + abs(extra) + 1
    result = sorted(xs + [new_max])
    assert result[-1] == new_max


@given(
    st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=1),
    st.integers(min_value=1, max_value=100),
)
def test_scaling_inputs_scales_sum(xs, k):
    """Multiplying every element by k multiplies the total sum by k."""
    assert sum(x * k for x in xs) == pytest.approx(sum(xs) * k)


# ---------------------------------------------------------------------------
# pytest.approx import needed for the last test
# ---------------------------------------------------------------------------
import pytest  # noqa: E402  (placed after tests for readability)
