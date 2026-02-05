# process-engine

> Workflow management and process monitoring

## What's Included

### Agents (1)
- **process-monitor** - Monitor running Process Engine executions and report progress with alerts for gates and failures

### Commands (18)
*Note: Commands are in the main scott-cc repo, not duplicated here*

## When to Use

**Install this if you**:
- Use process-driven development workflows
- Work with beads task tracking
- Need structured feature development pipelines
- Want to monitor multi-step processes

**Don't install if you**:
- Work ad-hoc without defined processes
- Don't use beads or structured workflows

## What is Process Engine?

A workflow orchestration system that:
- Defines multi-step development processes (epics → features → deployment)
- Tracks progress through gates and phases
- Integrates with beads for task management
- Monitors execution and alerts on failures

## Use Cases

### 1. Feature Development Process
```
Epic → Architecture Gate → Implementation → Quality Gate → Deployment
```

Process Engine ensures each phase completes before moving forward.

### 2. Process Monitoring
```
User: "Check the status of the authentication feature process"
process-monitor: Shows current phase, blockers, next steps
Output: Process status report
```

### 3. Failure Alerts
```
process-monitor: Detects stuck processes, failed gates
Output: Alert with recovery recommendations
```

## Quick Start

```bash
# Monitor active processes
Ask: "What's the status of ongoing processes?"

# Check specific process
Ask: "Show me the progress of the payment feature epic"

# Diagnose failures
Ask: "Why did the architecture gate fail?"
```

## Integration with Beads

Process Engine works seamlessly with beads:

```bash
# Process Engine creates beads tasks automatically
bd list --status=in_progress  # See active process tasks

# Process monitor tracks beads progress
process-monitor: "Feature X is 60% complete (3/5 tasks done)"
```

## Workflow Example

### Starting a Feature
```
1. Create epic: bd create --title="User Auth" --type=epic
2. Start process: Process Engine begins Architecture phase
3. Monitor: process-monitor reports progress
4. Gate check: Architecture review gate
5. Implement: Tasks created in beads
6. Quality gate: Tests run, mutation testing
7. Deploy: Feature goes live
```

## Process Phases

**Typical feature process**:
1. **Planning** - Requirements, specifications
2. **Architecture** - Design decisions, PRD/SPEC
3. **Implementation** - Code, tests, documentation
4. **Quality** - Code review, mutation testing, performance
5. **Deployment** - Deploy, monitor, validate

## Recommended Combinations

**Structured development**:
- process-engine ✅
- scott-cc ✅ (main plugin for architecture & core work)
- mutation-testing ✅ (for quality gate)

**Team workflows**:
- process-engine ✅
- scott-cc ✅ (main plugin for day-to-day work)
- browser-automation ✅ (for E2E validation gate)
