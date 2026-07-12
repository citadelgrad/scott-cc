# Worked Example: Order → Payment → Fulfillment

A single domain, shown before and after applying the 8 techniques from [TECHNIQUES.md](./TECHNIQUES.md). This is the reference example [SKILL.md](./SKILL.md) and [RED-FLAGS.md](./RED-FLAGS.md) point back to.

## The Domain

An order starts life in a cart, gets placed, gets paid, gets fulfilled (shipped), and may be cancelled or refunded along the way. Real rules the type should enforce:

- An order cannot ship before it's paid.
- An order cannot be both refunded and cancelled.
- A tracking number only exists once fulfillment happens.
- A payment ID only exists once payment happens.

## Before: Booleans and Optional Fields

Every language version of the "before" shape compiles fine while allowing nonsense: `shipped=true, isPaid=false` (shipped without payment), `isRefunded=true, isCancelled=true` (refunded AND cancelled), or `trackingNumber` set while `isShipped=false` (flag/data desync). The type system has no opinion on any of this — every invariant lives only in the developer's head and in scattered `if` checks that may or may not run before every mutation site.

**TypeScript — before**
```ts
interface Order {
  id: string;
  customerId: string;
  isPaid: boolean;
  isShipped: boolean;
  isCancelled: boolean;
  isRefunded: boolean;
  paymentId?: string;
  trackingNumber?: string;
}

// Compiles. Nonsensical. Nothing stops this:
const impossible: Order = {
  id: "o1", customerId: "c1",
  isPaid: false, isShipped: true,     // shipped without payment
  isCancelled: true, isRefunded: true, // cancelled AND refunded
  trackingNumber: "TRK-1",             // present despite isShipped logic being wrong anyway
};
```

**Python — before**
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class Order:
    id: str
    customer_id: str
    is_paid: bool = False
    is_shipped: bool = False
    is_cancelled: bool = False
    is_refunded: bool = False
    payment_id: Optional[str] = None
    tracking_number: Optional[str] = None

# Runs. Nonsensical. Nothing stops this:
impossible = Order(
    id="o1", customer_id="c1",
    is_paid=False, is_shipped=True,      # shipped without payment
    is_cancelled=True, is_refunded=True, # cancelled AND refunded
    tracking_number="TRK-1",
)
```

**Rust — before**
```rust
struct Order {
    id: String,
    customer_id: String,
    is_paid: bool,
    is_shipped: bool,
    is_cancelled: bool,
    is_refunded: bool,
    payment_id: Option<String>,
    tracking_number: Option<String>,
}
// Same problem: every field is independently settable, so every combination
// compiles, including the impossible ones.
```

## After: A Status-Tagged Union

Each variant carries **only** the fields valid for that state. `PaidOrder` doesn't have a `trackingNumber` field to forget to check — it simply doesn't exist until `ShippedOrder`. Cancellation and refund become their own terminal variants, so "cancelled AND refunded" has no representation.

**TypeScript — after**
```ts
type CartOrder = { status: "cart"; id: string; customerId: string; items: string[] };
type PlacedOrder = { status: "placed"; id: string; customerId: string; items: string[] };
type PaidOrder = { status: "paid"; id: string; customerId: string; paymentId: string };
type FulfilledOrder = { status: "fulfilled"; id: string; customerId: string; paymentId: string; trackingNumber: string };
type CancelledOrder = { status: "cancelled"; id: string; reason: string };
type RefundedOrder = { status: "refunded"; id: string; paymentId: string; refundId: string };

type Order = CartOrder | PlacedOrder | PaidOrder | FulfilledOrder | CancelledOrder | RefundedOrder;

type OrderError =
  | { kind: "paymentDeclined"; reason: string }
  | { kind: "alreadyProcessed"; id: string };

type Result<T, E> = { ok: true; value: T } | { ok: false; error: E };

// Each step: PrevState -> Result<NextState, StepError>
function pay(order: PlacedOrder, paymentId: string): Result<PaidOrder, OrderError> {
  return { ok: true, value: { status: "paid", id: order.id, customerId: order.customerId, paymentId } };
}

function fulfill(order: PaidOrder, trackingNumber: string): Result<FulfilledOrder, OrderError> {
  return {
    ok: true,
    value: { status: "fulfilled", id: order.id, customerId: order.customerId, paymentId: order.paymentId, trackingNumber },
  };
}

// fulfill(cartOrder, "TRK-1") is a COMPILE ERROR: CartOrder is not assignable to PaidOrder.
// There is no runtime check to forget — the impossible call cannot be written.
```

**Python — after**
```python
from dataclasses import dataclass
from typing import Union

@dataclass(frozen=True)
class CartOrder:
    id: str
    customer_id: str
    items: list[str]

@dataclass(frozen=True)
class PlacedOrder:
    id: str
    customer_id: str
    items: list[str]

@dataclass(frozen=True)
class PaidOrder:
    id: str
    customer_id: str
    payment_id: str

@dataclass(frozen=True)
class FulfilledOrder:
    id: str
    customer_id: str
    payment_id: str
    tracking_number: str

@dataclass(frozen=True)
class CancelledOrder:
    id: str
    reason: str

@dataclass(frozen=True)
class RefundedOrder:
    id: str
    payment_id: str
    refund_id: str

Order = Union[CartOrder, PlacedOrder, PaidOrder, FulfilledOrder, CancelledOrder, RefundedOrder]

@dataclass(frozen=True)
class PaymentDeclined:
    reason: str

@dataclass(frozen=True)
class AlreadyProcessed:
    id: str

OrderError = Union[PaymentDeclined, AlreadyProcessed]

@dataclass(frozen=True)
class Ok:
    value: object

@dataclass(frozen=True)
class Err:
    error: OrderError

def pay(order: PlacedOrder, payment_id: str) -> Union[Ok, Err]:
    return Ok(PaidOrder(id=order.id, customer_id=order.customer_id, payment_id=payment_id))

def fulfill(order: PaidOrder, tracking_number: str) -> Union[Ok, Err]:
    return Ok(FulfilledOrder(
        id=order.id, customer_id=order.customer_id,
        payment_id=order.payment_id, tracking_number=tracking_number,
    ))

# fulfill(cart_order, "TRK-1") is flagged by mypy/pyright: CartOrder is not PaidOrder.
# Python's runtime won't stop you (types erase at runtime) — enforce this in CI.
```

**Rust — after**
```rust
struct CartOrder { id: String, customer_id: String, items: Vec<String> }
struct PlacedOrder { id: String, customer_id: String, items: Vec<String> }
struct PaidOrder { id: String, customer_id: String, payment_id: String }
struct FulfilledOrder { id: String, customer_id: String, payment_id: String, tracking_number: String }
struct CancelledOrder { id: String, reason: String }
struct RefundedOrder { id: String, payment_id: String, refund_id: String }

enum OrderError {
    PaymentDeclined { reason: String },
    AlreadyProcessed { id: String },
}

// Note: transitions consume `order` BY VALUE (not `&order`). Once `pay` is
// called, the caller's PlacedOrder is moved and can no longer be used —
// a stale handle can't be replayed to call `pay` or `fulfill` twice.
fn pay(order: PlacedOrder, payment_id: String) -> Result<PaidOrder, OrderError> {
    Ok(PaidOrder { id: order.id, customer_id: order.customer_id, payment_id })
}

fn fulfill(order: PaidOrder, tracking_number: String) -> Result<FulfilledOrder, OrderError> {
    Ok(FulfilledOrder {
        id: order.id,
        customer_id: order.customer_id,
        payment_id: order.payment_id,
        tracking_number,
    })
}

// fulfill(cart_order, "TRK-1".into()) is a compile error: expected PaidOrder, found CartOrder.
```

## Why This Matters More Than It Looks

The "before" version's bugs are the kind that ship to production and get discovered by a customer, not a compiler: a shipped-but-unpaid order, a refund on a cancelled order, a tracking email sent with no tracking number. The "after" version turns every one of those into "this code does not compile" — the earliest, cheapest place to catch a bug. This is the concrete payoff of technique 2 (illegal states unrepresentable), built on technique 1 (ADTs), guarded by technique 3 (exhaustive matching) as new states get added, and composed via technique 8 (workflows as functions) end to end.
