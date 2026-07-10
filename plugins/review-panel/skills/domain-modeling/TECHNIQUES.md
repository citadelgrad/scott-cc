# The 8 Techniques

Taught in dependency order — each technique is the prerequisite for the one after it. Grounded in Scott Wlaschin's *Domain Modeling Made Functional*, Alexis King's "Parse, Don't Validate", and Marvin Minsky's observation that a system's state space should match its domain's real state space, not a superset of it.

Style baseline throughout: functional, immutable data, errors-as-values. Avoid classes/OOP entirely except for the one sanctioned use in technique 7 (custom error types as a closed sum type).

## 1. Algebraic Data Types: Sum vs Product

This is the foundation vocabulary everything else builds on.

- **Product type**: a value that holds *all* of its fields simultaneously (a struct/record/tuple — "AND"). `{ name: string; age: number }` is a product: every instance has a name AND an age.
- **Sum type** (tagged/discriminated union): a value that holds *exactly one* of several alternatives ("OR"), each of which may carry different data. This is the type most OOP-trained developers under-use — they reach for booleans, optional fields, or class hierarchies instead.

**TypeScript**
```ts
// Product
type Point = { x: number; y: number };

// Sum (discriminated union — the "tag" is the `kind` field)
type Shape =
  | { kind: "circle"; radius: number }
  | { kind: "rectangle"; width: number; height: number };
```

**Python** (3.10+, using `dataclass` + union, or `Enum` for closed variants without payload)
```python
from dataclasses import dataclass
from typing import Union

@dataclass(frozen=True)
class Circle:
    radius: float

@dataclass(frozen=True)
class Rectangle:
    width: float
    height: float

Shape = Union[Circle, Rectangle]  # sum type
```

**Rust** (sum types are `enum`, product types are `struct` — this is the language's native idiom)
```rust
struct Point { x: f64, y: f64 } // product

enum Shape {                     // sum
    Circle { radius: f64 },
    Rectangle { width: f64, height: f64 },
}
```

## 2. Make Illegal States Unrepresentable

The payoff of technique 1. Minsky's framing: don't model the domain and then bolt on validation to reject bad states — shape the *type* so the bad state has no representation at all. If a state is illegal, the compiler should refuse to construct it, not merely warn at runtime.

Classic anti-pattern: independent boolean/optional fields whose combinations imply invariants the type system doesn't enforce (`isPaid && !isShipped`, `trackingNumber` present while `isPaid` is false, etc — see [WORKED-EXAMPLE.md](./WORKED-EXAMPLE.md)). Fix: a sum type where each variant carries exactly the data valid for that state, and no more.

**TypeScript**
```ts
// Illegal state possible: paid=false but trackingNumber set
type OrderBad = { isPaid: boolean; trackingNumber?: string };

// Illegal state unrepresentable: trackingNumber only exists inside "shipped"
type OrderGood =
  | { status: "placed" }
  | { status: "paid"; paymentId: string }
  | { status: "shipped"; paymentId: string; trackingNumber: string };
```

**Python**
```python
from dataclasses import dataclass
from typing import Union

@dataclass(frozen=True)
class Placed: ...

@dataclass(frozen=True)
class Paid:
    payment_id: str

@dataclass(frozen=True)
class Shipped:
    payment_id: str
    tracking_number: str

OrderGood = Union[Placed, Paid, Shipped]
```

**Rust**
```rust
enum OrderGood {
    Placed,
    Paid { payment_id: String },
    Shipped { payment_id: String, tracking_number: String },
}
```

## 3. Exhaustive Matching

The compiler-enforced guardrail that keeps technique 2 true as the model grows. When you add a new variant to a sum type, every `match`/`switch` over it should fail to compile until you handle the new case. Non-exhaustive matching silently reintroduces illegal states through the back door — a forgotten `case` is a state the code doesn't know how to handle.

**TypeScript** — use `never` to force exhaustiveness at compile time:
```ts
function assertNever(x: never): never {
  throw new Error(`Unhandled case: ${JSON.stringify(x)}`);
}

function describe(order: OrderGood): string {
  switch (order.status) {
    case "placed": return "awaiting payment";
    case "paid": return "payment received";
    case "shipped": return `on the way (${order.trackingNumber})`;
    default: return assertNever(order); // compile error if a case is missing
  }
}
```

**Python** — no native exhaustiveness check; approximate it with `assert_never` from `typing` (3.11+) or `typing_extensions`, checked by a type checker (mypy/pyright) rather than the runtime:
```python
from typing import assert_never

def describe(order: OrderGood) -> str:
    match order:
        case Placed():
            return "awaiting payment"
        case Paid(payment_id=pid):
            return "payment received"
        case Shipped(tracking_number=tn):
            return f"on the way ({tn})"
        case _:
            assert_never(order)  # mypy/pyright flag this if a variant is unhandled
```

**Rust** — exhaustiveness is enforced natively by the compiler; no library needed:
```rust
fn describe(order: &OrderGood) -> String {
    match order {
        OrderGood::Placed => "awaiting payment".into(),
        OrderGood::Paid { .. } => "payment received".into(),
        OrderGood::Shipped { tracking_number, .. } => format!("on the way ({tracking_number})"),
        // omitting a variant here is a compile error, full stop
    }
}
```

## 4. Parse, Don't Validate

Alexis King's core move: validation checks a condition and discards the proof (`isEmailValid(s): boolean` tells you nothing at the call site five lines later). *Parsing* checks a condition and returns a **new, more precise type** that carries the proof in its shape — once you have an `Email`, nobody downstream needs to re-check it. This moves correctness checks from "somewhere in the middle of the code, maybe" to "the boundary, exactly once."

**TypeScript**
```ts
// Validate (loses the proof — anyone downstream still just has a string)
function isValidEmail(s: string): boolean { return /\S+@\S+\.\S+/.test(s); }

// Parse (keeps the proof — downstream code only ever sees a proven-valid Email)
type Email = { readonly _brand: "Email"; readonly value: string };
function parseEmail(s: string): Email | null {
  return /\S+@\S+\.\S+/.test(s) ? ({ _brand: "Email", value: s } as Email) : null;
}
```

**Python**
```python
from typing import NewType, Optional
import re

Email = NewType("Email", str)  # nominal-ish at type-check time only, see gotcha below

def parse_email(s: str) -> Optional[Email]:
    return Email(s) if re.match(r"\S+@\S+\.\S+", s) else None
```

**Rust**
```rust
struct Email(String); // tuple struct — private field, see smart constructors below

fn parse_email(s: &str) -> Option<Email> {
    if s.contains('@') { Some(Email(s.to_string())) } else { None }
}
```

## 5. Smart Constructors / Branded (Newtype) Primitives

The mechanism that makes technique 4 concrete and enforceable. A "primitive obsession" domain passes `string`/`number` everywhere (`createOrder(customerId: string, productId: string, ...)` — easy to swap two arguments and have it still compile). A **branded type** (TS) or **newtype** (Rust/Python `NewType`) wraps the primitive so the type checker rejects mixing them, and a **smart constructor** is the only way to produce one, gatekeeping validity at construction time.

**TypeScript** — brand via an intersection with a phantom tag:
```ts
type CustomerId = string & { readonly __brand: "CustomerId" };
type ProductId = string & { readonly __brand: "ProductId" };

function makeCustomerId(raw: string): CustomerId | null {
  return /^cus_[a-z0-9]+$/.test(raw) ? (raw as CustomerId) : null;
}
// makeCustomerId(x) and a raw ProductId are no longer interchangeable at compile time
```
**Gotcha (cannibalized from vibe-types' branded-type catalog entry):** branded types are a compile-time-only fiction — `JSON.stringify`/`JSON.parse` round-trips silently erase the brand, because the runtime value is just a plain string. Re-parse (technique 4) at every deserialization boundary; never trust a brand that crossed a JSON/IPC/DB boundary without re-validation.

**Python** — `NewType` is also compile-time-only (mypy/pyright erase it at runtime, same gotcha as TS):
```python
from typing import NewType

CustomerId = NewType("CustomerId", str)
ProductId = NewType("ProductId", str)

def make_customer_id(raw: str) -> CustomerId | None:
    return CustomerId(raw) if raw.startswith("cus_") else None
# a dict loaded from JSON is just `str` again — re-validate at the boundary
```

**Rust** — newtypes are real, runtime-enforced types (not erased), and privacy makes the constructor the only entry point:
```rust
pub struct CustomerId(String); // field is private to this module

impl CustomerId {
    pub fn parse(raw: &str) -> Option<Self> {
        raw.starts_with("cus_").then(|| CustomerId(raw.to_string()))
    }
}
// outside this module, the only way to get a CustomerId is through `parse`
```

## 6. Errors as Values — Result/Either

What a failed parse or workflow step returns, instead of throwing. Exceptions are invisible in a function's signature — nothing forces a caller to notice a `parseEmail` can fail. A `Result<T, E>` (or `Either<E, T>`) return type makes failure a first-class, visible, exhaustively-matchable part of the contract (technique 3 applies to it too).

**TypeScript** (no native `Result` — a minimal shape is enough; libraries like `neverthrow` add ergonomics but aren't required)
```ts
type Result<T, E> = { ok: true; value: T } | { ok: false; error: E };

function parseAge(raw: string): Result<number, string> {
  const n = Number(raw);
  return Number.isInteger(n) && n >= 0
    ? { ok: true, value: n }
    : { ok: false, error: `not a valid age: ${raw}` };
}
```

**Python** — no native `Result`; model it as a small `Union` of two `dataclass`es (or use a library like `returns`), and let `match` (technique 3) force handling both:
```python
from dataclasses import dataclass
from typing import Union

@dataclass(frozen=True)
class Ok:
    value: int

@dataclass(frozen=True)
class Err:
    error: str

Result = Union[Ok, Err]

def parse_age(raw: str) -> Result:
    return Ok(int(raw)) if raw.isdigit() else Err(f"not a valid age: {raw}")
```

**Rust** — `Result<T, E>` is in the standard library; this is the idiomatic default, not an add-on:
```rust
fn parse_age(raw: &str) -> Result<u32, String> {
    raw.parse::<u32>().map_err(|_| format!("not a valid age: {raw}"))
}
```

## 7. Custom Error Types

Structures technique 6's error channel as its own sum type instead of a bag of strings. This is the **one sanctioned use of a class-like construct** in this style — an error type is data (a closed set of named failure modes with attached context), not behavior, so it doesn't violate the FP bias.

**TypeScript**
```ts
type OrderError =
  | { kind: "invalidEmail"; raw: string }
  | { kind: "customerNotFound"; id: string }
  | { kind: "paymentDeclined"; reason: string };
// downstream `switch` on `.kind` is exhaustive-checked per technique 3
```

**Python** — a sum type of `dataclass`es, same shape as technique 1/2, used specifically as the error channel:
```python
from dataclasses import dataclass
from typing import Union

@dataclass(frozen=True)
class InvalidEmail:
    raw: str

@dataclass(frozen=True)
class CustomerNotFound:
    id: str

@dataclass(frozen=True)
class PaymentDeclined:
    reason: str

OrderError = Union[InvalidEmail, CustomerNotFound, PaymentDeclined]
```

**Rust** — an `enum` implementing `std::error::Error` (and typically `Display`) is the idiomatic custom error type; the `thiserror` crate removes the boilerplate but the underlying shape is still a plain enum:
```rust
enum OrderError {
    InvalidEmail { raw: String },
    CustomerNotFound { id: String },
    PaymentDeclined { reason: String },
}
```

## 8. Workflows as Functions; State Machines over Booleans

Composes all seven techniques above into a pipeline. A business workflow is a sequence of pure functions, each shaped `PrevState -> Result<NextState, StepError>` (techniques 2, 6, 7 combined). Each step consumes the previous state and either produces the next legal state or a typed error — it never mutates a shared "god object" of booleans in place. See [WORKED-EXAMPLE.md](./WORKED-EXAMPLE.md) for the full order → payment → fulfillment pipeline in all three languages.

**TypeScript**
```ts
declare function pay(order: PlacedOrder, paymentId: string): Result<PaidOrder, OrderError>;
declare function fulfill(order: PaidOrder, tracking: string): Result<ShippedOrder, OrderError>;
// `fulfill` cannot accept a PlacedOrder — that's a compile error, not a runtime check
```

**Python**
```python
def pay(order: Placed, payment_id: str) -> Result: ...
def fulfill(order: Paid, tracking: str) -> Result: ...
# a type checker rejects fulfill(placed_order, ...) — mypy/pyright catch it; the
# runtime itself won't, since Python erases types, so keep type-checking in CI
```

**Rust**
```rust
fn pay(order: PlacedOrder, payment_id: String) -> Result<PaidOrder, OrderError> { /* ... */ }
fn fulfill(order: PaidOrder, tracking: String) -> Result<ShippedOrder, OrderError> { /* ... */ }
// transitions consume `self`/the input by value — a stale PlacedOrder handle
// can't be reused to call fulfill twice, because it was moved into `pay`
```
