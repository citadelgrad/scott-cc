# Security Seat Pressure Test

**Task:** scc-4xa — "Phase 1a — Security seat in the review panel (cast security-suite's
security-engineer)"

This is the permanent artifact for scc-4xa's Run Tests step, following the same TDD-for-skills
methodology and honesty conventions as `tests/PRESSURE-TEST.md` (explicit **live** vs
**worked-by-hand** labeling per section). The fixture files under
`tests/fixtures/auth-token-service/` name this document as their intended home in their own header
comments, mirroring `PRESSURE-TEST.md`'s relationship to `fixtures/order-fulfillment/`.

**Provenance note:** this content was originally produced live during scc-4xa's Run Tests step and
written to the pipeline's ephemeral `.pas/test-results.md` scratch file, which that step's own
write-up explicitly flagged as needing promotion to this permanent path as "the next step's job" —
a promotion that did not happen at the time. `.pas/test-results.md` is overwritten by every
subsequent pipeline task, so by the time this gap was noticed (during PR review of the full
two-system-architecture branch), the original had been overwritten four times over by later phases.
It was recovered verbatim from git history (`git show eb5ee33:.pas/test-results.md`, the commit
that closed scc-4xa) and is reproduced below unchanged except for this header — the underlying
evidence (live `Task` dispatches, hand-worked MERGE/VALIDATE tables) reflects the real session
transcript from when scc-4xa was implemented, not new work.

**Verdict: all 4 ACs PASS.** Details below.

---

## 1. Doc-consistency re-check (no changes needed)

Re-read `plugins/review-panel/reviewers/persona-catalog.md` in full. Confirmed all three spots
identified by the investigation are consistently rewritten:

- The `### Security` entry (no longer `(conditional)`) casts `security-suite:security-engineer`
  directly, with cast-when list including IaC/CI config, a missing-plugin fallback keyed on
  agent-type-list absence (not live-scan), and Notes covering the tool-grant, model-pin, and
  output-shape caveats.
- The "Missing skill handling" bullet for Security matches the new primary-cast model.
- The Seat Summary Table row: `Security | security-suite:security-engineer | Diff touches
  auth/crypto/secrets/input-validation/deserialization/dependency-manifests/IaC/CI-config |
  Top-tier`.

`plugins/security-suite/agents/security-engineer.md` confirmed unedited, frontmatter has no
`tools:`/`model:` field, matching the catalog's caveats exactly. No stale "conditional on
live-scan" language remains anywhere in `review-panel` (repo-wide grep, confirmed by the prior
Implement step and spot-checked again here).

---

## 2. The fixture

`plugins/review-panel/tests/fixtures/auth-token-service/` (already present on disk, untracked;
verified `diff.patch` still matches `before.ts`/`after.ts` byte-for-byte via a fresh
`diff -u before.ts after.ts` regeneration — not stale).

| File | Role |
|---|---|
| `before.ts` | Clean baseline: verifies JWT signature (`jwt.verify`), reads secret from `process.env.AUTH_JWT_SECRET` with a fail-closed guard, looks up the profile keyed by the token's own verified `claims.sub` via a parameterized query. |
| `after.ts` | The diff under review — see seeded vulnerabilities below. |
| `auth-clients.ts` | Type-only support file; notably `JwtClient.decode()`'s own doc comment says "WITHOUT verifying its signature" — the vulnerability is a visible contract violation, not a hidden trap. |
| `diff.patch` | `diff -u before.ts after.ts`, regenerated and confirmed current. |

### Seeded vulnerabilities (the "answer key" — lives only here, never in the fixture files)

1. **Auth bypass (CWE-347)** — `after.ts:22` swaps `jwt.verify(req.token, JWT_SECRET)` for
   `jwt.decode(req.token)`, dropping signature verification entirely. Any caller can submit an
   unsigned/forged token and be treated as authenticated.
2. **Hardcoded secret (CWE-798)** — `after.ts:6` replaces `process.env.AUTH_JWT_SECRET` (with a
   fail-closed guard) with the literal `"supersecret-dev-key-2024"`, committed to source.
3. **SQL injection (CWE-89)** — `after.ts:24-26` replaces a parameterized query
   (`"...WHERE id = $1", [claims.sub]`) with string concatenation of unsanitized
   `req.requestedUserId`.
4. **IDOR / broken object-level authorization (CWE-639)** — independent of #3, the lookup key
   changed from the verified `claims.sub` to the caller-supplied `req.requestedUserId`, so even a
   parameterized version would let any caller read any other user's profile.

This is a richer fixture than a single-bug diff — four independently real, chained vulnerabilities
in one small file — which gives MERGE's 2+-seat-agreement mechanics something substantive to
exercise (see Section 4).

---

## 3. Live dispatches (2 independent seats, both real `Task` calls)

Following `tests/PRESSURE-TEST.md`'s precedent of live nested dispatch rather than a walkthrough.
**Both are live, real subagent runs** — full raw output is quoted below, not summarized, so MERGE's
fingerprint/quote-the-line work in Section 4 can be checked against the actual text.

### 3a. Security-engineer persona seat (stands in for `security-suite:security-engineer`)

`security-suite:security-engineer` is **not registered as a dispatchable agent-type in this
session** — confirmed empirically (Section 5 below), which is itself the live AC2 scenario. To
still validate that the *persona itself* produces a correct finding when applied to this fixture
(AC4's requirement), it was dispatched as a `general-purpose` subagent instructed to read
`plugins/security-suite/agents/security-engineer.md` verbatim and fully adopt its behavioral
instructions, then review the fixture, rendering output in `contracts/reviewer-output.md`'s
Critical/Important/Minor + verdict shape — exactly the instruction the catalog's own "Output-shape
caveat" says SPAWN's dispatch prompt must give this seat. Read-only (`Read`/`Grep`/`Glob` only).

**Raw output (verbatim):**

> ### Strengths
>
> - The function's return shape, imports, and type signature (`SessionRequest`, `DbClient`,
>   `JwtClient`) are preserved, so the change is narrowly scoped and easy to diff/audit.
> - `before.ts` establishes a correct pattern worth preserving: verified-signature JWT
>   (`jwt.verify`), parameterized SQL (`$1` placeholder), authorization scoped to the token's own
>   verified subject (`claims.sub`).
>
> ### Issues
>
> #### Critical (Must Fix)
>
> 1. **`after.ts:22`** — `const claims = jwt.decode(req.token);` — JWT signature verification
>    removed (CWE-347 / OWASP A07:2021). Per `auth-clients.ts:12-13`, `decode()` explicitly does
>    NOT verify the signature. Any caller can submit a forged JWT with an arbitrary `sub` claim and
>    be treated as authenticated. **Fix:** restore `jwt.verify(req.token, JWT_SECRET)` and the
>    `JWT_SECRET`-presence guard.
> 2. **`after.ts:6`** — `const JWT_SECRET = "supersecret-dev-key-2024";` — hardcoded credential
>    (CWE-798). Combined with #1, anyone with repo access can forge validly-signed tokens for any
>    subject regardless of environment. **Fix:** restore `process.env.AUTH_JWT_SECRET` with the
>    fail-closed check.
> 3. **`after.ts:24-26`** —
>    ```
>    const result = await db.query(
>        "SELECT * FROM users WHERE id = '" + req.requestedUserId + "'",
>    );
>    ```
>    SQL injection (CWE-89 / OWASP A03:2021) — unsanitized client input concatenated into query
>    text; `before.ts:27` was parameterized. An attacker can supply `' OR '1'='1` or a UNION
>    payload to exfiltrate the entire `users` table. **Fix:** parameterize:
>    `db.query("SELECT * FROM users WHERE id = $1", [userId])`.
> 4. **`after.ts:24-26` (with `after.ts:10`/`after.ts:22`)** — Broken Object-Level Authorization /
>    IDOR (CWE-639 / OWASP A01:2021). Even with parameterization, the lookup key changed from the
>    verified `claims.sub` to the caller-supplied `req.requestedUserId`. Any caller can pass any
>    other user's ID and retrieve their full profile row. **Fix:** key the lookup off `claims.sub`,
>    or gate cross-user lookup behind an explicit authorization check.
>
> #### Important (Should Fix)
>
> None beyond the items already captured as Critical.
>
> #### Minor (Nice to Have)
>
> 1. **`after.ts:13-15`** — the updated doc comment describes the new insecure behavior as if
>    intended ("looks up the requested user's profile") rather than flagging it. Update once the
>    above are fixed; consider an inline warning against reverting to `decode()`/literal secrets.
>
> ### Assessment
> **Ready to merge?** No
> **Reasoning:** The diff removes JWT signature verification, hardcodes the signing secret, and
> replaces a parameterized, identity-scoped query with a SQL-injectable, client-controlled lookup —
> together a full authentication bypass, credential exposure, SQL injection, and IDOR chain (CWE-347,
> CWE-798, CWE-89, CWE-639).

*(Live dispatch: `subagent_type: general-purpose`, 5 tool uses, 32.8s, ~25.7k tokens.)*

### 3b. Adversarial-reviewer seat (core seat, independent corroboration)

Dispatched as review-panel's actual core Correctness/Adversarial seat — instructed to read
`skills/adversarial-reviewer/SKILL.md` and follow it, with **no visibility into 3a's output or
existence**. This exercises the catalog's stated claim that "`adversarial-reviewer` Scope item 2
provides baseline security attention on every run even when [the Security seat] isn't cast" — see
Section 5, where this is exactly the fallback path that fires.

**Raw output (verbatim):**

> ### Strengths
>
> - `before.ts:22-24` fails closed on missing config rather than silently degrading — a defense
>   `after.ts` removes rather than preserves.
> - `before.ts:25,27` correctly derives the query key from the verified subject claim and uses a
>   parameterized query; `DbClient.query` still accepts `params?: unknown[]` in `after.ts` — nothing
>   forced abandoning it.
> - Neither version logs the token/secret/claims anywhere.
> - `auth-clients.ts:9-13`'s `decode()` doc comment is honest about the danger — the vulnerability is
>   a visible contract violation, not a hidden interface trap.
>
> ### Issues
>
> #### Critical (Must Fix)
>
> **1. Authentication bypass — signature verification removed** (`after.ts:22`,
> `const claims = jwt.decode(req.token);`). Attack: base64url-encode `{"alg":"none","typ":"JWT"}` /
> `{"sub":"<any-uuid>","scope":["admin"]}` with empty/garbage signature — `jwt.decode` returns it
> with zero cryptographic proof. **Fix:** revert to `jwt.verify(req.token, JWT_SECRET)`.
>
> **2. Hardcoded, source-committed JWT signing secret** (`after.ts:6`,
> `const JWT_SECRET = "supersecret-dev-key-2024";`). Attack: anyone with source/git-history access
> forges validly-signed tokens for any subject via `jwt.sign(..., "supersecret-dev-key-2024")`.
> Note: masked by #1 today, but nearly as bad as no verification the moment #1 alone is "fixed."
> **Fix:** restore `process.env.AUTH_JWT_SECRET` + fail-closed guard; rotate; add secret-scanning
> to CI.
>
> **3. SQL injection via string concatenation** (`after.ts:24-26`). Attack:
> `requestedUserId = "' OR '1'='1"` dumps the entire `users` table (open `DbRow` index signature);
> `"'; DROP TABLE users; --"` if statement-stacking is permitted; boolean/time-based blind
> injection works even without direct output. Requires no valid session given #1. **Fix:**
> parameterize, plus format validation (#5) and the authorization fix (#4).
>
> **4. IDOR — caller can request any user's profile, not just their own** (`after.ts:15,24-27`).
> `before.ts:14-15`'s docstring was explicit that the lookup was always the caller's own, verified
> subject; `after.ts` switches the key to fully caller-controlled `req.requestedUserId` — a
> deliberate scope change visible in the docstring edit itself, not incidental. Holds independently
> of #1-#3: even with `verify` restored and the query parameterized, nothing checks
> `claims.sub === req.requestedUserId` or an admin scope. **Fix:** query by `claims.sub`, or
> explicitly gate `requestedUserId` behind an authorization check.
>
> #### Important (Should Fix)
>
> **5. No type/format validation on `requestedUserId`** (`after.ts:8-11,24-26`) — compile-time-only
> `string` annotation, no runtime shape check; also what makes #3 trivially reachable. **Fix:**
> validate against an expected shape (UUID/numeric) before use.
>
> **6. Return value mixes an unverified identity with a caller-chosen lookup** (`after.ts:27`,
> `return { userId: claims.sub, profile: result.rows[0] ?? null };`) — `userId` and `profile` can
> now refer to different people; downstream code assuming they match (a reasonable assumption given
> the original docstring) will silently misattribute data. Call out separately in case #4 is fixed
> only partially.
>
> #### Minor (Nice to Have)
>
> **7. Unbounded `SELECT *` amplifies blast radius** (`after.ts:24`, present in both versions) —
> `DbRow`'s open index signature means any successful #3/#4 hit leaks the maximum possible column
> set. **Fix:** explicit column allowlist.
>
> ### Assessment
> **Ready to merge?** No.
> **Reasoning:** Zero valid credentials needed for full compromise — a self-forged unsigned JWT
> (worsened by the public hardcoded secret) grants arbitrary identity, and the injectable,
> IDOR-vulnerable lookup then hands over any row in `users`; each Critical finding independently
> blocks merge, and together they compound into a complete auth/data-access bypass.

*(Live dispatch: `subagent_type: general-purpose`, 25 tool uses, 112.9s, ~45.5k tokens. Per this
skill's own "Independence via clean-room-alternative" mechanism, this seat internally ran its own
blind first-read subagent before synthesizing the above — an internal sub-dispatch, which
`references/merge-and-validate.md`'s Step 3 explicitly says does NOT count as a second independent
seat for the 2+-agreement bump; it's treated as one seat's raw output below.)*

---

## 4. MERGE (worked by hand, per `references/merge-and-validate.md`)

### Step 1-2 — Fingerprint + confidence anchor

| # | Finding | Fingerprint (file, line-bucket, title) | Seats reporting | Quote-the-line | Base confidence |
|---|---|---|---|---|---|
| 1 | Auth bypass — `jwt.decode` replaces `jwt.verify` | `after.ts`, L22, "signature verification removed" | Security-engineer + Adversarial (2 independent) | Both quote `const claims = jwt.decode(req.token);` verbatim — matches `after.ts:22` exactly | 75 (2+ agreement, quote passes, mechanically checkable against `auth-clients.ts`'s `verify`/`decode` doc comments) |
| 2 | Hardcoded JWT secret | `after.ts`, L6, "hardcoded jwt signing secret" | Security-engineer + Adversarial (2 independent) | Both quote `const JWT_SECRET = "supersecret-dev-key-2024";` verbatim — matches `after.ts:6` exactly | 75 |
| 3 | SQL injection via concatenation | `after.ts`, L24-26, "sql injection via string concatenation" | Security-engineer + Adversarial (2 independent) | Both quote the `db.query("...'" + req.requestedUserId + "'")` block verbatim — matches `after.ts:24-26` exactly | 75 |
| 4 | IDOR / lookup keyed off caller-supplied ID instead of verified subject | `after.ts`, L24-27 (±3 tolerance absorbs the L15/L24-26/L27 citation spread across the two seats), "idor / broken object-level authorization" | Security-engineer + Adversarial (2 independent) | Both cite the same query block plus the `claims.sub`→`req.requestedUserId` key swap, verified against `before.ts:27`/`after.ts:25` | 75 |
| 5 | Doc comment normalizes the new insecure behavior | `after.ts`, L13-15 | Security-engineer only | Quotes the doc-comment text; matches `after.ts:13-15` | 50 (single seat, quote passes, but "is a comment itself worth flagging" is a judgment call) |
| 6 | No runtime format validation on `requestedUserId` | `after.ts`, L8-11/24-26 | Adversarial only | Quotes the `SessionRequest` interface + query block | 50 (single seat, quote passes, defense-in-depth judgment call, not itself an exploit in this diff) |
| 7 | Return value mixes verified `userId` with caller-chosen `profile` | `after.ts`, L27 | Adversarial only | Quotes `return { userId: claims.sub, profile: ... }` verbatim | 50 (single seat, quote passes, secondary/contextual consequence of #4) |
| 8 | `SELECT *` blast-radius amplification | `after.ts`, L24 (pre-existing in `before.ts` too) | Adversarial only | Quotes the query text | 50 (single seat, quote passes, but pre-existing-in-baseline weakens "is this a finding on *this diff*" to a judgment call) |

### Step 3 — 2+ agreement bump

Findings #1-#4 each have 2 independent seats reporting the same fingerprint → bump one level:
**75 → 100** for all four.

### Step 4 — Quote-the-line gate

Manually cross-referenced every quoted snippet above against the actual `after.ts` content read in
this session (Section "2. The fixture" / the file itself). All 8 findings' quotes are verbatim
matches at or within the claimed line numbers — **no finding is demoted**.

### Step 5 — Final merged list handed to VALIDATE

| Finding | Severity | Confidence | Contributing seats |
|---|---|---|---|
| Auth bypass (`jwt.decode` vs `jwt.verify`) | Critical | **100** | 2 (Security-engineer, Adversarial) |
| Hardcoded JWT secret | Critical | **100** | 2 |
| SQL injection | Critical | **100** | 2 |
| IDOR / caller-controlled lookup key | Critical | **100** | 2 |
| Doc comment normalizes insecure behavior | Minor | 50 | 1 |
| No runtime format validation | Important | 50 | 1 |
| Mixed verified/unverified identity in return value | Important | 50 | 1 |
| `SELECT *` blast-radius | Minor | 50 | 1 |

**AC4 is satisfied by this table alone**: at least one seeded vulnerable-diff fixture (in fact,
four chained ones) produced validated MERGE findings with fingerprints and confidence anchors,
sourced from real, live `Task` dispatches — not fabricated or hand-waved.

---

## 5. AC1/AC2 — Cast + Coverage Honesty (one live, one worked)

### AC2 is LIVE, not hypothetical

Before writing any walkthrough, the "without security-suite" condition was tested directly: this
session attempted `Agent({ subagent_type: "security-suite:security-engineer", ... })` and it
failed immediately with:

> `Agent type 'security-suite:security-engineer' not found. Available agents: beads-epic-builder:epic-planner, beads-epic-builder:feature-builder, beads:task-agent, claude, Explore, general-purpose, mutation-testing:*, Plan, research-tools:*, review-panel:clean-room-alternative, scott-cc:*, statusline-setup, task-agent`

This is a genuine, mechanically-checkable confirmation of exactly the condition the catalog's
"Missing-plugin fallback" text names ("`security-suite:security-engineer` is not present in the
current session's available Task/Agent-tool agent-type list"). **This session is a live instance of
AC2's premise**, not a constructed scenario.

**What the catalog says must happen:** apply baseline security attention via
`adversarial-reviewer`'s Scope item 2, and state explicitly that no dedicated security-specialist
seat was cast. **What actually happened in this session, live:** Section 3b's `adversarial-reviewer`
dispatch — run specifically to test the fallback claim — independently caught all 4 Critical
findings via its Scope item 2 (security holes) without any `security-suite` involvement. The
catalog's fallback text is not just plausible, it's empirically confirmed to produce real coverage
on this fixture. Coverage Honesty section (as the orchestrator would render it):

> **Coverage Honesty:** the Security seat (`security-suite:security-engineer`) was cast-eligible
> for this diff (touches auth, secrets, and a database query at a trust boundary) but
> `security-suite` is not installed/enabled in this session — no `security-suite:security-engineer`
> agent-type is available. No dedicated security-specialist seat was cast. Baseline security
> attention was still applied via `adversarial-reviewer`'s Scope item 2; see its findings above. A
> specialist security pass (deeper OWASP/CWE-systematic coverage, e.g. `security-suite`'s
> compliance-report and threat-modeling angles) was **not** performed and should be re-run once
> `security-suite` is available. **PASS** — gap stated explicitly, not silently dropped.

### AC1 (worked walkthrough — deterministic per the catalog's own cast-when text)

**Scenario:** `security-suite` installed (agent-type present in the session's list) + a diff that
touches a dependency lockfile (e.g. `package-lock.json` bumping a transitive dependency).

Per `cast-and-spawn.md` Step 2 ("Judgment-match against diff CONTENT, not paths") and the catalog's
Security entry cast-when list ("dependency manifests/lockfiles" is explicitly one of the eight
listed triggers), CAST reads the diff, sees the lockfile change, and matches it against that
trigger directly — no ambiguity, no fail-closed judgment call needed since it's an explicit,
named condition. The Cast section of the report would read:

> **Security** — cast. Rationale: diff modifies `package-lock.json` (dependency manifest/lockfile),
> matching this catalog's Security cast-when criteria. Dispatched as
> `security-suite:security-engineer`, top-tier model.

**PASS** — this is not a probabilistic judgment call the way risk-triggered seats like
Change-Trajectory are; "touches a lockfile" is a literal, named trigger in the catalog text, so the
seat is cast with certainty whenever that condition holds and the plugin is available.

### AC3 (worked walkthrough)

**Scenario:** a docs-only diff, e.g. editing a paragraph in `README.md` with no code changes.

Walking CAST Step 2 against the catalog's 8 Security triggers (auth, crypto, secrets, input
validation at a trust boundary, deserialization, dependency manifests/lockfiles, IaC, CI config):
a prose-only Markdown edit matches none of them — there is no code, no dependency file, no IaC/CI
file in the diff at all. This is not an ambiguous case that the fail-closed rule would flip to
"cast" (fail-closed applies when "a reasonable reviewer could argue either way" per Step 3 — a
README paragraph edit isn't a close call). CAST correctly **skips** the Security seat; no gap
statement is needed either, since "not cast because the diff had nothing to trigger it" is the
seat's normal not-applicable state, distinct from the coverage-honesty gap in AC2 (plugin absent
despite cast-eligibility). **PASS.**

---

## 6. VALIDATE (worked by hand, not live-redispatched — same limitation `PRESSURE-TEST.md` documents)

All 4 Critical findings would receive 2-3 independent validators per
`merge-and-validate.md` ("2-3 for Critical... 2 when confidence is 75+"); confidence is 100 here,
so 2 validators each. Not live-redispatched for this step (would require dispatching yet more
subagents purely to second-guess already-doubly-corroborated findings), but reasoned through
per VALIDATE's actual challenge framing (try to show the finding is WRONG using only the code, not
the finder's reasoning):

- **Auth bypass:** could a challenger show `jwt.decode` still enforces the signature some other
  way? No — `auth-clients.ts:12-13`'s own doc comment says decode is "WITHOUT verifying its
  signature," and nothing else in `after.ts` calls `verify` anywhere. **SURVIVES.**
- **Hardcoded secret:** could a challenger show this is test/dev-only code excluded from
  production? No signal in the fixture supports that — the file is a plain exported module with no
  environment guard. **SURVIVES.**
- **SQL injection:** could a challenger show the driver escapes concatenated strings automatically?
  `DbClient.query(sql, params?)`'s signature (`auth-clients.ts:22`) takes `sql: string,
  params?: unknown[]` — a driver-level auto-escape would make the `params` argument pointless, and
  `before.ts` already uses `params` for exactly this purpose, confirming the driver expects
  parameterization rather than providing it automatically. **SURVIVES.**
- **IDOR:** could a challenger show `requestedUserId` is validated elsewhere against the caller's
  own identity before reaching this function? Nothing in the fixture (a self-contained module) shows
  such a check, and the docstring change (`after.ts:14-15`) explicitly documents the new, different
  intent. **SURVIVES.**

All 4 Critical findings SURVIVE a hand-worked adversarial challenge using only the code — none are
refuted. This mirrors the challenge discipline VALIDATE formalizes, though — per this section's own
honesty label — it is reasoning-by-hand, not a second live subagent dispatch.

---

## 7. Summary — AC-by-AC

| AC | Requirement | Result |
|---|---|---|
| 1 | With security-suite + dependency lockfile diff → Security seat present in Cast output with rationale | **PASS** — worked walkthrough, Section 5 (deterministic per catalog's named trigger) |
| 2 | Without security-suite + same diff → Coverage Honesty states the gap explicitly | **PASS** — LIVE: `security-suite:security-engineer` confirmed absent from this session's agent-type list by an actual failed `Agent` call; fallback text verified against a live `adversarial-reviewer` dispatch that independently caught all 4 Critical findings via Scope item 2 |
| 3 | Docs-only diff → Security seat absent from Cast output | **PASS** — worked walkthrough, Section 5 (no trigger matched, not an ambiguous/fail-closed case) |
| 4 | Seeded vulnerable-diff fixture → validated MERGE finding with fingerprints + confidence anchors | **PASS** — `tests/fixtures/auth-token-service/`, 2 live independent `Task` dispatches (Section 3), hand-worked MERGE table with 4 Critical findings at confidence 100 (2+-seat agreement, quote-the-line gate passed) plus 4 lower-confidence single-seat findings (Section 4), hand-worked VALIDATE reasoning (Section 6) |

## 8. Limits of this test pass (stated explicitly, per this repo's own standard)

- No automated regression suite exists or was created — `review-panel` is markdown-driven subagent
  orchestration, not executable code, matching `tests/PRESSURE-TEST.md`'s own stated limits.
- Section 3's two dispatches are real, live, independent `Task` calls with full raw output quoted
  above — not summarized or fabricated. Sections 4 and 6 (MERGE, VALIDATE) are worked by hand
  against the literal rules in `references/merge-and-validate.md`, not live multi-round panel
  executions — same limitation `PRESSURE-TEST.md` documents for its own MERGE/VALIDATE sections.
- The security-engineer persona (Section 3a) was dispatched via `general-purpose` reading the
  actual `security-engineer.md` file, not via the real `security-suite:security-engineer`
  agent-type name, because that agent-type is genuinely unavailable in this session (which is
  itself the AC2 condition being tested). This means the *content* of what that persona produces is
  validated live, but the *cross-plugin dispatch plumbing itself* (does `Task` with
  `subagent_type: "security-suite:security-engineer"` actually work end-to-end when the plugin
  *is* installed) remains unverified by this test pass — it rests on the same precedent
  (`review-panel:clean-room-alternative` resolving correctly in this session's own agent-type list)
  `investigation.md` already identified, not on a fresh confirmation.
- AC1's walkthrough is deterministic reasoning against the catalog's literal cast-when text, not a
  live CAST-subagent dispatch — a live CAST dispatch against a real lockfile-diff fixture would be
  a stronger future check but was judged unnecessary here since the trigger condition (dependency
  lockfile) is named explicitly and unambiguously in the catalog, unlike a risk-triggered seat where
  judgment genuinely varies.
