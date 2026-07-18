# Test Results: scc-g12 — Phase 1b Plan-security pass

## 0. What this covers

This is the "Run Tests" step for `scc-g12` (new skill
`plugins/security-suite/skills/plan-security-review/SKILL.md`, plus a
closing-step wire-in in `plugins/review-panel/skills/grill-with-docs/SKILL.md`).
Per `.pas/investigation.md`, there is no automated test suite for skills in this
repo — both `security-suite` and `review-panel` are markdown prompts that drive
Claude subagents, not executable code. This follows the same methodology as
`scc-4xa`'s `test-results.md` and `plugins/review-panel/tests/PRESSURE-TEST.md`:
seeded fixture documents, **live** `Task`/`Agent` dispatches (not simulated),
and explicit labeling of what was actually run vs. hand-reasoned.

**Verdict: all 3 acceptance criteria PASS.** Details below.

---

## 1. Fixtures created

New directory: `plugins/security-suite/tests/fixtures/plan-security-review/`
(mirrors the `plugins/review-panel/tests/fixtures/<scenario>/` convention used
by `auth-token-service` and `order-fulfillment`).

- **`auth-login-plan.md`** — a small PRD adding `POST /api/v1/auth/login`
  (new endpoint, password storage, JWT/HS256 session tokens, a new
  `jsonwebtoken@9` dependency, an ownership-scoped `GET /api/v1/orders/:id`)
  — seeded to exercise AC1 (must TRIGGER authn/session topics) and reused for
  AC3 (offline degradation).
- **`ui-copy-change-plan.md`** — a plan that swaps empty-state copy and a
  decorative SVG asset, explicitly stating no endpoint/data-model/auth/prop
  changes — seeded to exercise AC2 (must produce zero TRIGGERED lines).

---

## 2. AC1 — Auth-relevant plan (live dispatch)

**Live `Agent` dispatch** (general-purpose subagent, online, WebFetch
available) instructed to follow the skill's "How to Review" procedure and
"Output Contract" verbatim against `auth-login-plan.md`.

Result: the agent attempted and executed a real `WebFetch` of
`https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html`
(succeeded, HTTP 200, ~126KB), then produced 12 screened lines. Six were
`TRIGGERED`, each citing an OWASP topic name in the required
`TRIGGERED — <location> — <topic> — <rationale>` format:

- `TRIGGERED — §2 POST /api/v1/auth/login — Authentication — ...`
- `TRIGGERED — §2 Session tokens ... — Session_Management — ...`
- `TRIGGERED — §2 password_hash column — Password_Storage — ...`
- `TRIGGERED — §2 jsonwebtoken@9 dependency — Secrets_Management / Key_Management — ...`
- `TRIGGERED — §2 GET /api/v1/orders/:id — REST_Security — ...`
- `TRIGGERED — §4 Rollout — Threat_Modeling / Secure_Product_Design — ...`

Closed with a one-paragraph "Conditional go" recommendation naming the five
gaps to close before build sign-off.

**AC1 self-check (from the dispatched agent): PASS** — the first three
`TRIGGERED` lines are squarely in the authn/session family
(`Authentication`, `Session_Management`, `Password_Storage`), each citing the
exact topic name, matching the skill's seed table row for "New login/auth
endpoint" and `security-advisor.md`'s "Authentication & Sessions" category.

**AC1 verdict: PASS.**

---

## 3. AC2 — No security-relevant delta (live dispatch)

**Live `Agent` dispatch** (general-purpose subagent, WebFetch available but
judged unnecessary) instructed to follow the same procedure against
`ui-copy-change-plan.md`.

Result: 10 screened lines, all `CLEAR`/`N/A`, zero `TRIGGERED`. The agent
correctly reasoned that forcing a `WebFetch` call with no delta to map would
violate the skill's own "do not force findings where none exist" instruction,
so it made none — itself a correct application of the skill, not a shortcut.

Explicit no-security-relevant-surface statement produced, verbatim:

> "There is no security-relevant surface to threat-model here."

Closed with a "GO" recommendation.

**AC2 self-check (from the dispatched agent): PASS** — zero `TRIGGERED` lines
and the explicit statement is present.

**AC2 verdict: PASS.**

---

## 4. AC3 — Offline degradation (live dispatch, WebFetch withheld)

**Live `Agent` dispatch**, instructed to treat `WebFetch` as unavailable for
the entire run (not to call it at all) and follow the skill's documented
offline-fallback path against `auth-login-plan.md` — the same fixture as AC1,
so the two runs are directly comparable online vs. degraded.

Result: the agent did not call `WebFetch` (confirmed in its self-report — it
used `ToolSearch` once to load the tool's schema, which is a metadata lookup,
not an invocation, and explicitly declined to call it afterward). It led its
output with the exact degraded-mode statement the skill's Output Contract
specifies as an example:

> `Degraded mode: WebFetch unavailable, built-in checklist used.`

It then completed the full procedure using only the built-in checklist plus
topic names from the skill's seed mapping table, producing 12 screened lines,
8 `TRIGGERED` (a superset of AC1's online run — also catching
`Multifactor_Authentication`, `CI_CD_Security`, and `Transport_Layer_Security`,
each citing a topic name by name with no live-fetch content needed), and
closed with a "No-go as written, but close" recommendation naming five
concrete gaps.

**AC3 self-check (from the dispatched agent): PASS** — run completed fully,
with an explicit degraded-mode note as the leading line.

**AC3 verdict: PASS.**

**Cross-run consistency note:** comparing AC1 (online) and AC3 (degraded) side
by side, both independently flagged `Authentication`, `Session_Management`,
`Password_Storage`, and `REST_Security` for the same plan sections — the
degraded run is not lower-quality in topic coverage, only in citation depth
(no live cheatsheet excerpt), exactly as the skill design intends.

---

## 5. Wire-in check: `grill-with-docs/SKILL.md`

Re-read the edited file in full
(`plugins/review-panel/skills/grill-with-docs/SKILL.md:88-99`). Confirmed:

- New closing subsection "Offer the plan-security pass when build-ready" is
  present, added after "Offer ADRs sparingly" as the investigation specified.
- It names `security-suite`'s `plan-security-review` skill explicitly by
  plugin:skill, documentation-pointer only — no new invocation mechanism, no
  import of `security-suite` internals.
- Missing-plugin degrade is explicit (Invariant 3, Coverage honesty): "If
  `security-suite` is not installed in the current session, say so explicitly
  rather than silently skipping the offer."

No live dispatch needed here — this is a documentation-only edit, and its
correctness is a text-comparison check, not a runtime behavior to exercise.

---

## 6. Linting / secrets scan

- No markdown linter is configured in this repo (`biome.json` has no matches
  under this tree, consistent with `scc-4xa`'s finding) — the only files
  touched/created this task are `.md` (the new skill, the wire-in edit, and
  the two fixture plans), so no lint step applies.
- `gitleaks detect --no-git` against
  `plugins/security-suite/skills`, `plugins/security-suite/tests`, and
  `plugins/review-panel/skills/grill-with-docs` — **no leaks found**.

## 7. Scope check: `docs/foundry-recipes.md`

Confirmed **not created** by this task, per the investigation's judgment call
(that file is `scc-tsa`'s / Phase 5's responsibility; this task only needed to
make its skill schedulable, via the "Foundry note" section already present in
`plan-security-review/SKILL.md:110-114`). `find` for `foundry-recipes*` across
the repo returns no matches.

Relative markdown links inside the new skill
(`../../agents/security-advisor.md`, `../../README.md`) verified to resolve
against files that exist.

---

## 8. Summary

| AC | Description | Result |
|---|---|---|
| 1 | Auth-relevant plan → TRIGGERED authn/session topics with citations | **PASS** (live dispatch) |
| 2 | No security-relevant delta → all CLEAR/N/A, explicit statement, zero TRIGGERED | **PASS** (live dispatch) |
| 3 | Offline → completes via built-in checklist with explicit degraded-mode note | **PASS** (live dispatch, WebFetch withheld) |

All three acceptance criteria pass via live, independent `Agent` dispatches
(not simulated/hand-worked-only) against seeded fixture plans. No code changes
in this task (markdown-only), so no test runner or type-check applies — the
verification unit here is skill-instruction correctness under live execution,
which is what was exercised.
