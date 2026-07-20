---
name: plan-security-review
description: Runs a lightweight threat-model checkpoint over a plan/PRD/spec document at the end of planning — trust boundaries crossed, new data flows, authn/authz surface changed, secrets introduced, third-party deps added — and produces a CLEAR/TRIGGERED/N/A findings report plus a one-paragraph go/no-go. Use when a planning or grilling session ends with a build-ready plan, or when the user asks for a "plan security review", "threat-model checkpoint", or "pre-build security pass". Not for reviewing code diffs (that is the panel's security seat, review-panel's Security seat casting security-suite:security-engineer), and not a comprehensive security audit.
argument-hint: "[plan/PRD/spec document path, or none if already in conversation]"
allowed-tools: Read, Grep, Glob, WebFetch
---

# Plan Security Review (Planning-Stage Threat-Model Checkpoint)

The planning-stage counterpart of the review seat: a checkpoint at the end of
planning, before build, not a comprehensive audit. Run this once a plan is
build-ready, before implementation starts.

**Boundary:** Not for reviewing code diffs — that is the panel's security seat
(review-panel's `Security` seat, which casts `security-suite:security-engineer`
on diffs at review time). This skill only reads plan/PRD/spec documents.

## When to Apply

- A planning or grilling session (e.g. `grill-with-docs`) has just concluded
  with a build-ready plan
- The user asks for a "plan security review", "threat-model checkpoint", or
  "pre-build security pass"
- Reviewing a plan/PRD/spec document before implementation begins
- **Not** for code diffs — use review-panel's Security seat instead
- **Not** a comprehensive security audit — this is a lightweight checkpoint

## How to Review

When invoked with `$ARGUMENTS` (a path) or against a plan already in
conversation context:

1. Read the plan/PRD/spec document first (do not skim from memory).
2. Extract security-relevant deltas — look specifically for:
   - New endpoints or new data flows
   - Authn/authz surface changes
   - Secrets or credentials introduced
   - Third-party dependencies added
   - Trust boundaries crossed
3. Map each delta to OWASP cheatsheet topics, reusing
   [security-advisor.md](../../agents/security-advisor.md)'s "Available Topics
   by Category" table — link to it, do not duplicate it. The table below seeds
   the most common delta → topic mappings for quick lookup:

   | Security-relevant delta | OWASP topic(s) |
   |---|---|
   | New login/auth endpoint | `Authentication`, `Session_Management`, `Password_Storage`, `Multifactor_Authentication` |
   | New data flow / API endpoint | `REST_Security`, `Input_Validation` |
   | Authz surface change (roles, permissions, ownership checks) | `Authentication`, `REST_Security` |
   | Secrets/credentials introduced | `Secrets_Management`, `Cryptographic_Storage`, `Key_Management` |
   | Third-party dependency added | `CI_CD_Security`, `Infrastructure_as_Code_Security` |
   | Trust boundary crossed / new data flow | `Threat_Modeling`, `Secure_Product_Design` |
   | User-supplied data reaches a query | `SQL_Injection_Prevention` |
   | User-supplied data gets rendered | `Cross_Site_Scripting_Prevention` |
   | New state-changing operation (form/mutation) | `Cross-Site_Request_Forgery_Prevention` |
   | Data encrypted at rest / in transit | `Cryptographic_Storage`, `Transport_Layer_Security` |

4. Fetch or fall back:
   - **Online:** `WebFetch` the mapped cheatsheet(s) using the URL pattern
     from security-advisor.md
     (`https://cheatsheetseries.owasp.org/cheatsheets/{Topic}_Cheat_Sheet.html`)
     for citation-quality detail.
   - **Offline / WebFetch unavailable:** fall back to the built-in checklist
     below plus the OWASP topic *names* from the mapping table — topic names
     alone are sufficient for citation, even without live fetch content. State
     the degraded mode explicitly in the output (see Output Contract).
5. Emit findings as `CLEAR` / `TRIGGERED` / `N/A` lines, one per delta area
   checked (same vocabulary as `domain-modeling`, for future merge-ability).
6. Close with a one-paragraph go/no-go recommendation.

### Built-in checklist (offline fallback)

Derived from [security-suite/README.md](../../README.md)'s Security
Checklist — use this when WebFetch is unavailable:

- No hardcoded secrets or credentials
- Input validation on all user inputs
- SQL injection protection
- XSS prevention
- CSRF protection for state-changing operations
- Authentication and authorization properly implemented
- Sensitive data encrypted at rest and in transit

## Output Contract

Output is **markdown**, using the same `CLEAR`/`TRIGGERED`/`N/A` screening
vocabulary as `review-panel`'s `domain-modeling` skill, so findings can merge
cleanly with other skills that share this vocabulary in the future. Only a
`TRIGGERED` line is a reportable finding; `CLEAR` and `N/A` carry no severity
and are not forced.

For every `TRIGGERED` line, report:

`TRIGGERED — <plan section/feature> — <OWASP topic name> — <one-line rationale>`

Example: `TRIGGERED — §3 Login endpoint — Authentication — new credential
check needs a documented lockout/rate-limit policy before build`

If the pass ran in degraded (no-WebFetch) mode, say so explicitly with a
leading line, e.g.: `Degraded mode: WebFetch unavailable, built-in checklist
used.`

If a plan has no security-relevant delta, every line is `CLEAR`/`N/A` — say
so plainly with an explicit "no security-relevant surface" statement. Do not
force findings where none exist.

Close every run with a one-paragraph go/no-go recommendation, regardless of
how many findings triggered.

## Foundry note

This pass is designed to be schedulable as a pre-build gate (e.g. run against
a plan doc before a build profile starts). It does not create or modify any
Foundry recipe file itself — that wiring is a Foundry-side concern.
