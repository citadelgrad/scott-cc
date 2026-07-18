# Investigation: scc-4rj (Phase 2d — Data-layer guard hook)

## Files to modify/create

- **New:** `hooks/data_layer_guard.py` — the PreToolUse hook implementation.
- **Modify:** `hooks/hooks.json` — register it as a second `PreToolUse` hook entry, alongside the
  existing `prefer_modern_tools.py` entry (same array, new object — Claude Code runs all matcher
  entries for a given event).
- **Modify:** `README.md` — the hooks count/table (`| Hooks | 3 | ... |` and the "Hooks (3)" section)
  is a repo-maintained index that a prior phase (`34cdbfb`, "bump to 13 skills / 3 hooks") bumped
  when a hook was added; bumping to 4 keeps that index honest. Not in the task's "Files to Create"
  list but the same category of doc-consistency upkeep this repo already practices.
- No other file needs edits — `data-steward/SKILL.md`, `persona-catalog.md`, and
  `DATA-MODEL-FORMAT.md` already forward-reference "the data-layer guard hook" correctly (confirmed
  via grep across the repo) and don't need updating for this task.

## Current behavior

- `hooks/hooks.json` (repo root = the "core" plugin) currently registers exactly one `PreToolUse`
  hook: `python3 ${CLAUDE_PLUGIN_ROOT}/hooks/prefer_modern_tools.py`, one `PostToolUse`
  (`toon_post_hook.sh`), and one `Stop` (`terminal_bell.sh`).
- `prefer_modern_tools.py` is the reference pattern for this repo's hook style: reads one JSON
  payload from stdin (`tool_name`, `tool_input`, ...), exits 0 on `JSONDecodeError` or irrelevant
  `tool_name` (fail-open), optionally prints a JSON object to stdout to influence the tool call
  (`{"tool_input": {...}}`), always `sys.exit(0)`. No existing hook in this repo currently blocks or
  asks for confirmation — this task introduces that pattern for the first time in this repo.
- No test harness exists for hooks anywhere in the repo (`tests/`, `tests/e2e/` are empty; no test
  references `prefer_modern_tools.py` either) — verification will be a live/manual dispatch (pipe a
  crafted JSON payload into the script and inspect stdout/exit code), same style as Phase 2a/2b's
  fixture-based live tests.

## Confirmed hook JSON contract (fetched from official docs, code.claude.com/docs/en/hooks)

- **stdin payload** for a `PreToolUse` event includes: `session_id`, `cwd`, `permission_mode`,
  `hook_event_name`, `tool_name`, `tool_input`. `permission_mode` is one of `default`, `plan`,
  `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`.
- **To warn-and-confirm:** exit `0` and print JSON:
  `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
  "permissionDecisionReason": "..."}}`. `permissionDecision` values: `allow` (proceed silently),
  `deny` (block, shown to Claude — a hard block, must NOT be used here per the task's "never
  hard-fail" constraint), `ask` (the confirm-prompt behavior this task wants), `defer` (fall through
  to normal permission flow).
- **Exit code 2** is a hard block (stderr fed to Claude as an error, JSON ignored) — also must not be
  used, since the task requires this to be a soft, dismissable prompt, never a hard failure.
- **Unattended/`mode:agent` detection:** `dual-mode-contract.md` (review-panel skill) defines
  `mode:agent` as *always* invoked as `claude -p "... --mode=agent" --dangerously-skip-permissions`
  (see its `foundry.yaml` example). `--dangerously-skip-permissions` is exactly what sets
  `permission_mode: "bypassPermissions"` in the hook payload — this is a documented, first-party
  field, so `permission_mode == "bypassPermissions"` is the precise, correct signal for "unattended
  /mode:agent" the R1 resolution describes, with no need for TTY-sniffing or new env var
  conventions. (No documented env var distinguishes interactive vs. headless generally, so this is
  the one reliable signal available.)

## Required changes / design

1. **`hooks/data_layer_guard.py`**
   - Read stdin JSON; fail open (`sys.exit(0)`, no output) on parse errors or if `tool_name` isn't
     `Edit`/`Write`/`NotebookEdit`.
   - Resolve the target path from `tool_input` (`file_path` for Edit/Write, `notebook_path` for
     NotebookEdit).
   - **Unattended check first:** if `payload.get("permission_mode") == "bypassPermissions"`, no-op
     immediately (exit 0, no `permissionDecision` — silent, since `bypassPermissions` sessions have
     no human to answer a prompt; this is the documented no-op path, not an accident).
   - Find repo root by walking up from `cwd` looking for `.git`; load `.data-guard.json` if present
     (`{"globs": [...]}` replaces the default glob set; any read/parse error falls back to defaults
     — never hard-fail on a malformed override file).
   - Match the target path against the glob set. Patterns with no `/` (e.g. `*.sql`) match the
     basename at any depth; patterns with `/` match the full repo-relative path, with a leading
     `**/` treated as an optional any-depth prefix and a trailing `/**` as an optional any-depth
     suffix (gitignore-style semantics) — implemented by hand since only stdlib is available (no
     `pathspec`/`wcmatch` dependency; `fnmatch`/`pathlib.match` don't support `**` pre-3.13, and
     `pyproject.toml` pins `python-version = "3.12"`).
   - No match → exit 0 silently.
   - Match → look for `DATA-MODEL.md` at repo root, search its `## Change log` section for a line
     starting with today's ISO date (`datetime.date.today()`, matches the format's
     `- YYYY-MM-DD SN: ...` convention). Present → allow silently. Absent (file missing entirely, or
     present but no dated line for today) → emit the `ask` JSON with a reason naming the matched
     path/pattern and pointing at `DATA-MODEL-FORMAT.md`'s change-log convention.
   - Wrap the whole body in a top-level try/except that exits 0 on any unexpected error — a hook bug
     must never block a developer's edit (fail-open, matching `prefer_modern_tools.py`'s existing
     defensive posture and the task's "never hard-fail" constraint applied more broadly).

2. **`hooks/hooks.json`**: add a second object to the `PreToolUse` array's `hooks` list —
   `python3 ${CLAUDE_PLUGIN_ROOT}/hooks/data_layer_guard.py` — alongside, not replacing, the
   existing `prefer_modern_tools.py` entry.

3. **`README.md`**: bump hook count 3→4 in the summary line and the "Hooks (N)" table, add a row for
   `data-layer-guard` (`PreToolUse`) describing the warn-and-confirm/no-op-when-unattended behavior,
   consistent with how `34cdbfb` documented `prefer-modern-tools` when it was added.

## Risks / open questions

- **`.data-guard.json` schema** isn't specified beyond "overridable" in the task/spec — using a
  minimal `{"globs": [...]}` shape that *replaces* the default set. This is an implementation
  decision, not contradicted by anything in the spec/PRD, but worth flagging as a design choice a
  human could revisit later.
- **"Current-work" change-log entry = dated today.** The format doc says the hook "checks for a
  current-work entry" but doesn't pin down the exact recency rule. Requiring today's date is the
  only mechanical reading that doesn't make the check trivially-satisfied-forever after one entry
  ever exists — but it does mean a change-log entry added yesterday for still-in-progress work
  would no longer silence the prompt today. Acceptable given "mechanical negation" is the task's own
  framing (simple, not semantic), but noting it as a judgment call.
- **AC1/AC2 need a real interactive session** to observe an actual confirm-prompt UI; verification
  will instead assert on the hook's stdout JSON contract directly (`permissionDecision: "ask"`
  present/absent), which is the documented, correct proxy for "prompt would appear" — the same
  contract Claude Code itself parses to decide whether to prompt.
