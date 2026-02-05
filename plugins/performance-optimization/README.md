# performance-optimization

> Performance engineering and bottleneck analysis

## What's Included

### Agents (1)
- **performance-engineer** - Optimize system performance through measurement-driven analysis and bottleneck elimination

## When to Use

**Install this if you**:
- Have performance issues (slow pages, slow APIs)
- Need to optimize critical paths
- Want to reduce resource usage
- Profile and benchmark code

**Don't install if you**:
- Performance is not a concern
- Haven't identified bottlenecks yet

## Use Cases

### 1. Performance Profiling
```
User: "Profile this API endpoint - it's taking 3 seconds"
performance-engineer: Analyzes code, identifies N+1 queries
Output: Bottleneck analysis with fixes
```

### 2. Optimization
```
User: "Optimize this data processing pipeline"
performance-engineer: Identifies algorithmic improvements
Output: Optimized code with benchmarks
```

### 3. Resource Analysis
```
User: "Why is this page using so much memory?"
performance-engineer: Analyzes memory leaks, large objects
Output: Memory optimization recommendations
```

### 4. Load Testing Insights
```
User: "Interpret these load test results"
performance-engineer: Analyzes throughput, latency, bottlenecks
Output: Scaling recommendations
```

## Quick Start

```bash
# Profile slow code
Ask: "Profile this function and find the bottleneck"

# Optimize performance
Ask: "Optimize this database query - it's taking 2 seconds"

# Analyze resource usage
Ask: "Why is this React component re-rendering so much?"

# Interpret benchmarks
Ask: "Explain these load test results and suggest improvements"
```

## Performance Optimization Workflow

### 1. Measure
```
performance-engineer: "Profile the current performance"
Output: Baseline metrics (response time, memory, CPU)
```

### 2. Identify Bottlenecks
```
performance-engineer: "Find the slowest parts"
Output: Bottleneck analysis (N+1 queries, large loops, etc.)
```

### 3. Optimize
```
performance-engineer: "Optimize the bottlenecks"
Output: Optimized code with explanations
```

### 4. Verify
```
performance-engineer: "Benchmark the improvements"
Output: Before/after comparison
```

## Common Optimizations

**Database**:
- N+1 query elimination
- Index optimization
- Query plan analysis
- Connection pooling

**Frontend**:
- React re-render optimization
- Code splitting
- Lazy loading
- Bundle size reduction

**Backend**:
- Caching strategies
- Algorithm optimization
- Async/parallel processing
- Memory leak fixes

## Recommended Combinations

**Full performance audit**:
- performance-optimization ✅
- scott-cc ✅ (main plugin for refactoring)
- browser-automation ✅ (to measure frontend performance)

**Backend optimization**:
- performance-optimization ✅
- security-suite ✅ (ensure optimizations don't break security)
