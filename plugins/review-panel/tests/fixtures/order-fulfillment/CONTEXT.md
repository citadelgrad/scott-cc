# Context: Order Fulfillment

This is a minimal `CONTEXT.md` fixture used only by
`plugins/review-panel/tests/PRESSURE-TEST.md` to exercise the Domain-Intent /
coherence axis (RE-REVIEW Axis (b) in `references/fix-and-rereview.md`). It is not part of any
real application — do not wire it into build tooling.

## Glossary

- **fulfillment**: the process of preparing and releasing a paid order to the customer, from
  payment confirmation through carrier hand-off. This module's public functions and variable
  names use `fulfillment` consistently as the domain term for this whole process.
- **shipping**: strictly the carrier-facing sub-step of fulfillment (label purchase + hand-off).
  `shipping` is a narrower term than `fulfillment` and must not be used interchangeably with it —
  a function that does more than carrier hand-off (e.g. validates payment, retries against the
  warehouse system) is a `fulfillment` operation, not a `shipping` operation.
- **attempt budget**: the number of times `processFulfillment` may retry the warehouse call
  before giving up and marking the order failed. Defined as `MAX_ATTEMPTS`.

## Decision log

- 2026-05-02: Chose `fulfillment` over `shipping` as the primary domain term for this module
  because the workflow includes payment-token validation and warehouse retries, not just the
  carrier hand-off step. `shipping` is reserved for the narrower carrier sub-step only.
