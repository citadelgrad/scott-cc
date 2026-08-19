---
name: epic-planner
description: Plan a complete feature from concept to implementation-ready beads tasks, with research, PRD/SPEC docs, and human approval gates
argument-hint: "<feature description> (e.g. \"a notification system for the app\")"
---

# Epic Planner

Plan a feature from initial concept to implementation-ready beads tasks. This command
starts the **epic-planner** agent, which runs a staged workflow with human approval gates:
research → approval → PRD/SPEC → approval → task decomposition.

## Arguments

$ARGUMENTS

Parse the arguments as:
- `feature_description` (optional): A short description of the feature to plan.

## Action

Launch the `beads-epic-builder:epic-planner` subagent with the Task tool.

1. If `$ARGUMENTS` is empty, first ask the user one question: "What feature do you want to
   plan?" Wait for the answer, then use that answer as `feature_description`.
2. Start the subagent:
   - `subagent_type`: `beads-epic-builder:epic-planner`
   - `description`: `Plan feature: <short slug>`
   - `prompt`: Pass the full `feature_description` verbatim. Add this line so the agent
     knows it owns the workflow: "You are the epic-planner agent. Run the full staged
     planning workflow (research, approval gate, PRD/SPEC, approval gate, task
     decomposition) for the feature described above. Persist all state to files under
     `.claude/epic-planner/<feature-slug>/` and stop at each approval gate for my sign-off."
3. The agent runs with isolated context. It persists state to
   `.claude/epic-planner/<feature-slug>/checkpoint.json`, so it can resume across sessions.

## Approval Gates

Do not skip the gates. The agent must stop and get the user's approval:
- After research (Stage 1 → 2).
- After the PRD and SPEC documents (before task creation).

Report the outputs at each gate so the user can approve or request changes.

## Example Usage

```
/epic-planner an automated error-fixing system that watches GlitchTip and proposes patches
```

This will:
1. Research approaches and write findings to `.claude/epic-planner/<slug>/stage-1-research.md`.
2. Stop for research approval.
3. Write `docs/prd-<slug>.md` and `docs/spec-<slug>.md`.
4. Stop for document approval.
5. Break the feature into beads tasks under a new epic and list the created IDs.

## Related

- `/build-feature <epic-id>` — build a planned epic sequentially with architecture review.
- `/epic-swarm <epic-id>` — build a planned epic with parallel workers in isolated worktrees.
