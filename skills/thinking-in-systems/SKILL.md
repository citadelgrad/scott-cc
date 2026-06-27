---
name: thinking-in-systems
description: >-
  Apply Donella Meadows' systems thinking framework to map, diagnose, and
  redesign any system — organizational, technical, ecological, or policy.
  Covers stocks/flows, feedback loops, system archetypes, leverage points,
  and concrete intervention recommendations.
license: MIT
tags: [systems-thinking, analysis, design, leverage-points, archetypes]
sources:
  - "Meadows, Donella H. Thinking in Systems: A Primer. Chelsea Green Publishing, 2008."
---

# Thinking in Systems

Apply Donella Meadows' systems thinking framework to any system — organizational,
technical, ecological, or policy. The skill runs four phases: map the system's
structure, diagnose which system traps are active, rank leverage points by impact,
and produce concrete intervention recommendations.

Use this skill when:
- Analyzing why a system keeps producing the same bad outcomes despite repeated fixes
- Designing a new system and wanting to avoid classic failure traps from the start
- Looking for the highest-leverage intervention in a complex, interconnected problem
- Helping a team stop treating symptoms and start addressing root structure

---

## Parse Arguments

Extract from `$ARGUMENTS`:

| Argument | Effect |
|---|---|
| (none) | Ask for system description, then run all four phases |
| `--system "<text>"` | Inline system description — skip the prompt |
| `--focus map` | Phase 1 only (stocks/flows map) |
| `--focus archetypes` | Phases 1–2 (map + archetype diagnosis) |
| `--focus leverage` | Phases 1 + 3 (map + leverage points, abbreviated archetype pass) |
| `--design` | Design mode: user is building a new system, not analyzing an existing one |

---

## Phase 1: Map the System

### Gather Context

If no system was provided via `--system`, ask:

> **Describe the system you want to analyze.**
> Include: what it's trying to accomplish, who the key actors are, what resources or
> quantities flow through it, and what problem or behavior pattern you're concerned about.
> Example: "A fishing economy where fleets keep collapsing despite regulations," or
> "A software team that ships faster but accumulates more bugs with each release."

### Produce the System Map

Work through each layer in order. Every layer must have at least one entry or an explicit "none identified."

---

#### Elements

The visible, tangible parts — people, organizations, physical components, infrastructure.
List them in a simple table:

| Element | Type | Role in the system |
|---|---|---|
| [name] | Person / Org / Infrastructure / Resource | [what it does] |

---

#### Stocks and Flows

Stocks are accumulations measurable at a point in time. Flows are the rates that change them.

| Stock | What increases it (Inflows) | What decreases it (Outflows) | Current state |
|---|---|---|---|
| [name] | [inflow 1], [inflow 2] | [outflow 1] | Growing / Shrinking / Stable / Unknown |

**Delays:** Note any significant time lag between a flow and its effect. Delays are a primary
source of oscillation, overshoot, and policy failure.

| Delay | Between what and what | Estimated lag | Risk |
|---|---|---|---|
| [name] | [cause] → [effect] | [duration] | Oscillation / Overshoot / Both |

---

#### Feedback Loops

Identify every feedback loop and label it:
- **Reinforcing (R):** A change in the stock causes more change in the same direction. Drives
  exponential growth or collapse. Label: **R — [name]**
- **Balancing (B):** A change triggers corrective action returning the stock toward a target.
  Drives stability or oscillation. Label: **B — [name]**

Format each loop as a causal chain:

```
R — Compound Growth
  Cash in bank → interest earned → more cash in bank → ...
  Direction: self-amplifying (growth or collapse depending on starting sign)

B — Thermostat Control
  Room temperature → gap from setpoint → heater on/off → room temperature
  Direction: stabilizing toward target (with overshoot if delay is large)
```

---

#### System Purpose

State what the system *actually does* — inferred from its behavior pattern over time, not from
its mission statement or designers' intent.

> The system's real purpose is revealed by what it consistently produces, not by what
> stakeholders say it's for. A hiring process that consistently selects people from elite
> universities has "prestige filtering" as its actual purpose, regardless of stated diversity goals.

Write: **"This system's actual purpose appears to be: [one sentence]"**

---

### Worked Example (abbreviated)

**System:** A fishing economy

| Stock | Inflows | Outflows |
|---|---|---|
| Fish population | Natural reproduction | Fishing harvest |
| Fleet capacity | New boat purchases | Boat retirement / bankruptcy |
| Fishing profit | Revenue from catch | Operating costs |

**Feedback loops:**
```
R — Fleet Expansion
  Profit → buy more boats → larger harvest → more profit → ...
  Self-amplifying: drives rapid fleet growth in good years

B — Population Recovery
  Fish population → reproduction rate → population grows back
  Stabilizing: self-limiting when fish are abundant

B — Depletion Brake (weak, delayed)
  Fewer fish → harder to catch → less profit → fewer boats
  Stabilizing, BUT: long delay between depletion and fleet reduction;
  by the time profit falls, fish stock may already be below recovery threshold
```

**System purpose (actual):** Maximize short-term harvest returns, with population sustainability
as a secondary constraint that gets sacrificed whenever it conflicts with profit.

---

## Phase 2: Diagnose System Archetypes

> **If `--focus leverage` is active:** Do a single-pass only — mark each archetype Present/Absent with one line of evidence, skip expanded analysis, then proceed directly to Phase 3.

Check the mapped system against all six archetypes. State: **Present / Absent / Suspected**.
For "Present" entries, identify which elements play which role.

| Archetype | How to recognize it | Present? | Evidence |
|---|---|---|---|
| **Policy Resistance** | Multiple actors pulling the same stock toward different goals, actions cancel each other out, effort is wasted | | |
| **Tragedy of the Commons** | Shared, depletable resource overused because personal benefit > shared cost; no actor has incentive to hold back unilaterally | | |
| **Drift to Low Performance** | Bad past performance lowers the target, which allows more bad performance — standards erode over time in a vicious cycle | | |
| **Escalation** | Two actors each respond to the other's moves with more of the same, creating a reinforcing arms-race loop | | |
| **Success to the Successful** | Winners gain resources that let them win bigger next time; losers are starved of resources; outcome monopolizes over time | | |
| **Shifting the Burden / Addiction** | A quick symptom-fix reduces pressure to solve the root cause; over time the system becomes dependent on the fix and the underlying problem worsens | | |

### Additional Traps

**Non-linearities:** Are there thresholds in the system where a small additional nudge triggers a
sudden, large, hard-to-reverse shift? (Stock-recruitment collapse in fisheries; bank runs; ecological
tipping points.) Identify any suspected threshold stocks.

**Bounded rationality:** Are actors making locally rational decisions that produce globally
irrational outcomes? Name the actor, the information they lack, and the collective result.

---

## Phase 3: Leverage Point Analysis

Meadows' 12 leverage points, ordered **least to most powerful**. For each point that applies to
the mapped system, fill in the intervention and feasibility.

> **The Leverage Point Paradox:** The most commonly targeted interventions (numbers, subsidies,
> tax rates) are the least effective. The most powerful interventions (paradigm shifts, system
> goals) are systematically ignored by policy. Flag this explicitly when you see it.

### Low Leverage — Constants and Structure (12–9)

| Point | What it is | Intervention | Feasibility | Notes |
|---|---|---|---|---|
| **12 — Numbers** | Tax rates, subsidies, standards, quotas | | High/Med/Low | Most lobbied, least impactful |
| **11 — Buffer size** | Size of a stock relative to its flows (large buffers are stable; small buffers are fragile) | | | |
| **10 — Material flows** | Physical infrastructure — pipes, roads, factories (expensive and slow to change) | | | |
| **9 — Delays** | Time lags between action and feedback | | | Reducing delays often has high impact despite its "low" ranking |

### Medium Leverage — Information and Feedback (8–6)

| Point | What it is | Intervention | Feasibility | Notes |
|---|---|---|---|---|
| **8 — Balancing loop strength** | Strength of negative feedback (e.g., how aggressively a regulator responds to deviations) | | | |
| **7 — Reinforcing loop gain** | Speed of a runaway loop (faster = more dangerous; slower = more controllable) | | | |
| **6 — Information flows** | Who gets what information when; missing feedback is a major system failure mode | | | Often high impact in practice — easy to overlook |

### High Leverage — Rules, Goals, Paradigms (5–1)

| Point | What it is | Intervention | Feasibility | Notes |
|---|---|---|---|---|
| **5 — Rules** | Incentives, constraints, enforcement mechanisms — who can do what | | | |
| **4 — Self-organization** | The system's power to change its own structure, learn, and evolve | | | |
| **3 — System goals** | What the system is actually optimizing for | | | Changing this changes everything downstream |
| **2 — Paradigm** | The shared mental model, beliefs, and assumptions from which the system arose | | | Hard to change; enormously powerful when shifted |
| **1 — Transcend paradigms** | Ability to hold all paradigms lightly; not being locked into any one worldview | | | Rarely actionable, but worth naming |

### Top Recommendations

After filling the table, highlight the **top 2–3 interventions** — the highest-leverage points
that are also feasible to act on. Format:

```
RECOMMENDED INTERVENTIONS
─────────────────────────
1. [Point #N — Name]: [one-sentence description]
   Why: [what changes in the system if this lever moves]
   Feasibility: [who can do this and how hard]

2. ...

3. ...
```

---

## Phase 4: Intervention Recommendations

For each recommended intervention from Phase 3, produce a concrete implementation plan.

### Intervention Template

```
## Intervention: [Name]
**Leverage point:** #N — [category]
**System target:** [which stock, flow, loop, or goal this changes]

### What to change
[Specific, actionable description — not "improve communication" but
"create a public dashboard showing fish stock levels updated weekly,
visible to all fleet operators before booking trips"]

### Who holds this lever
[Actor, institution, or role with the authority or capability to make this change]

### Expected behavior change
[What system behavior shifts if the lever is moved — use stock/flow language]
"If [intervention], then [stock] should [increase/decrease/stabilize] because
[causal chain], reducing [problem behavior] within [timeframe]."

### Watch for
- [Likely resistance: who benefits from the current structure]
- [Rebound effects: ways the system might route around the fix]
- [Unintended consequences: second-order effects to monitor]

### Monitoring signal
[The single most important metric or observable that shows this intervention is working.
Must be directly tied to the target stock or feedback loop.]
```

---

### Living in the System Checklist

Meadows closes the book with principles for navigating systems we cannot fully control.
After presenting interventions, run this checklist and flag any gaps:

```
LIVING IN THE SYSTEM
────────────────────
[ ] Get the beat first — watch actual system behavior over time before
    intervening. Data before action.

[ ] Surface mental models — all system maps are simplifications. Write down
    the assumptions in this analysis; they are wrong in some way.

[ ] Distribute information — who in the system lacks feedback they need?
    Hoarded or distorted information is a leading cause of system failure.

[ ] Locate responsibility in structure — avoid blaming individual actors.
    Ask: what incentive structure produced this behavior?

[ ] Design for resilience — redundant feedback loops over pure efficiency.
    What fails if a single connection breaks?

[ ] Stay adaptive — the system will surprise you. Set a review date to
    reassess this analysis after the first intervention has run.
```

Present the full analysis as a structured report. Offer to drill deeper into any single phase or produce a one-page executive summary on request.

---

## Design Mode (`--design`)

When `--design` is active, all phases shift from analysis to construction:

**Phase 1 (Design):** Help the user define the system they want to build:
- What stocks should exist, and at what levels?
- What inflows and outflows will govern each stock?
- Which reinforcing loops are desired (growth engines)?
- Which balancing loops are essential (governors, safety valves)?
- Where should delays be minimized? Where is delay acceptable?

**Phase 2 (Design):** Proactively flag which archetypes the proposed design is structurally
vulnerable to, before it's built. Ask: does this design create a commons? Does it create a
success-to-the-successful dynamic? Does it offer a symptom-fix escape hatch?

**Phase 3 (Design):** Guide toward high-leverage design choices:

> **Note on coverage:** Points 12–7 (numbers, buffers, material flows, delays, loop gains, loop strengths) are shaped by your stock/flow and loop design choices in Phase 1. Phase 3 focuses on the structural and paradigmatic levers (6–1) that are fixed at design time and hardest to change later.

- What information should every key actor receive? (Point 6)
- What rules will govern the system? Are they enforceable? (Point 5)
- What is the explicit goal the system will optimize for? (Point 3)
- Can the system be designed to learn and evolve its own structure over time? (Point 4 — self-organization)
- What paradigm does this system embody, and is that paradigm correct? (Point 2)

**Phase 4 (Design):** Produce a design spec with explicit resilience mechanisms:
- Named backup feedback loops for each critical balancing function
- Explicit threshold stocks with defined intervention triggers
- Monitoring dashboard specification (what gets measured and by whom)
- Review cadence for reassessing whether the system's actual purpose has drifted from intent

---

## Anti-Patterns to Call Out

Flag these explicitly whenever you spot them — whether in an existing system being analyzed
or in a proposed design:

| Anti-pattern | What it looks like | Correct response |
|---|---|---|
| **Element fixation** | Analysis focuses on visible parts (people, buildings, budgets) while ignoring interconnections | Redirect to flows and feedback loops |
| **Goal displacement** | Stated purpose and actual behavior have diverged; metrics being gamed | Name the real purpose; redesign the metric |
| **Delay blindness** | Assuming cause and effect are close in time and space | Map every delay explicitly; estimate lag |
| **Single-variable fix** | Proposing to change one number while the rest of the structure stays the same | Check for compensating feedback loops that will neutralize the fix |
| **Resilience sacrifice** | Optimizing for efficiency by eliminating redundancy | Name what breaks when the single path fails |
| **Paradigm lock** | Proposing only technical fixes for a problem rooted in a shared mental model | Escalate to leverage points 2–3 |
| **Short-term symptom addiction** | Repeated application of a fix that works briefly but worsens the root cause | Name the reinforcing loop being created; identify structural alternative |

Flag any anti-pattern you spot throughout the live analysis — not just during this final review pass.
