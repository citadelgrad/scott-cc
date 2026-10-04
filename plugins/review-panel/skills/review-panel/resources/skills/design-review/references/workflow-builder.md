# Building a Design Review Workflow

How to turn the five-phase funnel in SKILL.md into a Dynamic Workflow script, for reviews too large to run once per file in a single conversation.

## The Mapping

The funnel is already phase-shaped. Each phase becomes a workflow stage, not a rewrite:

- **Phase 1 (Complexity Triage)** → the fan-out stage. One agent per file or module, run concurrently, applying only the complexity-recognition checks. This is deliberately cheap and broad: its job is to rank targets, not diagnose them.
- **Phases 2-4 (Structural, Interface, Surface)** → the deep-dive stage. Runs only on targets Phase 1 flagged (or, if nothing was flagged anywhere, the largest or most-connected targets — same early-termination logic as the single-target funnel, just applied per target instead of once).
- **Phase 5 (Red Flags Sweep) + Prioritization** → the verification and synthesis stage. This is where findings get challenged and ranked, not just collected.

## Structure It as a Pipeline, Not a Barrier

Use a pipeline over targets, not a `parallel()` triage pass followed by a separate `parallel()` deep-dive pass. A file that triages clean should exit immediately; a file that triages dirty should move straight into its deep-dive while other files are still being triaged. Waiting for every file to finish triage before starting any deep-dive wastes exactly the wall-clock this exercise exists to save.

A barrier is justified in exactly one place: before final synthesis, since prioritization (syndrome clusters, boundary issues, canary flags) requires comparing findings across the whole target set, not just within one file.

## Hard Bounds

- Read only `design-review-scope.json` in the parent before dispatch. Reject more than 20 files or
  1,200 changed lines.
- Run at most 4 target workers concurrently, 4 targets per batch, 3 batches, and 12 target
  assignments total.
- Keep at most 40 candidate finding records. Assign one challenger per candidate, never 2-3, with
  at most 4 concurrent challengers and 40 validator assignments total.
- Each worker writes detailed JSON to the run workspace and returns a manifest no larger than
  2 KiB containing path, SHA-256, status, counts, and coverage gaps.
- The synthesis worker reads artifacts directly and writes `final-summary.json`. It returns at most
  4 KiB and 12 finding IDs; the parent never loads complete scorecards or finding bodies.
- Any missing worker isolation, artifact, hash, or valid schema is terminal. Do not replace a
  worker with an inline or sequential parent-context pass.

## Adversarial Verification

A design-quality finding is a judgment call, not a compile error. "Getter/setter exposing internal state" can be a real information leak or a defensible choice given the module's actual callers. Treat every candidate finding from the deep-dive stage as a claim to be challenged, not a fact to be reported:

- Spawn exactly one independent challenger per retained finding, asked to argue it is *not* real
  given the surrounding code. Keep it only when the challenger cannot invalidate its cited evidence.
- This matters more here than in a typical bug-finding workflow: correctness bugs are usually binary, design smells are contextual, and an unverified sweep will over-report defensible code as broken.

## Scale and Cost

Never accept a codebase with thousands of files as one target. The preflight rejects it and reports
coherent partitions. Do not sample silently or descend beyond the 12-assignment total.

## Skeleton

The shape, not exact syntax (this evolves; match whatever workflow-scripting conventions your current session actually exposes):

```text
phase('Triage')
targets = list of files/modules to review (batched, not necessarily one-per-file)
triageResults = pipeline(
  targets,
  target => agent(apply complexity-recognition to `target`, return ranked signal),
)

phase('Deep dive')
flagged = triageResults.filter(has a signal worth investigating)
deepDiveResults = pipeline(
  flagged,
  target => agent(apply structural + interface + surface lenses to `target`, return candidate findings),
)

phase('Verify')
verified = pipeline(
  deepDiveResults.flatMap(findings),
  finding => one challenger agent arguing it's not real,
    keep if the challenge cannot invalidate cited evidence
)

phase('Synthesize')
one final agent: dedupe verified findings, group into syndrome clusters,
apply the Prioritization ranking from SKILL.md, write the report
```

## Unavailable Workflow

If isolated Dynamic Workflows are unavailable, stop with `ISOLATION_UNAVAILABLE`. Running the
funnel per file or module in this same conversation is prohibited because it defeats the context
contract.
