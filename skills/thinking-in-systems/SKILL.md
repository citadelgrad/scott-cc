---
name: thinking-in-systems
description: >-
  Use when mapping, diagnosing, or redesigning any system — organizational,
  technical, ecological, or policy. Applies Donella Meadows' systems thinking
  framework: stocks/flows, feedback loops, system archetypes, leverage points,
  and concrete intervention recommendations.
license: MIT
metadata:
  category: pattern
  triggers: [systems-thinking, stocks-and-flows, feedback-loops, reinforcing-loop, balancing-loop, leverage-points, system-archetypes, tragedy-of-commons, policy-resistance, shifting-the-burden, root-cause-structure, Donella-Meadows]
sources:
  - "Meadows, Donella H. Thinking in Systems: A Primer. Chelsea Green Publishing, 2008."
---

# Thinking in Systems

Apply Donella Meadows' systems thinking framework to any system — organizational,
technical, ecological, or policy. The skill runs four phases: map the system's
structure, diagnose which system traps are active, rank leverage points by impact,
and produce concrete intervention recommendations.

## When to Use
- Analyzing why a system keeps producing the same bad outcomes despite repeated fixes
- Designing a new system and wanting to avoid classic failure traps from the start
- Mapping feedback loops, stocks, and flows in organizational or technical systems
- Diagnosing system archetypes (tragedy of the commons, shifting the burden, etc.)
- Ranking leverage points to find the highest-impact interventions
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

Check the mapped system against six recurring archetypes. For detailed framework and tables, see [archetypes.md](references/archetypes.md).

> **If `--focus leverage` is active:** Do a single-pass only — mark each archetype Present/Absent with one line of evidence, then proceed directly to Phase 3.

Also check for non-linearities (tipping points, stock-recruitment collapse) and bounded rationality traps (locally rational decisions producing globally irrational outcomes).

---

## Phase 3: Leverage Point Analysis

Identify highest-leverage interventions using Meadows' 12-point framework. See [leverage-points.md](references/leverage-points.md) for the complete framework with all tables and categories (least to most powerful).

> **The Leverage Point Paradox:** The most commonly targeted interventions (numbers, subsidies, tax rates) are the least effective. The most powerful interventions (paradigm shifts, system goals) are systematically ignored by policy.

After filling the leverage points table, highlight the **top 2–3 interventions** that are both high-impact and feasible to act on.

---

## Phase 4: Intervention Recommendations

For each recommended intervention from Phase 3, produce a concrete implementation plan using the intervention template and living-in-the-system checklist. See [interventions-and-checklists.md](references/interventions-and-checklists.md) for the complete template and checklist.

Present the full analysis as a structured report. Offer to drill deeper into any single phase or produce a one-page executive summary on request.

---

## Design Mode (`--design`)

When `--design` is active, all four phases shift from analysis to construction. Help the user build a new system from scratch, avoiding classic failure traps from the start. See [design-mode.md](references/design-mode.md) for detailed phase-by-phase guidance on defining structure, detecting vulnerabilities, making high-leverage design choices, and producing resilient specifications.

---

## Anti-Patterns to Call Out

Flag seven recurring analysis traps whenever you spot them during live analysis — not just at the end. See [anti-patterns.md](references/anti-patterns.md) for the complete table with definitions and correct responses.

## Limitations
- Use this skill only when the task clearly matches the scope described above.
- Systems thinking is a diagnostic and design framework, not an execution plan — it identifies leverage points, not implementation steps.
- Requires sufficient information about the system's structure; stop and ask for clarification if stocks, flows, or boundaries are unclear.
- Model accuracy depends on the quality of inputs — garbage in, garbage out.
- Does not replace domain expertise in the specific system being analyzed (organizational, ecological, policy, etc.).
