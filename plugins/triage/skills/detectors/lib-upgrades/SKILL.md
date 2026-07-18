---
name: lib-upgrades
description: Scans a project's dependency manifest/lockfile(s) for outdated or CVE-flagged libraries and emits one normalized triage item per finding, per the triage-spine's Triage Item Contract. Use when running a scheduled dependency-health sweep, or when asked to check for outdated/vulnerable dependencies.
argument-hint: "[path to repo or manifest, or none for the current working tree]"
allowed-tools: Read, Grep, Glob, Bash, WebFetch
---

# Lib-Upgrades Detector

A **detector**, not a fixer: this skill's only job is to find outdated or vulnerability-flagged
dependencies and hand each one to `triage-spine` as a normalized item. It never files a bead, never
produces a fix, and never invokes `review-panel` itself — that's the spine's job, downstream of
this detector's output (`skills/triage-spine/SKILL.md`'s registered `source: lib-upgrades`).

## When to Apply

- A scheduled Foundry check (see `../../../docs/foundry-recipes.md`) periodically runs this
  detector over the repo's manifest(s)
- A human asks to check for outdated or vulnerable dependencies
- Not for reviewing a diff that changes dependencies (that's `review-panel`'s cast-in Security
  seat reviewing a PR); this detector runs proactively against the current manifest, not against a
  diff

## How to Detect

1. **Locate the manifest(s).** Identify the project's package manager from its lockfile/manifest
   (`package.json`/`package-lock.json`, `pyproject.toml`/`uv.lock`, `Gemfile`/`Gemfile.lock`,
   `go.mod`/`go.sum`, etc.) — support whichever is present, don't assume a single ecosystem.
2. **Enumerate installed versions vs. latest/advisory data.**
   - **Online:** use the package manager's own outdated/audit command where available (e.g. `npm
     outdated --json`, `npm audit --json`, `uv pip list --outdated`, `pip-audit`, `bundle outdated`,
     `bundle audit`) via `Bash`, or `WebFetch` a public advisory database (e.g. OSV) for a specific
     package@version pair.
   - **Offline / tool unavailable:** fall back to reading the manifest/lockfile directly and
     flagging only dependencies with an obviously stale major version pin (e.g. pinned two or more
     majors behind a version already vendored elsewhere in the repo, or a version explicitly listed
     in a locally-cached advisory list if one exists). State the degraded mode explicitly in the
     output (coverage honesty), same convention as `security-suite`'s `plan-security-review`.
3. **Filter to reportable findings.** A finding is reportable when either is true:
   - The dependency has a known CVE/security advisory against the installed version.
   - The installed version is outdated enough to represent real risk (not merely "not the latest
     patch") — use judgment; do not flag every dependency that is one patch version behind.
4. **Emit one Triage Item Contract entry per finding** (per `../../triage-spine/SKILL.md`'s
   contract table):

```json
{
  "source": "lib-upgrades",
  "severity": "Critical",
  "evidence": "lodash@4.17.11 flagged CVE-2021-23337 (prototype pollution) — found in package-lock.json",
  "affected-paths": ["package-lock.json", "package.json"],
  "suggested-loop": "bump lodash to >=4.17.21 and re-run the dependent test suite"
}
```

- `severity`: `Critical` for a CVE with a known exploit path reachable by the project's actual
  usage of the package; `Important` for a CVE present but not obviously reachable, or a
  significantly outdated version with no CVE but real breaking-change/maintenance risk; `Minor` for
  a routine outdated-but-not-vulnerable version bump.
- `evidence`: the exact package name, installed version, and advisory ID (if any) — verbatim, not
  paraphrased.
- `affected-paths`: the manifest/lockfile path(s); add the specific source files importing the
  package only if that's already known from this scan (don't do a separate full-repo grep just to
  populate this field more precisely than necessary).
- `suggested-loop`: the concrete upgrade action, e.g. target version and the verification step
  (re-run tests) — one line, not a full remediation plan (the spine's Phase 5 owns producing the
  actual fix diff).

## Output Contract

Hand the full list of Triage Item Contract entries to `triage-spine` for Phase 1 intake. If the
scan finds zero reportable findings, still report that plainly (`lib-upgrades: clean, 0 outdated/
vulnerable dependencies found`) rather than emitting nothing — `triage-spine`'s Phase 2 zero-
findings boundary depends on this detector saying so explicitly, not just returning silently.

## Foundry note

This detector is designed to be schedulable as a periodic Foundry check (see
`../../../docs/foundry-recipes.md`). It does not create or modify any `foundry.yaml` file itself —
that wiring is a Foundry-side concern, per the same convention `plan-security-review` already
establishes.
