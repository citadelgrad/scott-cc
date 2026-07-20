# PRD: Customer Self-Service Login

## §1. Background

Customers currently call support to reset their order status lookup. We want
to let them log in directly.

## §2. Scope

- Add a new `POST /api/v1/auth/login` endpoint accepting `{ email, password }`
  and returning a session token.
- Store password hashes in the existing `customers` Postgres table (new
  `password_hash` column).
- Session tokens are signed JWTs, `HS256`, stored in an httpOnly cookie,
  7-day expiry.
- A new third-party dependency, `jsonwebtoken@9`, is added to sign/verify
  tokens.
- Rate-limit login attempts per IP using the existing Redis-backed limiter.
- Add a `GET /api/v1/orders/:id` endpoint, scoped to the logged-in customer's
  own orders (ownership check against `customer_id`).

## §3. Out of scope

- Social login (Google/Apple) — future phase.
- Password reset flow — future phase, tracked separately.

## §4. Rollout

Ship behind a feature flag, 10% of traffic for the first week.
