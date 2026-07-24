# ADR: Canonical source for "delegate-first"

- Status: Decided
- Issue: scc-ncs.26
- Date: 2026-07-24

## Context

Three copies of "delegate-first" content existed and had diverged:

1. Global `~/.claude/skills/delegate-first/SKILL.md` (52 lines, user-global, outside this repo)
2. This repo's `commands/delegate-first.md` (52-53 lines, near-verbatim match to #1)
3. This repo's `skills/delegate-first/SKILL.md` (97 lines, independently drifted; adds a
   "Fork Trigger Checklist" section not present in #1 or #2)

A fourth location was checked as a precaution: `~/.claude/plugins/marketplaces/scott-cc/`
and `~/.claude/plugins/cache/scott-cc/scott-cc/{4.4.0,5.0.0,5.0.1}/`. These are **not**
an independent source — `marketplaces/scott-cc` is a separate git clone of this same
repo (`origin: git@github.com:citadelgrad/scott-cc.git`, currently one commit behind
this repo's HEAD at time of writing), and its `skills/delegate-first/SKILL.md` and
`commands/delegate-first.md` are byte-identical (clean `diff`) to this repo's copies.
The plugin cache directories are installed-version snapshots of the same lineage. They
require no separate decision and will inherit whatever this ADR designates as canonical
once the plugin is republished/reinstalled from this repo.

Content comparison:

- Copies #1 and #2 are near-verbatim twins of a terse draft: fork noisy work, keep
  quick/direct things inline, use `subagent_type: "fork"`, give a brief summary on
  return, respect explicit "do it inline" requests. Differences between them are
  cosmetic wording only (e.g. "Activate when..." vs "Use when...").
- Copy #3 (`skills/delegate-first/SKILL.md`) preserves every rule present in #1/#2 and
  adds: a "When to Use" section, a "Fork Trigger Checklist" (explicit bullet-form
  fork-vs-inline criteria), a "Parent-Thread Behavior" section, a "Prompting Forks
  Well" section with a worked example, and proper frontmatter (`license`, `tags`).
  Nothing in #3 contradicts #1/#2 — it is additive, forward drift, not a competing
  design.

## Decision

**Canonical source: this repo's `skills/delegate-first/SKILL.md` (97 lines).**

It is a strict superset of the other two copies' substance and materially more useful
(concrete, checklist-driven guidance vs. a terse restatement of the same rules). Copies
#1 and #2 have no content absent from #3, so there is nothing to lose by treating #3 as
canonical.

**Fork Trigger Checklist disposition: kept as-is**, in place, in the canonical copy
(`skills/delegate-first/SKILL.md`, `## Fork Trigger Checklist` section). It is the most
concrete and actionable part of the document and has no competing/conflicting version
in copies #1 or #2 to reconcile against — keeping it is a pure improvement, and
discarding it would be a regression with no offsetting benefit.

## Consequences

- `commands/delegate-first.md` (this repo) and the global
  `~/.claude/skills/delegate-first/SKILL.md` are non-canonical going forward. They are
  left untouched by this decision — no deletion or repointing is performed here.
- Follow-up work (tracked separately, not part of scc-ncs.26): update or retire
  `commands/delegate-first.md` and the global skill copy to match/point at the
  canonical `skills/delegate-first/SKILL.md`, and confirm the plugin
  marketplace/cache copies pick up the change on next publish/install.
