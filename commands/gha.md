---
name: gha
description: Debug failing GitHub Actions runs and audit workflow YAML. Fetches logs via gh CLI, analyzes errors, suggests fixes.
allowed-tools: Bash, Read, Edit, Glob, Grep, AskUserQuestion
---

# /gha — GitHub Actions Debugger

Parse `$ARGUMENTS` to determine mode:

| Argument | Mode |
|----------|------|
| *(empty)* | **Debug** — auto-detect latest failed run on current branch |
| `<number>` | **Debug** — debug specific run ID |
| `fix <path>` | **Fix** — audit workflow YAML at path |
| `fix <bare-name>` | **Fix** — resolve to `.github/workflows/<name>.yml` |
| `fix` | **Fix** — list workflows, ask which to audit |
| `help` | Show this argument table and stop |

## Prerequisites

Run `gh auth status`. If it fails, tell the user what to do and stop:
- If `gh` is not found: "Install the GitHub CLI: https://cli.github.com"
- If not authenticated: "Run `gh auth login` to authenticate"

Verify this is a git repo with a GitHub remote. If not: "This command requires a GitHub repository."

Stop on the first failure. Do not continue.

---

## Debug Mode

### Step 1: Find the failed run

**If no run ID provided**, auto-detect:

```bash
BRANCH="$(git branch --show-current)"
```

If `$BRANCH` is empty (detached HEAD), skip branch filtering and go straight to the all-branches query.

If `$BRANCH` is set:
```bash
gh run list --status=failure --branch="$BRANCH" --limit=1 --json databaseId,displayTitle,workflowName,headBranch,conclusion,createdAt
```

If no failures on current branch, fall back to all branches:
```bash
gh run list --status=failure --limit=5 --json databaseId,displayTitle,workflowName,headBranch,conclusion,createdAt
```

If no failures found anywhere, show the 5 most recent runs and offer Fix mode.

**If a run ID is provided**, validate it is numeric (digits only). If not numeric, show the argument table and stop.

Then fetch the run:
```bash
gh run view "$RUN_ID" --json status,conclusion,displayTitle,workflowName
```

Note: `gh run view` returns exit code 1 for failed runs. This is by design — do not treat it as an error. Check the `conclusion` field from JSON output.

Handle non-failure runs:
- `in_progress` → "Run is still in progress. Watch with `gh run watch $RUN_ID`"
- `success` → "Run passed. No failures to debug."
- `cancelled` → "Run was cancelled." Then show what logs are available.

### Step 2: Fetch failed logs

Use two-window truncation to preserve both setup context and error tail:

```bash
gh run view "$RUN_ID" --log-failed 2>&1 | { head -50; echo "--- [truncated] ---"; tail -450; }
```

If the output is empty, say: "No failed step logs available for this run." This is normal for succeeded or cancelled runs.

For runs with multiple failed jobs, also fetch job names:
```bash
gh run view "$RUN_ID" --json jobs --jq '.jobs[] | select(.conclusion == "failure") | {name, conclusion}'
```

### Step 3: Read the workflow YAML

Get the workflow file name and commit SHA from the run:
```bash
gh run view "$RUN_ID" --json headSha,workflowName
```

Find the matching file in `.github/workflows/` using Glob. Read it with the Read tool (not cat).

If the run's `headSha` differs from the current HEAD, note: "Local workflow file may differ from the version that ran (run triggered from `<sha>`)."

### Step 4: Analyze and suggest fixes

Read any referenced source files if the failure is in application code (test files, build configs, lock files).

Present:
1. **Root cause** — what failed and why
2. **Evidence** — quote the specific error lines from the logs
3. **Context** — show the relevant section of the workflow YAML or source file
4. **Fix** — concrete, specific suggestion

Ask for confirmation before applying any edits.

---

## Fix Mode

### Step 1: Locate the workflow file

Accept a full path (`.github/workflows/ci.yml`) or bare name (`ci`).

For bare names, resolve by searching `.github/workflows/` for `<name>.yml` and `<name>.yaml`. If multiple matches, list them and ask the user to pick.

Only read files within `.github/workflows/`. If the path points elsewhere, say it is not a workflow file and stop.

If no file argument given, list all files in `.github/workflows/` and ask which to audit.

### Step 2: Read and audit

Read the workflow YAML with the Read tool.

Check for these common issues (not exhaustive — flag anything else that looks wrong):

- **Unpinned actions** — using `@v3` or `@main` instead of a full commit SHA. This is a supply chain risk. To find current SHAs, run:
  ```bash
  gh api "repos/OWNER/REPO/git/ref/tags/TAG" --jq '.object.sha'
  ```
  Example: `gh api "repos/actions/checkout/git/ref/tags/v4" --jq '.object.sha'`

- **Deprecated syntax** — `::set-output name=X::Y` or `::save-state`. Replace with `echo "X=Y" >> "$GITHUB_OUTPUT"` or `"$GITHUB_STATE"`.

- **Deprecated runtimes** — actions still using Node 16 (removed) or Node 20 (deprecated, removal June 2026). Check the action's `action.yml` or release notes.

- **Missing permissions block** — no top-level `permissions:`. Add least-privilege permissions for the workflow's needs.

- **Missing concurrency** — PR-triggered workflows without `concurrency:` to cancel stale runs. Add:
  ```yaml
  concurrency:
    group: ${{ github.workflow }}-${{ github.ref }}
    cancel-in-progress: true
  ```

- **Missing timeout** — jobs without `timeout-minutes:`. Add a reasonable timeout (10-30 min depending on the job).

- **Runner pinning** — `ubuntu-latest` resolves to `ubuntu-24.04`. Note the trade-off: `latest` gets updates automatically but may break; pinned is reproducible but needs manual updates.

- **Expression injection** — untrusted input (`github.event.issue.title`, `github.event.pull_request.title`, etc.) used directly in `run:` blocks. Move to `env:` first:
  ```yaml
  env:
    TITLE: ${{ github.event.issue.title }}
  run: echo "$TITLE"
  ```

### Step 3: Suggest fixes

Present each issue found with:
1. What the issue is
2. Why it matters (one sentence)
3. The proposed change

Ask for confirmation before applying any edits. Only edit files within `.github/workflows/`.

---

## Security Rules

These rules apply to both modes. Do not violate them.

- **Validate run IDs**: must be numeric (digits only). Never pass unvalidated input to shell commands.
- **Quote variables**: always use `"$VAR"` in bash commands, never bare `$VAR`.
- **Path confinement**: Fix mode only reads and edits files in `.github/workflows/`. Debug mode may suggest edits to source files outside this directory — that is expected.
- **Sensitive data**: GHA logs may contain leaked secrets. If you spot patterns like `ghp_*`, `ghs_*`, `AKIA*`, or base64-encoded tokens, do not echo them back. Note that sensitive data was found and suggest the user check their secret management.
- **No auto-apply**: always ask for confirmation before editing any file.
