# Native worker adapters

This is a dispatch procedure, not a new tool API. Use the **live tool schema** and
capability descriptions actually supplied by the running host. A brand name, a
CLI binary on PATH, installed prompt files, or a successful package doctor is
not proof that worker dispatch or context isolation exists.

## Detect before work

1. Inspect available tool metadata. Identify a tool that actually launches a
   worker, its accepted parameters, wait/result mechanism, context behavior,
   permission controls and filesystem working-directory support. Record the
   exact exposed tool name, not a guessed API. If a tool requires deferred schema
   loading, load that schema before constructing a call.
2. Classify context as `fresh` (only explicit inputs), `inherited` (parent
   conversation copied), or `unknown`. A fork may have a separate context window
   but inherited reasoning: **not clean-room independence**. Never label unknown
   isolation as fresh. Filesystem/worktree isolation does not isolate reasoning.
3. Check the task needs: ordinary implementation can use inherited context;
   blind builders, fresh-eyes review and independent validation require fresh
   contexts and explicit artifact-only inputs. Workers must be able to read the
   supplied absolute paths and persist artifacts in their allowed workspace.
4. If no matching native worker exists, select the task's documented sequential
   mode, or report `unsupported` **before work** when independent workers are a
   requirement. Do not make up `Agent(...)`, `Task(...)`, fork types, model names,
   isolation flags or parameters. Do not start a paid CLI/provider as an implicit
   fallback. Installation/configuration requires separate authorization.

## Host adapters

| Host | Dispatch mapping |
|---|---|
| Claude Code | Use its exposed Agent or Task tool only when present; use a named plugin agent only if listed. Otherwise feed the bundled prompt to an available general worker through that tool's actual schema. Forks require explicit supported semantics and count as inherited if they copy history. |
| Codex | Use the session's exposed native agent-launch tool if present, then its documented wait/result tool. Configure fresh context/working directory only through fields it actually supports; otherwise require a bounded prompt and verify the context guarantee or decline independent mode. |
| Hermes | Load the exposed delegation tool schema if available and pass the explicit prompt/task using that schema. Nested delegation may be absent in a subagent; do not recurse or invent an alternate API. |
| Gemini CLI / Pi | Use an installed native worker extension only when its tool and schema are exposed. Do not infer worker support from skill loading. Without it, use the explicitly disclosed sequential mode or stop as unsupported. |

For every native adapter, supply the bundled role prompt as instructions plus the
allowed task inputs; do not send the worker the whole parent conversation unless
the selected mode explicitly allows inheritance. Tool names inside vendored
prompts are role descriptions, not authority to invoke nonexistent functions.
The task's safety, scope and artifact limits override example commands in them.

## Handoff and readback

A worker receives goal, absolute workspace, base revision/target hash, read/write
scope, permissions, resource/time limits, test commands, role prompt path and
expected artifact location. Request a bounded manifest: status, artifact paths
and hashes, changed files/counts, commands and exit codes, blockers. Persist logs
instead of returning raw builds or diffs. Verify actual files, hashes and tests;
self-reported success is not evidence of completion.

Sequential execution in the current conversation is **not independent**, not
parallel, and not delegated. Label it that way in every report and do not claim
clean-room validation, blind generation, or model diversity. If the user requires
those guarantees, report unsupported rather than substituting sequential work.
