# Scott's Claude Code Setup

My personal Claude Code configuration for productive web development. This plugin provides **14 slash commands** and **11 specialized AI agents** to supercharge your development workflow.

Copied and enhanced from https://github.com/edmund-io/edmunds-claude-code

## Quick Install

```bash
# Step 1: Add the marketplace
/plugin marketplace add citadelgrad/scott-cc

# Step 2: Install the plugin
/plugin install scott-cc
```

## What's Inside

### 📋 Development Commands (7)

- `/scott-cc:new-task` - Analyze code for performance issues
- `/scott-cc:code-explain` - Generate detailed explanations
- `/scott-cc:code-optimize` - Performance optimization
- `/scott-cc:code-cleanup` - Refactoring and cleanup
- `/scott-cc:feature-plan` - Feature implementation planning
- `/scott-cc:lint` - Linting and fixes
- `/scott-cc:docs-generate` - Documentation generation

### 🔌 API Commands (3)

- `/scott-cc:api-new` - Create new API endpoints
- `/scott-cc:api-test` - Test API endpoints
- `/scott-cc:api-protect` - Add protection & validation

### 🎨 UI Commands (2)

- `/scott-cc:component-new` - Create React components
- `/scott-cc:page-new` - Create Next.js pages

### 💾 Supabase Commands (2)

- `/scott-cc:types-gen` - Generate TypeScript types
- `/scott-cc:edge-function-new` - Create Edge Functions

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
/plugin marketplace add citadelgrad/scott-cc

# Install plugin
/plugin install scott-cc
```

### From Local Clone (for development)

```bash
git clone https://github.com/citadelgrad/scott-cc.git
cd scott-cc

# Add as local marketplace
/plugin marketplace add /path/to/scott-cc

# Install plugin
/plugin install scott-cc
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
/scott-cc:feature-plan
# Then describe your feature idea
```

### Creating an API

```bash
/scott-cc:api-new
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
