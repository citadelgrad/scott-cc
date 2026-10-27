# OpenClaw (Peter Steinberger's agent platform; formerly Clawdbot, Moltbot) - Security Defaults in the Redesign

Scope note: This is the AI agent platform at github.com/openclaw/openclaw, NOT the Captain Claw game reimplementation. Research date 2026-10-17. I found NO single announcement of a "security-by-default redesign." What exists is a series of date-versioned releases (2026.1.29 ... 2026.7.1, 2026.7.33 LTS, 2026.8.1), a docs set describing "conservative defaults," a Trail of Bits audit, and an enterprise control plane (OpenClaw Enterprise, "OCE"). Treat "the redesign" as the current docs/release state. Several protections are OFF by default (sandbox, exec approvals) - this contradicts a "secure by default" framing.

## What security problems did earlier OpenClaw versions have? (EARLIER HISTORY)

### Takeaway
Early 2026 versions had a token-leak/RCE class CVE (CVE-2026-25253), large numbers of internet-exposed gateways, and a malicious-skill campaign on ClawHub (ClawHavoc, 341 skills per Koi). Secondary sources disagree on counts and some CVE details; treat numbers as rough.

### Cited Findings
- Koi Security audited all 2,857 ClawHub skills (Feb 1, 2026) and flagged 341 as malicious in a campaign called "ClawHavoc"; 335 reportedly came from a single supply-chain attempt (secondary reporting) - [CSO Online via search summary](https://csoonline.com/article/4129393/openclaw-integrates-virustotal-malware-scanning-as-security-firms-flag-enterprise-risks.html)
- Another source says the campaign ran in a 72-hour window Jan 27-29, 2026 and that 335 skills delivered Atomic Stealer (AMOS) on macOS via fake install hooks (search-summary of unofficial blogs; unverified) - [Mothasa Substack](https://mothasa.substack.com/p/the-most-popular-ai-agent-on-github), [Known Vulnerabilities (clawdocs.org, unofficial)](https://clawdocs.org/security/known-vulnerabilities)
- Aviatrix (July 2, 2026) says threat actors uploaded "over 1,100 malicious 'skills' to ClawHub" and lists CVE-2026-25253 (CVSS 8.8, auth token leakage, exploited in the wild), CVE-2026-24763 (CVSS 8.8, command injection), CVE-2026-25157 (CVSS 7.5, command injection), affecting versions before 2026.1.29. The page does not reconcile 1,100 vs 341 - [Aviatrix](https://aviatrix.ai/threat-research-center/openclaw-clawhub-malicious-skills-supply-chain-attack-2026/)
- CVE-2026-25253 described in search results as a WebSocket flaw letting a malicious webpage steal the gateway auth token even on localhost-bound instances, patched in 2026.1.29 (Jan 29, 2026). A separate Oasis Security disclosure "ClawJacked" was reported as patched in 2026.2.25 (Feb 26, 2026). One docs site describes the CVE differently (CVSS 9.8 REST RCE, "v3.x") - conflicting; NOT verified against NVD - [Mothasa Substack](https://mothasa.substack.com/p/the-most-popular-ai-agent-on-github); contradicted by [clawdocs.org](https://clawdocs.org/security/known-vulnerabilities)
- Exposure estimates range ~21,000 (late Jan) to 135,000+ instances, "63% without authentication" attributed to ARMO (March 2026) and Bitdefender; not independently confirmed - search summary of [betterclaw.io](https://betterclaw.io/blog/openclaw-security-2026) and similar blogs (unofficial)
- Cloud Security Alliance hardening guide states default bind was 0.0.0.0:18789 (listening on all interfaces) - older guide, likely predates loopback default - [CSA Labs](https://labs.cloudsecurityalliance.org/agentic/agentic-openclaw-hardening-guide-v1/)
- Unit 42 (Feb-May 2026 analysis) found five ClawHub skills that evaded blocking, reported for takedown; accounts banned and skills deleted - [Unit 42](https://unit42.paloaltonetworks.com/openclaw-ai-supply-chain-risk/) (via search summary)
- July 2, 2026 coordinated batch of at least 14 advisories: authorization/allowlist checks not applied uniformly across invocation paths; message reads could bypass channel allowlists; hook-triggered runs could inherit owner-level authority (third-party summary) - [CellCog blog, Aug 21 2026](https://cellcog.ai/blog/openclaw-security/)
- Third-party CVEs from that period: CVE-2026-53818 (MCP loopback path could skip owner-only tool policy), CVE-2026-53854 (Control UI locality spoofing could mint a durable admin device token), CVE-2026-53810 (marketplace runtime-extension metadata could point at unscanned payloads) - [CellCog](https://cellcog.ai/blog/openclaw-security/) (unofficial; not checked against NVD)
- Secrets: plaintext credentials remain readable by the agent in `openclaw.json`, `.env`, retired auth-profile JSON archives and generated `agents/*/agent/models.json` - [Docs: secrets](https://docs.openclaw.ai/gateway/secrets)

### Inferences
- The early problems were three layers: gateway reachability/auth, supply chain (ClawHub), and plaintext secrets. Each later feature below maps to one.
- Counts (341 vs 1,100 vs 2,400) are not reconciled across sources; the report writer should cite Koi's 341/2,857 as the best-attributed figure.

### Gaps
- I did not fetch Koi Security's original report, NVD entries, or the official GHSA text for CVE-2026-25253; details come from secondary sources.
- No primary source found for "Bitdefender 135,000" or "ARMO 63%".

## What does the current state change by default? (auth, binding, sandbox, approvals, skills, secrets, prompt injection, audit, updates, telemetry)

### Takeaway
Host installs bind to loopback and unknown DM senders get a pairing code, with group allowlists plus mention gating. But sandboxing is off by default and exec approvals default to `security: full`, `ask: off`, so tool execution is broadly permissive unless the operator tightens it.

### Cited Findings
- Network/pairing/groups: "On regular host installs the Gateway binds to loopback"; container images default to an exposed bind (pair with auth); most channels "answer an unknown DM sender with a pairing code instead of processing the message"; DM modes are pairing, allowlist, open, disabled; groups are allowlisted, usually mention-gated; ClickClack trusts workspace membership by default - [Docs: gateway security](https://docs.openclaw.ai/gateway/security)
- Tool policy default: agents with message-tool access can send across conversations and providers by default; restricting needs config - [Docs: gateway security](https://docs.openclaw.ai/gateway/security)
- Sandbox: "Sandboxing is off by default." Gateway always runs on host; only tool execution moves into sandbox. Enable via `agents.defaults.sandbox` or `agents.entries.*.sandbox`; example `mode: "non-main"`, `scope: "session"`, `workspaceAccess: "none"`. Backends: Docker (default local), Podman, SSH, OpenShell, Crabbox. `tools.elevated` runs exec outside sandbox. Sandbox "is not a perfect security boundary" but "materially limits filesystem and process access." Tool deny policy applies before sandbox rules. `agents.entries.<id>.tools.github.allowInSandbox` is disabled by default - [Docs: sandboxing](https://docs.openclaw.ai/gateway/sandboxing)
- Exec approvals defaults: `security` = `full` on gateway/node hosts (`deny` on sandbox hosts); `ask` = `off`; `askFallback` = `deny`; `autoAllowSkills` = false; `tools.exec.strictInlineEval` = false (when true, `python -c` etc. need approval); `tools.exec.grantExpiryDays` unset = grants last until revoked. Preferred setting `tools.exec.mode` (deny/allowlist/ask/auto/full). "YOLO" needs `tools.exec.mode: "full"` plus host `security: full`, `ask: off`, `askFallback: full`. Allowlist entries from `allow-always` are bound to exact argv and working directory. Stricter of config and approvals file wins - [Docs: exec approvals](https://docs.openclaw.ai/tools/exec-approvals)
- Secrets: "Plaintext still works. SecretRefs are opt-in per credential." Providers `env`, `file`, `exec`, `store` (shared SQLite store). Commands `openclaw secrets audit|configure|apply`; `audit --check` reports plaintext residue. Secret values injected at egress time via sentinels. Recipes for 1Password, Bitwarden Secrets Manager, HashiCorp Vault, pass, sops - [Docs: secrets](https://docs.openclaw.ai/gateway/secrets)
- Model auth: "OpenClaw never reads, stores, refreshes, or forwards the native login tokens" when reusing Claude CLI login; manual tokens go to a SQLite auth store; `openclaw doctor --fix` imports legacy JSON auth files - [Docs: authentication](https://docs.openclaw.ai/gateway/authentication)
- Audit: `openclaw security audit` "checks for drift from the defaults" ("one command tells you if you have drifted"); `openclaw security` applies supported auto-fixes; `openclaw policy` inspects/tests tool policy - [Docs: gateway security](https://docs.openclaw.ai/gateway/security)
- Prompt injection: docs describe untrusted-input wrapping to bound injected content; "Bypass flags (keep off in production)"; `dangerous*` / `dangerously*` config keys exist - [Docs: gateway security](https://docs.openclaw.ai/gateway/security). SECURITY.md treats prompt-injection-only reports (no policy/auth/sandbox bypass) as out of scope - [SECURITY.md](https://github.com/openclaw/openclaw/blob/main/SECURITY.md)
- Trust model: "local-first agent infrastructure for trusted operators," "Authenticated Gateway callers are treated as trusted operators," "Plugins/extensions are part of OpenClaw's trusted computing base," "The model/agent is not a trusted principal." One user per host/gateway recommended - [SECURITY.md](https://github.com/openclaw/openclaw/blob/main/SECURITY.md)
- ClawHub scanning: announced Feb 7, 2026 (Steinberger, security advisor Jamieson O'Reilly, VirusTotal's Bernardo Quintero). Bundles hashed and checked against VirusTotal; Code Insight (Gemini) summarizes code; benign auto-approved, suspicious labeled but listed, malicious blocked; active skills rescanned daily. OpenClaw warned scans do not catch prompt injection - [CSO Online](https://csoonline.com/article/4129393/openclaw-integrates-virustotal-malware-scanning-as-security-firms-flag-enterprise-risks.html), [iTnews](https://itnews.com.au/news/under-malware-threat-runaway-ai-agent-project-openclaw-turns-to-googles-virustotal-623450) (via search summary; not fetched in full)
- v2026.7.1 (July 13, 2026) hardening per third party: sandbox file ops tightened against symlink/hard-link/directory-race escapes; credential residue in historical config-audit logs and diagnostics/proxy captures addressed; browser permissions behind admin checks; stricter SSRF handling; marketplace pre-download screening with explicit acknowledgment for suspicious releases; persistent approvals no longer implicitly trust later payloads from package runners; deep audit command for old credential residue. Fix flag does not rotate credentials. Skill env vars and API keys are injected into the host agent process, not the sandbox - [CellCog](https://cellcog.ai/blog/openclaw-security/) (unofficial)
- Patch delivery: Trail of Bits fixes shipped in 2026.8.1 and 2026.7.33 LTS stable releases - [OpenClaw blog](https://openclaw.ai/blog/openclaw-trail-of-bits-engagement-recap)
- Enterprise (OCE, announced Sep 29, 2026): claims multi-tenant admin, fine-grained permissions, workload isolation, sandboxing, auditing, self-hosting on Docker Compose/Kubernetes; Red Hat OpenShift namespaces and credential proxies; Nvidia OpenShell deny-by-default with policy enforcement and audit trails. Foundation recommends OCE only for internal pilots, not production; reference architecture and 1.0 are "forthcoming" - [VentureBeat](https://venturebeat.com/orchestration/openclaw-launches-free-enterprise-control-plane-for-persistent-ai-agents-backed-by-openai-red-hat-and-nvidia)
- Defaults drifting looser (single unverified blog): `tools.sessions.visibility` changed tree -> agent -> all (at 8.2 and 9.2) and `tools.swarm.enabled` off -> on at 9.2; the audit reportedly does not flag these - [Substack](https://youcanbuildthings.substack.com/p/how-to-stop-openclaw-updates-from) (unverified against release notes)
- Operator-opt-out risk: guide says exposure is "an opt-out problem" - public binding, `gateway.controlUi.allowInsecureAuth: true`, trivial secrets - [Pinchy](https://heypinchy.com/openclaw-for-teams/) (unofficial)

### ON / opt-in / can-disable matrix (from the above)
- ON by default: loopback bind (host installs); DM pairing for unknown senders; group allowlist and mention gating; `askFallback: deny`; `autoAllowSkills: false`; ClawHub VirusTotal scanning (service-side, per Feb 2026 announcement).
- OFF by default / opt-in: sandboxing; exec approval prompts (`ask: off`, `security: full`); SecretRefs (plaintext still works); `strictInlineEval`; cross-provider messaging restriction; OCE controls.
- User can disable/loosen: sandbox, approvals (YOLO combo), `tools.elevated`, `dangerous*` keys, `gateway.controlUi.allowInsecureAuth`, DM `open` mode.

### Inferences
- "Secure by default" is true for exposure (loopback, pairing) but not for execution (no sandbox, no approvals). The default posture is "trusted single operator," consistent with SECURITY.md.
- Container default is an exposed bind, so Docker users do not get the loopback protection.

### Gaps
- Gateway auth default (token/password required or not) not stated on pages I fetched; I did not read the Configuration or Trusted Proxy Auth docs.
- No source found on skill signing or capability scoping/permission manifests for skills beyond `autoAllowSkills` and scanning.
- Telemetry defaults: nothing found for OpenClaw core. NVIDIA NemoClaw v0.0.135 (Oct 15, 2026, a separate NVIDIA wrapper) adds a prompt to enable OpenShell audit logging - [NVIDIA release notes](https://docs.nvidia.com/nemoclaw/user-guide/openclaw/release-notes/2026/10/15)
- Audit-log defaults for core (what is logged, retention) not found. Update-delivery mechanism (auto-update, signing) not found.
- Release notes/changelog for 2026.8.x-2026.10.x were not read.

## External audits, bug bounty, and advisory process

### Takeaway
Trail of Bits audited via OpenAI's Patch the Planet (published Sep 21, 2026): no Critical, 2 High findings, all actionable fixed. No paid bug bounty; GHSA private advisory process is active (73 advisories listed).

### Cited Findings
- Trail of Bits engagement, post by Josh Avant (OpenClaw Foundation), Sep 21, 2026: 27 private advisories + 3 hardening PRs; 24 severity-rated: 0 Critical, 2 High, 16 Medium, 6 Low; 3 defense-in-depth with no rating; all actionable issues fixed, 3 PRs merged. Scope: "core permissions and how OpenClaw handles user data." Method: Codex-assisted search with manual Trail of Bits checks - [OpenClaw blog](https://openclaw.ai/blog/openclaw-trail-of-bits-engagement-recap)
- Themes: permissions lost between steps (follow-on work lacked limits; "A filename generator, for example, does not need tools."); inconsistent names (check one name, use another); checks not matching use (partial archive check before extraction; file path changed after approval; fix "bind approval to the exact file, identity, or action that will be used"); permissions changing mid-run (agent kept reading memory after memory access disabled) - [OpenClaw blog](https://openclaw.ai/blog/openclaw-trail-of-bits-engagement-recap)
- Advisories page: 73 advisories; 10 on page one all published Sep 11, 2026, by joshavant. Examples: GHSA-3mq7-q27j-mq7q (High) "Exec approvals could outlive their reviewed working directory"; GHSA-9m4p-cqp4-jppq (High) "WhatsApp login tool could reach non-owner turns"; GHSA-5rx7-34fw-64qg (Moderate) "Unicode fallback could escape workspaceOnly roots"; GHSA-5j57-84cx-r295 (Moderate) "iOS deep-link logs could expose unattended credentials"; GHSA-vhpg-cq3w-v8p9 (Moderate) "OpenAI-compatible transport could send provider credentials to the wrong endpoint"; GHSA-7jfq-rmfm-29wp (Moderate) "File-transfer approvals could widen durable authority"; also Slack file download authorization, Discord media policy, Prometheus `operator.read`, browser relay pending-capacity exhaustion - [GitHub advisories](https://github.com/openclaw/openclaw/security/advisories)
- Bug bounty: "OpenClaw does not currently run a paid bug bounty program." Private GHSA reporting; security@openclaw.ai fallback - [SECURITY.md](https://github.com/openclaw/openclaw/blob/main/SECURITY.md)
- Out of scope per SECURITY.md: public internet exposure, multi-adversary shared gateway, prompt-injection-only, malicious already-installed plugins, findings depending on "dangerous" config options - [SECURITY.md](https://github.com/openclaw/openclaw/blob/main/SECURITY.md)
- Independent academic analyses exist: arXiv 2603.10387, 2603.13151, 2606.15008 (titles only seen; not read) - [arXiv 2606.15008](https://arxiv.org/pdf/2606.15008)

### Inferences
- The Trail of Bits report is OpenClaw's own recap, not an independent report; the underlying Trail of Bits report was not found. Note the audit was Codex-assisted, scoped to permissions/data handling, not a full-product audit.
- The recurring "permission lost between steps / approval not bound to exact resource" themes match the Sep 11 High advisories.

### Gaps
- Trail of Bits' own publication not found. CVE IDs for the Sep 2026 GHSAs not shown on the listing.

## Known remaining weaknesses / open CVEs as of October 2026

### Takeaway
No fully verified list of open CVEs found. Known residual risks are design-level (trusted-operator model, plugins in TCB, sandbox not a perfect boundary, defaults that are permissive) plus a steady flow of Moderate/High GHSAs through Sep 2026.

### Cited Findings
- 73 advisories exist; Sep 11, 2026 batch includes two High (exec approvals outliving cwd; WhatsApp login tool reaching non-owner turns) - [GitHub advisories](https://github.com/openclaw/openclaw/security/advisories). Patched versions not shown on the listing.
- Docs admit sandbox "is not a perfect security boundary" - [Docs: sandboxing](https://docs.openclaw.ai/gateway/sandboxing)
- Skill API keys/env injected into host process, not sandbox; plugins are in the trusted computing base - [CellCog](https://cellcog.ai/blog/openclaw-security/) (unofficial); [SECURITY.md](https://github.com/openclaw/openclaw/blob/main/SECURITY.md)
- Marketplace evasion persisted (Unit 42, five skills, Feb-May 2026); OpenClaw itself says scanning will not stop prompt injection - [CSO Online](https://csoonline.com/article/4129393/openclaw-integrates-virustotal-malware-scanning-as-security-firms-flag-enterprise-risks.html)
- HalluSquatting research published July 15, 2026 (title only, via CellCog; not read) - [CellCog](https://cellcog.ai/blog/openclaw-security/)
- CellCog reported no confirmed large-scale breach in July-August 2026 (unofficial, as of Aug 21) - [CellCog](https://cellcog.ai/blog/openclaw-security/)

### Inferences
- Because multi-tenant isolation is explicitly out of scope, shared-gateway deployments carry design-accepted risk.

### Gaps
- No NVD query done; I cannot confirm which CVEs are open/unpatched in the latest release. Nothing found dated Oct 2026 for OpenClaw core security, other than the NVIDIA NemoClaw note.
- Prompt-injection mitigation effectiveness not independently tested in any source found.
