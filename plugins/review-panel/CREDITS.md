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

_To be filled in by the vendoring task that pulls from this source._

## obra/superpowers (MIT)

_To be filled in by the vendoring task that pulls from this source._

## DietrichGebert/ponytail (MIT)

_To be filled in by the vendoring task that pulls from this source._

## mattpocock/skills (MIT)

Source: https://github.com/mattpocock/skills, `skills/engineering/domain-modeling/`.

Files copied verbatim, each with a one-line `Vendored from` attribution comment
added at the top (per the License-Header Policy below, since the source files
had no existing license header):

- `formats/CONTEXT-FORMAT.md` — verbatim copy of
  `skills/engineering/domain-modeling/CONTEXT-FORMAT.md`
- `formats/ADR-FORMAT.md` — verbatim copy of
  `skills/engineering/domain-modeling/ADR-FORMAT.md`

Explicitly NOT copied from this source: `domain-modeling/SKILL.md` (confirmed
inadequate — no type-driven content) and any `code-review`, `codebase-design`,
or `writing-great-skills` material (overlaps with other vendored sources).
This plugin's own `skills/domain-modeling/SKILL.md` and
`skills/adversarial-reviewer/SKILL.md` are authored from scratch by a separate
task and are not derived from mattpocock's files.

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
