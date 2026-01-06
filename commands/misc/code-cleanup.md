---
description: Refactor and clean up code following best practices
model: claude-sonnet-4-5
---

Clean up and refactor the following code to improve readability, maintainability, and follow best practices.

## Code to Clean

$ARGUMENTS

## Cleanup Checklist for Solo Developers

### 1. **Code Smells to Fix**

**Naming**
- Descriptive variable/function names
- Consistent naming conventions (camelCase, PascalCase, snake_case, kebab-case - follow your language's conventions)
- Avoid abbreviations unless obvious
- Boolean names start with is/has/can/should (or appropriate prefix for your language)

**Functions**
- Single responsibility per function
- Keep functions small (<50 lines, adjust for your language)
- Reduce parameters (max 3-4, use parameter objects/structs if needed)
- Extract complex logic
- Avoid side effects where possible

**DRY (Don't Repeat Yourself)**
- Extract repeated code to utilities
- Create reusable components/modules
- Use generics/templates for type reuse (where supported)
- Centralize constants/configuration

**Complexity**
- Reduce nested if statements
- Replace complex conditions with functions
- Use early returns/guard clauses
- Simplify boolean logic

**Type Safety** (where applicable)
- Remove `any`/untyped data structures
- Add proper type annotations
- Use interfaces/structs for object shapes
- Leverage utility types (Pick, Omit, Partial, etc. where available)

### 2. **Modern Patterns to Apply**

**General Patterns** (adapt to your language)
```python
# Python example: Use context managers
with open('file.txt') as f:
    content = f.read()

# Python example: Use comprehensions
filtered = [x for x in items if x.active]
```

```javascript
// JavaScript/TypeScript: Use optional chaining
const value = obj?.prop?.nested

// Use nullish coalescing
const result = value ?? defaultValue

// Use destructuring
const { name, email } = user

// Use template literals
const message = `Hello, ${name}!`
```

```rust
// Rust: Use pattern matching
match value {
    Some(x) => println!("{}", x),
    None => println!("No value"),
}

// Use Result for error handling
let result = operation()?;
```

**Framework-Specific Patterns**

**React/Component Frameworks**
- Extract custom hooks/composable functions
- Use proper TypeScript/types for props
- Avoid prop drilling with composition/context
- Keep components small and focused

**Backend Frameworks**
- Use dependency injection
- Separate business logic from framework code
- Use middleware/plugins appropriately
- Follow framework conventions

### 3. **Refactoring Techniques**

**Extract Function**
```python
# Before: Long function
def process():
    # 50 lines of code

# After: Broken into smaller functions
def validate():
    pass

def transform():
    pass

def save():
    pass

def process():
    validate()
    data = transform()
    save(data)
```

**Replace Conditional with Polymorphism/Strategy**
```python
# Before: Multiple conditionals
if type == 'A':
    return process_a()
elif type == 'B':
    return process_b()

# After: Strategy pattern
processors = {
    'A': process_a,
    'B': process_b
}
return processors[type]()
```

**Introduce Parameter Object**
```python
# Before: Many parameters
def create(name, email, age, address):
    pass

# After: Parameter object
class UserData:
    def __init__(self, name, email, age, address):
        self.name = name
        self.email = email
        self.age = age
        self.address = address

def create(user_data: UserData):
    pass
```

### 4. **Common Cleanup Tasks**

**Remove Dead Code**
- Unused imports
- Unreachable code
- Commented out code
- Unused variables
- Unused functions/methods

**Improve Error Handling**
```python
# Before: Generic catch
try:
    do_something()
except:
    print("Error")

# After: Specific error handling
try:
    do_something()
except ValidationError as e:
    handle_validation(e)
except Exception as e:
    logger.error('Unexpected error', exc_info=e)
    raise
```

**Consistent Formatting**
- Proper indentation
- Consistent quotes (follow language conventions)
- Line length (<100 characters recommended)
- Organized imports (alphabetical, grouped by source)

**Better Comments**
- Remove obvious comments
- Add why, not what
- Document complex logic
- Update outdated comments
- Use docstrings/documentation comments where appropriate

### 5. **Framework-Specific Considerations**

**Server vs Client Components** (Next.js/React Server Components)
- Move state to client component
- Keep data fetching in server component
- Use appropriate directives ('use client', etc.)

**Proper Data Fetching** (adapt to your framework)
- Use appropriate data fetching patterns
- Implement caching where beneficial
- Handle loading and error states
- Use framework-recommended patterns

## Output Format

1. **Issues Found** - List of code smells and problems
2. **Cleaned Code** - Refactored version
3. **Explanations** - What changed and why
4. **Before/After Comparison** - Side-by-side if helpful
5. **Further Improvements** - Optional enhancements

Focus on practical improvements that make code more maintainable without over-engineering. Balance clean code with pragmatism, following the conventions and best practices of your chosen language and framework.
