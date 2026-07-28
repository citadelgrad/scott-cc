---
description: >-
  Framework-specific simplification patterns for React, Next.js, Express,
  and Node.js TypeScript/JavaScript code.
metadata:
  tags: [react, nextjs, express, nodejs, framework, patterns]
---

# Framework-Specific Simplifications

## React - Composition Over Prop Drilling
```typescript
// Before - prop drilling
function App() {
  const [user, setUser] = useState<User | null>(null);
  return <Layout user={user}><Main user={user} /></Layout>;
}

function Layout({ user, children }) {
  return <div><Header user={user} />{children}</div>;
}

function Header({ user }) {
  return <nav>{user?.name}</nav>;
}

// After - context or composition
const UserContext = createContext<User | null>(null);

function App() {
  const [user, setUser] = useState<User | null>(null);
  return (
    <UserContext.Provider value={user}>
      <Layout><Main /></Layout>
    </UserContext.Provider>
  );
}

function Header() {
  const user = useContext(UserContext);
  return <nav>{user?.name}</nav>;
}
```

## React - Memoization (When Needed)
```typescript
// Only memoize when you have performance issues
// Use useMemo for expensive calculations
const sortedItems = useMemo(
  () => items.sort((a, b) => a.name.localeCompare(b.name)),
  [items]
);
```

## Express - Middleware Extraction
```typescript
// Before - repeated validation in every route
app.post('/users', async (req, res) => {
  if (!req.body.email || !req.body.name) {
    return res.status(400).json({ error: 'Missing fields' });
  }
  // create user...
});

// After - use validation middleware (e.g., zod)
import { z } from 'zod';

const validateBody = (schema: z.ZodSchema) => (req, res, next) => {
  const result = schema.safeParse(req.body);
  if (!result.success) {
    return res.status(400).json({ error: result.error.flatten() });
  }
  req.body = result.data;
  next();
};

const createUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1)
});

app.post('/users', validateBody(createUserSchema), async (req, res) => {
  // create user with validated data...
});
```

## Next.js - Server Actions
```typescript
// Before - API route + client fetch
// pages/api/users.ts
export default async function handler(req, res) {
  const user = await prisma.user.create({ data: req.body });
  res.json(user);
}

// After - server action (Next.js 14+)
// actions/users.ts
'use server';

export async function createUser(data: CreateUserDto) {
  return prisma.user.create({ data });
}

// components/UserForm.tsx
import { createUser } from '@/actions/users';

async function onSubmit(data) {
  const user = await createUser(data);
}
```
