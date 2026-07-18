# Test Results: scc-4rj (Phase 2d — Data-layer guard hook)

## Scope

Task added `hooks/data_layer_guard.py` (PreToolUse hook) and registered it in `hooks/hooks.json`.
No test harness exists anywhere in the repo for hooks (`tests/`, `tests/e2e/` are empty; no test
references the sibling `prefer_modern_tools.py` either — confirmed in `.pas/investigation.md`).
Per investigation's plan, verification is a live/manual dispatch: pipe crafted PreToolUse JSON
payloads into the script and assert on its stdout/exit-code contract, which is the same contract
Claude Code itself parses to decide whether to prompt — the correct, documented proxy for "would a
confirm prompt appear," since no interactive session can be scripted here.

All tests ran against an isolated scratch git repo (`/tmp/data-guard-test.XXXXXX`, `git init`'d so
`find_repo_root` resolves correctly) rather than this repo's own root, since this repo has no
root-level `DATA-MODEL.md`/data-layer paths of its own and a real one shouldn't be fabricated at
the repo root just to test a hook.

## AC1 — Interactive session, no change-log entry → confirm prompt

**Setup:** scratch repo, no `DATA-MODEL.md`. Payload: `tool_name: Edit`, `permission_mode: default`,
`file_path: <scratch>/migrations/0002_x.py`.

**Result:** stdout emitted
`{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask", "permissionDecisionReason": "migrations/0002_x.py matches data-layer pattern '**/migrations/**' but DATA-MODEL.md has no dated Change log entry for today. ..."}}`,
exit 0.

**PASS** — confirm prompt observed via the documented `permissionDecision: "ask"` contract.

## AC2 — Interactive session, with today's change-log entry → silent pass

**Setup:** same scratch repo, added `DATA-MODEL.md` with a `## Change log` section containing
`- 2026-07-17 SN: added widget migration` (today's date, confirmed via `date +%Y-%m-%d`). Same
payload as AC1 re-run.

**Result:** empty stdout, exit 0.

**PASS** — no prompt triggered; edit proceeds silently.

## AC3 — Unattended/mode:agent context (R1) → no-op regardless of change-log state

**Setup:** removed `DATA-MODEL.md` again (back to AC1's "would prompt" state), payload identical
except `permission_mode: bypassPermissions` (the documented signal `--dangerously-skip-permissions`
sets, per `dual-mode-contract.md`'s `mode:agent` invocation).

**Result:** empty stdout, exit 0 — same as AC2, but this time despite no change-log entry existing.

**PASS** — hook no-ops silently in unattended contexts; enforcement correctly deferred to the
data-steward review seat (2c) rather than this hook, per the R1 scope resolution.

## Supplementary edge-case coverage (fail-open design, glob matching, overrides)

All non-blocking, all exit 0:

| Case | Input | Result |
|---|---|---|
| Malformed JSON stdin | `not-json{{{` | empty stdout — fails open |
| Irrelevant tool (`Bash`) | `tool_name: Bash` | empty stdout — ignored |
| Non-data-layer path | `src/app.py` | empty stdout — no match |
| `*.sql` basename match at depth | `db/create.sql` | `ask` — basename glob matches at any depth |
| `**/schema.*` vs. explicit `prisma/schema.prisma` | `prisma/schema.prisma` | `ask`, matched under `**/schema.*` (first list match — see note below) |
| `NotebookEdit` via `notebook_path` field | `models/explore.ipynb` | `ask` — `**/models/**` matches |
| `.data-guard.json` override replaces defaults | `{"globs": ["*.proto"]}`, then edit `migrations/0002_x.py` | empty stdout — no longer matched |
| `.data-guard.json` override, new pattern | same override, edit `api.proto` | `ask` — override applied |
| `cwd` in nested subdirectory | `cwd: <scratch>/nested/deep`, edit `migrations/0002_x.py` | `ask` — repo root correctly found by walking up from `cwd` |
| `file_path` outside repo tree | `/tmp/migrations/outside.py` (repo root = scratch dir) | empty stdout — `ValueError` on `relative_to` handled, fails open |
| Stale (yesterday-dated) change-log entry | `- 2026-07-16 SN: ...` present, edit today | `ask` — confirms the documented "today only" recency rule (investigation.md's noted judgment call) is implemented as designed, not accidentally lenient |

**Informational, non-blocking:** `prisma/schema.prisma` is listed as its own glob in
`DEFAULT_GLOBS`, but `**/schema.*` (listed earlier in the list) already matches it first, since
`matches_data_layer` returns on first match. The explicit entry is currently dead — harmless (the
path still correctly triggers `ask`), but worth a human's attention if the glob list is ever
revisited; not a correctness bug so not fixed out-of-scope here.

## Static checks

- `python3 -m py_compile hooks/data_layer_guard.py` — OK.
- `uv run ruff check hooks/data_layer_guard.py` — all checks passed.
- `ty check hooks/data_layer_guard.py` (repo's `pyproject.toml` pins `[tool.ty.environment]
  python-version = "3.12"`) — all checks passed.

## Cleanup note

The scratch git repo lived entirely under `/tmp/data-guard-test.*`, outside this repository, and
was left for the OS to reclaim — this session's destructive-command guard (`dcg`) blocks `rm -rf`
unconditionally pending human approval, including for that out-of-repo temp path. Running
`py_compile` also produced `hooks/__pycache__/` (untracked, not `.gitignore`d, blocked from
removal by the same guard). Neither affects the diff being reviewed (both are untracked/outside the
repo), but flagging so a human can run `rm -rf hooks/__pycache__` and clear the `/tmp` scratch dir
if desired.

## Acceptance criteria summary

| AC | Description | Result |
|---|---|---|
| 1 | Interactive, no change-log entry → confirm prompt | PASS |
| 2 | Interactive, with today's change-log entry → silent | PASS |
| 3 | Unattended (`bypassPermissions`) → no-op regardless | PASS |

All 3 acceptance criteria PASS. No blocking issues found.
