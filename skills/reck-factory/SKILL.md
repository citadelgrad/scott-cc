---
name: reck-factory
description: Manage the Reck software factory — register repos, run AI tasks in containers, schedule background pipelines, and monitor results. Use when provisioning a new task, checking task status, or setting up recurring automation.
license: MIT
tags: [reck, automation, containers, factory, pas]
---

# Reck Software Factory

Operates `reck` (Reckoner) — a software factory that wraps `pas`. It manages repos, provisions containers, runs PAS pipelines, and collects results. Version: 0.1.0.

Use this skill when:
- Running an AI-driven task against a registered repo (`reck task`)
- Registering or managing repos in the factory
- Setting up or troubleshooting scheduled background pipelines
- Checking task status or retrieving logs
- Diagnosing system health issues

---

## Step 1: Identify the Operation

| Goal | Command |
|---|---|
| Initialize Reckoner | `reck init` |
| Register a repo | `reck add <repo-url>` |
| List registered repos | `reck list` |
| Run a task | `reck task <repo> "<prompt>"` |
| Check task status | `reck status` |
| View task logs | `reck logs <task-id>` |
| Sync repo to latest | `reck sync <repo>` |
| Remove a repo | `reck remove <repo>` |
| Run linters | `reck lint <repo>` |
| Manage schedules | `reck schedule add/list/remove/run` |
| Start observability infra | `reck infra` |
| Open dashboard | `reck observe` |
| Check system health | `reck doctor` |
| Show configuration | `reck config` |

---

## Step 2: Running a Task

`reck task` is the primary command. Give it a repo name and a prompt; it handles container provisioning, PAS pipeline execution, and result collection.

```bash
reck task my-repo "Fix the authentication bug in the login flow"
```

### What happens under the hood

1. Provisions an isolated container for the repo
2. Auto-generates a PAS pipeline from the prompt (or uses `--pipeline` if provided)
3. Runs the pipeline inside the container
4. Collects results and creates a PR by default

### Key flags

```bash
# Use a specific pipeline instead of auto-generating one
reck task my-repo "..." --pipeline path/to/pipeline.dot

# Skip PR creation, just collect logs
reck task my-repo "..." --no-pr
```

**Always use `--no-pr` for exploratory or debugging tasks** where you want to review results before committing to a PR.

---

## Step 3: Repo Lifecycle

### Register a new repo

```bash
reck add https://github.com/org/repo
```

Reck clones the repo as a bare treeless clone (fast, low disk). The repo name used in subsequent commands is derived from the URL (the final path segment without `.git`).

### Keep repos current

```bash
reck sync my-repo      # fetch latest from remote
```

Reck does not auto-sync before tasks. Run `reck sync` manually or add it to a schedule before recurring tasks that need fresh code.

### Remove a repo

```bash
reck remove my-repo
```

Removes the registration and cloned data. Does not affect the remote.

---

## Step 4: Scheduled Pipelines

Use `reck schedule` for recurring automation. This is the correct interface for background pipelines — do NOT use crontab, launchd plists, or CCR routines.

```bash
# Add a schedule
reck schedule add

# List active schedules
reck schedule list

# Trigger a schedule manually (useful for testing)
reck schedule run <name>

# Remove a schedule
reck schedule remove <name>
```

**Note:** For project-level scheduling, `foundry.yaml` is the control layer. `reck schedule` manages factory-level recurring pipelines that operate across repos.

---

## Step 5: Checking Results

### Task status

```bash
reck status
```

Shows all tasks with their current state: pending, running, succeeded, failed.

### Logs

```bash
reck logs <task-id>
```

Reck preserves logs from completed tasks. Use the task ID from `reck status` output.

### Linting a repo

```bash
reck lint my-repo
```

Runs toolchain + architectural linters against the repo without provisioning a full task container. Useful for quick health checks.

---

## Step 6: Observability

```bash
# Start Loki + Grafana infra (run once per machine)
reck infra

# Open dashboard in browser
reck observe
```

The observability stack aggregates logs from all tasks. Run `reck infra` once to provision it; `reck observe` opens the Grafana dashboard.

---

## Step 7: Diagnostics

```bash
reck doctor
```

Checks: container runtime availability, repo registration integrity, schedule daemon status, infra health. Run this first when anything behaves unexpectedly.

```bash
reck config
```

Shows current configuration (paths, defaults, active model). Useful for verifying what `reck task` will use before running a task.
