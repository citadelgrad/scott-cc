# Detector Registry

One spine, five detector slots. The registry design is the v1 deliverable — filling all five
slots with working detector skills is not. Each slot's job is to emit zero or more items matching
`SKILL.md`'s Triage Item Contract; the spine consumes any of them identically regardless of which
slot produced it.

| Slot (`source` value) | Status | Skill | What it scans |
|---|---|---|---|
| `lib-upgrades` | **Implemented (v1)** | [`skills/detectors/lib-upgrades/SKILL.md`](../../detectors/lib-upgrades/SKILL.md) | Manifest/lockfiles for outdated or CVE-flagged dependencies |
| `prod-errors` | **Implemented (v1)** | [`skills/detectors/prod-errors/SKILL.md`](../../detectors/prod-errors/SKILL.md) | Log/Sentry-shaped input for stack-trace-bearing production errors |
| `system-upgrades` | Stub — not yet implemented | — | OS/runtime/base-image version drift (e.g. EOL'd language runtime, outdated base Docker image) |
| `iac-drift` | Stub — not yet implemented | — | Infrastructure-as-code drift between declared config (Terraform/Ansible) and live infrastructure state |
| `security-advisory-sweeps` | Stub — not yet implemented | — | Periodic sweep of security advisory feeds (e.g. GitHub Security Advisories, OSV) not already caught by `lib-upgrades`' point-in-time manifest scan |

## Adding a detector

A future detector slot must:

1. Live at `skills/detectors/<slot-name>/SKILL.md`, following the same frontmatter shape as
   `lib-upgrades`/`prod-errors` (`name`, `description`, `argument-hint`, `allowed-tools`).
2. Emit only items matching the Triage Item Contract in `../SKILL.md` — no bespoke output shape.
3. Use its own registered `source` name from the table above, exactly (the spine's Phase 1
   validation rejects any `source` not listed here).
4. Update this table's Status column from "Stub" to "Implemented" and link its `SKILL.md`.

No other change to the spine or the registry's shape is needed to add a detector — this is the
whole point of the registry design: the spine, the contract, and the gate step are all
detector-count-agnostic.
