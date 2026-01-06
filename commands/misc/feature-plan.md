---
description: Plan feature implementation with technical specifications
model: claude-sonnet-4-5
---

Create a detailed implementation plan for the following feature.

## Feature Description

$ARGUMENTS

## Planning Framework for Solo Developers

### 1. **Feature Breakdown**

Analyze and break down into:
- User stories
- Technical requirements
- Dependencies
- Edge cases
- Success criteria

### 2. **Technical Specification**

**Architecture**
- Where does this fit in the codebase?
- Which components/pages/modules affected?
- New vs modified files
- Database schema changes (if applicable)
- API endpoints needed (if applicable)

**Technology Choices**
- Libraries/packages needed
- Why each choice?
- Alternatives considered
- Trade-offs

**Data Flow**
```
User Action → Frontend → API → Database → Response
```
(Adapt to your architecture)

### 3. **Implementation Steps**

Break into logical, sequential tasks:

1. **Setup** - Dependencies, configuration
2. **Database** - Schema, migrations, policies (if applicable)
3. **Backend** - API routes, validation, logic (if applicable)
4. **Frontend** - Components, pages, forms (if applicable)
5. **Integration** - Connect pieces
6. **Testing** - Unit, integration, E2E
7. **Polish** - Error handling, loading states, UX

### 4. **Risk Assessment**

Identify potential issues:
- **Technical Risks** - Complexity, unknown territory
- **Time Risks** - Underestimated tasks
- **Dependency Risks** - External APIs, third-party services
- **Data Risks** - Migration, backward compatibility

### 5. **Estimation**

Realistic time estimates:
- Small task: 1-2 hours
- Medium task: Half day
- Large task: 1-2 days
- Complex task: 3-5 days

**Rule of thumb**: Double your initial estimate for solo development.

### 6. **Success Criteria**

Define "done":
- Feature works as specified
- Tests pass
- No console/runtime errors
- Accessible (if UI)
- Responsive (if UI)
- Error handling
- Loading states (if applicable)
- Documentation updated

## Output Format

### 1. **Feature Overview**
- What problem does this solve?
- Who is it for?
- Key functionality

### 2. **Technical Design**
```
[Frontend] → [API] → [Database]
```
(Adapt diagram to your architecture)
- Component/module structure
- API endpoints (if applicable)
- Database schema (if applicable)
- State management (if applicable)

### 3. **Implementation Plan**

**Phase 1: Foundation** (Day 1)
- [ ] Task 1
- [ ] Task 2

**Phase 2: Core Feature** (Day 2-3)
- [ ] Task 3
- [ ] Task 4

**Phase 3: Polish** (Day 4)
- [ ] Task 5
- [ ] Task 6

### 4. **File Changes**

**New Files**
```
path/to/new-file.ext
components/FeatureComponent.ext
lib/feature-utils.ext
```

**Modified Files**
```
path/to/existing-file.ext (add new section)
lib/types.ext (add new types)
```

### 5. **Dependencies**

**Packages to install** (adapt to your package manager)
```bash
# npm/pnpm/yarn
npm install package-name

# pip
pip install package-name

# cargo
cargo add package-name

# go
go get package-name
```

**Environment variables**
```bash
FEATURE_API_KEY=xxx
```

### 6. **Testing Strategy**

- Unit tests for utilities
- Integration tests for API (if applicable)
- Component tests for UI (if applicable)
- E2E test for full flow

### 7. **Rollout Plan**

- Feature flag if needed
- Gradual rollout strategy
- Rollback plan
- Monitoring and metrics

### 8. **Next Steps**

1. Review plan
2. Set up environment
3. Start with Phase 1
4. Test incrementally
5. Deploy to staging (if applicable)
6. Production deploy

Provide a clear, actionable plan that a solo developer can follow step-by-step, adapted to your chosen language and framework.
