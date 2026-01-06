---
description: Create a new page/route with modern best practices
model: claude-sonnet-4-5
---

Generate a new page/route following modern best practices.

## Page Specification

$ARGUMENTS

## Modern Page/Route Standards

### 1. **Framework Structure**
- Follow your framework's routing conventions
- Use appropriate file naming and organization
- Server-side rendering where beneficial
- Client-side routing where appropriate

### 2. **Type Safety**
- Strict typing where available (TypeScript, Python type hints, etc.)
- Type definitions for route parameters
- Type-safe data fetching
- NO `any`/untyped data structures

### 3. **Page Patterns**

**Server-Side Rendered Pages** (Next.js, SvelteKit, etc.)
```typescript
// Next.js App Router example
interface PageProps {
  params: { id: string }
  searchParams: { [key: string]: string | string[] | undefined }
}

export default async function Page({ params, searchParams }: PageProps) {
  // Fetch data
  const data = await fetchData(params.id)
  
  return (
    <div>
      {/* Page content */}
    </div>
  )
}
```

**Client-Side Rendered Pages** (React Router, Vue Router, etc.)
```typescript
// React Router example
import { useParams } from 'react-router-dom'

export function Page() {
  const { id } = useParams<{ id: string }>()
  // Component logic
  return <div>{/* Page content */}</div>
}
```

**Static Pages** (Gatsby, Next.js static, etc.)
- Pre-render at build time
- Optimize for performance
- Use appropriate data fetching methods

### 4. **Data Fetching**
- Server-side: Direct database/API calls (Next.js, SvelteKit)
- Client-side: Use appropriate data fetching libraries
- Implement caching strategies
- Handle loading and error states

### 5. **SEO and Metadata**
- Set appropriate meta tags
- Open Graph tags (if applicable)
- Structured data (if applicable)
- Proper heading hierarchy

### 6. **Performance**
- Code splitting by route
- Lazy load below-the-fold content
- Optimize images and assets
- Minimize JavaScript bundle size

## What to Generate

1. **Page File** - Main page component with proper typing
2. **Route Configuration** - If needed by framework
3. **Data Fetching Logic** - Server/client data fetching
4. **Metadata** - SEO and meta tags
5. **Example Usage** - How the page is accessed

## Code Quality Standards

**Structure**
- Follow framework conventions for file organization
- Co-locate related files (components, utilities)
- Clear file naming conventions
- Proper folder structure

**Type Safety** (where applicable)
- Type route parameters
- Type search/query parameters
- Type data fetching responses
- Use proper error types

**Data Fetching**
- Handle loading states
- Handle error states
- Implement proper error boundaries
- Use appropriate caching

**SEO**
- Semantic HTML
- Proper heading hierarchy
- Meta descriptions
- Alt text for images
- Proper link structure

**Accessibility**
- Keyboard navigation
- Screen reader support
- Focus management
- ARIA labels where needed

**Performance**
- Code splitting
- Image optimization
- Font optimization
- Minimize render blocking resources

## Framework-Specific Considerations

**Next.js**
- Use App Router or Pages Router conventions
- Server Components for data fetching
- Client Components for interactivity
- Metadata API for SEO

**SvelteKit**
- Use `+page.svelte` for pages
- `+page.server.ts` for server logic
- `+page.ts` for shared load functions
- Proper error handling with `+error.svelte`

**React Router**
- Use route components
- Proper route configuration
- Data loaders (v6.4+)
- Error boundaries

**Vue Router**
- Use route components
- Navigation guards
- Route meta fields
- Proper component structure

**Remix**
- Use route modules
- Loader functions
- Action functions
- Error boundaries

Generate production-ready pages that follow your framework's conventions, with proper SEO, accessibility, and performance optimizations.
