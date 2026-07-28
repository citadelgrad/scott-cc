---
description: >-
  Code examples for removing duplicate Python code: extracting shared functions,
  decorators, base classes, parameterized queries, and context managers.
metadata:
  tags: [python, DRY, deduplication, refactoring, patterns]
---

# Deduplication Patterns

## Extract Shared Functions

```python
# Before - duplicated in multiple modules
# users/views.py
def format_date(date):
    return date.strftime("%B %d, %Y")

# orders/views.py
def format_date(date):
    return date.strftime("%B %d, %Y")

# After - extract to shared helper
# utils/formatting.py
def format_date(date):
    return date.strftime("%B %d, %Y")

# Then import where needed
from utils.formatting import format_date
```

## Extract Common Patterns with Decorators

```python
# Before - repeated validation in every route
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user

@app.get("/orders/{order_id}")
async def get_order(order_id: int):
    order = await Order.get(order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    return order

# After - extract to dependency or decorator
async def get_or_404(model, id: int, name: str = "Resource"):
    instance = await model.get(id)
    if not instance:
        raise HTTPException(404, f"{name} not found")
    return instance

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    return await get_or_404(User, user_id, "User")
```

## Extract Base Classes

```python
# Before - repeated CRUD in every service
class UserService:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        return self.db.query(User).all()

    def get_by_id(self, id):
        return self.db.query(User).filter(User.id == id).first()

    def create(self, data):
        instance = User(**data)
        self.db.add(instance)
        self.db.commit()
        return instance

class OrderService:
    # Same methods duplicated...

# After - extract base class
class BaseService:
    model = None

    def __init__(self, db):
        self.db = db

    def get_all(self):
        return self.db.query(self.model).all()

    def get_by_id(self, id):
        return self.db.query(self.model).filter(self.model.id == id).first()

    def create(self, data):
        instance = self.model(**data)
        self.db.add(instance)
        self.db.commit()
        return instance

class UserService(BaseService):
    model = User

class OrderService(BaseService):
    model = Order
```

## Consolidate Similar Queries

```python
# Before - separate functions doing similar things
def list_active_users():
    return db.query(User).filter(User.active == True).order_by(User.name).all()

def list_inactive_users():
    return db.query(User).filter(User.active == False).order_by(User.name).all()

# After - parameterized function
def list_users(*, active: bool | None = None):
    query = db.query(User)
    if active is not None:
        query = query.filter(User.active == active)
    return query.order_by(User.name).all()
```

## Use Context Managers for Resource Patterns

```python
# Before - repeated setup/teardown
def process_file_a(path):
    f = open(path)
    try:
        data = f.read()
        # process data
    finally:
        f.close()

# After - use context manager
def process_file_a(path):
    with open(path) as f:
        data = f.read()
        # process data

# Or extract common pattern
from contextlib import contextmanager

@contextmanager
def read_file_data(path):
    with open(path) as f:
        yield f.read()
```
