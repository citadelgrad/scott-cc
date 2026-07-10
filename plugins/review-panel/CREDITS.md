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

_To be filled in by the vendoring task that pulls from this source._

## Local Trial-Copies

The four sources below are **not** from the 5 main vendored MIT repos listed
above. They were trial-installed locally by Scott as user-level skills
(under `~/.agents/skills/<name>/`) prior to this repo's existence, from
sources whose upstream repository/license could not be independently
re-verified at copy time. This section is tracked separately from the 5
main source-repo sections for that reason.

**License/provenance status**: No license header, copyright notice, or
provenance comment was found at the top of any file in any of the 4 source
directories (checked every file, including `.js` scripts and `.md` docs).
No license is fabricated here — each skill is copied as-is with an explicit
"no header found" note. If the original upstream source and license are
later identified, update this section and add proper headers.

### adr-skill

Copied verbatim from `~/.agents/skills/adr-skill/` (local trial install,
origin unknown, no license header found in source). Includes 3 `.js`
scripts (`scripts/bootstrap_adr.js`, `scripts/new_adr.js`,
`scripts/set_adr_status.js`) that require Node.js to run.

- `SKILL.md` — verbatim, attribution comment added (no header in source).
- `scripts/bootstrap_adr.js`, `scripts/new_adr.js`, `scripts/set_adr_status.js` — content vendored as-is (no dependencies installed, no logic changes). This repo's pre-commit `biome check --write` hook auto-reformatted these 3 files on commit (2-space indent → tabs, line-wrap/trailing-comma style, one `let`→`const` for a never-reassigned binding). Whitespace/style only — verified no functional diff by diffing against the original source with `diff -w`.
- `assets/templates/adr-simple.md`, `assets/templates/adr-madr.md`, `assets/templates/adr-readme.md` — verbatim, no header in source. Left uncommented since these are meant to be copied out into user-authored ADR files verbatim.
- `references/adr-conventions.md`, `references/examples.md`, `references/review-checklist.md`, `references/template-variants.md` — verbatim, no header in source.
- `ADR-TEMPLATE.md` — **new file, added during this vendoring task** (not present in the original source). Provides a manual markdown-template fallback workflow for use when `scripts/*.js` cannot run because Node.js is unavailable, reproducing the directory-detection, filename, and template steps the scripts automate. Documented as the fallback path in `SKILL.md`.

### improve-codebase-architecture

Copied verbatim from `~/.agents/skills/improve-codebase-architecture/`
(local trial install, origin unknown, no license header found in source).

- `SKILL.md` — verbatim, attribution comment added (no header in source).
- `DEEPENING.md`, `INTERFACE-DESIGN.md`, `LANGUAGE.md` — verbatim, no header in source.

### grill-with-docs

Copied verbatim from `~/.agents/skills/grill-with-docs/` (local trial
install, origin unknown, no license header found in source).

- `SKILL.md` — verbatim, attribution comment added (no header in source).
- `ADR-FORMAT.md`, `CONTEXT-FORMAT.md` — verbatim, no header in source.

### tdd

Copied verbatim from `~/.agents/skills/tdd/` (local trial install, origin
unknown, no license header found in source).

- `SKILL.md` — verbatim, attribution comment added (no header in source), plus an inline redundancy-check note (see below).
- `deep-modules.md`, `interface-design.md`, `mocking.md`, `refactoring.md`, `tests.md` — verbatim, no header in source.

**Redundancy check against existing scott-cc skills**: No `tdd` skill exists
in this repo's own top-level `skills/` directory or elsewhere in the
`scott-cc` marketplace plugin. The closest comparable skill reachable from
this environment is `superpowers:test-driven-development` (from the
separately-installed `superpowers` plugin, not part of scott-cc). This local
`tdd` skill is **distinct, not redundant**:

- `superpowers:test-driven-development` is a strict process-discipline
  skill built around an "Iron Law" (no production code without a failing
  test written and observed failing first), with a rationalization-busting
  checklist aimed at preventing agents from skipping test-first discipline.
- This local `tdd` skill is design-philosophy-oriented, grounded in
  Ousterhout's *A Philosophy of Software Design* (deep modules, interface
  design for testability, what/when to mock, refactor candidates after
  green). It assumes test-first discipline and focuses on *how* to design
  testable interfaces and write tests that survive refactors.

The two are complementary (one governs *when*/*whether* to write the test,
the other governs *how* to design the code and test well) rather than
overlapping, so both are retained.

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
