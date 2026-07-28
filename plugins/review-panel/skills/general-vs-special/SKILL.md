---
name: general-vs-special
description: >-
  Use when the user asks to check interface generality, when a module has
  if-branches or parameters serving only one caller, when getters/setters expose
  internal representation, or when an interface is over-specialized. Evaluates
  general-purpose design, special-general mixture, and defaults. Not for
  information-leakage (use information-hiding) or configuration-parameter
  necessity (use pull-complexity-down).
argument-hint: "[file or module path]"
allowed-tools: Read, Grep
metadata:
  category: pattern
---

# General vs. Special-Purpose Review Lens

When invoked with $ARGUMENTS, focus the analysis on the specified file or module. Read the target code first, then apply the checks below.

General-purpose modules are surprisingly simpler, deeper and less effort to build. They produce better information hiding and can even provide these benefits when used in a single context. Because a general-purpose interface doesn't need to know about specific callers, the knowledge always stays where it belongs.

## When to Use

- Designing a new module, API, or utility
- When a module has use-case-specific logic embedded in it
- When a module's interface is cluttered with rarely-used parameters
- When deciding between a flexible API and a specific one

## Core Principles

### The Generality Test

> "What is the simplest interface that will cover all my current needs?" — John Ousterhout, _A Philosophy of Software Design_

Not "the most general interface possible." The target is **somewhat general-purpose**.

- **Functionality**: Scoped to current needs. Doesn't build features you don't need.
- **Interface**: General enough to support multiple uses. Doesn't tie it only to today's caller.

**A general-purpose interface is usually simpler than a special-purpose one**. Fewer methods means lower cognitive load. Fewer methods per capability is the signal of increasing generality.

Two companion questions:

- **In how many situations will this method be used?** If exactly one, it's over-specialized.
- **Is this API easy to use for my current needs?** If callers must write loops or compose many calls for basic tasks, the abstraction level is wrong.

### Special-General Mixture

Special-purpose code mixed into a general-purpose module makes it shallower. Two forms:

#### At the Interface

Methods or parameters that only serve specific callers. The interface widens, and policy decisions from a higher layer get encoded in a lower one.

#### Inside Method Bodies

Special cases tend to show up as extra `if` statements. Instead of adding more of them, try to create a design where they disappear. A search function that returns `null` when nothing is found forces every caller to check for `null` before using the result. If you return an empty list instead, the check loop runs zero times on its own with no extra check required.

### Getters/Setters as Representation Leakage

Before writing a getter or setter, ask the gatekeeping question: should callers know about this property at all? A `rename()` method absorbs related logic and hides the representation; the goal is for the module to do work, not expose data. For the fuller audit of why `private` plus getter/setter doesn't hide anything, see **information-hiding**.

### Defaults as a Depth Tool

**Every sensible default is one less decision pushed to callers.** If nearly every user of a class needs a behavior, it belongs inside the class by default.

Gatekeeping question: "Will callers be able to determine a better value than we can determine here?" The answer is usually no.

### The Default Position

When unsure, err on the side of slightly more general. A slightly-too-general interface has unused capabilities (low cost). A slightly-too-special interface requires a rewrite when the second use case arrives (high cost).

But "slightly more general" means one step, not three. Generality should come from simplifying the interface, not from adding parameters.

## Review Process

1. **Identify the general mechanism**: What is the core operation?
2. **Separate special from general**: Is caller-specific logic in the core? Special-case `if` branches that could be eliminated?
3. **Apply the generality test**: Simplest interface that covers all current needs?
4. **Audit getters/setters**: Exposing representation or abstraction?
5. **Review defaults**: Could required parameters become optional?
6. **Recommend**: Push specialization to edges. Deepen with defaults.

## Relationship to Other Lenses

This skill asks "is this interface over-specialized for one caller?": a single-module, single-interface question. **information-hiding** asks the broader question of whether a design decision is known by more than one module at all; over-specialization is one *cause* of leakage (a general-purpose module absorbing a caller-specific method), but information-hiding covers leakage that has nothing to do with generality (e.g. two modules independently encoding the same file format). **pull-complexity-down** is about a different axis entirely: whether complexity is pushed to callers or absorbed internally, not whether an interface serves one caller or many. Use this skill when a module's interface looks tailored to a single caller; use **information-hiding** when the concern is a design decision leaking across a boundary; use **pull-complexity-down** when the concern is who does the work, not who the interface serves.

Red flag signals for generality are cataloged in **red-flags** (Special-General Mixture, Overexposure).

## Limitations
- Use this skill only when the task clearly matches the scope described above.
- This is a read-only review lens — it identifies issues but does not write or refactor code.
- Findings are diagnostic signals, not definitive verdicts — use judgment in context.
- Stop and ask for clarification if the target scope, module boundary, or review criteria are unclear.
