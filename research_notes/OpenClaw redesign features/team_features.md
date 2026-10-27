# OpenClaw redesign: team, multi-user, and organization features (as of 2026-10-17)

Scope note: this is OpenClaw the AI agent platform (Peter Steinberger; ex-Clawdbot, ex-Moltbot), not the Captain Claw reimplementation. Research used ~12 tool calls. Docs pages fetched via WebFetch are summaries by a small model, so config keys should be re-verified against the live docs.

## 1. Was OpenClaw originally single-user, and what changed in the redesign?

### Takeaway
Yes. Older material and the current security docs describe a "one agent, one owner" design. The "OpenClaw 2.0" release (reported as v2026.8.1, end of Aug 2026) added multi-user Gateways, shared sessions, roles and admin features. The project still states a Gateway is ONE trust domain, so collaboration is not hostile-tenant isolation.

### Cited Findings
- OpenClaw 2.0 = version 2026.8.1, per TechBriefly (dated Sep 1, 2026) and VentureBeat (Aug 31, 2026). Crypto Briefing says 2.0 was released Aug 30, 2026 (one-day discrepancy among sources). — [TechBriefly](https://techbriefly.com/2026/09/01/openclaw-2-0-launches-enterprise-collaboration-security/); [VentureBeat](https://venturebeat.com/technology/openclaw-2-0-is-here-what-it-means-for-enterprises); [Crypto Briefing](https://cryptobriefing.com/openclaw-enterprise-ai-agent-control-plane/)
- Steinberger (X, Aug 31): "Two months ago, we started the mission to 'build OpenClaw with OpenClaw.'" and "Multiplayer coding + infinite compute with nodes and cloud sessions has been a game changer for how we build." The team moved from individual local setups to team.openclaw.ai, a shared environment. — [TechBriefly](https://techbriefly.com/2026/09/01/openclaw-2-0-launches-enterprise-collaboration-security/)
- Release stats: 933 contributors (569 first-time), 16,000+ pull requests. — [VentureBeat](https://venturebeat.com/technology/openclaw-2-0-is-here-what-it-means-for-enterprises)
- Governance: stewarded by the OpenClaw Foundation, an independent 501(c)(3); listed partners OpenAI, Microsoft, GitHub, NVIDIA, Atlassian, Tencent. OpenAI donated the project to the Foundation. VentureBeat says the release was not shared by OpenAI, Steinberger's employer. — [VentureBeat](https://venturebeat.com/technology/openclaw-2-0-is-here-what-it-means-for-enterprises); [RuntimeWire](https://runtimewire.com/article/openclaw-enterprise-free-agent-control-plane)
- Official docs now say: the same Gateway "can run as a shared team deployment instead of a personal assistant. Only the configuration differs." — [docs.openclaw.ai](https://docs.openclaw.ai)
- Older/pre-redesign framing: DMs share the agent's main session; each group chat gets its own session (per-sender/per-group sessions). — [docs.openclaw.ai](https://docs.openclaw.ai)
- A third-party guide (OpenClaw Launch, dated Sep 2026, v2026.9.x line) says the design is still built around "one agent belonging to one owner," and the claimed "OpenClaw 2.0" version number "does not exist" (conflicts with VentureBeat/TechBriefly naming). — [OpenClaw Launch](https://openclawlaunch.com/guides/openclaw-multi-user)
- Latest releases seen on GitHub (as of Oct 15-16, 2026): 2026.10.4 (Latest), 2026.10.10-beta.1 (pre-release; Control UI "filter sidebar users by online status", "principal-bound" relay and remote Control UI for trusted plugins, conversation-level tool policy). Page read only in part (first 100k of 175k chars). — [GitHub releases](https://github.com/openclaw/openclaw/releases)

### Inferences
- "2.0" appears to be a marketing label used by press and the project; the actual versioning is calendar-based (YYYY.M.N). Treat the "2.0" name as informal.

### Gaps
- Did not read the full release notes for v2026.8.1 or v2026.9.x to date each individual team feature.
- Primary Steinberger/Foundation blog post not directly fetched; quotes come via press.

## 2. What team features exist now?

### Takeaway
Shipped: multi-user mode with session ownership/attribution/presence, config-defined roles (`gateway.roles`), per-session permission modes, sandbox-required roles, approvals, team Secret Store, provider budget view, audit log, per-person provider accounts, Publish PR. Absent or weak: SSO/OIDC/SAML (only trusted-proxy and Tailscale identity), per-user quotas, memory isolation between users, hostile-tenant isolation.

### Cited Findings
**Identity and sessions**
- Multi-user Gateways record who created a conversation and which identified participants submitted each prompt; UI adds session ownership, participant attribution, presence, typing indicators. — [VentureBeat](https://venturebeat.com/technology/openclaw-2-0-is-here-what-it-means-for-enterprises)
- Three attribution layers: immutable creator, assignable owner, history of prompters. Sessions can be reassigned from the context menu (does not replace the session's skills). Drafts never reach the model or transcript. Git co-author trailers added when co-author credit is enabled. — [Teams doc](https://docs.openclaw.ai/start/teams)
- Shared cloud sessions let a colleague join work in progress. Quote from Colin Johnson, CEO of Solvely: "The session itself became the handoff document." — [VentureBeat](https://venturebeat.com/technology/openclaw-2-0-is-here-what-it-means-for-enterprises)
- Session Share: a source operator pairs a node advertising only two read-only session commands; viewers cannot continue the source session. — [Teams doc](https://docs.openclaw.ai/start/teams)
- Owners and admins decide whether a user can read a session, suggest changes, work in draft mode, or participate directly. — [VentureBeat](https://venturebeat.com/technology/openclaw-2-0-is-here-what-it-means-for-enterprises)

**Authentication to the Gateway**
- Default bind is loopback. Options: `gateway.auth.allowTailscale` (Control UI sign-in via each person's Tailscale identity with Tailscale Serve); trusted proxy with an identity-aware proxy such as Cloudflare Access; shared token/password (small teams; everyone shares one owner profile). — [Teams doc](https://docs.openclaw.ai/start/teams)
- Security page: no SSO/OIDC guidance in the content fetched; trusted-proxy auth is only linked. — [Security doc](https://docs.openclaw.ai/gateway/security)
- Example team deployment: Gateway on a dev server behind GitHub authentication, Cloudflare Access and Cloudflare Tunnel, listening "only on the server's loopback interface." — [VentureBeat](https://venturebeat.com/technology/openclaw-2-0-is-here-what-it-means-for-enterprises)

**Roles / RBAC-like controls**
- `gateway.roles.default: "guest"`; `gateway.roles.definitions.<name>` accepts `sessions.others` ("write" or "view"), `agents` (permitted agent IDs), `scopes` (max operator scopes), `sandbox: "required"`. Example roles: `maintainer` (sessions.others write; operator.read, operator.write, operator.approvals) and `guest` (sessions.others view; operator.sessions.write; sandbox required). Assign with Gateway method `users.setRole`. — [Teams doc](https://docs.openclaw.ai/start/teams)
- Caveat from the docs: "`operator.read` and `operator.write` are Gateway-wide"; a guest with `sessions.others: "view"` can still read every shared session, including tool output. — [Teams doc](https://docs.openclaw.ai/start/teams)
- Session permission levels: read-only, guarded, workspace, full-access; only administrators can use full-access. Limited-access browser users can request admin privileges; another admin must approve. — [VentureBeat](https://venturebeat.com/technology/openclaw-2-0-is-here-what-it-means-for-enterprises)
- Operator roles can require sandboxed execution for sessions from specific identities: "if the required sandbox cannot be provisioned, execution fails rather than silently falling back to the host." — [VentureBeat](https://venturebeat.com/technology/openclaw-2-0-is-here-what-it-means-for-enterprises)

**Approvals**
- Approvals can be tied to a specific request, command, session and person; command permissions limited by arguments and working directories; script-backed execution checked against the originally reviewed script. — [VentureBeat](https://venturebeat.com/technology/openclaw-2-0-is-here-what-it-means-for-enterprises)
- Sandboxing and execution approvals are "off by default"; baseline assumes a trusted single operator. — [TechBriefly](https://techbriefly.com/2026/09/01/openclaw-2-0-launches-enterprise-collaboration-security/)

**Guest sandboxing and publishing**
- `agents.entries.<agent>.sandbox.workspaceAccess: "none"` (default): tools use a private writable workspace; managed skill instructions read-only; child sessions inherit the sandbox requirement; `sandbox.docker.network: "bridge"` enables outbound network; local sandboxes have no network by default. — [Teams doc](https://docs.openclaw.ai/start/teams)
- Guests use "Publish PR" (shared GitHub account, opens a draft PR). "OpenClaw never merges"; protect base branch with GitHub rules; point `origin` at a fork owned by the shared account. — [Teams doc](https://docs.openclaw.ai/start/teams)

**Secrets, admin, audit, cost**
- Team-scoped Secret Store separates protected credentials from ordinary env data; protected credentials can be substituted into Gateway-hosted HTTPS requests without exposure to the model; can reference 1Password and Vault. Limits: values not encrypted at rest (rely on filesystem protections); substitution does not cover some raw sockets, containers, remote nodes, provider-native harnesses. — [VentureBeat](https://venturebeat.com/technology/openclaw-2-0-is-here-what-it-means-for-enterprises)
- Settings workspace covers agents, memory, plugins, MCP servers, devices, channels, device pairing. — [TechBriefly](https://techbriefly.com/2026/09/01/openclaw-2-0-launches-enterprise-collaboration-security/)
- Model-provider admin shows credential status and, where providers expose it, availability, quota, balance, budget, spending. Per-person provider accounts: Settings > Profile > Connected accounts (new sessions prefer it; not the Gateway default). — [VentureBeat](https://venturebeat.com/technology/openclaw-2-0-is-here-what-it-means-for-enterprises); [Teams doc](https://docs.openclaw.ai/start/teams)
- Auditing covers execution identity, approvals, session actions, outbound messages; plugin installs trigger capability reviews. CLI: `openclaw security audit` (checks inbound access and exposure; audit-checks page lists `checkId`s). — [VentureBeat](https://venturebeat.com/technology/openclaw-2-0-is-here-what-it-means-for-enterprises); [Security doc](https://docs.openclaw.ai/gateway/security)
- Plugin marketplace ClawHub with publishing, curation, trust guidance. — [docs.openclaw.ai](https://docs.openclaw.ai)

**Multi-agent routing, memory, skills (isolation per agent, not per user)**
- `bindings[]` with `agentId`, `match.channel`, `match.accountId`, `match.peer{kind,id}`, guild/team ids; first match in a specificity tier wins; `agents.ownership: "explicit"`; `agents.entries.<id>` has workspace, agentDir, model, sandbox, tools, skills. — [Multi-agent doc](https://docs.openclaw.ai/concepts/multi-agent)
- Per-agent workspace and `agentDir` (auth profiles, sessions in `openclaw-agent.sqlite`). Builtin memory searches only the agent's own memory; the QMD cross-agent search path was removed in v2026.8.1; shared material via `memory.search.extraPaths`; `plugins.entries.memory-wiki.config.vault.scope: "agent"` for per-agent wiki. Cross-agent session access (`tools.agentToAgent`) is ON by default; narrow with `tools.sessions.visibility`. Workspace is not a sandbox. — [Multi-agent doc](https://docs.openclaw.ai/concepts/multi-agent)
- Skills: shared baseline `agents.defaults.skills`, per-agent `agents.entries.*.skills` replaces (no merge). Personal skill libraries and connected accounts can sit alongside workspace-wide ones on a shared Gateway. — [Multi-agent doc](https://docs.openclaw.ai/concepts/multi-agent); [OpenClaw Launch](https://openclawlaunch.com/guides/openclaw-multi-user)

**Trust limits**
- "Everyone who can message a tool-enabled agent shares that agent's delegated tool authority." Session ownership and presence are "collaboration guardrails, not isolation." For mutually untrusted users, one gateway per tenant. — [Teams doc](https://docs.openclaw.ai/start/teams)
- "OpenClaw is not a hostile multi-tenant security boundary." — [Security doc](https://docs.openclaw.ai/gateway/security)
- Recommended separation: separate Gateway instances called "cells" with own state, credentials, workspaces; fleet tooling for cells is experimental. — [VentureBeat](https://venturebeat.com/technology/openclaw-2-0-is-here-what-it-means-for-enterprises)
- Skeptical third-party view (not official): no tenancy model with per-user permissions, quotas or data boundaries; memory, history, credentials and workspace files are shared; no per-user quotas; one shared key means one bill unless users connect personal accounts; no admin who can view/revoke others' activity. This partly conflicts with the official roles and audit features above; likely written against the v2026.9.x line and may understate `gateway.roles`. — [OpenClaw Launch](https://openclawlaunch.com/guides/openclaw-multi-user)

### Inferences
- The role model is a collaboration/permission layer inside a single trust domain, closer to "team of trusted colleagues with guardrails" than enterprise RBAC. Memory is isolated per agent, not per human user.
- No official SSO/SAML/OIDC/SCIM in the core Gateway; identity comes from Tailscale or a trusted proxy (which can front an enterprise IdP, e.g. Cloudflare Access).

### Gaps
- No official source found on per-user/team cost caps (only provider budget display), on shared memory semantics in multi-user mode, or on SAML/OIDC. The "Multi-user mode" and "Deploy a team server" doc pages were linked from Teams doc but my guessed URLs returned 404; real URLs not found.
- Policy management console details unverified.

## 3. Deployment, and paid tiers

### Takeaway
Self-hosted Gateway (Docker/Podman sandboxes, remote nodes, cloud workers). Foundation shipped "OpenClaw Enterprise" (Sep 29, 2026), a free self-hosted control plane in internal pilot. No paid tier from the Foundation found; paid managed hosting exists only from third parties.

### Cited Findings
- Sandboxing: Docker and Podman, per-agent and per-session scopes, workspace read-only or read-write; remote execution nodes; disposable cloud workers; sessions can move to paired devices or cloud workers. — [VentureBeat](https://venturebeat.com/technology/openclaw-2-0-is-here-what-it-means-for-enterprises)
- OpenClaw Enterprise (OCE): released Sep 29, 2026 by the OpenClaw Foundation; open-source control plane for deploying and governing persistent agents; self-hosted; "available now for internal pilot workloads"; Foundation says it "will always be free for organizations to use." — [RuntimeWire](https://runtimewire.com/article/openclaw-enterprise-free-agent-control-plane)
- Crypto Briefing: multi-tenancy ("teams can run their own agents without accessing each other's data"), auditability, governance controls, admins monitor activity and enforce policies; docker-compose for dev, Kubernetes for production; model-agnostic; no paid tiers, hosted services or premium features; pilots at Red Hat and OpenAI; Red Hat and NVIDIA involved; quote from Kevin Lin: enterprises want "the flexibility of open source combined with the governance frameworks" they're used to. Origin: development began inside OpenAI before donation. — [Crypto Briefing](https://cryptobriefing.com/openclaw-enterprise-ai-agent-control-plane/). Note RuntimeWire does NOT list RBAC/SSO/audit/multi-tenancy; these feature claims rest on Crypto Briefing alone.
- Third-party managed hosts (not official; prices from comparison blogs, may be stale): OpenClawHosting.io Team $49/mo (10 instances); KiloClaw $9/mo after $4 first month, mentions enterprise SSO/SCIM, but status (waitlist vs live) unclear; Ampere.sh Business $499/mo. — [search results summary, unverified individually](https://www.hostinger.com/ph/tutorials/openclaw-costs/); [Kilo](https://kilo.ai/kiloclaw/hosted-openclaw); [Ampere](https://www.ampere.sh/blog/openclaw-enterprise-ai)
- Third-party open-source add-on: TeamClaw (ChenKuanSun) wraps OpenClaw with per-user containers, shared API key pool, team-configurable agents on AWS ECS/Fargate. Community project, not official. — [GitHub](https://github.com/ChenKuanSun/teamclaw)

### Inferences
- OCE is the route for multi-tenancy; the core Gateway's 2.0 features are single-tenant. Relationship between OCE and the "cells" fleet tooling is not documented in what I read.

### Gaps
- OCE license name unconfirmed (one search summary says MIT; Crypto Briefing names none). Primary Foundation announcement not fetched. Third-party prices not verified on vendor pages.

## 4. Integration with team tools in a multi-user way

### Takeaway
Channels (Slack, Discord, Telegram, WhatsApp, iMessage) are configured with allowlists and mention rules; GitHub integration is Publish PR via a shared account. Per-user identity mapping from chat tools to roles is not documented in what I read.

### Cited Findings
- Slack: `channels.slack.enabled`, `mode: "socket"`, `appToken`/`botToken` (env `SLACK_APP_TOKEN`, `SLACK_BOT_TOKEN`), `groupPolicy: "allowlist"`, `channels.<id>.requireMention: true`, DMs via pairing (`openclaw pairing approve slack <code>`), `contextVisibility` for broad rooms; access groups defined once and reused across channel allowlists. — [Teams doc](https://docs.openclaw.ai/start/teams)
- Channels named: Telegram, iMessage, WhatsApp, Discord. — [VentureBeat](https://venturebeat.com/technology/openclaw-2-0-is-here-what-it-means-for-enterprises)
- Agents with message-tool access can send across conversations and channel providers by default; cross-provider restrictions available. — [Security doc](https://docs.openclaw.ai/gateway/security)
- Security fix in 2026.10.4/10.5-beta.4: Tlon group DM authors never treated as owner. — [GitHub releases](https://github.com/openclaw/openclaw/releases)

### Inferences
- Atlassian, Microsoft, GitHub are Foundation partners but no shipped Jira/Teams/Google Workspace multi-user integration was found.

### Gaps
- No sourced info on Microsoft Teams, Jira, Google Workspace integrations.

## 5. Planned or missing as of October 2026

### Takeaway
Roadmap evidence is thin: OCE 1.0 is expected, fleet/cell tooling is experimental, and several enterprise items are not documented.

### Cited Findings
- OCE v1.0 "expected in the near future" (Crypto Briefing); a search summary attributes "end of this year" to Foundation statements to Quartz (Quartz not fetched, unverified). — [Crypto Briefing](https://cryptobriefing.com/openclaw-enterprise-ai-agent-control-plane/)
- Fleet tooling for managing cells: experimental. — [VentureBeat](https://venturebeat.com/technology/openclaw-2-0-is-here-what-it-means-for-enterprises)
- VentureBeat: the release "is not secure by default and requires deliberate configuration"; no roadmap or pricing given. — [VentureBeat](https://venturebeat.com/technology/openclaw-2-0-is-here-what-it-means-for-enterprises)

### Inferences
- Not shipped or not evidenced: SAML/OIDC SSO and SCIM in core, per-user quotas/rate limits, hard per-user data isolation in one Gateway, official hosted/paid tier.

### Gaps
- GitHub roadmap, RFCs and Discussions not reviewed.
