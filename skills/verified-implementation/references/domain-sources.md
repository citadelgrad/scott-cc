# Authoritative Sources by Domain

Quick lookup for Step 2 (FETCH) of the verified-implementation workflow.
Always fetch the specific section, not the document root.

## Cryptography

| Topic | Source | URL |
|-------|--------|-----|
| AES, SHA, RSA key sizes | FIPS 180-4 (hashing), FIPS 186-5 (signatures) | https://csrc.nist.gov/publications/detail/fips/180/4/final |
| Symmetric encryption modes (GCM, CBC) | NIST SP 800-38D (GCM), 800-38A (CBC) | https://csrc.nist.gov/publications/detail/sp/800-38d/final |
| Key derivation (HKDF) | RFC 5869 | https://datatracker.ietf.org/doc/html/rfc5869 |
| Password hashing (Argon2id) | RFC 9106, Section 4 (parameter recommendations) | https://www.rfc-editor.org/rfc/rfc9106.html#section-4 |
| Password hashing (bcrypt) | OWASP Password Storage Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html |
| ChaCha20-Poly1305 | RFC 8439 | https://datatracker.ietf.org/doc/html/rfc8439 |
| Elliptic curves (ECDH, ECDSA) | FIPS 186-5, SEC 1 v2.0 | https://csrc.nist.gov/publications/detail/fips/186/5/final |
| Random number generation | NIST SP 800-90A Rev. 1 | https://csrc.nist.gov/publications/detail/sp/800-90a/rev-1/final |
| Python cryptography library | cryptography.io | https://cryptography.io/en/latest/ |
| NIST test vectors | NIST CAVP | https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program |

**Never use:** MD5 or SHA-1 for security purposes, DES, 3DES, RC4, ECB mode, RSA < 2048-bit, `random.random()` / `Math.random()` for secrets.

## Authentication and Sessions

| Topic | Source | URL |
|-------|--------|-----|
| JWT structure and validation | RFC 7519 §7.2 | https://datatracker.ietf.org/doc/html/rfc7519#section-7.2 |
| JWT security best practices | OWASP JWT Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Tokens_Cheat_Sheet_for_Java.html |
| OAuth 2.0 | RFC 6749 | https://datatracker.ietf.org/doc/html/rfc6749 |
| OAuth 2.0 security (PKCE, etc.) | RFC 9700 (OAuth 2.0 Security BCP) | https://datatracker.ietf.org/doc/html/rfc9700 |
| OpenID Connect | OIDC Core 1.0 | https://openid.net/specs/openid-connect-core-1_0.html |
| Session management | OWASP Session Management Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html |
| Authentication general | OWASP Authentication Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html |
| Multi-factor auth | OWASP MFA Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/Multifactor_Authentication_Cheat_Sheet.html |

## Authorization and Access Control

| Topic | Source | URL |
|-------|--------|-----|
| Authorization general | OWASP Authorization Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html |
| RBAC | NIST RBAC standard (NIST IR 7316) | https://csrc.nist.gov/publications/detail/nistir/7316/final |
| IDOR prevention | OWASP IDOR Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/Insecure_Direct_Object_Reference_Prevention_Cheat_Sheet.html |
| CSRF | OWASP CSRF Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html |

## Transport Security

| Topic | Source | URL |
|-------|--------|-----|
| TLS 1.3 | RFC 8446 | https://datatracker.ietf.org/doc/html/rfc8446 |
| TLS configuration | OWASP TLS Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Security_Cheat_Sheet.html |
| HSTS | RFC 6797 | https://datatracker.ietf.org/doc/html/rfc6797 |
| CORS | Fetch Living Standard (CORS section) | https://fetch.spec.whatwg.org/#http-cors-protocol |
| HTTP security headers | OWASP Secure Headers | https://owasp.org/www-project-secure-headers/ |
| Cookie security | RFC 6265 §5 | https://datatracker.ietf.org/doc/html/rfc6265#section-5 |

## Financial and Monetary Arithmetic

| Topic | Source | URL |
|-------|--------|-----|
| Floating-point representation risks | IEEE 754-2019 | https://ieeexplore.ieee.org/document/8766229 |
| Decimal arithmetic (Python) | Python decimal module docs | https://docs.python.org/3/library/decimal.html |
| Money handling patterns | Martin Fowler — Money pattern | https://martinfowler.com/eaaCatalog/money.html |
| PCI-DSS (card data) | PCI DSS v4.0 | https://www.pcisecuritystandards.org/document_library/ |

**Rule:** Never use `float`/`double` for monetary values. Use `Decimal` (Python), `BigDecimal` (Java/Kotlin), or an integer cents representation.

## Input Validation and Injection Prevention

| Topic | Source | URL |
|-------|--------|-----|
| SQL injection prevention | OWASP SQL Injection Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html |
| Command injection prevention | OWASP OS Command Injection | https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html |
| Input validation general | OWASP Input Validation Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html |
| XSS prevention | OWASP XSS Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html |
| XXE prevention | OWASP XXE Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html |

## Deserialization

| Topic | Source | URL |
|-------|--------|-----|
| Deserialization risks | OWASP Deserialization Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html |
| Python pickle risks | Python docs warning | https://docs.python.org/3/library/pickle.html#security-warning |
| YAML safe loading | PyYAML docs | https://pyyaml.org/wiki/PyYAMLDocumentation |

## Network Protocols and Identifiers

| Topic | Source | URL |
|-------|--------|-----|
| UUID v4/v7 | RFC 9562 | https://datatracker.ietf.org/doc/html/rfc9562 |
| URI/URL structure | RFC 3986 | https://datatracker.ietf.org/doc/html/rfc3986 |
| HTTP semantics | RFC 9110 | https://datatracker.ietf.org/doc/html/rfc9110 |
| HTTP/2 | RFC 9113 | https://datatracker.ietf.org/doc/html/rfc9113 |
| DNS | RFC 1035 | https://datatracker.ietf.org/doc/html/rfc1035 |
| Email (SMTP) | RFC 5321 | https://datatracker.ietf.org/doc/html/rfc5321 |
| SSRF prevention | OWASP SSRF Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html |

## Distributed Systems

| Topic | Source | URL |
|-------|--------|-----|
| Raft consensus | Ongaro & Ousterhout, "In Search of an Understandable Consensus Algorithm", USENIX ATC 2014 | https://raft.github.io/raft.pdf |
| Logical clocks | Lamport, "Time, Clocks, and the Ordering of Events", CACM 1978 | https://doi.org/10.1145/359545.359563 |
| Idempotency keys | Stripe idempotency guide | https://stripe.com/docs/idempotency |
| Database isolation levels | PostgreSQL isolation docs | https://www.postgresql.org/docs/current/transaction-iso.html |

## How to Find RFC Section Deep Links

```
https://datatracker.ietf.org/doc/html/rfc{NUMBER}#section-{X.Y}
https://datatracker.ietf.org/doc/html/rfc{NUMBER}#appendix-{A}

Examples:
  RFC 7519 §7.2  → https://datatracker.ietf.org/doc/html/rfc7519#section-7.2
  RFC 8446 §4.2  → https://datatracker.ietf.org/doc/html/rfc8446#section-4.2
```

## How to Find NIST Publication Links

NIST PDFs lack stable section anchors. Link to the publication landing page; cite section in prose.

```
FIPS: https://csrc.nist.gov/publications/detail/fips/{NUMBER}/{PART}/final
SP:   https://csrc.nist.gov/publications/detail/sp/{SERIES}-{NUMBER}/rev-{N}/final

Examples:
  FIPS 180-4     → https://csrc.nist.gov/publications/detail/fips/180/4/final
  NIST SP 800-56A Rev. 3 → https://csrc.nist.gov/publications/detail/sp/800-56a/rev-3/final
```
