# CLAUDE.md Management Best Practices

**Research date:** 2026-06-16
**Method:** Deep research — 104 agents, 22 sources, 25 adversarially-verified claims (13 confirmed, 12 killed)
**Primary sources:** Anthropic official docs (code.claude.com/docs/en/memory, features-overview, best-practices, context-window)

---

## TL;DR

- Root CLAUDE.md loads **in full on every request** — every token costs
- `@path` imports **do not save context** — they eagerly expand at session start (organizational only)
- Plain text references like `"See docs/foo.md"` **do not trigger auto-fetch** — dead text
- **Skills are the only genuine JIT mechanism** — body loads only on invocation
- **Subdirectory CLAUDE.md files** load on-demand when Claude reads files in that directory
- Target **under 200 lines** per file — attention degrades past this (not truncation)

---

## Verified Findings

### 1. Root CLAUDE.md is always-on, always-paid context (3-0)

CLAUDE.md loads its full content at session start and stays in every request. Token cost is proportional to file size, paid on every API call. Prompt caching reduces billing cost after the first turn but the content still occupies context-window space.

### 2. @path imports do NOT save context (3-0)

```
@path/to/docs/tool-overview.md   ← this loads eagerly, not lazily
```

Imported files are fully expanded into context at session launch alongside the CLAUDE.md that references them. A GitHub feature request for lazy loading (issue #11759) was closed as "not planned" — eager load is intentional design. `@path` is useful for **organization only**, not context savings.

### 3. Skills are the official JIT loading mechanism (3-0)

- Skill **descriptions** (one-liners) cost ~450 tokens at every session start
- Skill **bodies** load only when the skill is invoked
- Anthropic docs: *"For task-specific instructions that don't need to be in context all the time, use skills instead, which only load when you invoke them"*
- Skill bodies: *"long reference material costs almost nothing until you need it"*

**This is the answer to "reference another doc vs inline."** Move tool details to a Skill, not a @-referenced file.

### 4. Subdirectory CLAUDE.md files provide path-scoped JIT loading (3-0)

Files in subdirectories load on-demand when Claude reads files in that directory — not at session start. Root-level and parent-directory CLAUDE.md files load at launch; subdirectory ones do not.

> Caveat: implementation reliability has varied across client versions (documented VS Code extension regression in issue #24987). Verify against current Claude Code version.

### 5. 200-line target is the official size limit (3-0)

Anthropic docs verbatim: *"Size: target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence."*

- **Mechanism is attention degradation, not truncation** — files load in full regardless of length
- Anthropic names "The over-specified CLAUDE.md" as an explicit common failure pattern
- *"Bloated CLAUDE.md files cause Claude to ignore your actual instructions"*

### 6. What doesn't belong in CLAUDE.md (2-1)

Anthropic explicitly lists exclusions:

- Detailed API documentation → link to external docs or put in a Skill
- Long explanations or tutorials → Skill
- File-by-file descriptions of the codebase → never
- Tool overviews longer than ~50 tokens → Skill

*"A common mistake is adding extensive content without iterating on its effectiveness. Treat CLAUDE.md like code: review it when things go wrong, prune it regularly, and test changes by observing whether Claude's behavior actually shifts."*

---

## Refuted Claims (killed in verification)

| Claim | Vote |
|---|---|
| `.claude/rules/` with YAML frontmatter provides genuine JIT path-scoped loading | 0-3 |
| Plain text references (`"See docs/foo.md"`) enable JIT loading because Claude fetches on demand | 0-3 |
| @import supports nesting up to 5 levels deep | 0-3 |
| CLAUDE.md should be under 500 tokens | 0-3 |
| Files over 2,000 tokens should be audited as bloat | 0-3 |
| Code examples can be moved to external files and referenced for on-demand fetch | 1-2 |

---

## Recommended Content Routing

| Content type | Where it goes |
|---|---|
| Behavioral rules, conventions, project norms | Root CLAUDE.md (≤200 lines total) |
| Tool reference details (>50 tokens) | Dedicated Skill |
| API docs, tutorials, overviews | Skill or external link |
| Path-scoped rules for a subsystem | Subdirectory `CLAUDE.md` |
| Short always-needed reminders | Root CLAUDE.md (count the lines) |

---

## Open Questions

1. Do `.claude/rules/` with YAML frontmatter actually provide JIT path-scoped loading? (refuted 0-3 — unconfirmed mechanism)
2. What is the exact token count at the 200-line target? (no documented number)
3. Can Skills be auto-invoked based on file path/glob without manual invocation?
4. How does prompt caching interact with CLAUDE.md size — does caching change the calculus for files modestly over 200 lines?

---

## Implication for the `context-file-optimizer` Skill

The skill should **not** recommend `@path` imports as a context-saving technique. The correct guidance:

1. **Keep root CLAUDE.md under 200 lines of behavioral rules only**
2. **Move tool/reference details into Skills** — the only real JIT mechanism
3. **Use subdirectory CLAUDE.md files** for path-scoped context in large repos
4. **Prune and test iteratively** — don't add content without observing behavior change
