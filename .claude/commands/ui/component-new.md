---
description: Create a new component with type safety and modern best practices
model: claude-sonnet-4-5
---

Generate a new component following modern best practices.

## Component Specification

$ARGUMENTS

## Modern Component Standards

### 1. **Component Structure**
- Use function components (not class components, where applicable)
- Follow framework conventions (React, Vue, Angular, Svelte, etc.)
- Server Components where appropriate (Next.js, SvelteKit, etc.)

### 2. **Type Safety Best Practices**
- Strict typing where available (TypeScript, Python type hints, etc.)
- Interface/type definitions for props
- Proper utility types (where applicable)
- NO `any`/untyped data structures
- Explicit return types for complex components

### 3. **Component Patterns**

**Client Components** (interactive, use hooks/state)
```typescript
// React example
'use client'
import { useState } from 'react'

interface Props {
  // typed props
}

export function Component({ }: Props) {
  // implementation
}
```

**Server Components** (default in Next.js App Router, SvelteKit, etc.)
```typescript
// Next.js example
interface Props {
  // typed props
}

export async function Component({ }: Props) {
  // can fetch data directly
}
```

**Vue Example**
```vue
<script setup lang="ts">
interface Props {
  // typed props
}

const props = defineProps<Props>()
</script>
```

### 4. **State Management**
- Local state: `useState` (React), `ref`/`reactive` (Vue), etc.
- Global state: Zustand, Redux (React), Pinia (Vue), etc.
- Context/Provide for theme/auth (where applicable)

### 5. **Performance**
- Lazy loading with `React.lazy()` / dynamic imports
- Code splitting
- Memoization for expensive computations
- Callback memoization where needed

### 6. **Styling Approach** (choose based on project)
- **Utility-first CSS** - Tailwind CSS, UnoCSS
- **CSS Modules** - Scoped styles
- **CSS-in-JS** - Styled Components, Emotion
- **Scoped CSS** - Vue scoped styles, Svelte styles
- **Plain CSS** - With BEM or similar methodology

## What to Generate

1. **Component File** - Main component with proper typing
2. **Props Interface** - Fully typed props/parameters
3. **Styles** - Appropriate styling approach
4. **Example Usage** - How to import and use
5. **Documentation** - Component documentation (Storybook, etc. if applicable)

## Code Quality Standards

**Structure**
- Feature-based folder organization
- Co-locate related files
- Barrel exports (index.ts/index.js) where appropriate
- Clear file naming conventions

**Type Safety** (where applicable)
- Explicit prop types via interface/type
- Proper generics where needed
- Utility types (Pick, Omit, Partial, etc. where available)
- Discriminated unions for variants

**Props**
- Required vs optional props
- Default values where appropriate
- Destructure in function signature
- Props spread carefully

**Accessibility**
- Semantic HTML
- ARIA labels where needed
- Keyboard navigation
- Screen reader friendly
- Focus management

**Best Practices**
- Single Responsibility Principle
- Composition over inheritance
- Extract complex logic to hooks/composables/utils
- Keep components small (<200 lines recommended)

## Component Types to Consider

**Presentational Components**
- Pure UI rendering
- No business logic
- Receive data via props
- Easy to test

**Container Components**
- Data fetching
- Business logic
- State management
- Pass data to presentational components

**Compound Components**
- Related components working together
- Shared context
- Flexible API
- Example: `<Select><Select.Trigger/><Select.Content/></Select>`

## Framework-Specific Features

**React**
- React 19 features: `use()`, `useActionState()`, `useFormStatus()`, `useOptimistic()`
- Server Actions for mutations
- Server Components for data fetching

**Vue**
- Composition API
- `<script setup>` syntax
- Composables for reusable logic

**Svelte**
- Reactive declarations
- Stores for state management
- Server-side rendering support

**Angular**
- Component decorators
- Dependency injection
- RxJS for reactive programming

Generate production-ready, accessible, and performant components following your chosen framework's conventions and best practices.
