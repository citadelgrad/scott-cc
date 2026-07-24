# SkillOpt-Sleep: failure-transcript ingestion with mandatory redaction (scc-ncs.24)

## Why

SkillOpt-Sleep mines local session transcripts to propose entries for the
`<!-- SKILLOPT-SLEEP:LEARNED START/END -->` block in this repo's committed
`CLAUDE.md` and `skills/skillopt-sleep-learned/SKILL.md` (see
`docs/skillopt-sleep-occurrence-gate.md` for the prior gate on that same
pipeline). Every existing input source — `~/.claude/history.jsonl`,
`~/.claude/projects/<slug>/<sessionId>.jsonl` — is a session transcript,
harvested and scored regardless of whether the session ultimately succeeded
or failed, but every rule shipped in this repo's own learned-preferences
block so far ("never end a turn on a bare tool call", "read the named
skill's own definition first", etc.) was derived from *failures inside those
sessions*, not from a distinct failure-only corpus. Two categories of
signal never reach the corpus at all today:

1. **Circuit-breaker escalations** — `foundry.yaml` gates that hit
   `decision_on_failure: fail` / `FOUNDRY_NEEDS_HUMAN`, or any other
   automation's circuit-breaker trip, produce exactly the kind of clear,
   human-adjudicated failure signal SkillOpt-Sleep's scoring already
   depends on (see `diagnostics.json`'s `holdout_detail[].why` fields in
   `.skillopt-sleep/staging/*/diagnostics.json`) — but these run outside a
   Claude Code session transcript and are invisible to `harvest.py`.
2. **bd (beads) human-flagged failures** — issues moved to
   `needs_human`, or closed with a failure/blocked resolution a human
   annotated, are a curated, already-labeled failure signal that beads
   itself tracks (see `bd show <id>` / `bd blocked`), but SkillOpt-Sleep's
   harvester never reads the beads DB.

Without these, the learning loop is **survivorship-biased toward wins**:
only sessions that happened to succeed (whose in-session failures were
self-corrected) contribute rules, whole failed sessions and escalations
that never got a session-transcript-shaped resolution contribute nothing.
This spec requires both categories as first-class harvested input, and adds
a **mandatory redaction step** before any failure-derived summary reaches a
committed file, because these sources are far more likely than a
successful-session transcript to contain pasted secrets (stack traces,
env dumps, leaked credentials copied into an error report).

## Where the implementation lives

Per the `docs/skillopt-sleep-occurrence-gate.md` precedent: this repo
(`scott-cc`) has no editable SkillOpt-Sleep *engine* source. The engine
lives in the separate repo `/Volumes/qwiizlab/projects/oss/SkillOpt`
(remote: `microsoft/SkillOpt`, branch `main`), which the `skillopt-sleep`
plugin's marketplace entry points at directly
(`{"source": "directory", "path": "/Volumes/qwiizlab/projects/oss/SkillOpt/plugins/claude-code"}`).
That repo's working tree currently carries uncommitted changes from a
concurrent sibling task (scc-ncs.16's occurrence-gate, and possibly
scc-ncs.23's periodic re-derivation work) touching
`skillopt_sleep/harvest_sources.py`-adjacent files
(`consolidate.py`, `dream.py`, `types.py`, `__main__.py`, `config.py`); this
spec intentionally does **not** touch that live external tree, to avoid
colliding with in-flight work there. This document is the scott-cc-side
spec: precise enough to implement and test against, without assuming who
implements it or when.

The one piece that legitimately lives in *this* repo — because the
redaction primitive it must reuse already lives here — is implemented and
tested in this commit:

- `plugins/security-suite/hooks/failure_redaction.py` — reuses
  `secret_scan.py`'s `RULES` (aws-access-key-id, private-key-header,
  github-token, slack-token, jwt, generic-api-key-assignment) and its
  `redact()` masking convention. Exposes:
  - `has_secret(text: str) -> bool` — cheap gate: does this transcript
    contain anything matching a known secret shape?
  - `redact_transcript(text: str) -> tuple[str, list[tuple[str, str]]]` —
    replaces every matched span in `text` with `[REDACTED:<rule-name>]`
    and returns `(safe_text, findings)`, where `findings` holds only
    `(rule_name, redacted_sample)` pairs (never a raw value). A transcript
    with no matches is returned **byte-for-byte unchanged**.
- `plugins/security-suite/hooks/tests/test_failure_redaction.py` — 9
  tests covering: a clean synthetic failure transcript passing through
  untouched; a bd-flagged-failure-shaped transcript with a fake AWS key
  being detected; redaction of AWS/GitHub/generic-secret patterns with
  zero occurrences of the raw value surviving in the output or in
  `findings`; multiple secrets in one transcript; and that non-secret
  surrounding text is preserved verbatim.

## Required engine-side behavior (SkillOpt, not yet implemented there)

This is the spec for whoever lands the corresponding change in
`/Volumes/qwiizlab/projects/oss/SkillOpt`:

1. **Input corpus, `skillopt_sleep/harvest_sources.py` /
   `harvest.py`**: `harvest_for_config()` must merge in two additional
   digest sources alongside the existing Claude/Codex transcript harvest,
   each normalized into the same `SessionDigest`-shaped record with a new
   `origin: Literal["session", "circuit_breaker", "bd_human_flagged"]`
   field (defaulting to `"session"` for all existing sources, so this is
   additive and backward compatible):
   - **circuit-breaker escalations**: read `foundry.yaml`-produced run
     artifacts (the `{run_dir}/explanation.md` and gate results Foundry
     already writes on a `fail`/`needs_human` decision — see this repo's
     root `CLAUDE.md` "Scheduling & Automation" section for the Foundry
     contract) for the invoked project, and any other circuit-breaker trip
     record the host environment exposes. Each escalation becomes one
     digest whose "transcript" is the gate id, command, exit status, and
     explanation text.
   - **bd human-flagged failures**: shell out to `bd` (or read
     `.beads/issues.jsonl` directly, matching this repo's "passive export"
     architecture) for issues with a `needs_human` status or a
     failure/blocked resolution a human annotated. Each becomes one digest
     whose "transcript" is the issue's title, description, and closing/
     status-change comment.
2. **Mandatory redaction before persistence**: every digest with
   `origin != "session"` MUST be passed through a `redact_transcript()`
   -equivalent function **before** its text reaches `mine.py`/`llm_miner.py`
   summarization and **before** `consolidate.py` writes any resulting edit
   into `applied_edits` — i.e., redaction happens at harvest time, on the
   raw transcript text, not as a post-hoc scrub of the generated summary
   (a summary can quote the source verbatim, so redacting only the summary
   is not sufficient). Concretely: import or vendor the redaction contract
   from this repo's `plugins/security-suite/hooks/failure_redaction.py`
   (`has_secret` / `redact_transcript`) — same `RULES` set, same
   "byte-for-byte unchanged when clean" behavior, same "no raw value in
   findings" guarantee — and apply it to the harvested `text` field of
   every `origin != "session"` digest immediately after it is read, before
   it is handed to any downstream stage. Session-origin digests already
   pass through the interactive `secret_scan.py` PreToolUse hook at
   write/edit time and are out of scope for this change.
3. **Gate composition**: this redaction step composes with, and runs
   independently of, the existing `MIN_OCCURRENCES` occurrence-count gate
   (`docs/skillopt-sleep-occurrence-gate.md`) — a failure-derived candidate
   edit must still clear the occurrence gate before being proposed;
   redaction only guarantees that *if and when* it is proposed, no raw
   secret value is embedded in the proposal or in the persisted
   `CLAUDE.md`/`SKILL.md` block.

## Acceptance criteria mapping

| # | Criterion | Where enforced |
|---|-----------|----------------|
| 1 | Input corpus includes circuit-breaker escalations and bd human-flagged failures, not only successful sessions | Spec'd in `harvest_for_config()` above (engine-side, not yet landed); this repo has no local wrapper/config for harvesting to extend, only the plugin's marketplace pointer at the external engine |
| 2 | Secrets/tokens in a failure transcript are redacted before a derived summary is persisted | `failure_redaction.redact_transcript()` (this repo, implemented + tested) is the required primitive; spec'd call site is harvest time, before `mine.py`/`consolidate.py`, per "Required engine-side behavior" #2 |
| 3 | A failure transcript with no detectable secret remains eligible for inclusion | `redact_transcript()` returns clean text **unchanged** (not dropped, not blocked) — see `test_clean_failure_transcript_is_returned_unchanged` |
| 4 | A failure transcript with a detected secret pattern: persisted summary has zero occurrences of the matched value | `redact_transcript()` replaces every matched span with `[REDACTED:<rule>]` and `findings` carries only `redact()`-masked samples — see `test_aws_key_is_redacted_with_zero_occurrences_of_raw_value`, `test_github_token_is_redacted_with_zero_occurrences_of_raw_value`, `test_findings_never_carry_the_raw_matched_value` |

Tests: `plugins/security-suite/hooks/tests/test_failure_redaction.py` (9
new tests) plus the pre-existing `test_secret_scan.py` (9 tests, unchanged,
still green) — `uv run pytest plugins/security-suite/hooks/tests/` — 18
passed.

## Status

- This repo (`scott-cc`): redaction primitive implemented, tested, and
  committed — this is the one piece of scc-ncs.24 that legitimately lives
  here, since it is the reusable redaction logic itself (per scc-ncs.5),
  not engine plumbing.
- SkillOpt engine (`/Volumes/qwiizlab/projects/oss/SkillOpt`): the harvest-
  source and call-site wiring described above is **not yet implemented**
  there. That repo's working tree already has uncommitted, in-flight
  changes from concurrent sibling tasks (scc-ncs.16, possibly scc-ncs.23);
  landing this spec's engine-side change as an uncoordinated edit into that
  live tree was judged out of scope for this task, matching the scc-ncs.16
  precedent of leaving engine-side implementation as a separately-scoped,
  explicitly authorized contribution to that external project.
