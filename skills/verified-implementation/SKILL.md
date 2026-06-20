---
name: verified-implementation
description: Use when implementing security-critical code (auth, crypto, secrets, TLS, CORS), financial arithmetic, protocol parsers, deserialization of untrusted data, or any code the user wants to be "production-ready," "correct," or "verified." Requires citing authoritative sources — RFCs, NIST, OWASP, official library docs — before writing, not after.
license: MIT
---

# Verified Implementation

Every critical implementation decision must trace to an authoritative source. Don't implement from memory — verify, cite, and let the user see the chain. Training data goes stale. Algorithms get deprecated. Correct-looking code can be subtly wrong in ways that produce zero runtime errors but full security failures.

This skill extends [source-driven-development](https://github.com/addyosmani/agent-skills/blob/main/skills/source-driven-development/SKILL.md) beyond framework version compatibility to correctness-critical domains where the ground truth is a specification, not a docs page: cryptography, authentication, financial arithmetic, network protocols, and deserialization of untrusted data.

For **framework-specific patterns** (which library version to use, how an API changed): use the `context7` skill first — it resolves library IDs and fetches version-pinned docs automatically. Use *this* skill when the authority is an RFC, NIST publication, OWASP cheat sheet, or specification.

## When to Use

- Implementing cryptographic primitives, key derivation, secure RNG, or key management
- Writing authentication, session management, JWT handling, or authorization enforcement
- Adding financial or monetary arithmetic
- Parsing network protocols, binary formats, or external serialized data
- Configuring TLS/SSL, CORS, cookie security, or transport-level settings
- Writing code that will be copied as a project template or starter
- The user asks for code that is "production-ready," "correct," "secure," or "verified"

**When NOT to use:**
- Renaming variables, fixing typos, or moving files
- Pure refactoring with no logic changes
- UI components with no security or correctness sensitivity
- Framework API usage (use `context7` or `source-driven-development`)
- The user explicitly wants speed over verification ("just do it quickly")

## Criticality Triage

Before fetching anything, decide the tier. State it.

| Tier | Applies when | Action |
|------|-------------|--------|
| **1 — Always verify** | Crypto primitives, auth/password logic, authorization enforcement, financial arithmetic, deserialization of untrusted data | Full workflow: fetch spec, implement from it, cite inline and in PR |
| **2 — Verify if non-obvious** | TLS/SSL config, SQL/command execution, state machine transitions, protocol parsing | Fetch authoritative source; cite when the decision is non-trivial |
| **3 — Note the risk** | HTTP input trust boundaries, file paths from user input, concurrent shared state | Flag the risk; no full citation unless the pattern itself is non-obvious |

**Quick Tier 1 signals:**

```
imports:  crypto, ssl, cipher, hashlib, argon2, bcrypt, jwt, oauth, saml
imports:  pickle, marshal, yaml (without SafeLoader), subprocess
keywords: password, secret, api_key, token (in string assignments)
keywords: price, amount, balance, fee, total (with float types)
keywords: permission, role, admin, authorize
patterns: SQL string concatenation, eval(), random.random() near auth/token code
patterns: float arithmetic on monetary variable names without Decimal type
```

State the tier before proceeding:

```
CRITICALITY: Tier 1 — JWT signature verification
→ Fetching RFC 7519 §7.2 and library docs before implementing.
```

## Source Authority Hierarchy

| Priority | Source | Examples |
|----------|--------|---------|
| **1** | Authoritative specifications | IETF RFCs, FIPS publications, NIST SP 800-series, SEC specifications |
| **2** | Security bodies and standards organizations | OWASP Cheat Sheet Series, W3C specs, IANA registries |
| **3** | Official library documentation | cryptography.io, pyjwt.readthedocs.io, pkg.go.dev |
| **4** | Official changelogs and errata | RFC errata, NIST revision notices |
| **Never** | Training data, Stack Overflow, blog posts, AI summaries | These are not sources |

For cryptographic algorithms and protocols: start at Priority 1. The RFC or FIPS publication is the ground truth — not any library's documentation, which may simplify, omit, or lag behind the specification.

See `references/domain-sources.md` for authoritative URLs by domain (auth, crypto, payments, distributed systems, protocols).

## The Workflow

```
TRIAGE → FETCH → IMPLEMENT → CITE → FLAG
```

### Step 1 — Triage

Classify the pattern using the tier table above. State it explicitly before fetching anything.

### Step 2 — Fetch

Fetch the specific section for the pattern being implemented. Not a homepage. Not a search result. The relevant section.

```
FETCHING: RFC 7519 §7.2 — Validating a JWT
FETCHING: https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Tokens_Cheat_Sheet_for_Java.html

BAD:  "Fetching JWT documentation"
GOOD: "Fetching RFC 7519, Section 7.2 — validation steps"
```

After fetching, extract:
- The authoritative pattern or API to follow
- Any deprecation warnings or migration guidance
- The version, revision, or date the source applies to

When official sources conflict (e.g., a migration guide contradicts the API reference), surface the discrepancy to the user. Do not silently resolve it.

### Step 3 — Implement

Write code that matches the fetched source:
- Use API signatures from the specification, not from memory
- If the spec deprecates a pattern, don't use the deprecated version
- If the spec doesn't cover something, flag it as UNVERIFIED in Step 5

### Step 4 — Cite

Every Tier 1 decision gets an inline citation. Every non-obvious Tier 2 decision gets a citation.

**In code comments:**

```python
# JWT validation per RFC 7519, Section 7.2.
# Source: https://datatracker.ietf.org/doc/html/rfc7519#section-7.2
decoded = jwt.decode(token, key, algorithms=["RS256"])
```

```go
// SHA-256 as defined in FIPS 180-4, Section 6.2.
// See: https://csrc.nist.gov/publications/detail/fips/180/4/final
h := sha256.New()
```

```python
# Argon2id parameters per RFC 9106, Section 4.
# Source: https://www.rfc-editor.org/rfc/rfc9106.html#section-4
# OWASP minimum: m=19456, t=2, p=1
ph.hash(password)
```

**Citation rules:**
- Full URLs only — no shortened links
- Always include the section: "RFC 7519, Section 7.2" not "RFC 7519"
- Deep anchor links preferred: `#section-7.2` over the document root
- Quote the relevant passage when supporting a non-obvious decision
- NIST PDFs have no stable URL anchors — link to the CSRC publication page, cite section in prose

### Step 5 — Flag unverified patterns

When a pattern cannot be sourced from an authoritative document:

```
UNVERIFIED: No authoritative documentation found for this pattern.
This is based on training data and may be outdated or incorrect.
Verify before using in production.
Suggested source to check: [URL]
```

Explicit flagging is more honest and more useful than a confident but uncited answer.

## Citing in PR Descriptions

For Tier 1 changes, add a "Sources consulted" block to the PR body. The citation survives code review and becomes a permanent record.

```markdown
## Sources consulted
- RFC 7519 §7.2 — JWT validation steps: https://datatracker.ietf.org/doc/html/rfc7519#section-7.2
- OWASP JWT Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Tokens_Cheat_Sheet_for_Java.html
- PyJWT 2.8.0 decode docs: https://pyjwt.readthedocs.io/en/stable/usage.html
```

## Citation Format Reference

| Source type | Format |
|-------------|--------|
| RFC | `RFC NNNN, Section X.Y` + `https://datatracker.ietf.org/doc/html/rfcNNNN#section-X.Y` |
| IETF draft | `draft-ietf-[wg]-[name]-NN` + `https://datatracker.ietf.org/doc/html/draft-ietf-[wg]-[name]-NN` |
| FIPS | `FIPS NNN, Section N.N` + `https://csrc.nist.gov/publications/detail/fips/NNN/[part]/final` |
| NIST SP 800-series | `NIST SP 800-NNN Rev. N, Section N.N.N` + `https://csrc.nist.gov/publications/detail/sp/800-NNN/rev-N/final` |
| OWASP Cheat Sheet | Name + `https://cheatsheetseries.owasp.org/cheatsheets/[Name]_Cheat_Sheet.html` |
| Academic paper | `Author(s), "Title", Venue Year` + DOI (`https://doi.org/[DOI]`) |
| Library docs | Library + version + section URL |

**The most important rule:** Always cite to the specific section, never just the document. "See RFC 8446" is nearly useless. "See RFC 8446, Section 4.2.1" is actionable.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'm confident about this algorithm" | Confidence is not evidence. Cryptographic APIs and recommended parameters change. Deprecated algorithms look identical to current ones in code. |
| "This is a simple crypto call" | Wrong mode, reused IV, or weak algorithm provides zero security with no runtime error. Simple calls have the highest surface area for subtle failure. |
| "Fetching docs wastes tokens" | A hallucinated algorithm wastes hours of debugging and can create a CVE. One fetch prevents this. |
| "I'll just note it might be wrong" | A disclaimer doesn't help. Either verify and cite, or flag explicitly as UNVERIFIED. Hedging is the worst option. |
| "The docs won't say anything different" | If they don't, the fetch costs 30 seconds. If they do, the fetch prevents a production incident. |

## Red Flags

- Writing crypto, auth, or financial code without fetching from an authoritative source
- Using "I believe" or "I think" about a security-critical API or algorithm
- Implementing from memory because "this algorithm is well-known"
- Citing Stack Overflow or blog posts for cryptographic or protocol decisions
- Using deprecated algorithms (MD5, SHA1, DES, RC4, ECB mode) without explicit justification from the spec
- Float arithmetic on monetary variable names without `Decimal` / `BigDecimal`
- Missing section number in an RFC or NIST citation ("See RFC 8446" with no section)
- Missing the `UNVERIFIED:` block when a pattern has no authoritative source

## Pre-Merge Checklist

- [ ] Criticality tier identified before implementation began
- [ ] Authoritative sources fetched (not recalled from training data)
- [ ] All Tier 1 decisions have inline citations with full URLs and section numbers
- [ ] No deprecated algorithms used in security contexts (MD5, SHA1, DES, RC4, ECB)
- [ ] No non-cryptographic RNG in security or auth contexts (`random.random()`, `Math.random()`)
- [ ] No float types used for monetary arithmetic
- [ ] Patterns without an authoritative source are explicitly flagged UNVERIFIED
- [ ] PR description includes "Sources consulted" block for Tier 1 changes
- [ ] Doc/code conflicts surfaced to the user, not silently resolved
