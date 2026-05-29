# Logging Best Practices Skill

This skill implements the logging philosophy from loggingsucks.com by Boris Tane, focusing on wide events, high-cardinality data, and queryable structured logging instead of traditional string-based logging.

## Core Philosophy

**Stop logging what your code is doing. Start logging what happened to this request.**

Traditional logging is fundamentally broken for modern distributed systems. Instead of scattering 13+ log lines per request across your codebase, emit ONE comprehensive wide event per request per service that contains all the context you'll need for debugging.

## Key Concepts

### Wide Events (Canonical Log Lines)
- **One event per request per service** - not 13 scattered log statements
- **High dimensionality** - 50+ fields capturing complete context
- **High cardinality** - include user IDs, order IDs, session IDs - the fields that make debugging possible
- **Business context** - subscription tier, account age, lifetime value, feature flags
- **Complete error context** - error type, code, retriability, provider-specific codes

### Why Traditional Logging Fails
- Optimized for writing, not querying
- No understanding of structure or relationships
- Cannot correlate events across services
- Forces you to play detective with grep at 2am
- Same identifier logged 47 different ways: `user-123`, `user_id=user-123`, `{"userId": "user-123"}`

### What OpenTelemetry Does NOT Do
- Doesn't decide what to log - you still must instrument deliberately
- Doesn't add business context automatically
- Doesn't fix your mental model - bad logging in OTel format is still bad logging

## Implementation Pattern

### 1. Middleware/Context Builder Pattern

Build the event throughout the request lifecycle, emit once at the end:

```python
# Python FastAPI example
from contextvars import ContextVar
from datetime import datetime
import time
from typing import Dict, Any

wide_event_var: ContextVar[Dict[str, Any]] = ContextVar('wide_event')

@app.middleware("http")
async def wide_event_middleware(request: Request, call_next):
    start_time = time.time()
    
    # Initialize wide event with request context
    event = {
        "request_id": request.headers.get("x-request-id", str(uuid.uuid4())),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "method": request.method,
        "path": request.url.path,
        "service": os.getenv("SERVICE_NAME", "unknown"),
        "version": os.getenv("SERVICE_VERSION", "unknown"),
        "deployment_id": os.getenv("DEPLOYMENT_ID", "unknown"),
        "region": os.getenv("REGION", "unknown"),
    }
    
    # Store in context for enrichment by handlers
    wide_event_var.set(event)
    
    try:
        response = await call_next(request)
        event["status_code"] = response.status_code
        event["outcome"] = "success"
        return response
    except Exception as e:
        event["status_code"] = 500
        event["outcome"] = "error"
        event["error"] = {
            "type": e.__class__.__name__,
            "message": str(e),
            "code": getattr(e, "code", None),
            "retriable": getattr(e, "retriable", False),
        }
        raise
    finally:
        event["duration_ms"] = int((time.time() - start_time) * 1000)
        
        # Emit the wide event (structured JSON)
        logger.info(event)
```

### 2. Handler Enrichment Pattern

Enrich the event with business context as you process the request:

```python
@app.post("/checkout")
async def checkout(request: CheckoutRequest, user: User = Depends(get_current_user)):
    event = wide_event_var.get()
    
    # Add user context - HIGH VALUE
    event["user"] = {
        "id": user.id,
        "subscription": user.subscription_tier,
        "account_age_days": (datetime.utcnow() - user.created_at).days,
        "lifetime_value_cents": user.lifetime_value,
        "is_flagged": user.is_flagged,
    }
    
    # Add business context
    cart = await get_cart(user.id)
    event["cart"] = {
        "id": cart.id,
        "item_count": len(cart.items),
        "total_cents": cart.total,
        "coupon_applied": cart.coupon.code if cart.coupon else None,
        "contains_preorder": any(item.is_preorder for item in cart.items),
    }
    
    # Add feature flag context - CRITICAL for correlating issues with rollouts
    event["feature_flags"] = {
        "new_checkout_flow": await is_enabled("new_checkout_flow", user),
        "express_payment": await is_enabled("express_payment", user),
        "one_click_upsell": await is_enabled("one_click_upsell", user),
    }
    
    # Process payment and capture detailed metrics
    payment_start = time.time()
    try:
        payment_result = await payment_service.process(cart, user)
        
        event["payment"] = {
            "method": payment_result.method,
            "provider": payment_result.provider,
            "latency_ms": int((time.time() - payment_start) * 1000),
            "attempt": payment_result.attempt_number,
            "transaction_id": payment_result.transaction_id,
        }
        
        return {"order_id": payment_result.order_id}
        
    except PaymentError as e:
        # Enrich error with payment-specific context
        event["error"] = {
            "type": "PaymentError",
            "code": e.code,
            "message": str(e),
            "retriable": e.retriable,
            "provider_code": e.provider_code,
            "decline_reason": e.decline_reason,
        }
        raise
```

### 3. TypeScript/Node.js Example

```typescript
// middleware/wideEvent.ts
import { Context, Next } from 'hono';

export function wideEventMiddleware() {
  return async (ctx: Context, next: Next) => {
    const startTime = Date.now();

    const event: Record<string, unknown> = {
      request_id: ctx.get('requestId') || crypto.randomUUID(),
      timestamp: new Date().toISOString(),
      method: ctx.req.method,
      path: ctx.req.path,
      service: process.env.SERVICE_NAME,
      version: process.env.SERVICE_VERSION,
      deployment_id: process.env.DEPLOYMENT_ID,
      region: process.env.REGION,
    };

    ctx.set('wideEvent', event);

    try {
      await next();
      event.status_code = ctx.res.status;
      event.outcome = 'success';
    } catch (error: any) {
      event.status_code = 500;
      event.outcome = 'error';
      event.error = {
        type: error.name,
        message: error.message,
        code: error.code,
        retriable: error.retriable ?? false,
        stack: process.env.NODE_ENV === 'development' ? error.stack : undefined,
      };
      throw error;
    } finally {
      event.duration_ms = Date.now() - startTime;
      console.log(JSON.stringify(event)); // Use proper structured logger
    }
  };
}
```

## What to Include in Wide Events

### Always Include (Infrastructure)
- `request_id` / `trace_id` - for correlation across services
- `timestamp` - ISO 8601 format with timezone
- `method`, `path`, `status_code` - HTTP basics
- `service`, `version`, `deployment_id`, `region` - deployment context
- `duration_ms` - request latency
- `outcome` - "success" | "error" | "timeout"

### Always Include (User Context)
- `user.id` - HIGH CARDINALITY - this is what makes debugging possible
- `user.subscription` - premium users get priority
- `user.account_age_days` - context for churn analysis
- `user.lifetime_value_cents` - business impact
- `user.session_id` - for multi-request flows

### Always Include (Business Context)
- Domain-specific IDs: `order_id`, `cart_id`, `payment_id`
- Business metrics: `cart.total_cents`, `discount_applied`, `shipping_method`
- Feature flags: which experiments/features were active for this request
- A/B test variants: which variant the user saw

### Always Include (Error Context)
- `error.type` - exception class name
- `error.code` - application-specific error code
- `error.message` - human-readable description
- `error.retriable` - can the client retry?
- `error.provider_code` - third-party API error codes (Stripe, AWS, etc.)
- `error.correlation_id` - for tracing through external systems

### Include When Relevant (Dependencies)
- Database: `db.query_count`, `db.latency_ms`, `db.rows_returned`, `db.cache_hit`
- External APIs: `external_api.latency_ms`, `external_api.status_code`, `external_api.retry_count`
- Cache: `cache.hit`, `cache.key`, `cache.ttl_seconds`
- Message queue: `queue.name`, `queue.lag`, `queue.processing_time_ms`

## Tail Sampling Strategy

Keep costs manageable while never losing important events:

```python
def should_sample(event: dict) -> bool:
    """Tail sampling: decide AFTER request completes based on outcome."""
    
    # ALWAYS keep errors - 100%
    if event.get("status_code", 200) >= 500:
        return True
    if event.get("error"):
        return True
    
    # ALWAYS keep slow requests (above p99)
    if event.get("duration_ms", 0) > 2000:
        return True
    
    # ALWAYS keep VIP users
    if event.get("user", {}).get("subscription") in ["enterprise", "premium"]:
        return True
    
    # ALWAYS keep specific feature flag combinations (debugging rollouts)
    if event.get("feature_flags", {}).get("new_checkout_flow"):
        return True
    
    # ALWAYS keep high-value transactions
    if event.get("cart", {}).get("total_cents", 0) > 50000:  # $500+
        return True
    
    # Random sample the rest at 5%
    return random.random() < 0.05
```

## Anti-Patterns to Avoid

### ❌ DON'T: Scatter logs throughout request lifecycle
```python
# BAD - scattered debugging diary
logger.info("Processing checkout request")
logger.debug(f"User {user_id} cart loaded")
logger.info("Validating payment method")
logger.debug(f"Calling payment API for user {user_id}")
logger.info("Payment successful")
logger.info("Order created")
```

### ✅ DO: Build one comprehensive event
```python
# GOOD - one wide event with all context
event = build_wide_event(request, user, cart, payment_result, feature_flags)
logger.info(event)
```

### ❌ DON'T: Log strings
```python
logger.info(f"Payment failed for user {user_id} with error {error_code}")
```

### ✅ DO: Log structured data
```python
logger.info({
    "user_id": user_id,
    "error_code": error_code,
    "error_type": "PaymentError",
    "retriable": True,
})
```

### ❌ DON'T: Avoid high-cardinality fields
```python
# BAD - useless without user_id
event = {"status": "failed", "reason": "payment_declined"}
```

### ✅ DO: Include high-cardinality fields
```python
# GOOD - can actually debug specific user issues
event = {
    "user_id": "user_abc123",  # HIGH CARDINALITY
    "order_id": "ord_xyz789",  # HIGH CARDINALITY
    "status": "failed",
    "reason": "payment_declined",
}
```

## Querying Wide Events

With wide events in a proper columnar database (ClickHouse, BigQuery, etc.), you can answer real questions:

```sql
-- Show me all checkout failures for premium users in the last hour
-- where the new checkout flow was enabled, grouped by error code
SELECT 
    error.code,
    COUNT(*) as failure_count,
    AVG(duration_ms) as avg_duration,
    APPROX_PERCENTILE(duration_ms, 0.95) as p95_duration
FROM wide_events
WHERE timestamp > NOW() - INTERVAL '1 hour'
  AND path = '/checkout'
  AND status_code >= 400
  AND user.subscription = 'premium'
  AND feature_flags.new_checkout_flow = true
GROUP BY error.code
ORDER BY failure_count DESC;

-- Find slow requests that eventually succeeded
SELECT 
    request_id,
    user.id,
    duration_ms,
    db.query_count,
    external_api.latency_ms
FROM wide_events
WHERE duration_ms > 5000
  AND status_code = 200
  AND timestamp > NOW() - INTERVAL '24 hours'
ORDER BY duration_ms DESC
LIMIT 100;

-- Analyze payment failures by provider and decline reason
SELECT 
    payment.provider,
    error.provider_code,
    COUNT(*) as failures,
    COUNT(DISTINCT user.id) as affected_users,
    SUM(cart.total_cents) / 100.0 as lost_revenue_dollars
FROM wide_events
WHERE path = '/checkout'
  AND error.type = 'PaymentError'
  AND timestamp > NOW() - INTERVAL '7 days'
GROUP BY payment.provider, error.provider_code
ORDER BY lost_revenue_dollars DESC;
```

## Storage Recommendations

- **Small scale (<1M requests/day)**: PostgreSQL with JSONB columns
- **Medium scale (1M-100M requests/day)**: ClickHouse, TimescaleDB
- **Large scale (>100M requests/day)**: ClickHouse, BigQuery, or specialized observability platforms

Avoid traditional logging systems (Elasticsearch, Splunk) for high-cardinality data - they're expensive and slow for this use case.

## Migration Strategy

1. **Start with one critical path** - implement wide events for your most important endpoint (checkout, login, etc.)
2. **Run in parallel** - keep existing logs, add wide events alongside
3. **Validate queries** - ensure you can answer your most common debugging questions
4. **Expand coverage** - add wide events to more endpoints
5. **Deprecate old logs** - once wide events prove their value

## Key Takeaways

- **One event per request** - stop scattering log statements
- **High cardinality is good** - user IDs, order IDs make debugging possible
- **Business context is critical** - subscription tier, account age, feature flags
- **Tail sampling keeps costs down** - keep all errors, sample happy paths
- **Query, don't grep** - structured data enables real analytics
- **OpenTelemetry is delivery, not strategy** - you still must decide what to capture

## Resources

- Original article: https://loggingsucks.com/
- Author: Boris Tane (me@boristane.com)
- Agent skill: `npx add-skill boristane/agent-skills --skill "logging-best-practices"`
