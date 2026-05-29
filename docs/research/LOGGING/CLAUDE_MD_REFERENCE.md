## Logging Best Practices Reference

Based on [loggingsucks.com](https://loggingsucks.com/) by Boris Tane.

### Core Philosophy

**Traditional logging is broken.** Stop logging what your code is doing. Start logging what happened to this request.

Instead of scattering 13+ log lines per request across your codebase, emit **ONE comprehensive wide event per request per service** that contains all the context you'll need for debugging.

### The Problem with Traditional Logging

- **Optimized for writing, not querying** - `console.log()` is easy to write, impossible to query
- **No structure or relationships** - grep can't understand that `user-123`, `user_id=user-123`, and `{"userId": "user-123"}` are the same thing
- **Cannot correlate across services** - you're playing detective at 2am with scattered breadcrumbs
- **Missing context** - when checkout fails, you need to know: subscription tier, feature flags, account age, payment provider, attempt number, cart value

### The Solution: Wide Events (Canonical Log Lines)

**Wide events** = One comprehensive event per request with 50+ fields capturing everything you might need.

Key characteristics:
- **High dimensionality** - many fields (50+)
- **High cardinality** - include user IDs, order IDs, session IDs (the fields that make debugging actually possible)
- **Business context** - subscription tier, account age, lifetime value, feature flags, A/B test variants
- **Complete error context** - error type, code, retriability, provider-specific decline codes

### Implementation Pattern

```python
# 1. Initialize wide event in middleware
@app.middleware("http")
async def wide_event_middleware(request: Request, call_next):
    event = {
        "request_id": request.headers.get("x-request-id"),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "method": request.method,
        "path": request.url.path,
        "service": os.getenv("SERVICE_NAME"),
        "version": os.getenv("SERVICE_VERSION"),
    }
    
    # Store in context for handlers to enrich
    wide_event_var.set(event)
    
    try:
        response = await call_next(request)
        event["status_code"] = response.status_code
        event["outcome"] = "success"
    except Exception as e:
        event["outcome"] = "error"
        event["error"] = {
            "type": e.__class__.__name__,
            "code": getattr(e, "code", None),
            "retriable": getattr(e, "retriable", False),
        }
        raise
    finally:
        event["duration_ms"] = int((time.time() - start_time) * 1000)
        logger.info(event)  # ONE log line with everything

# 2. Enrich in handlers with business context
@app.post("/checkout")
async def checkout(user: User):
    event = wide_event_var.get()
    
    # Add user context - HIGH VALUE
    event["user"] = {
        "id": user.id,
        "subscription": user.subscription_tier,
        "account_age_days": (datetime.utcnow() - user.created_at).days,
        "lifetime_value_cents": user.lifetime_value,
    }
    
    # Add feature flags - critical for correlating issues with rollouts
    event["feature_flags"] = {
        "new_checkout_flow": await is_enabled("new_checkout_flow", user),
        "express_payment": await is_enabled("express_payment", user),
    }
    
    # Add business metrics
    event["cart"] = {
        "total_cents": cart.total,
        "item_count": len(cart.items),
    }
```

### What to Include in Wide Events

**Infrastructure (always):**
- `request_id`, `trace_id` - correlation across services
- `timestamp`, `method`, `path`, `status_code` - HTTP basics
- `service`, `version`, `deployment_id`, `region` - deployment context
- `duration_ms` - latency

**User context (always):**
- `user.id` - **HIGH CARDINALITY** - this is what makes debugging possible
- `user.subscription` - premium users get priority
- `user.account_age_days`, `user.lifetime_value_cents` - business impact

**Business context (always):**
- Domain IDs: `order_id`, `cart_id`, `payment_id`
- Metrics: `cart.total_cents`, `discount_applied`
- **Feature flags** - which experiments were active (critical for rollout correlation)
- A/B test variants

**Error context (when errors occur):**
- `error.type`, `error.code`, `error.message`
- `error.retriable` - can the client retry?
- `error.provider_code` - third-party error codes (Stripe, AWS, etc.)

**Dependencies (when relevant):**
- `db.query_count`, `db.latency_ms`, `db.cache_hit`
- `external_api.latency_ms`, `external_api.retry_count`
- `cache.hit`, `queue.lag`

### Tail Sampling: Keeping Costs Under Control

Make sampling decisions **AFTER** the request completes, based on outcome:

```python
def should_sample(event: dict) -> bool:
    # ALWAYS keep errors - 100%
    if event.get("status_code", 200) >= 500 or event.get("error"):
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
    
    # Random sample happy, fast requests at 5%
    return random.random() < 0.05
```

### Anti-Patterns to Avoid

❌ **DON'T scatter logs:**
```python
logger.info("Processing checkout")
logger.debug(f"User {user_id} loaded")
logger.info("Calling payment API")
logger.info("Payment successful")
```

✅ **DO emit one wide event:**
```python
event = build_wide_event(request, user, cart, payment_result)
logger.info(event)
```

❌ **DON'T log strings:**
```python
logger.info(f"Payment failed for user {user_id}")
```

✅ **DO log structured data:**
```python
logger.info({"user_id": user_id, "error_code": error_code})
```

❌ **DON'T avoid high-cardinality fields:**
```python
event = {"status": "failed"}  # Useless without user_id
```

✅ **DO include high-cardinality fields:**
```python
event = {
    "user_id": "user_abc123",  # This is what makes debugging possible
    "order_id": "ord_xyz789",
    "status": "failed",
}
```

### What OpenTelemetry Does NOT Do

- ❌ Doesn't decide what to log - you must instrument deliberately
- ❌ Doesn't add business context automatically
- ❌ Doesn't fix your mental model - bad logging in OTel format is still bad

OpenTelemetry is a **delivery mechanism**, not a strategy. You still must decide what to capture.

### Querying Power

With wide events in a columnar database (ClickHouse, BigQuery), you can answer real questions:

```sql
-- All checkout failures for premium users in last hour
-- with new checkout flow enabled, grouped by error
SELECT 
    error.code,
    COUNT(*) as failures,
    AVG(duration_ms) as avg_duration
FROM wide_events
WHERE timestamp > NOW() - INTERVAL '1 hour'
  AND path = '/checkout'
  AND status_code >= 400
  AND user.subscription = 'premium'
  AND feature_flags.new_checkout_flow = true
GROUP BY error.code;
```

### The Transformation

**Before (grep):**
> "User can't checkout. Let me search 15 services hoping to find something..."

**After (query):**
> "Show me all checkout failures for premium users where new_checkout_flow was enabled, grouped by error code."

One query. Sub-second results. Root cause identified.

### Key Principles

1. **One event per request** - not 13 scattered statements
2. **High cardinality is good** - user IDs, order IDs make debugging possible
3. **Business context is critical** - subscription tier, feature flags, account age
4. **Tail sampling keeps costs down** - keep errors, sample happy paths
5. **Query, don't grep** - structured data enables analytics
6. **OpenTelemetry is delivery, not strategy** - you decide what to capture

### Resources

- Full article: https://loggingsucks.com/
- Author: Boris Tane (me@boristane.com)
- Agent skill: `npx add-skill boristane/agent-skills --skill "logging-best-practices"`
