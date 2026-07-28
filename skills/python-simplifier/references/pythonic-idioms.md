---
description: >-
  Python-specific simplification patterns: comprehensions, builtins, walrus
  operator, unpacking, f-strings, dataclasses, and enums.
metadata:
  tags: [python, idioms, comprehensions, dataclasses, enums, PEP8]
---

# Pythonic Idioms

## List Comprehensions

```python
# Before
result = []
for x in items:
    if x > 0:
        result.append(x * 2)

# After
result = [x * 2 for x in items if x > 0]
```

## Dictionary Comprehensions

```python
# Before
user_map = {}
for user in users:
    user_map[user.id] = user.name

# After
user_map = {user.id: user.name for user in users}
```

## Use `any()` and `all()`

```python
# Before
has_admin = False
for user in users:
    if user.is_admin:
        has_admin = True
        break

# After
has_admin = any(user.is_admin for user in users)
```

## Walrus Operator (Python 3.8+)

```python
# Before
match = pattern.search(text)
if match:
    process(match.group())

# After
if match := pattern.search(text):
    process(match.group())
```

## Use `get()` for Dictionaries

```python
# Before
if "key" in data:
    value = data["key"]
else:
    value = default

# After
value = data.get("key", default)
```

## Unpacking

```python
# Before
first = items[0]
rest = items[1:]

# After
first, *rest = items

# Before
x = point[0]
y = point[1]

# After
x, y = point
```

## F-strings

```python
# Before
message = "Hello, " + name + "! You have " + str(count) + " messages."
message = "Hello, {}! You have {} messages.".format(name, count)

# After
message = f"Hello, {name}! You have {count} messages."
```

## Use `dataclasses` or Pydantic

```python
# Before
class User:
    def __init__(self, name, email, age):
        self.name = name
        self.email = email
        self.age = age

    def __repr__(self):
        return f"User(name={self.name!r}, email={self.email!r}, age={self.age!r})"

    def __eq__(self, other):
        return (self.name, self.email, self.age) == (other.name, other.email, other.age)

# After - dataclass
from dataclasses import dataclass

@dataclass
class User:
    name: str
    email: str
    age: int

# After - Pydantic (if validation needed)
from pydantic import BaseModel, EmailStr

class User(BaseModel):
    name: str
    email: EmailStr
    age: int
```

## Enum Instead of String Constants

```python
# Before
STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"

def process(status: str):
    if status == STATUS_PENDING:
        ...

# After
from enum import Enum, auto

class Status(Enum):
    PENDING = auto()
    APPROVED = auto()
    REJECTED = auto()

def process(status: Status):
    if status == Status.PENDING:
        ...
```
