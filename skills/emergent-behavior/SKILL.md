---
name: emergent-behavior
description: >-
  Use when inspecting a codebase, architecture, incident, or design for
  system-level behavior that arises from component interactions rather than
  being explicitly owned by one component.
license: MIT
metadata:
  category: analysis
  triggers: [emergence, emergent-behavior, feedback-loop, self-organization, adaptation, resilience, decentralized-intelligence, complex-adaptive-system]
---

# Emergent Behavior Analysis

Identify behaviors, properties, and failure or recovery modes that arise from
interactions among components rather than from one explicitly coded mechanism.
Keep the analysis grounded in observed control flow, data flow, shared state,
and operational evidence. Biological parallels are optional explanatory tools,
not evidence.

## When to Use

- Architecture reviews where system-level behavior is surprising or unowned
- Codebase analysis for self-organizing, adaptive, or decentralized patterns
- Resilience and fault-tolerance audits beyond local error handling
- Post-incident analysis of cascading failure, stabilization, or recovery
- Design reviews for complex adaptive system characteristics

Do not use this skill for ordinary local behavior with a clear owner, generic
code review, or speculative analogy unsupported by system evidence.

## Inputs

Gather enough evidence to identify:

1. The system boundary and relevant environment
2. Components, actors, and shared resources inside that boundary
3. Communication paths, state changes, and control signals
4. Time delays, retries, thresholds, queues, and resource constraints
5. The observed or hypothesized system-level behavior

If the behavior is only hypothesized, label it as such and state what evidence
would confirm or falsify it.

## Procedure

### 1. Map the Interaction

List the smallest set of components that can produce the behavior. For each
interaction, record:

- Source and destination
- Data, signal, or resource exchanged
- State changed by the interaction
- Timing, ordering, and delay
- Local rule or decision each component applies

Do not attribute the behavior to emergence until the local mechanisms are
understood.

### 2. Trace the Causal Loop

Write the interaction as a causal chain. Identify feedback as:

- **Reinforcing:** amplifies growth, congestion, failure, or adoption
- **Balancing:** pushes the system toward a target or stable range
- **Coupled:** reinforcing and balancing loops compete, often with delays

Call out thresholds, saturation points, and delayed effects. These are common
sources of phase changes, oscillation, and collapse.

### 3. Test Whether the Property Is Emergent

A property qualifies only when all of these are true:

- No single component implements or owns the complete behavior
- The behavior depends on interactions among multiple components
- Changing an interaction, topology, timing, or local rule changes the behavior
- The causal mechanism can be explained without relying on metaphor

Classify the result as:

- **Designed emergence:** local rules intentionally produce a global property
- **Incidental beneficial emergence:** an unplanned interaction improves outcomes
- **Incidental harmful emergence:** an unplanned interaction creates failure risk
- **Not emergent:** ordinary composed behavior with a clear explicit owner

### 4. Evaluate Adaptation and Resilience

Check whether the interaction creates:

- Self-healing through redundancy, rerouting, re-election, or retries
- Adaptation through measurements that alter future decisions
- Decentralized intelligence through local decisions yielding a global outcome
- Latent safety or failure properties that appear only under load or disruption

Distinguish real adaptation from fixed fallback logic. A static retry count is
not adaptive merely because it handles failure.

### 5. Seek Disconfirming Evidence

Try to falsify the emergent explanation:

- Can one component fully explain the behavior?
- Is the behavior explicitly orchestrated elsewhere?
- Does it disappear when one interaction is isolated?
- Is the evidence only correlation or a biological analogy?
- Would the same result occur without feedback or shared state?

Downgrade or reject the finding when the interaction-level evidence does not
survive these checks.

### 6. Recommend an Intervention

For beneficial behavior, recommend how to preserve or amplify it without making
it opaque. For harmful behavior, recommend how to dampen, bound, observe, or
break the causal loop. Prefer changes to interaction rules, information flows,
delays, or constraints over adding a vague coordinating layer.

State the expected effect and a concrete measurement that would verify it.

## Output Contract

For each finding, report:

### [Finding name]

- **Classification:** Designed / beneficial / harmful / not emergent
- **Confidence:** High / medium / low
- **Components:** The participating components or actors
- **Core mechanism:** The specific interaction and causal loop
- **Emergent property:** The system-level behavior no component owns alone
- **Evidence:** Code paths, traces, metrics, documents, or incident observations
- **Disconfirming test:** What could prove this explanation wrong
- **Biological parallel:** Optional; omit when it does not improve understanding
- **Intervention:** How to amplify, preserve, dampen, or eliminate the behavior
- **Verification:** Observable signal that the intervention had the expected effect

End with a short interaction map and rank findings by impact and confidence.

## Boundaries

**Will:**

- Analyze codebases, architectures, incidents, and designs for emergent patterns
- Identify feedback loops, adaptation, self-healing, and decentralized outcomes
- Separate observed evidence from hypotheses and analogies
- Recommend measurable interaction-level interventions

**Will not:**

- Implement or refactor the analyzed system
- Replace correctness, security, performance, or conventional code review
- Label ordinary composition as emergence to make the analysis sound profound
- Treat biomimicry as proof

## Limitations

- Static artifacts may not reveal runtime timing, load, or topology effects.
- Causal claims require traces, experiments, or operational evidence when available.
- The chosen system boundary can hide external causes; state it explicitly.
