---
name: reck-factory
description: Manage the Reck software factory — register repos, run AI tasks in containers, schedule background pipelines, and monitor results. Use when provisioning a new task, checking task status, or setting up recurring automation.
license: MIT
tags: [reck, automation, containers, factory, pas]
---

# Reck Software Factory

Operates `reck` (Reckoner) — a software factory that wraps `pas`. It manages repos, provisions containers, runs PAS pipelines, and collects results. Version: 0.1.0.

**Architecture:** Reckoner is the factory layer. It never invokes Claude directly — all task execution routes through PAS. Foundry sits above as the platform quality layer (gates, schedules, CI-style profiles).

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
| Run a task | `reck task <repo> --pipeline <file>` |
| Set repo working directory | `reck repo set-working-dir <repo> <path>` |
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

`reck task` is the primary command. It handles container provisioning, PAS pipeline execution, and result collection.

```bash
# Current: --pipeline is required
reck task my-repo --pipeline path/to/pipeline.dot
```

### Intent flags (wired, resolution pending)

`reck task` accepts mutually exclusive `IntentSource` flags. These are wired to the CLI but not yet fully resolved to `.dot` files — until resolution is complete, `--pipeline` is required.

```bash
--prompt "Fix the auth bug"     # → pas plan --spec --from-prompt → pas generate → run (pending)
--spec path/to/spec.md          # → pas generate <spec> → run (pending)
--epic beads-123                # → pas scaffold <epic-id> → run (pending)
--prd path/to/prd.md            # → pas generate <prd> → run (pending)
```

When intent resolution lands, `--pipeline` will become optional for prompt/spec/epic/prd workflows.

### Other flags

```bash
# Skip PR creation, just collect logs
reck task my-repo --pipeline my.dot --no-pr
```

**Always use `--no-pr` for exploratory or debugging tasks** where you want to review results before committing to a PR.

### What happens under the hood

1. Provisions an isolated container for the repo
2. Runs the PAS pipeline (`.dot` file) inside the container
3. Collects results and creates a PR by default
4. After a successful PR, automatically fires `foundry run post-feature` (see §5)

---

## Step 3: Repo Lifecycle

### Register a new repo

```bash
reck add https://github.com/org/repo
```

Reck clones the repo as a bare treeless clone (fast, low disk). The repo name used in subsequent commands is derived from the URL (the final path segment without `.git`).

`reck add` nudges you to set a `working_dir` but does not require it. Set it at any time:

```bash
reck repo set-working-dir my-repo /local/path/to/checkout
```

When `working_dir` is set, Reckoner checks out the PR branch there after successful PR creation so you can review or test immediately.

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

## Step 5: Foundry Post-Feature Hook

After every successful PR creation, Reckoner automatically calls:

```bash
foundry run post-feature
```

This is a **zero-config convention hook** — no wiring required. Opt in by defining a `post-feature` profile in the repo's `foundry.yaml`; if the profile doesn't exist, Reckoner silently continues.

```yaml
# foundry.yaml in the target repo
profiles:
  post-feature:
    gates:
      - id: security-scan
        run: rg -r "TODO|FIXME|HACK"
        allow_failure: true
      - id: test
        run: cargo test --workspace
        timeout: 5m
```

---

## Step 6: Checking Results

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

## Step 7: Observability

```bash
# Start Loki + Grafana infra (run once per machine)
reck infra

# Open dashboard in browser
reck observe
```

The observability stack aggregates logs from all tasks. Run `reck infra` once to provision it; `reck observe` opens the Grafana dashboard.

---

## Step 8: Diagnostics

```bash
reck doctor
```

Checks: container runtime availability, repo registration integrity, schedule daemon status, infra health. Run this first when anything behaves unexpectedly.

```bash
reck config
```

Shows current configuration (paths, defaults, active model). Useful for verifying what `reck task` will use before running a task.
