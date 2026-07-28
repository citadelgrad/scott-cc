---
description: >-
  Framework-specific simplification patterns for FastAPI, Django, and Flask:
  dependency injection, response models, QuerySet methods, and manager patterns.
metadata:
  tags: [python, FastAPI, Django, Flask, framework, patterns]
---

# Framework-Specific Patterns

## FastAPI - Dependency Injection

```python
# Before - repeated in every route
@app.get("/users")
async def get_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        return users
    finally:
        db.close()

# After - use dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/users")
async def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()
```

## FastAPI - Response Models

```python
# Before - manual dict construction
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email
    }

# After - Pydantic response model
class UserResponse(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    return db.query(User).filter(User.id == user_id).first()
```

## Django - QuerySet Methods

```python
# Before - filtering in Python
def get_active_premium_users():
    users = User.objects.all()
    result = []
    for user in users:
        if user.is_active and user.plan == "premium":
            result.append(user)
    return result

# After - database-level filtering
def get_active_premium_users():
    return User.objects.filter(is_active=True, plan="premium")
```

## Django - Manager Methods

```python
# Before - repeated query logic
# In views.py
users = User.objects.filter(is_active=True, created_at__gte=last_week)

# In another_view.py
users = User.objects.filter(is_active=True, created_at__gte=last_week)

# After - custom manager
class UserManager(models.Manager):
    def recent_active(self, days=7):
        cutoff = timezone.now() - timedelta(days=days)
        return self.filter(is_active=True, created_at__gte=cutoff)

class User(models.Model):
    objects = UserManager()

# Usage
users = User.objects.recent_active()
```
