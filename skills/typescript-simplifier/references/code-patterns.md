---
description: >-
  Detailed code examples for TypeScript/JavaScript simplification patterns
  including deduplication, modern ES features, and framework-specific idioms.
metadata:
  tags: [typescript, javascript, patterns, examples, deduplication]
---

# TypeScript/JavaScript Code Patterns

## Removing Duplicate Code

### Extract Shared Functions
```typescript
// Before - duplicated in multiple modules
// users/utils.ts
function formatDate(date: Date): string {
  return date.toLocaleDateString('en-US', {
    year: 'numeric', month: 'long', day: 'numeric'
  });
}

// orders/utils.ts
function formatDate(date: Date): string {
  return date.toLocaleDateString('en-US', {
    year: 'numeric', month: 'long', day: 'numeric'
  });
}

// After - extract to shared helper
// utils/formatting.ts
export function formatDate(date: Date): string {
  return date.toLocaleDateString('en-US', {
    year: 'numeric', month: 'long', day: 'numeric'
  });
}

// Then import where needed
import { formatDate } from '@/utils/formatting';
```

### Extract Custom Hooks (React)
```typescript
// Before - repeated in multiple components
function UserList() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    fetch('/api/users')
      .then(res => res.json())
      .then(setUsers)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  // render...
}

// After - extract to custom hook
function useUsers() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    fetch('/api/users')
      .then(res => res.json())
      .then(setUsers)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  return { users, loading, error };
}

// Usage
function UserList() {
  const { users, loading, error } = useUsers();
  // render...
}
```

### Extract Generic Data Fetching
```typescript
// Before - repeated fetch pattern everywhere
async function getUsers() {
  const res = await fetch('/api/users');
  if (!res.ok) throw new Error('Failed to fetch users');
  return res.json();
}

async function getOrders() {
  const res = await fetch('/api/orders');
  if (!res.ok) throw new Error('Failed to fetch orders');
  return res.json();
}

// After - generic fetcher
async function fetcher<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch ${url}`);
  return res.json();
}

// Usage
const users = await fetcher<User[]>('/api/users');
const orders = await fetcher<Order[]>('/api/orders');
```

### Extract Base Classes/Services
```typescript
// Before - repeated CRUD in every service
class UserService {
  async getAll() {
    return prisma.user.findMany();
  }

  async getById(id: string) {
    return prisma.user.findUnique({ where: { id } });
  }

  async create(data: CreateUserDto) {
    return prisma.user.create({ data });
  }
}

// After - extract base class
class BaseService<T, CreateDto> {
  constructor(private model: any) {}

  async getAll(): Promise<T[]> {
    return this.model.findMany();
  }

  async getById(id: string): Promise<T | null> {
    return this.model.findUnique({ where: { id } });
  }

  async create(data: CreateDto): Promise<T> {
    return this.model.create({ data });
  }
}

class UserService extends BaseService<User, CreateUserDto> {
  constructor() {
    super(prisma.user);
  }
}
```

### Consolidate Similar Functions
```typescript
// Before - separate functions doing similar things
function listActiveUsers() {
  return prisma.user.findMany({
    where: { active: true },
    orderBy: { name: 'asc' }
  });
}

function listInactiveUsers() {
  return prisma.user.findMany({
    where: { active: false },
    orderBy: { name: 'asc' }
  });
}

// After - parameterized function
interface ListUsersOptions {
  active?: boolean;
}

function listUsers(options: ListUsersOptions = {}) {
  return prisma.user.findMany({
    where: options.active !== undefined ? { active: options.active } : undefined,
    orderBy: { name: 'asc' }
  });
}
```

### Extract Reusable Components
```typescript
// Before - duplicated JSX in multiple components
function UserCard({ user }: { user: User }) {
  return (
    <div className="flex items-center gap-2">
      <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white">
        {user.name[0]}
      </div>
      <span>{user.name}</span>
    </div>
  );
}

// After - extract to shared component
interface AvatarProps {
  name: string;
  size?: 'sm' | 'md' | 'lg';
}

function Avatar({ name, size = 'md' }: AvatarProps) {
  const sizeClasses = {
    sm: 'w-6 h-6 text-xs',
    md: 'w-8 h-8 text-sm',
    lg: 'w-12 h-12 text-base'
  };

  return (
    <div className={`${sizeClasses[size]} rounded-full bg-blue-500 flex items-center justify-center text-white`}>
      {name[0]}
    </div>
  );
}
```

## JavaScript/TypeScript-Specific Simplifications

### Destructuring
```typescript
// Before
const name = user.name;
const email = user.email;
const age = user.age;

// After
const { name, email, age } = user;
```

### Optional Chaining & Nullish Coalescing
```typescript
// Before
const street = user && user.address && user.address.street;
const name = user.nickname !== null && user.nickname !== undefined
  ? user.nickname
  : 'Anonymous';

// After
const street = user?.address?.street;
const name = user.nickname ?? 'Anonymous';
```

### Template Literals
```typescript
// Before
const message = 'Hello, ' + name + '! You have ' + count + ' messages.';

// After
const message = `Hello, ${name}! You have ${count} messages.`;
```

### Array Methods Over Loops
```typescript
// Before
const results = [];
for (let i = 0; i < items.length; i++) {
  if (items[i].active) {
    results.push(items[i].name);
  }
}

// After
const results = items
  .filter(item => item.active)
  .map(item => item.name);
```

### Spread Operator
```typescript
// Before
const merged = Object.assign({}, defaults, options);
const combined = arr1.concat(arr2);

// After
const merged = { ...defaults, ...options };
const combined = [...arr1, ...arr2];
```

### Async/Await Over Promises
```typescript
// Before
function fetchUser(id: string) {
  return fetch(`/api/users/${id}`)
    .then(res => res.json())
    .then(user => {
      return fetch(`/api/users/${user.id}/posts`)
        .then(res => res.json())
        .then(posts => ({ user, posts }));
    });
}

// After
async function fetchUser(id: string) {
  const userRes = await fetch(`/api/users/${id}`);
  const user = await userRes.json();

  const postsRes = await fetch(`/api/users/${user.id}/posts`);
  const posts = await postsRes.json();

  return { user, posts };
}
```

### Use `Map` and `Set` When Appropriate
```typescript
// Before - using object as map
const counts: { [key: string]: number } = {};
items.forEach(item => {
  counts[item.category] = (counts[item.category] || 0) + 1;
});

// After - using Map (better for dynamic keys)
const counts = new Map<string, number>();
items.forEach(item => {
  counts.set(item.category, (counts.get(item.category) || 0) + 1);
});
```

### Type Guards
```typescript
// Before
function process(value: string | number) {
  if (typeof value === 'string') {
    return value.toUpperCase();
  } else {
    return value * 2;
  }
}

// After - with type guard for complex types
function isDog(animal: Dog | Cat): animal is Dog {
  return 'bark' in animal;
}
```

### Enums and Union Types
```typescript
// Before - string constants
const STATUS_PENDING = 'pending';
const STATUS_APPROVED = 'approved';
const STATUS_REJECTED = 'rejected';

// After - union type (preferred for most cases)
type Status = 'pending' | 'approved' | 'rejected';
```
