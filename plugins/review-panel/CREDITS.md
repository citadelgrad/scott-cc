# Credits and Attribution

The `review-panel` plugin vendors and adapts material from several open-source
projects. This document tracks attribution for all sources, and defines the
license-header policy that applies to every vendored or adapted file in this
plugin.

Each section below will be filled in by the later vendoring task responsible
for that source, noting which files were copied verbatim vs. adapted.

## EveryInc/compound-engineering-plugin (MIT)

**Not vendored.** No files, code, or verbatim text from this source appear anywhere in this
plugin. `reviewers/persona-catalog.md` (scc-ns8.9) credits this source as a casting-philosophy
inspiration only: its `/ce:review` command casts reviewer seats from a persona-catalog-style
manifest using LLM judgment against actual diff content (not keyword/path matching), combines a
small always-on core with risk-triggered additions, fails closed on casting ambiguity, and tiers
models (top-tier for correctness/security/adversarial seats, mid-tier for the rest). This
plugin's `persona-catalog.md` independently reimplements that *casting philosophy* for this
plugin's own seat roster; no compound-engineering source file was read, copied, or paraphrased.

**Live-scan discovery note (scc-ns8.11, manual check, 2026-07-10):** confirmed by direct
filesystem inspection that `compound-engineering` was installed on the machine this plugin was
authored on (present under
`~/.claude/plugins/marketplaces/every-marketplace/plugins/compound-engineering/`, with a matching
entry in `~/.claude/plugins/cache/every-marketplace/compound-engineering/`). Its ~15 review
personas — `agent-native-reviewer`, `architecture-strategist`, `code-simplicity-reviewer`,
`data-integrity-guardian`, `data-migration-expert`, `deployment-verification-agent`,
`dhh-rails-reviewer`, `julik-frontend-races-reviewer`, `kieran-python-reviewer`,
`kieran-rails-reviewer`, `kieran-typescript-reviewer`, `pattern-recognition-specialist`,
`performance-oracle`, `schema-drift-detector`, `security-sentinel` — live under that plugin's
`agents/review/*.md`, **not** under its `skills/` tree, and are surfaced to the host session as
dispatchable `compound-engineering:review:<persona>` agent types (independently confirmed: this
exact session's own available-agent-types list included all of the above under that naming
scheme). `reviewers/references/cast-and-spawn.md`'s live-scan Step 1 originally said "enumerate
skills," which — read literally — would have walked `skills/` directories only and silently missed
all ~15 of these, since compound-engineering's `skills/` tree holds unrelated skills (e.g.
`document-review`, `agent-native-architecture`) rather than the review personas themselves. Step 1
and Step 3 were amended (this task, scc-ns8.11) to explicitly enumerate agent types as a second
source alongside skill directories, closing that gap. This was a manual, one-time verification on
the machine/session available at authoring time, not an automated test — a live-scan on a
different machine without compound-engineering installed correctly finds nothing from that source.

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

Two review seats vendored verbatim from the upstream `skills/` directory.
Both files have a one-line `<!-- Vendored from DietrichGebert/ponytail (MIT).
See CREDITS.md. -->` attribution comment inserted immediately after the YAML
frontmatter (per the License-Header Policy below).

- `skills/ponytail-review/SKILL.md` — verbatim (diff-scoped simplicity review seat)
- `skills/ponytail-audit/SKILL.md` — verbatim (repo-scoped simplicity audit seat)

Explicitly out of scope and NOT vendored: `ponytail-debt`, `ponytail-gain`,
`ponytail-help`, the base `ponytail` generation-time persona/mode, and its
hooks, statusline, and MCP server config. These are a separate UX decision
and were confirmed absent from `plugins/review-panel/` via `fd` search
(zero matches for `ponytail-debt|ponytail-gain|ponytail-help`, zero matches
for a bare `ponytail` skill, and zero matches for `hooks|statusline|mcp`).

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
- `ADR-FORMAT.md`, `CONTEXT-FORMAT.md` — originally copied verbatim (no header in source), but were near-duplicates of the mattpocock-vendored `formats/ADR-FORMAT.md` / `formats/CONTEXT-FORMAT.md` and had already started to drift (this local `CONTEXT-FORMAT.md` had gained a Relationships/Example-dialogue/Flagged-ambiguities structure the canonical copy lacked). Consolidated: the canonical `formats/CONTEXT-FORMAT.md` was updated to fold in those improvements, and both local copies were deleted in favor of `SKILL.md` referencing `formats/CONTEXT-FORMAT.md` and `formats/ADR-FORMAT.md` directly. See "mattpocock/skills (MIT)" above.

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

Source: https://github.com/jpablo/vibe-types. This repo was **not** vendored,
copied, or fetched — this task ran offline with no network access, so no
verbatim text from `vibe-types` appears anywhere in this plugin.

What was actually done: `skills/domain-modeling/TECHNIQUES.md` and
`skills/domain-modeling/WORKED-EXAMPLE.md` were authored from scratch, using
`vibe-types`' publicly-known catalog entry **names** as a checklist of
well-established, generic patterns to cover — `T01-algebraic-data-types`,
`T03-newtypes-opaque`, `T14-type-narrowing`, `T57-typestate` — plus one
specific, independently-verifiable gotcha attributed to that catalog: that
branded/opaque types are compile-time-only and a JSON serialize/deserialize
round-trip silently erases the brand, so re-validation is required at
deserialization boundaries (see `TECHNIQUES.md` §5, "Gotcha" callout).

All prose and code examples (TypeScript, Python, Rust) in this plugin's
`domain-modeling` skill are original work, not verbatim or paraphrased copies
of `vibe-types` source text (which was never fetched). This is credited as
**inspiration / pattern-naming**, not verbatim vendoring, and no
`vibe-types`-specific license header or NOTICE content is reproduced here
since no source file was read. If `vibe-types` is vendored into this repo in
the future with actual network access, this section should be updated to
reflect real file-level provenance and any upstream NOTICE file contents.

### 0xBigBoss/claude-code

**Not used.** This source's `typescript-best-practices` skill has no root
`LICENSE` file, so its license could not be verified in this offline task.
Per this plugin's policy of only vendoring or cannibalizing from
license-verified sources, no text, code, or structure from
`0xBigBoss/claude-code` appears anywhere in `skills/domain-modeling/` or
elsewhere in this plugin. If the upstream license is verified in the future,
this section can be revisited.

### 0xMassi/claude-skills (MIT)

Also not fetched (no network access in this task). `TECHNIQUES.md` §3
includes a standard `assertNever`/`assert_never` exhaustiveness-check
pattern — a well-known, generic TypeScript/Python idiom, not unique to this
source. It is authored independently here, not copied from
`0xMassi/claude-skills`. Noted as inspiration/pattern-naming credit only,
per the same policy applied to `jpablo/vibe-types` above.

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
