---
description: Add authentication, authorization, and security to API endpoints
model: claude-sonnet-4-5
---

Add comprehensive security, authentication, and authorization to the specified API route.

## Target API Route

$ARGUMENTS

## Security Layers to Implement

### 1. **Authentication** (Who are you?)
- Verify user identity
- Token validation (JWT, session, API keys, OAuth)
- Handle expired/invalid tokens
- Secure token storage and transmission

### 2. **Authorization** (What can you do?)
- Role-based access control (RBAC)
- Resource-level permissions
- Check user ownership
- Attribute-based access control (ABAC) where appropriate

### 3. **Input Validation**
- Sanitize all inputs
- SQL/NoSQL injection prevention
- XSS prevention
- Type validation using your chosen validation library
- Parameterized queries/prepared statements

### 4. **Rate Limiting**
- Prevent abuse and DoS attacks
- Per-user/IP limits
- Sliding window or token bucket algorithm
- Configurable thresholds

### 5. **CORS** (if needed)
- Whitelist allowed origins
- Proper headers configuration
- Credentials handling
- Preflight request handling

## Implementation Approach

### Authentication Methods

**JWT-based Authentication**
- Verify token signature
- Validate expiration and claims
- Check token revocation (if applicable)
- Use secure algorithms (HS256, RS256)

**Session-based Authentication**
- Secure session storage
- Session expiration handling
- CSRF protection
- Secure cookie configuration

**API Key Authentication**
- Secure key storage
- Key rotation support
- Scope-based permissions
- Rate limiting per key

**OAuth/OIDC Integration**
- Use established libraries for your language
- Validate tokens from identity providers
- Handle refresh tokens
- Secure callback handling

### Framework-Specific Patterns

**For Database-as-a-Service (Supabase, Firebase, etc.)**
- Use built-in authentication features
- Leverage row-level security (RLS) policies
- Service role keys for admin operations
- Client-side auth state management

**For Framework Auth Libraries**
- Use established auth middleware/plugins
- Follow framework conventions
- Integrate with existing user models
- Leverage built-in session management

**For Custom Auth**
- Implement JWT validation
- Verify tokens and decode claims
- Check expiration and signature
- Validate user state

## Security Checklist

**Authentication**
- Verify authentication tokens/credentials
- Handle missing/invalid tokens (401 Unauthorized)
- Check token expiration
- Secure token storage recommendations
- Implement token refresh where applicable

**Authorization**
- Check user roles/permissions (403 Forbidden)
- Verify resource ownership
- Implement least privilege principle
- Log authorization failures
- Handle permission inheritance

**Input Validation**
- Validate all inputs with your chosen validation library
- Sanitize SQL/NoSQL inputs
- Escape special characters
- Limit payload sizes
- Validate file uploads (if applicable)

**Rate Limiting**
- Per-user limits
- Per-IP limits
- Per-endpoint limits
- Clear error messages (429 Too Many Requests)
- Retry-After headers

**CORS**
- Whitelist specific origins
- Handle preflight requests
- Secure credentials handling
- Appropriate headers configuration

**Error Handling**
- Don't expose stack traces in production
- Generic error messages for users
- Log detailed errors server-side
- Consistent error format
- Don't leak sensitive information

**Logging & Monitoring**
- Log authentication attempts
- Log authorization failures
- Track suspicious activity
- Monitor rate limit hits
- Alert on security events

## What to Generate

1. **Protected Route Handler** - Secured version of the API route
2. **Middleware/Utilities** - Reusable auth helpers and middleware
3. **Type Definitions** - User, permissions, roles (types/interfaces/models)
4. **Error Responses** - Standardized auth error responses
5. **Usage Examples** - Client-side integration examples

## Common Patterns for Solo Developers

**Pattern 1: Simple Token Auth**
```python
# For internal tools, admin panels
# Python example
token = request.headers.get('Authorization')
if token != os.getenv('ADMIN_TOKEN'):
    return {'error': 'Unauthorized'}, 401
```

```javascript
// JavaScript/TypeScript example
const token = request.headers.get('authorization')
if (token !== process.env.ADMIN_TOKEN) {
  return new Response('Unauthorized', { status: 401 })
}
```

**Pattern 2: User-based Auth**
```python
# Python example
user = get_current_user(request)
if not user:
    return {'error': 'Unauthorized'}, 401
```

```javascript
// JavaScript/TypeScript example
const user = await getCurrentUser(request)
if (!user) {
  return new Response('Unauthorized', { status: 401 })
}
```

**Pattern 3: Role-based Auth**
```python
# Python example
user = get_current_user(request)
if not user or not has_role(user, 'admin'):
    return {'error': 'Forbidden'}, 403
```

```javascript
// JavaScript/TypeScript example
const user = await getCurrentUser(request)
if (!user || !hasRole(user, 'admin')) {
  return new Response('Forbidden', { status: 403 })
}
```

Generate production-ready, secure code that follows the principle of least privilege and uses the conventions of your chosen language and framework.
