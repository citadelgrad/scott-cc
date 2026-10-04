# Install skills with the pinned `skills` CLI

The formerly documented floating command `npx skills add citadelgrad/scott-cc`
is not reproducible. Use **skills@1.7.0** below (Node 22.20 or later). Installer
placement, native discovery, and executing a workflow are three different checks.

## Choose the installation surface

- **Skill packages:** `npx --yes skills@1.7.0 add citadelgrad/scott-cc --copy`.
  Select packages and agents interactively. This copies `SKILL.md` and its local
  assets; it does **not** install Claude agents, hooks, slash commands, plugin
  registration, external CLIs, browser profiles, credentials, or model access.
- **Full Claude plugin:** `/plugin marketplace add citadelgrad/scott-cc`, then
  `/plugin install scott-cc@scott-cc` for the core or
  `/plugin install <name>@scott-cc` for a sub-plugin. Registration alone installs
  nothing; review the details, choose the intended scope, and check `claude plugin list`. Plugin hooks, named-agent
  registration, security-suite dispatch and Foundry triage require that setup.
- **Portable orchestration:** review-panel, mutation-test and explore-variants
  bundle their worker prompts and support files. They inspect the live agent's
  delegation capabilities before using native workers; where unavailable, their
  explicit standalone/sequential modes do not claim independent verification.
  Catalog maintenance additionally requires an explicitly selected scott-cc
  source checkout. Read each package's mode preflight before invoking it.
- Other skills may have optional integrations. Read each package's prerequisites
  and limitations; a successful copy is not a certification for every agent.

The `beads` package can be installed, but its advanced swarm/runtime candidate is
**not production-approved**. The recorded model-backed release decision is
**REJECT**, `release_eligible=false`; integrity tests do not override failed/stale
model evidence or authorize promotion. See the
[release decision](../docs/plans/2026-09-02-hermes-beads-skill/release-decision-v1.md)
and, when included with the evaluation bundle,
`evaluation/beads-skill/public-reports/release-v1.json`. No live-model safety claim
is made by the installation matrix.

## Discovery and exact selection

```bash
npx --yes skills@1.7.0 add citadelgrad/scott-cc --list
npx --yes skills@1.7.0 add citadelgrad/scott-cc \
  --skill acceptance-criteria --agent hermes-agent --global --copy --yes
```

Agent IDs tested for placement: `codex`, `hermes-agent`, `claude-code`,
`gemini-cli`, and `pi`. Prefer one explicit agent and scope per command; retain
that command and the reviewed source revision for upgrades. `--copy` avoids
cross-agent symlink dependencies. Without `--global`, the current directory is
the project destination. Never run from the source checkout by accident.

For reproducible source bytes, clone the repository, check out an explicitly
reviewed commit, and substitute its **absolute local path** for
`citadelgrad/scott-cc`. The remote examples follow the published default branch,
not unpublished working-tree fixes. After publication, both nested detectors
(`lib-upgrades`, `prod-errors`) are selectable at repository root through the
marketplace's explicit paths. Equal-name TDD and adversarial packages must be
byte-identical mirrors; the repository-local `.agents/skills/beads` development
stub is not the distributed Beads package.

There are 30 core skills; the complete physical inventory also includes optional
plugin packages and equal-name mirrors.

Avoid `--all` (every skill and agent) and blanket `--skill '*'`: discovery also
includes optional/plugin-dependent packages.

## Exact locations and native activation

| Target | Project copy | Global copy | Profile/home support in skills 1.7.0 |
|---|---|---|---|
| Codex | `.agents/skills/<name>` | `$HOME/.agents/skills/<name>` | Universal shared directory; `CODEX_HOME` does not relocate it |
| Hermes Agent | `.hermes/skills/<name>` | `$HERMES_HOME/skills/<name>` (default `$HOME/.hermes`) | Honors `HERMES_HOME`; choose the intended profile explicitly |
| Claude Code | `.claude/skills/<name>` | `$CLAUDE_CONFIG_DIR/skills/<name>` (default `$HOME/.claude`) | Honors `CLAUDE_CONFIG_DIR` globally |
| Gemini CLI | `.agents/skills/<name>` | `$HOME/.agents/skills/<name>` | Does **not** honor custom `GEMINI_CLI_HOME` |
| Pi | `.pi/skills/<name>` | `$HOME/.pi/agent/skills/<name>` | Does **not** honor custom `PI_CODING_AGENT_DIR` |

Codex and Gemini use the same physical directory, even in copy mode. They cannot
be independently uninstalled there. Use native per-agent configuration to disable
visibility, or keep the shared package until every consumer agrees to remove it.

**Custom Pi/Gemini homes:** do not use this global installer path with a nondefault
`PI_CODING_AGENT_DIR` or `GEMINI_CLI_HOME`. Upstream can report success while the
native loader sees nothing. Prefer the tested project layout in a trusted project,
or the native agent's documented skill install/configuration mechanism and verify
its own listing. No automatic profile migration is supplied here.

**Hermes project scope:** start at the real Git root (`git rev-parse
--show-toplevel`), review the repository and its skills, then explicitly run
`hermes skills trust` in that project if you decide to trust it. Project skills
are not automatically trusted; arbitrary non-Git directories and an untrusted
Git root are not equivalent to a discoverable project installation. Installer
tests never grant trust. `HERMES_HOME` selects the global profile instead.
See the [official skills documentation](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills).

Restart/reload the native agent after changing files and use its native skill
listing. `skills list` verifies installer inventory, **not** native activation.
Prior offline probes observed default-home Codex/Pi/Gemini discovery and Hermes
library trust behavior; the full isolated Hermes CLI was unavailable. The current
copy matrix does not rerun native loaders, authenticated Claude, or model calls.

## Safe lifecycle: avoid upstream update/remove defects

**Do not use generic `skills update` or narrowly scoped project `skills remove`
with this pin.** These are upstream defects we avoid, not fixes to upstream:
update can forget selected targets and `--copy`; project removal can delete the
shared `.agents` package still used by unselected agents (and break symlinks).

### Update by explicit reinstall

Review/check out the desired source revision and repeat the original `add` command
with the same skill, agent, scope, and mode. For the example installation above:

```bash
npx --yes skills@1.7.0 add citadelgrad/scott-cc \
  --skill acceptance-criteria --agent hermes-agent --global --copy --yes
```

This preserves selection and copy mode; it overwrites that selected package, so
back up local edits first. Keep immutable source revisions for auditability.
For legacy symlink installations, repeat the original explicit command *without*
`--copy`; do not change mode accidentally. Verify the exact destination and any
shared canonical consumers afterward. Do not replay `skills-lock.json` blindly:
upstream lock records do not preserve the full target/mode intent.

### Remove only the Hermes project entry (reversible quarantine)

This narrowly scoped alternative does not invoke upstream remove, edit lockfiles,
or delete canonical/shared packages. Run it only for the named project install:

<!-- BEGIN SAFE HERMES QUARANTINE -->
```bash
set -euo pipefail
project_root="$(git rev-parse --show-toplevel)"
target="$project_root/.hermes/skills/acceptance-criteria"
test -e "$target" || test -L "$target"
mkdir -p "$HOME/scott-cc-skill-backups"
backup="$(mktemp -d "$HOME/scott-cc-skill-backups/remove.XXXXXX")"
mv -- "$target" "$backup/acceptance-criteria"
printf 'Quarantined only %s at %s\n' "$target" "$backup/acceptance-criteria"
```
<!-- END SAFE HERMES QUARANTINE -->

No trailing slash is used on `target`: a symlink itself is moved, not its target.
Other agents' copies and canonical contents remain. Keep the backup for rollback;
move it back only after ensuring the original path is still absent. Installer
lock data may remain stale: use filesystem/native listing for verification and
continue explicit `add`, not generic update/remove. This is not a replacement
package manager. Adapt a nonshared agent path only after verifying the table and
its actual destination; **never quarantine `.agents` for only one consumer**.

## Maintainer gates and reproducible setup

```bash
npm ci --ignore-scripts --no-audit --no-fund
uv sync --frozen
uv run pytest
```

The full pytest gate includes both current-checkout verifier entrypoints,
orchestration static contracts, strict YAML/body and whole-payload duplicate
checks, and the real pinned installer matrix: every root/plugin physical package
× five agents × project/global in copy mode, plus every unique root selection ×
five agents. Exact paths, full copied file hashes, post-install dependency
closure (including installer-filtered required files), missing/corrupt assets,
wrong-target routing, invalid metadata and lifecycle alternatives are checked.
Installed-package doctors, public helper execution and the custodian/operational
scorer separation also run in this gate. Beads scoring stays outside the skill:
use `evaluation/beads-skill/harness/evaluate_skill.py` from an explicit source
checkout. Historical scorer hashes and release reports are not re-pinned.
No installer prerequisite is silently skipped: missing Node or `npm ci` fails.
Tests allowlist subprocess environments and isolate HOME, all five agent homes,
XDG/npm/uv caches, Git config, temp directories and cwd. No real profile is used.

`make verify` is the local full gate; `make verify-distribution` is the mandatory
portable distribution gate used by CI/release, including the complete matrix.
`uv run pytest -m 'not installer'` is a fast developer subset, **not** release
verification. The broader native Beads contract suite requires **bd 1.2.2**. A local 1.3.0
run produced native contract failures; do not treat that version as compatible
just because package installs pass. Optional PAS/native-Hermes probes report
their own availability separately.

For just static checks, use `make verify-static`. To export the machine-readable
package inventory and capability boundaries, run
`uv run python scripts/verify_skills_distribution.py --inventory-json`.

Public `--list` is a separate post-publish smoke, not proof of local changes.
Failing or partial gates block distribution acceptance. Neither a passing matrix
nor a clean static gate promotes the rejected Beads runtime candidate.
