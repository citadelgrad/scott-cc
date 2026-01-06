# Scott's Claude Code Setup

My personal Claude Code configuration for productive web development. This plugin provides **14 slash commands** and **11 specialized AI agents** to supercharge your development workflow.

The started as a clone of https://github.com/edmund-io/edmunds-claude-code

## Quick Install

```bash
# Step 1: Add the marketplace
/plugin marketplace add citadelgrad/scott-claude-code

# Step 2: Install the plugin
/plugin install scott-claude-code
```

## What's Inside

### 📋 Development Commands (7)

- `/scott-claude-code:new-task` - Analyze code for performance issues
- `/scott-claude-code:code-explain` - Generate detailed explanations
- `/scott-claude-code:code-optimize` - Performance optimization
- `/scott-claude-code:code-cleanup` - Refactoring and cleanup
- `/scott-claude-code:feature-plan` - Feature implementation planning
- `/scott-claude-code:lint` - Linting and fixes
- `/scott-claude-code:docs-generate` - Documentation generation

### 🔌 API Commands (3)

- `/scott-claude-code:api-new` - Create new API endpoints
- `/scott-claude-code:api-test` - Test API endpoints
- `/scott-claude-code:api-protect` - Add protection & validation

### 🎨 UI Commands (2)

- `/scott-claude-code:component-new` - Create React components
- `/scott-claude-code:page-new` - Create Next.js pages

### 💾 Supabase Commands (2)

- `/scott-claude-code:types-gen` - Generate TypeScript types
- `/scott-claude-code:edge-function-new` - Create Edge Functions

### 🤖 Specialized AI Agents (11)

**Architecture & Planning**
- **tech-stack-researcher** - Technology choice recommendations with trade-offs
- **system-architect** - Scalable system architecture design
- **backend-architect** - Backend systems with data integrity & security
- **frontend-architect** - Performant, accessible UI architecture
- **requirements-analyst** - Transform ideas into concrete specifications

**Code Quality & Performance**
- **refactoring-expert** - Systematic refactoring and clean code
- **performance-engineer** - Measurement-driven optimization
- **security-engineer** - Vulnerability identification and security standards

**Documentation & Research**
- **technical-writer** - Clear, comprehensive documentation
- **learning-guide** - Teaching programming concepts progressively
- **deep-research-agent** - Comprehensive research with adaptive strategies

## Installation

### From GitHub (Recommended)

```bash
# Add marketplace
/plugin marketplace add citadelgrad/scott-claude-code

# Install plugin
/plugin install scott-claude-code
```

### From Local Clone (for development)

```bash
git clone https://github.com/citadelgrad/scott-claude-code.git
cd scott-claude-code

# Add as local marketplace
/plugin marketplace add /path/to/scott-claude-code

# Install plugin
/plugin install scott-claude-code
```

## Best For

- Next.js developers
- TypeScript projects
- Supabase users
- React developers
- Full-stack engineers

## Usage Examples

### Planning a Feature

```bash
/scott-claude-code:feature-plan
# Then describe your feature idea
```

### Creating an API

```bash
/scott-claude-code:api-new
# Claude will scaffold a complete API route with types, validation, and error handling
```

### Research Tech Choices

Just ask Claude questions like:
- "Should I use WebSockets or SSE?"
- "How should I structure this database?"
- "What's the best library for X?"

The tech-stack-researcher agent automatically activates and provides detailed, researched answers.

## Philosophy

This setup emphasizes:
- **Type Safety**: Never uses `any` types
- **Best Practices**: Follows modern Next.js/React patterns
- **Productivity**: Reduces repetitive scaffolding
- **Research**: AI-powered tech decisions with evidence

## Requirements

- Claude Code 2.0.13+
- Works with any project (optimized for Next.js + Supabase)

## Customization

After installation, you can customize any command by editing files in `commands/` and `agents/` directories at the plugin root.

## Contributing

Feel free to:
- Fork and customize for your needs
- Submit issues or suggestions
- Share your improvements

## License

MIT - Use freely in your projects

---

**Note**: This is my personal setup that I've refined over time. Commands are optimized for Next.js + Supabase workflows but work great with any modern web stack.
