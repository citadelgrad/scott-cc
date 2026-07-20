# Fixture: malformed-batch (AC5)

`batch.json` is a batch of 5 items exercising every Phase 1 validation rule in
`triage-spine/SKILL.md`, in the order the spine checks them. **Only items 1-3 are actual
contract violations; items 4 and 5 both correctly survive Phase 1** — this is intentional (see
item 4's note below), not a mistake in the fixture.

| # | Outcome | Rule |
|---|---|---|
| 1 | REJECTED | missing `evidence` field entirely — rule 1, all five fields present |
| 2 | REJECTED | `severity: "urgent"` — rule 3, must be one of Critical\|Important\|Minor |
| 3 | REJECTED | `affected-paths` is a string, not an array — rule 5, must be a non-empty array of strings |
| 4 | **Valid — survives Phase 1** | `source: "iac-drift"` — rule 2 only checks that `source` is a *registered slot name*, not that its detector is implemented; `iac-drift` is a registered stub slot per the registry table, so this item correctly passes rule 2 and every other rule. Included to confirm the spine doesn't special-case stub-sourced items, not to trigger a rejection. |
| 5 | **Valid — survives Phase 1** | fully valid on every rule — proves a malformed sibling never blocks a valid item from proceeding to Phase 3 |
