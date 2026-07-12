# Manual ADR Fallback (No-Node Environments)

Use this file when `scripts/new_adr.js`, `scripts/set_adr_status.js`, or
`scripts/bootstrap_adr.js` cannot run because Node.js is unavailable in the
current environment. It reproduces, by hand, the same fields the `.js`
scripts would generate — so an ADR authored this way is equivalent to one
produced by the scripts.

## Manual Workflow

1. **Find or choose the ADR directory.** Check, in order: `docs/decisions/`,
   `adr/`, `docs/adr/`, `docs/adrs/`, `decisions/`. If none exists, create
   `docs/decisions/` (MADR default) or `adr/` (simpler repos) — see
   `references/adr-conventions.md`.

2. **Choose a filename.**
   - If existing ADRs use numeric prefixes (`0001-...`), find the highest
     existing number in the directory and increment it: `000N-slug.md`.
   - Otherwise use a slug-only filename: `choose-database.md`.
   - Slugify the title: lowercase, spaces to hyphens, strip punctuation.

3. **Copy the template body below** (or `assets/templates/adr-simple.md` /
   `assets/templates/adr-madr.md` for the full versions) into the new file
   and fill every section — do not leave placeholder text.

4. **Update the index manually**, if the ADR directory has one
   (`README.md` or `index.md`): add a bullet linking to the new file,
   keeping existing ordering (numeric or date/alpha).

5. **To change status later** (accept/reject/deprecate/supersede), edit the
   `status:` field in the frontmatter directly, following the same rules
   `scripts/set_adr_status.js` would apply — see
   `references/adr-conventions.md` for valid status values and transitions.

## Minimal Template

Copy everything below the line into your new ADR file and fill in every
`{...}` placeholder. This mirrors the fields `scripts/new_adr.js --template
simple` would produce.

---

```markdown
---
status: "proposed"
date: {YYYY-MM-DD}
decision-makers: "{list everyone who owns the decision}"
---

# {short title, representative of solved problem and found solution}

## Context and Problem Statement

{Why does this decision need to happen now? What constraints exist? Include
enough background that someone (or an agent) reading this for the first
time can understand without follow-up questions.}

## Decision

{What are we choosing to do? Be specific — include scope and non-goals.}

## Consequences

* Good, because {positive consequence}
* Bad, because {negative consequence}
* …

## Implementation Plan

* **Affected paths**: {files and directories that change}
* **Dependencies**: {packages to add/remove/update}
* **Patterns to follow**: {existing code patterns to match}
* **Patterns to avoid**: {what NOT to do}

### Verification

- [ ] {how to confirm the decision was implemented correctly}
- [ ] {another verification criterion}

<!-- Optional — remove if not needed -->
## Alternatives Considered

* {Alternative 1}: {Why it was rejected, in one or two sentences.}
* {Alternative 2}: {Why it was rejected.}

<!-- Optional — remove if not needed -->
## More Information

{Related ADRs, PRs, issues, docs, or conditions that would trigger
revisiting this decision.}
```

For decisions with multiple real options that need structured pros/cons,
use the MADR-style fields from `assets/templates/adr-madr.md` instead
(adds `Decision Drivers`, `Considered Options`, `Decision Outcome`, and a
`Pros and Cons of the Options` section per option).
