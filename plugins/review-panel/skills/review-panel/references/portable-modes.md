# Portable modes and resource routing

`review-panel` is a prompt orchestrator with real bundled packaging/checkpoint
helpers. It is not a standalone model service. The host supplies file tools,
Git/Bash/Python, and (for full mode) real fresh-context worker dispatch.

## Preflight before target work

1. Locate this loaded skill directory as `PANEL_DIR`. Never climb to plugin parents
   or assume a repository clone. Run
   `python3 "$PANEL_DIR/scripts/package_contract.py" doctor`.
   Missing scripts/catalogs/contracts/prompts are fatal, not grounds to improvise.
2. Read [worker-adapters.md](worker-adapters.md). Inspect live tool schemas, context
   inheritance and result/artifact support. Select and record the exact available
   native tool. No `Task`/`Agent` or named plugin type is assumed from the host name.
3. **Full mode requires fresh independent workers**, artifact-only handoffs and
   an isolated fixer lane or explicit edit permission. Nested independent roles
   (for example adversarial validation) may be dispatched by the parent if workers
   cannot nest; never simulate them in an inherited context. If the host cannot
   provide these, fail `subagent_runtime_unavailable` before packaging or reading
   the target and offer `--standalone`. Do not silently convert an automated gate.
4. Readback/persistence, model selection and read-only enforcement must be real.
   Prompt-only tool limits are not an OS sandbox. Disclose any weaker enforcement
   and obtain approval where the review needs a hard boundary. A model tier is a
   preference among already-authorized choices, never authorization to buy access.
5. For resume, require host evidence of a fresh session in addition to the existing
   hash/session fields. Do not self-certify freshness by setting an environment
   variable. Checkpoint claim is bundled; invoke it from the reviewed repo root.

## Path mapping (all modes)

The package contains its transitive resources rather than searching installed
siblings. `resource-map.json` maps source-style identifiers to actual package-local
paths. Look up a catalog `skills/<name>/SKILL.md` there and read that snapshot;
its entry file is called `INSTRUCTIONS.md` **only inside the resource bundle** to
avoid exposing extra installable skills. The published skill names are unchanged.

- `scripts/workspace`, `scripts/review-package`, `scripts/checkpoint-claim` mean
  `$PANEL_DIR/scripts/...`; invoke Bash scripts with `bash` and the claim helper
  with `python3`. Cwd is the explicit target repository, not the skill directory.
- `reviewers/`, `contracts/`, `formats/`, `agents/`, `hooks/` mean the corresponding
  directories under `$PANEL_DIR/resources/`.
- Local links *inside* a snapshot are relative to that snapshot. Its package doctor
  (when present) verifies that snapshot's assets; the enclosing doctor verifies
  the entire distribution. No hook is registered or installed by bundling it.
- The Security role is bundled from `security-suite`; dispatch its prompt through
  the native adapter, even without a named plugin agent. Add read-only tools and
  the bundled reviewer-output contract to its packet. If permission restrictions
  cannot be enforced, disclose that before dispatch, not after an unsafe run.
- Discover **optional enrichment** through the host's actual skill/agent registry
  and returned skill locations. `~/.claude/skills` in source catalogs is the Claude
  adapter example, never a mandatory cross-agent search path. No home-wide clone scan.
- `Task` in stage references means the verified native worker adapter. Plugin agent
  names in source prompts are optional shortcuts, not invocable APIs everywhere.
  Instructions to invoke another bundled lens mean read its mapped local snapshot.
  The parent owns orchestration when workers cannot dispatch nested workers.

Source snapshots, small path rewrites and digests are recorded in
`package-manifest.json`; `doctor --source-root <explicit-maintainer-checkout>`
detects drift. Do not manually edit a snapshot and reset its digest to hide drift.

## Explicit standalone mode (`--standalone`)

This is a useful **sequential, read-only multi-lens review**, not an independent
panel and not a replacement for its full-mode CI verdict. It requires no Claude
plugin or worker tool. Only use it if requested/accepted before target work.
Do not combine it with `--resume`, full-panel JSON mode or automatic fixing.

1. Run package doctor. Resolve one target and use the same bundled workspace and
   review-package commands as full mode. Worktree packaging includes tracked
   changes; untracked files are listed but not reviewed unless explicitly added
   to the approved target. Report that gap. Capture the target/diff hash.
2. Bound scope to 25 files and 1,500 changed lines. Use Git's machine-readable
   counts in a tool, not mental arithmetic; reject oversized targets and ask for
   coherent narrower ranges. The packaged diff is a file, not a chat attachment.
3. Read the persona catalog and apply its casting criteria to the bounded target.
   Apply each applicable bundled lens sequentially, including security, data,
   domain, test-quality, mental-model and taste rules. No arbitrary small-seat cap.
   Read each snapshot just-in-time; record which actually ran and why others did not.
   Fresh-Eyes and genuinely independent validator passes are **unavailable**, not
   faked by switching role labels. Use ordinary adversarial/control-backed probes
   where safe, but label their same-context evidence honestly.
4. Persist detailed findings using the reviewer-output shape. Deduplicate by
   file/line and underlying defect; cite evidence, preconditions and actual probe
   results. No finding is valid merely because several same-context lenses agree.
5. Return a concise human report: `mode: standalone`, `independence: none`, target
   hash, covered/skipped lenses, findings/evidence, unverified assumptions and
   artifact paths. State **not a full-panel convergence/merge gate**. Do not emit
   `converged`, `ready`, or a fabricated full-mode JSON result.
6. Stop after this single review. Offer fixes or an independent full run separately;
   no automatic commits, tracker writes, edits or repeated loops.

## Full mode

With verified native capabilities, follow the existing seven-stage references,
tiers, bounded handoffs, validation, sovereignty gates and convergence rules.
The entire catalog and its transitive lens resources are bundled. The standalone
mode does not remove any full-mode seat or weaken its independent-validation gate.
