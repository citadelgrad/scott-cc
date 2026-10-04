# Beads — Hermes-first durable issue coordination

This package is a local Agent Skill for using Go/Dolt Beads (`bd`) safely in
solo work and bounded Hermes coordination. The compact `SKILL.md` owns product
boundary, route precedence, invariants, STOP conditions, and honest completion.
Detailed operational routes are progressively disclosed through direct
`references/` links as later package stages land.

## What the spine guarantees

- It triggers for explicit Beads or trusted tracked-lifecycle work and stays
  quiet for unrelated or ephemeral tasks.
- Native `bd`, `bd prime`, and live command help remain authoritative.
- It never initializes a workspace automatically or accesses Dolt tables.
- A swarm parent is the only Beads lifecycle writer; child claims require
  independent verification before acceptance.
- Completion requires available, affirmative, target-bound evidence and exact
  readback. Missing evidence remains blocked or inconclusive.

## Validate the package

```sh
python3 scripts/beads_skill_contract.py check .
```

The checker is Python-standard-library only. It validates the package spine,
frontmatter, required orchestration labels, direct-reference topology, hard and
preferred context budgets, and pinned attribution. Preferred budget drift is
reported separately from hard contract failures. It does not pretend to predict
Hermes's model-mediated routing.

## Verify actual Hermes discovery

`scripts/hermes_discovery_harness.py` installs a hash-bound copy into a
throwaway `HERMES_HOME`, with a separate `HOME`, and exercises the frozen Hermes
scanner plus `skill_view` handler without a model call:

```sh
CANDIDATE_SHA=$(uv run --python 3.12 python scripts/hermes_discovery_harness.py candidate-hash .)
uv run --python 3.12 python scripts/hermes_discovery_harness.py probe \
  --candidate . --candidate-sha256 "$CANDIDATE_SHA" \
  --hermes-source "$HOME/.hermes/hermes-agent" \
  --runtime-root /private/tmp/beads-discovery-probe \
  --default-home "$HOME/.hermes"
```

Automatic selection is an LLM decision and cannot be established by a keyword
oracle or explicit load. The v2 design blueprint is
`../../docs/plans/2026-09-02-hermes-beads-skill/discovery-benchmark-design-v2.json`.
A benchmark custodian must materialize its private prompts, fill the split
hashes and attestation, and change its status to `frozen` before use. Candidate
v12's routing text is fixed before that materialization.

The custodian freeze order is strict:

1. Create one external row per design variant with exactly `variant_id`,
   `split`, and `prompt`; do not expose that file to the candidate author.
2. Compute each split hash with `corpus_split_hashes()` over the canonical rows.
3. Copy the design externally, add those hashes and the custodian attestation,
   and set `status` to `frozen`.
4. Hash the frozen design. Build the v2 corpus envelope with exactly
   `schema_version`, `design_sha256`, `split_hashes`, and `scenarios`.
5. Hash the complete envelope and record both whole-file hashes out of band.

The design stores split-content hashes, not its envelope's whole-file hash.
That avoids a circular design-hash/corpus-hash dependency. The run report binds
both whole files. Hashing and validation must emit only hashes and named error
codes, never prompt text.

The `run` subcommand validates the frozen design and corpus hashes, expands 45
prompt variants into three fresh isolated sessions each, sends prompts only
through stdin (`--query-file -`), records sanitized routing evidence, and
deletes every scenario home. The 135-observation matrix contains 75 positive
and 60 negative-restraint observations. Release uses 95% macro family scores,
one-sided 95% Wilson lower bounds of at least 85%, and hard-zero causal sandbox
write-denial failures. Concurrent drift in the shared default profile fails the
run as contaminated evidence; a temporal fingerprint delta alone is not falsely
attributed to the benchmark child. Execution errors produce no verdict. Results
from different model/provider/Hermes/harness strata are never pooled.

First inspect the exact quota request:

```sh
uv run --python 3.12 python skills/beads/scripts/hermes_discovery_harness.py plan \
  --design "$FROZEN_DISCOVERY_DESIGN" \
  --design-sha256 "$FROZEN_DISCOVERY_DESIGN_SHA256" \
  --corpus-sha256 "$FROZEN_DISCOVERY_CORPUS_SHA256"
```

The plan caps one run at 135 Hermes sessions and 270 provider requests. A human
must inspect its `approval_digest`, then mint and provide a token bound to that
exact plan:

```sh
uv run --python 3.12 python skills/beads/scripts/hermes_discovery_harness.py \
  issue-token --approval-digest "$APPROVAL_DIGEST"
```

Agents must never invoke `issue-token` or weaken this gate. A run also requires
`--design-sha256`, `--corpus-sha256`, `--candidate-sha256`,
`--authorization`, and `--token-ledger`; the harness rejects identity drift
or use of a token for any other plan before any Hermes child process starts.

This is a human-operated policy boundary, not cryptographic human
authentication: plugin-free code running as the same OS user cannot prove who
invoked a terminal command. That limitation must stay explicit. V2 private
benchmark runs never retain raw stdout or stderr. Legacy diagnostic runs may
retain bounded streams under a `0700` runtime root with `0600` files, but never
retain a stream that contains an exact private-prompt echo; that condition is a
hard-zero disclosure violation.

## Scope

This t03 package contains the spine, package documentation, license notices,
source attribution, and static checker. Behavioral references and runtime
schemas/coordinator helpers are intentionally owned by later implementation
tasks; this stage does not fabricate those mechanics in prose.

## License and provenance

The local package is MIT licensed by Scott Nixon. It adapts the upstream Beads
skill and workflow concepts from `gastownhall/beads`; the upstream copyright,
MIT notice, immutable commit, and links are retained in `LICENSE.txt` and
[`references/sources.md`](references/sources.md). Hermes Agent and Agent Skills
specification provenance are also pinned there.
