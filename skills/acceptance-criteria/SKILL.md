---
name: acceptance-criteria
description: >-
  Generate acceptance criteria for a user story or feature. Produces testable,
  specific criteria in Gherkin (Given/When/Then), checklist, or rules-based
  format with a completeness check. Use when writing or reviewing AC for any
  story, ticket, or feature spec.
allowed-tools: Read, Write
---

# Acceptance Criteria Skill

You are helping write or review acceptance criteria (AC) for a software feature.
AC are the specific, testable conditions that define when a story is **done** —
they are story-specific (unlike the Definition of Done, which is a universal
team checklist applied to every story).

## Parse Arguments

Extract from `$ARGUMENTS`:

| Argument | Effect |
|----------|--------|
| (none) | Ask for the story/feature, then produce Gherkin AC |
| `--format gherkin` | Output in Given/When/Then format (default) |
| `--format checklist` | Output as a simple checkbox list |
| `--format rules` | Output as "The system must..." rules (good for business logic) |
| `--review` | Review existing AC instead of generating new ones |
| `--story "<text>"` | Inline story — skip the prompt |

---

## Phase 1: Gather Context

If no story was provided inline via `--story`, ask:

> **What is the user story or feature you need acceptance criteria for?**
> Include: who the user is, what they're doing, and why it matters.
> Example: "As a logged-in user, I want to reset my password via email so I can regain access when I forget it."

Also ask (or infer from context):
- **Format**: Gherkin, checklist, or rules? (default: Gherkin)
- **Scope**: Are there known edge cases, error states, or constraints to cover?
- **Existing AC**: Any draft criteria already written? (enables `--review` mode)

---

## Phase 2: Understand the Story

Before writing, decompose the story into:

1. **Happy path** — the primary success scenario
2. **Alternate paths** — valid variations of the flow
3. **Error/failure scenarios** — invalid input, system errors, permission denials
4. **Boundary conditions** — limits, empty states, maximums
5. **Non-functional requirements** — performance thresholds, accessibility rules (if stated)

Write these down internally before generating AC. Every category above should
produce at least one criterion unless you can explicitly justify omitting it.

---

## Phase 3: Generate Acceptance Criteria

### Format: Gherkin (Given/When/Then)

Use for complex flows, BDD teams, or anything that will drive automated tests.

**Rules (research-verified):**
- **One behavior per scenario.** Each `Scenario:` block covers exactly one business rule or path.
- **Declarative, not imperative.** Describe *what* the system does, not *how* to click through the UI.
  - ✗ Imperative: `When I click the "Submit" button and wait for the spinner to disappear`
  - ✓ Declarative: `When I submit the form`
- **Self-contained.** Each scenario must be runnable in isolation — no shared state between scenarios, no "assuming scenario 2 ran first."
- **No vague outcomes.** `Then` clauses must be objectively verifiable.

**Template:**
```gherkin
Scenario: [concise behavior label]
  Given [precondition — system state before the action]
  When  [triggering action — one thing the user or system does]
  Then  [expected outcome — observable, testable result]

Scenario: [error/edge case label]
  Given [precondition]
  When  [action that triggers the failure]
  Then  [specific error state or system response]
```

Use `And` to extend a step (not to add a second behavior):
```gherkin
  Given I am a logged-in user
  And   my account has been active for more than 30 days
```

---

### Format: Checklist

Use for simple flows, non-technical stakeholders, or stories with minimal branching.

```
Acceptance Criteria:
☐ [Specific, verifiable condition]
☐ [Another condition]
☐ [Error/edge case condition]
```

Each item must pass the testability gate (see Phase 4).

---

### Format: Rules-based

Use for business logic, validation rules, or regulatory requirements.

```
The system must:
- [Rule 1: specific, measurable behavior]
- [Rule 2: ...]

The system must not:
- [Exclusion or constraint]
```

---

## Phase 4: Testability Gate

**Every criterion must pass this gate before inclusion.** Ask for each item:

> *Can a tester look at this criterion and give it an unambiguous PASS or FAIL?*

If the answer is "it depends" or "that's subjective" — rewrite or remove it.

### Vague language red list — replace with specifics:

| ❌ Vague | ✓ Specific |
|---------|-----------|
| loads quickly | loads within 3 seconds |
| user-friendly | user completes checkout in ≤ 3 steps |
| handles errors gracefully | displays the message "Unable to connect. Try again." |
| works on mobile | renders correctly on viewport widths 375px–768px |
| secure | passwords are hashed using bcrypt (min cost factor 12) |
| accessible | meets WCAG 2.1 AA for the affected components |
| large number of users | supports 1,000 concurrent users |
| recent | within the last 30 days |

---

## Phase 5: Completeness Check

After generating AC, run this checklist. Flag any category that has zero coverage
and either add a criterion or explicitly note "not applicable — [reason]."

```
COMPLETENESS REVIEW
-------------------
[ ] Happy path          — Does at least one AC cover the primary success flow?
[ ] Alternate paths     — Are valid variations covered (e.g., different user roles, optional fields)?
[ ] Error/failure       — Are failure states explicit (invalid input, system unavailable, permission denied)?
[ ] Boundary conditions — Are limits tested (empty state, max length, first/last page, zero results)?
[ ] Non-functional      — Are any stated performance, accessibility, or security requirements captured?
[ ] DoD excluded        — Are DoD items (code reviewed, tests passing) absent from this list?
```

The last check matters: "Code is reviewed" or "Tests are written" belong in the
team's Definition of Done — not in story-level AC.

---

## Phase 6: Output

Present the final AC with this structure:

```
## Acceptance Criteria: [Story Title]

### Scenarios / Criteria
[formatted AC block]

### Completeness Notes
[any gaps identified in Phase 5, or "All categories covered."]

### Out of Scope
[anything explicitly excluded and why — prevents scope creep disputes]
```

If in `--review` mode: present the original AC, then a critique against the
testability gate and completeness check, then a revised version.

---

## Anti-Patterns to Call Out

If you see these in existing AC (review mode) or catch yourself writing them, fix them:

- **Criteria that describe implementation** ("The backend stores the value in Redis") — AC describe *behavior*, not *how* it's built.
- **Duplicate DoD items** — "Unit tests pass" is not an acceptance criterion.
- **Compound scenarios** — two distinct behaviors in one Gherkin scenario means split it.
- **Passive outcomes** without observable effect — "The system processes the request" is not testable unless you say what "processed" looks like.
- **Missing actor** — Who performs the When? Be explicit: user, admin, background job, external system.
- **Scope creep bait** — "And also the user can export to PDF" buried in the Then. New behavior = new story.
