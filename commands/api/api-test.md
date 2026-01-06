---
description: Test API endpoints with automated test generation
model: claude-sonnet-4-5
---

Generate comprehensive API tests for the specified endpoint.

## Target

$ARGUMENTS

## Test Strategy for Solo Developers

Create practical, maintainable tests using modern tools:

### 1. **Testing Approach**
- Unit tests for validation logic
- Integration tests for full API flow
- Edge case coverage
- Error scenario testing
- Performance testing where applicable

### 2. **Tools** (choose based on your language/framework)

**JavaScript/TypeScript**
- **Vitest** - Fast, modern (recommended for new projects)
- **Jest** - Established, widely used
- **Supertest** - HTTP assertions
- **MSW** - API mocking

**Python**
- **pytest** - Modern, feature-rich
- **unittest** - Standard library
- **httpx** - Async HTTP client for testing
- **responses** - Mocking library

**Go**
- **testing** - Standard library
- **testify** - Assertions and mocks
- **httptest** - HTTP testing utilities

**Rust**
- **cargo test** - Built-in testing
- **reqwest** - HTTP client for integration tests
- **mockito** - HTTP mocking

**Other Languages**
- Use idiomatic testing frameworks for your language
- Choose HTTP client libraries that support testing
- Consider mocking libraries for external dependencies

### 3. **Test Coverage**

**Happy Paths**
- Valid inputs return expected results
- Proper status codes (200, 201, etc.)
- Correct response structure
- Expected data transformations

**Error Paths**
- Invalid input validation
- Authentication failures (401)
- Authorization failures (403)
- Rate limiting (429)
- Server errors (500)
- Missing required fields
- Invalid data types

**Edge Cases**
- Empty requests
- Malformed JSON/XML
- Large payloads
- Special characters and encoding
- SQL injection attempts
- XSS attempts
- Boundary value testing

### 4. **Test Structure**

**JavaScript/TypeScript Example:**
```typescript
describe('API Endpoint', () => {
  describe('Success Cases', () => {
    it('should handle valid request', () => {})
    it('should return correct status code', () => {})
  })

  describe('Validation', () => {
    it('should reject invalid input', () => {})
    it('should validate required fields', () => {})
  })

  describe('Error Handling', () => {
    it('should handle server errors', () => {})
    it('should return proper error format', () => {})
  })
})
```

**Python Example:**
```python
class TestAPIEndpoint:
    class TestSuccessCases:
        def test_valid_request(self):
            pass
        
        def test_correct_status_code(self):
            pass
    
    class TestValidation:
        def test_reject_invalid_input(self):
            pass
        
        def test_validate_required_fields(self):
            pass
    
    class TestErrorHandling:
        def test_handle_server_errors(self):
            pass
        
        def test_proper_error_format(self):
            pass
```

**Go Example:**
```go
func TestAPIEndpoint(t *testing.T) {
    t.Run("SuccessCases", func(t *testing.T) {
        t.Run("ValidRequest", func(t *testing.T) {})
        t.Run("CorrectStatusCode", func(t *testing.T) {})
    })
    
    t.Run("Validation", func(t *testing.T) {
        t.Run("RejectInvalidInput", func(t *testing.T) {})
    })
})
```

### 5. **What to Generate**

1. **Test File** - Complete test suite with all scenarios
2. **Mock Data** - Realistic test fixtures
3. **Helper Functions** - Reusable test utilities
4. **Setup/Teardown** - Database/state management
5. **Test Runner Script** - Command to run tests (make, npm, pytest, go test, etc.)

## Key Testing Principles

- Test behavior, not implementation
- Clear, descriptive test names
- Arrange-Act-Assert pattern (or Given-When-Then)
- Independent tests (no shared state)
- Fast execution (<5s for unit tests)
- Realistic mock data
- Test error messages and formats
- Don't test framework internals
- Don't mock what you don't own
- Avoid brittle tests
- Use test fixtures for consistency
- Clean up after tests (database, files, etc.)

## Additional Scenarios to Cover

1. **Authentication/Authorization**
   - Valid tokens/credentials
   - Expired tokens
   - Missing tokens
   - Invalid tokens
   - Invalid permissions
   - Role-based access

2. **Data Validation**
   - Type mismatches
   - Out of range values
   - SQL/NoSQL injection attempts
   - XSS payloads
   - Path traversal attempts
   - Command injection attempts

3. **Rate Limiting**
   - Within limits
   - Exceeding limits
   - Reset behavior
   - Different user/IP limits

4. **Performance**
   - Response times
   - Large dataset handling
   - Concurrent requests
   - Timeout handling

5. **Integration Points**
   - External API calls (mocked)
   - Database operations
   - File system operations
   - Cache interactions

Generate production-ready tests that can be run immediately with your project's standard test command (npm test, pytest, go test, cargo test, etc.).
