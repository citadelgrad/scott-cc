# Credits and Attribution

The `review-panel` plugin vendors and adapts material from several open-source
projects. This document tracks attribution for all sources, and defines the
license-header policy that applies to every vendored or adapted file in this
plugin.

Each section below will be filled in by the later vendoring task responsible
for that source, noting which files were copied verbatim vs. adapted.

## EveryInc/compound-engineering-plugin (MIT)

_To be filled in by the vendoring task that pulls from this source._

## codybrom/clairvoyance (MIT)

Full design-review lens set (16 skills) and the `clean-room-alternative` agent,
vendored verbatim from https://github.com/codybrom/clairvoyance. Each file
below carries a `<!-- Vendored from codybrom/clairvoyance (MIT). See
CREDITS.md. -->` attribution comment (placed after YAML frontmatter where
present) since none of the source files had their own license headers.

All files copied verbatim, no adaptation:

- `skills/abstraction-quality/SKILL.md`
- `skills/code-evolution/SKILL.md`
- `skills/comments-docs/SKILL.md`
- `skills/comments-docs/references/comments-first-workflow.md`
- `skills/complexity-recognition/SKILL.md`
- `skills/deep-modules/SKILL.md`
- `skills/design-it-twice/SKILL.md`
- `skills/design-it-twice/references/pre-mortem-fallback.md`
- `skills/design-review/SKILL.md`
- `skills/design-review/references/workflow-builder.md`
- `skills/diagnose/SKILL.md`
- `skills/error-design/SKILL.md`
- `skills/general-vs-special/SKILL.md`
- `skills/information-hiding/SKILL.md`
- `skills/information-hiding/references/back-door-leakage.md`
- `skills/module-boundaries/SKILL.md`
- `skills/naming-obviousness/SKILL.md`
- `skills/pull-complexity-down/SKILL.md`
- `skills/pull-complexity-down/references/configuration-parameter-audit.md`
- `skills/red-flags/SKILL.md`
- `skills/red-flags/references/flag-interaction-map.md`
- `skills/strategic-mindset/SKILL.md`
- `agents/clean-room-alternative.md`

## obra/superpowers (MIT)

Review-related artifacts only. Non-review workflow skills (brainstorming,
writing-plans, executing-plans, tdd, using-git-worktrees) are explicitly
excluded from this plugin.

- `contracts/reviewer-output.md` — adapted from
  `skills/requesting-code-review/code-reviewer.md`. Content preserved
  verbatim (Strengths / Issues: Critical, Important, Minor w/ file:line /
  Recommendations / Assessment structure); attribution header added.
- `contracts/verification-before-completion.md` — adapted from
  `skills/verification-before-completion/SKILL.md`. Content preserved
  verbatim; attribution header added.
- `scripts/review-package` — copied verbatim from
  `skills/subagent-driven-development/scripts/review-package`, with its
  internal call to `sdd-workspace` updated to call the renamed `workspace`
  script below.
- `scripts/workspace` — copied verbatim (content unchanged) from
  `skills/subagent-driven-development/scripts/sdd-workspace`; renamed to
  `workspace` for this plugin.

## DietrichGebert/ponytail (MIT)

_To be filled in by the vendoring task that pulls from this source._

## mattpocock/skills (MIT)

_To be filled in by the vendoring task that pulls from this source._

## Snippet-Cannibalization Sources

These are not vendored files but sources of cannibalized code patterns and
ideas, credited here as inspiration/snippet sources distinct from the
verbatim-vendored MIT plugins above (used primarily by the domain-modeling
skill).

### jpablo/vibe-types (Apache-2.0)

_To be filled in by the domain-modeling vendoring task. Retain the upstream
NOTICE file contents here if present in the source repo._

### 0xBigBoss/claude-code

_To be filled in by the domain-modeling vendoring task, only if the source
repo's license is verified as compatible._

## License-Header Policy

This policy applies to every file copied or adapted into this plugin from an
external source:

1. **Preserve original license headers verbatim.** If a copied file already
   contains a license/copyright header, that header must be kept intact and
   unmodified at the top of the file, exactly as it appeared upstream.
2. **Attribute files with no existing header.** If a vendored or adapted file
   has no license header of its own (e.g. a plain Markdown skill file), add a
   one-line attribution comment near the top of the file, in the
   language-appropriate comment syntax, pointing back to this CREDITS.md:

   - Markdown / HTML:
     `<!-- Vendored from <org>/<repo> (MIT). See CREDITS.md. -->`
   - Shell scripts:
     `# Vendored from <org>/<repo> (MIT). See CREDITS.md.`
   - Adapted (not verbatim) files should say "Adapted from" instead of
     "Vendored from", e.g.
     `<!-- Adapted from <org>/<repo> (MIT). See CREDITS.md. -->`

3. **Record verbatim vs. adapted status in this file.** Each per-source
   section above must note, for every file it introduces, whether that file
   was copied verbatim or adapted, so provenance stays auditable.
