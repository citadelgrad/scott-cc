# Instructions: Generating Meaningful Tests

This document defines the standards for "Meaningful Tests" within this codebase. When generating, refactoring, or fixing tests, adhere to these principles.

## The Core Philosophy

A test is **meaningful** only if:
1. **It tests behavior, not implementation.** (Refactoring internals shouldn't break the test).
2. **It documents the code.** (The test name explains the business rule).
3. **It is diagnostic.** (A failure reveals exactly *what* broke without needing a debugger).

---

## Anti-Patterns (What to Avoid)

* **Tautological Tests:** Asserting `result == result` or mocking a return value and immediately asserting it matches the mock.
* **Existence Checks:** `assert result is not None` or `expect(data).toBeDefined()` are rarely sufficient. Assert *properties* of the result.
* **Implementation Leakage:** Mocking private methods or checking internal state fields.
* **Generic Naming:** `test_process` or `it('should work')`.

---

## Framework Specifics: Pytest

### 1. Structure & Naming
* **File naming:** `test_<module_name>.py`
* **Test naming:** `test_<unit>_<condition>_<expected_result>`
    * *Example:* `test_calculate_tax_with_negative_price_raises_value_error`

### 2. Using Fixtures over Setup
Do not use global variables. Use `pytest.fixture` to explicitly state dependencies.
* **Meaningful:** Fixtures should yield valid, realistic data states.

### 3. Parametrization for Boundaries
Don't write 5 separate tests for similar logic. Use `@pytest.mark.parametrize` to cover edge cases meaningfully.

```python
# GOOD: Meaningful Boundary Testing
@pytest.mark.parametrize("input_age, expected_status", [
    (17, "minor"),
    (18, "adult"),
    (150, "error")
])
def test_age_categorization_logic(input_age, expected_status):
    assert categorize_age(input_age) == expected_status
```

### 4. Error Assertions

Never just check if "an error occurred." Check the **type** and the **message**.

```python
# GOOD
with pytest.raises(ValueError, match="Price cannot be negative"):
    calculate_total(-100)
```

---

## Framework Specifics: Vitest

### 1. Structure & Naming

* Use `describe()` blocks to group the unit/feature being tested.
* Use `it()` or `test()` for specific scenarios.
* **Description Format:** `it('should <action> when <condition>', ...)`

### 2. Async & Timing

* Never use `setTimeout`. Use Vitest's `vi.useFakeTimers()` for time-dependent tests.
* Always `await` promises explicitly.

### 3. Mocking Boundaries

* Use `vi.mock()` strictly for external boundaries (API calls, DB queries).
* **Do not mock** the logic inside the function you are testing.

### 4. Assertion Specificity

* Avoid `toBeTruthy()`. Use strict equality.

```typescript
// BAD: Ambiguous
expect(user.isAdmin).toBeTruthy();

// GOOD: Meaningful
expect(user.role).toBe('ADMIN');
```

---

## Examples: Meaningful vs. Useless

### Scenario: User Registration

#### The Useless Test (Do Not Generate)

*Why it fails:* It mocks the outcome, proving nothing. It doesn't verify the side effect (DB save).

```typescript
it('creates a user', async () => {
  const mockRepo = { create: vi.fn().mockResolvedValue({ id: 1 }) };
  const service = new UserService(mockRepo);

  const result = await service.create("test");
  expect(result).toBeDefined(); // Meaningless
});
```

#### The Meaningful Test

*Why it works:* It verifies inputs are passed correctly and business rules (email normalization) are applied.

```typescript
it('should normalize email to lowercase before saving', async () => {
  // Arrange
  const mockRepo = { create: vi.fn() };
  const service = new UserService(mockRepo);

  // Act
  await service.create("TeSt@Example.COM");

  // Assert: Verify the behavior (the argument passed to the dependency)
  expect(mockRepo.create).toHaveBeenCalledWith(
    expect.objectContaining({
      email: "test@example.com"
    })
  );
});
```

---

## Edge Cases & Error Paths

The "Happy Path" (where everything goes right) is only 20% of the work. Meaningful tests must aggressively verify the system's behavior at its **boundaries** and during **failures**.

### 1. Edge Cases (The Boundaries)

An edge case is a valid input that is pushed to the limit. The system should not crash; it should handle it gracefully.

**The "Z.O.M." Heuristic**

Always check:
* **Z**ero: Empty arrays, empty strings, `0`, `null`, `undefined`.
* **O**ne: Single element arrays, single character strings.
* **M**any: Large payloads, pagination limits (e.g., 1000 items), maximum integer values.

#### Pytest Example: Boundary Testing

```python
# Testing a discount calculator
@pytest.mark.parametrize("cart_total, expected_discount", [
    (0, 0),         # Edge: Zero
    (0.01, 0),      # Edge: Smallest positive
    (99, 0),        # Edge: Just below threshold
    (100, 10),      # Edge: Exactly on threshold
    (1000000, 10)   # Edge: Large number
])
def test_calculate_discount_boundaries(cart_total, expected_discount):
    assert calculate_discount(cart_total) == expected_discount
```

#### Vitest Example: Empty States

```typescript
it.each([
  { items: [], desc: 'empty array' },
  { items: null, desc: 'null input' },
  { items: undefined, desc: 'undefined input' }
])('returns default total for $desc', ({ items }) => {
  const result = calculateTotal(items);
  expect(result).toBe(0); // Should handle gracefully, not throw
});
```

---

### 2. Error Paths (The Unhappy Paths)

An error path is when something goes wrong (invalid input, network failure, missing file). Meaningful tests verify that the system **fails safely**.

**The "Force Fail" Checklist**

Must verify:
* **Validation Errors:** Inputs that violate business rules (e.g., negative age, duplicate email).
* **Resource Failures:** What if the DB is down? What if the API returns 500?
* **Timeouts:** What if the async operation hangs?

#### Pytest Example: Resource Failure

```python
def test_fetch_user_handles_api_timeout(mocker):
    # Arrange: Simulate a network timeout
    mocker.patch('requests.get', side_effect=requests.exceptions.Timeout)

    # Act & Assert: Ensure custom exception is raised, not raw stack trace
    with pytest.raises(ServiceUnavailableError, match="User service timed out"):
        user_service.get_user_by_id(123)
```

#### Vitest Example: Business Logic Rejection

```typescript
it('rejects registration if user is under 18', async () => {
  // Arrange
  const minorUser = { dob: '2020-01-01' };

  // Act & Assert
  // Specifically check for the Domain Error, not just generic Error
  await expect(registerUser(minorUser))
    .rejects
    .toThrowError(/User must be at least 18/);
});
```

---

### 3. Negative Test Case Strategy

When generating tests, always include:

1. **Malformed Input** - Wrong types/formats
2. **Business Rule Violations** - Logic limits exceeded
3. **Dependency Failures** - Mocked DB/API errors

---

## Quick Reference Checklist

When reviewing generated tests, verify:

- [ ] Test name describes the business rule being tested
- [ ] Assertions check specific properties, not just existence
- [ ] Mocks are only used for external boundaries
- [ ] Error tests verify both type and message
- [ ] Parametrized tests cover meaningful boundary cases
- [ ] No implementation details are being tested
- [ ] A failure would clearly indicate what broke
- [ ] Z.O.M. boundaries covered (Zero, One, Many)
- [ ] Error paths tested (validation, resource failures, timeouts)
- [ ] Negative test cases included (malformed, business rules, dependencies)
