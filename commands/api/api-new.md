---
description: Create a new route with validation, error handling, and type safety
model: claude-sonnet-4-5
---

Create a new route following modern best practices for solo developers.

## Requirements

API Endpoint: $ARGUMENTS

## Implementation Guidelines

### 1. **Framework Structure**
- Follow the conventions of your chosen framework (Express, FastAPI, Next.js, etc.)
- Organize routes in a clear directory structure
- Use appropriate file naming conventions for your stack

### 2. **Validation**
- Use runtime validation libraries appropriate for your language:
  - JavaScript/TypeScript: Zod, Joi, Yup, class-validator
  - Python: Pydantic, Marshmallow, Cerberus
  - Go: go-playground/validator, ozzo-validation
  - Rust: validator, serde with validation
  - Other: Choose idiomatic validation for your language
- Validate input early (before DB/API calls)
- Return clear validation error messages with field-level details

### 3. **Error Handling**
- Global error handling (try/catch, error middleware, exception handlers)
- Consistent error response format across all endpoints
- Appropriate HTTP status codes
- Never expose sensitive error details (stack traces, internal paths, etc.)
- Log errors server-side for debugging

### 4. **Type Safety**
- Use strong typing where available (TypeScript, Python type hints, Go types, Rust types)
- Strict typing for requests/responses
- Shared type/interface definitions
- Avoid `any` types or untyped data structures
- If using a dynamically typed language, use validation schemas as contracts

### 5. **Security**
- Input sanitization and escaping
- CORS configuration if needed
- Rate limiting considerations
- Authentication/authorization checks
- SQL injection prevention (parameterized queries)
- XSS prevention
- CSRF protection where applicable

### 6. **Response Format**
Use a consistent response structure:
```json
// Success
{
  "data": <response_data>,
  "success": true
}

// Error
{
  "error": "Error message",
  "details": <optional_details>,
  "success": false
}
```

## Code Structure

Create a complete API route with:

1. **Route Handler File** - Main endpoint implementation following your framework's conventions
2. **Validation Schema** - Request/response validation schemas using your chosen library
3. **Type Definitions** - Shared types/interfaces/models for requests and responses
4. **Error Handler** - Centralized error handling middleware/utility
5. **Example Usage** - Client-side example (curl, fetch, requests, etc.)

## Best Practices to Follow

- Early validation before expensive operations
- Proper HTTP status codes (200, 201, 400, 401, 403, 404, 422, 500)
- Consistent error response format across all endpoints
- Strong typing where available (strict mode, type hints, etc.)
- Minimal logic in routes (extract to services/utils/helpers)
- Environment variable validation on startup
- Request/response logging for debugging (without sensitive data)
- No sensitive data in responses (passwords, tokens, internal IDs)
- No database queries without validation
- No inline business logic (extract to services/business layer)
- Proper async/await or promise handling
- Timeout handling for external API calls
- Idempotency considerations for POST/PUT operations where appropriate

Generate production-ready code that follows the conventions and best practices of your chosen language and framework.
