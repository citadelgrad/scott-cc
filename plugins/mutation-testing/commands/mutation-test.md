---
name: mutation-test
description: Run the bounded mutation-testing orchestrator against one source file, with quick, standard, or deep mutation budgets
argument-hint: "[path] [--quick | --deep] [--focus=<area>] [--auto-approve]"
allowed-tools: Task(mutation-testing:test-quality-reviewer), Read, Grep, Glob, Bash, AskUserQuestion
---

# Mutation Test

Human entry point for the mutation-testing plugin. This command parses the invocation and hands
one complete request to the `mutation-testing:test-quality-reviewer` agent; it does not create
mutations, worktrees, or reports itself.

## Arguments

$ARGUMENTS

Parse and pass these fields to the agent:

- **Target:** the remaining source file path. If omitted, pass `null`; the agent owns its
  documented conversation-context / git-status discovery flow and user selection.
- **Mode:** `quick` for `--quick`, `deep` for `--deep`, otherwise `standard`. `--quick` and
  `--deep` together are a hard error; do not dispatch.
- **Focus:** the value after `--focus=`, or `null` when absent.
- **Auto approve:** `true` only when `--auto-approve` is present. This permits applying a
  refactoring proposal without a second confirmation; it never permits deleting tests that the
  audit did not classify as zombie or redundant.

## Action

Dispatch exactly one agent call:

```text
Task(
  subagent_type="mutation-testing:test-quality-reviewer",
  description="Run mutation test workflow",
  prompt="""Run the mutation-testing workflow with:
  target: <path-or-null>
  mode: <quick|standard|deep>
  focus: <value-or-null>
  auto_approve: <true|false>

  Follow your documented hard context contract. Preserve the primary checkout, use artifact-only
  handoffs, report executor coverage gaps separately from survived mutations, and return only the
  bounded final summary plus detailed artifact paths and the user's apply/refuse decision."""
)
```

Do not substitute a `scott-cc:*` agent name. Agents shipped by this plugin are exposed under the
`mutation-testing:` namespace.

## Boundary behavior

- No target and no discoverable candidate: ask for a target; do not dispatch downstream agents.
- Multiple discoverable candidates: ask the user to choose; do not guess.
- `--quick --deep`: reject before dispatch with a named conflicting-flags error.
- Downstream `ERROR` or `INVALID_MUTATION`: preserve it as an execution gap; never count it as a
  survived mutation or include it in the mutation-score denominator.

## Output contract

Return the orchestrator agent's bounded final summary unchanged. It must stay at or below 4 KiB,
name no more than 10 finding IDs, include the chosen target and mode, mutation counts
(total/evaluated/caught/survived), execution-gap counts, mutation score or `null`, detailed report
artifact paths and hashes, and whether the user accepted the proposal. Never inline the detailed
mutation, executor, audit, or refactor artifacts.
