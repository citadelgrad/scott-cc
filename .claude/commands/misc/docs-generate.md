---
description: Generate documentation for code, APIs, and components
model: claude-sonnet-4-5
---

Generate comprehensive documentation for the following code.

## Code to Document

$ARGUMENTS

## Documentation Strategy for Solo Developers

### 1. **Documentation Types**

**Code Documentation**
- Function/method descriptions
- Parameter descriptions
- Return types and values
- Usage examples
- Exception/error documentation
- Use appropriate docstring/documentation comment format for your language

**API Documentation**
- Endpoint descriptions
- Request/response formats
- Authentication requirements
- Error codes
- Examples with curl/fetch/requests/etc.

**Component Documentation** (for component-based frameworks)
- Props/parameters interface
- Usage examples
- Visual examples (if applicable)
- Accessibility notes

**README Documentation**
- Project overview
- Setup instructions
- Environment variables
- Available scripts/commands
- Deployment guide

### 2. **Documentation Comment Formats**

**Python (docstrings)**
```python
def fetch_user_data(user_id: str, options: dict = None) -> dict:
    """
    Fetches user data from the database.
    
    Args:
        user_id: The unique identifier for the user
        options: Optional fetch parameters (default: None)
    
    Returns:
        Dictionary containing user data
    
    Raises:
        NotFoundError: When user doesn't exist
        DatabaseError: When database query fails
    
    Example:
        >>> user = fetch_user_data('123', {'include_profile': True})
        >>> print(user['email'])
    """
    pass
```

**JavaScript/TypeScript (JSDoc/TSDoc)**
```typescript
/**
 * Fetches user data from the database
 *
 * @param userId - The unique identifier for the user
 * @param options - Optional fetch parameters
 * @returns Promise resolving to user data
 * @throws {NotFoundError} When user doesn't exist
 * @throws {DatabaseError} When database query fails
 *
 * @example
 * ```typescript
 * const user = await getUser('123', { includeProfile: true })
 * console.log(user.email)
 * ```
 */
async function getUser(
  userId: string,
  options?: FetchOptions
): Promise<User> {
  // implementation
}
```

**Go (godoc)**
```go
// GetUser fetches user data from the database.
//
// Parameters:
//   - userId: The unique identifier for the user
//   - options: Optional fetch parameters
//
// Returns:
//   - User data and error (if any)
//
// Example:
//   user, err := GetUser("123", FetchOptions{IncludeProfile: true})
//   if err != nil {
//       log.Fatal(err)
//   }
func GetUser(userId string, options FetchOptions) (User, error) {
    // implementation
}
```

**Rust (rustdoc)**
```rust
/// Fetches user data from the database.
///
/// # Arguments
///
/// * `user_id` - The unique identifier for the user
/// * `options` - Optional fetch parameters
///
/// # Returns
///
/// Returns `Ok(User)` if successful, `Err(DatabaseError)` otherwise.
///
/// # Examples
///
/// ```rust
/// let user = get_user("123", FetchOptions::default())?;
/// println!("{}", user.email);
/// ```
pub fn get_user(user_id: &str, options: FetchOptions) -> Result<User, DatabaseError> {
    // implementation
}
```

### 3. **API Documentation**

```markdown
## POST /api/users

Create a new user account.

### Authentication
Requires valid API key in `Authorization` header.

### Request Body
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "role": "user"
}
```

### Response (201 Created)
```json
{
  "id": "user_123",
  "email": "user@example.com",
  "name": "John Doe",
  "createdAt": "2025-01-01T00:00:00Z"
}
```

### Errors
- `400` - Invalid request body
- `401` - Missing or invalid API key
- `409` - Email already exists
- `500` - Server error

### Example
```bash
curl -X POST https://api.example.com/api/users \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","name":"John Doe"}'
```
```

### 4. **Component Documentation** (for component frameworks)

```typescript
/**
 * UserCard Component
 *
 * Displays user information in a card layout with avatar,
 * name, email, and optional actions.
 *
 * @component
 * @example
 * ```tsx
 * <UserCard
 *   user={userData}
 *   onEdit={() => handleEdit(userData.id)}
 *   showActions={true}
 * />
 * ```
 */
interface UserCardProps {
  /** User data to display */
  user: User

  /** Optional callback when edit button is clicked */
  onEdit?: () => void

  /** Whether to show action buttons (default: false) */
  showActions?: boolean

  /** Additional CSS classes */
  className?: string
}
```

### 5. **README Template**

```markdown
# Project Name

Brief description of what the project does.

## Features

- Feature 1
- Feature 2
- Feature 3

## Tech Stack

- Language: [Python/JavaScript/Go/Rust/etc.]
- Framework: [Django/Express/FastAPI/etc.]
- Database: [PostgreSQL/MySQL/etc.]
- Other tools

## Getting Started

### Prerequisites

- [Language] [version]+
- Package manager (npm/pip/cargo/go/etc.)

### Installation

```bash
# Clone the repository
git clone https://github.com/username/project.git

# Install dependencies
# npm install / pip install -r requirements.txt / cargo build / etc.

# Set up environment variables
cp .env.example .env
```

### Environment Variables

```bash
DATABASE_URL=           # Database connection string
API_KEY=                # API key
```

### Development

```bash
# Start dev server (adapt to your project)
npm run dev / python manage.py runserver / cargo run / etc.

# Run tests
npm test / pytest / go test / cargo test / etc.

# Run linter
npm run lint / pylint / golangci-lint / cargo clippy / etc.
```

## Project Structure

```
app/                # Application code
components/         # Reusable components (if applicable)
lib/                # Utilities and helpers
tests/              # Test files
```

## Deployment

[Deployment instructions specific to your platform]

## License

MIT
```

### 6. **Inline Documentation Best Practices**

**Good Comments**
```python
# Cache expensive calculation for 5 minutes
cached_result = cache.get_or_set('key', expensive_calc, timeout=300)

# Retry failed requests up to 3 times with exponential backoff
result = retry(api_call, max_attempts=3, backoff='exponential')
```

**Bad Comments** (Don't document the obvious)
```python
# Set x to 5
x = 5

# Loop through items
for item in items:
    pass
```

### 7. **Auto-Generated Docs** (where applicable)

**TypeDoc** (for TypeScript projects)
```bash
npm install -D typedoc
npx typedoc --out docs src
```

**Sphinx** (for Python projects)
```bash
pip install sphinx
sphinx-quickstart
```

**godoc** (for Go projects)
```bash
godoc -http=:6060
```

**rustdoc** (for Rust projects)
```bash
cargo doc --open
```

**Storybook** (for React/Vue components)
```bash
npx storybook@latest init
npm run storybook
```

## What to Generate

1. **Documentation Comments** - For all exported/public functions/classes
2. **README Section** - Relevant project documentation
3. **API Docs** - For API routes (if applicable)
4. **Component Props** - TypeScript interface/Python dataclass with descriptions (if applicable)
5. **Usage Examples** - Real-world code examples
6. **Troubleshooting** - Common issues and solutions

Focus on documentation that helps future you (or other developers) understand and use the code quickly. Don't document the obvious. Use the documentation format appropriate for your language and framework.
