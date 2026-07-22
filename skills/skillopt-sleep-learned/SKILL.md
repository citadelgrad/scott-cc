---
name: skillopt-sleep-learned
description: Preferences and procedures learned from past local agent sessions.
---

# skillopt-sleep-learned

Preferences and procedures learned from your past local agent sessions.

<!-- SKILLOPT-SLEEP:LEARNED START -->
## Learned preferences & procedures

_This block is maintained by SkillOpt-Sleep. Edits here are proposed offline, validated against your past tasks, and adopted only after you approve them. Hand-edits outside this block are never touched._

- Never end a turn immediately after stating intent to use a tool (e.g. 'I'll look for X', 'I'll fetch Y', 'I'll search for Z'). Always execute the tool call(s) and include the actual results, findings, or produced content in the same response. A reply consisting only of a one-sentence preamble plus a bare tool invocation (e.g. a tool-call header with no output shown) counts as a FAILED response, not a valid answer.
- When a skill, plan, or prior message already contains explicit steps, commands, or instructions to follow (e.g. a skill's 'Step 1' with concrete detection commands, or a plan document to review), execute those steps directly. Do not respond that the task 'was interrupted' or that you lack enough information when the needed instructions are already present in context — treat provided steps/skills/plans as sufficient direction to proceed.
- OVERRIDE: this environment has 'Auto Mode Active' — do not pause to ask clarifying questions on ambiguous but actionable requests (e.g. 'review the last 100 sessions', 'give an overview of the review panel skill', 'run skillopt on the pas skill'). Make the reasonable interpretation, use available local search/file tools to gather real content, and deliver a substantive answer in the same turn. Only stop short if genuinely blocked with no reasonable default (e.g. missing credentials, destructive/irreversible action, or truly no viable interpretation).
- For requests asking for a deliverable (an overview, a settings.json file, a reviewed/improved plan, a demo file), the final response must contain the complete deliverable content itself — not a description of the plan to produce it, and not a truncated fragment. If the deliverable is large, complete it fully within the turn rather than stopping after outlining the approach.
<!-- SKILLOPT-SLEEP:LEARNED END -->
