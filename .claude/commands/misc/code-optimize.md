---
description: Analyze and optimize code for performance, memory, and efficiency
model: claude-sonnet-4-5
---

Optimize the following code for performance and efficiency.

## Code to Optimize

$ARGUMENTS

## Optimization Strategy for Solo Developers

### 1. **Profiling First**
- Identify actual bottlenecks
- Don't optimize prematurely
- Measure before and after
- Focus on high-impact areas
- Use appropriate profiling tools for your language

### 2. **Performance Optimization Areas**

**Frontend Frameworks** (React, Vue, Angular, etc.)
- Memoization (React.memo, useMemo, useCallback, computed properties)
- Code splitting and lazy loading
- Image optimization
- Font optimization
- Remove unnecessary re-renders
- Virtual scrolling for long lists
- Component-level optimizations

**Database Queries**
- Add indexes for frequently queried fields
- Batch queries (reduce N+1 problems)
- Use select to limit fields
- Implement pagination
- Cache frequent queries
- Use database views for complex joins
- Optimize query plans

**API Calls**
- Implement caching (appropriate for your framework)
- Debounce/throttle requests
- Parallel requests where possible
- Request deduplication
- Optimistic updates
- Connection pooling

**Bundle Size** (for compiled/bundled languages)
- Tree-shaking unused code
- Dynamic imports for large libraries
- Replace heavy dependencies
- Code splitting by route/feature
- Lazy load below-the-fold content

**Memory**
- Fix memory leaks (cleanup resources, event listeners)
- Avoid unnecessary object creation
- Use const/immutable for non-changing values
- Clear intervals/timeouts
- Remove event listeners
- Proper resource disposal (files, connections, etc.)

### 3. **Optimization Checklist**

**General Optimizations**
- Use appropriate data structures (Map/Set for lookups, arrays for sequences)
- Minimize expensive operations in loops
- Cache expensive calculations
- Debounce/throttle expensive operations
- Use appropriate algorithms (O(n log n) vs O(n²))

**Framework-Specific** (adapt to your framework)
- Memo components that render often
- Move static values outside components/functions
- Use keys properly in lists (React, Vue, etc.)
- Avoid inline functions in render
- Lazy load routes and components
- Use server-side rendering where beneficial

**Database**
- Add indexes on foreign keys and frequently queried columns
- Use prepared statements/parameterized queries
- Batch inserts/updates
- Implement connection pooling
- Cache expensive queries
- Normalize/denormalize appropriately

**Network**
- Compress responses (gzip/brotli)
- Use CDN for static assets
- Implement HTTP/2 or HTTP/3
- Set proper cache headers
- Minimize payload size
- Use appropriate serialization formats

### 4. **Measurement Tools**

**Frontend**
- Browser DevTools Performance tab
- Lighthouse CI
- Framework-specific profilers (React DevTools, Vue DevTools)
- Bundle analyzers

**Backend**
- Language-specific profilers (cProfile for Python, pprof for Go, etc.)
- Database query analyzer
- APM tools (DataDog, New Relic, etc.)
- Load testing (k6, Artillery, wrk, etc.)

**General**
- Memory profilers
- CPU profilers
- Network analyzers

### 5. **Common Optimizations**

**Replace inefficient iterations**
```python
# Before: Multiple iterations
result = sum(x * 2 for x in filter(lambda x: x > 0, arr))

# After: Single iteration (if more readable)
result = sum(x * 2 for x in arr if x > 0)
```

**Memoize expensive calculations**
```python
# Python example with functools.lru_cache
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_calculation(n):
    # complex calculation
    return result
```

```javascript
// JavaScript/React example
const expensiveValue = useMemo(() => {
  return complexCalculation(props.data)
}, [props.data])
```

**Use appropriate data structures**
```python
# Before: List lookup O(n)
if item in list:  # Slow for large lists

# After: Set lookup O(1)
if item in set:  # Fast lookup
```

**Virtual scrolling for long lists** (where applicable)
- Only render visible items
- Use libraries appropriate for your framework
- Implement pagination as alternative

## Output Format

1. **Analysis** - Identify performance bottlenecks
2. **Optimized Code** - Improved version
3. **Explanation** - What changed and why
4. **Benchmarks** - Expected performance improvement (if measurable)
5. **Trade-offs** - Any complexity added
6. **Next Steps** - Further optimization opportunities

Focus on practical, measurable optimizations that provide real user value. Don't sacrifice readability for micro-optimizations. Use profiling data to guide optimizations rather than guessing.
