# OpenClaw 2.0 redesign: what it is, features, architecture, stability

Disambiguation: this is OpenClaw the self-hosted personal AI agent (creator Peter Steinberger), NOT the Captain Claw game reimplementation. Earlier history (Clawdbot -> Moltbot -> OpenClaw renames, early 2026) is out of scope and not covered by the sources fetched here.

## What is the redesign, and when was it announced/released? GA or beta?

### Takeaway
The redesign is "OpenClaw 2.0", shipped as stable version 2026.8.1 on about 30-31 Aug 2026, announced by Community Manager Hannes Rudolph in the blog post "OpenClaw 2.0, Accidentally". It is GA (stable); as of 17 Oct 2026 the latest stable is 2026.10.4, with 2026.10.x betas in flight. The team says it was not planned as a 2.0.

### Cited Findings
- Official name/version: "OpenClaw 2.0" = version 2026.8.1; release notes at docs.openclaw.ai/releases/2026.8.1, announcement at openclaw.ai/blog/openclaw-2-accidentally — [InfoQ](https://www.infoq.com/news/2026/09/openclaw-2-release/)
- Announcement post by Hannes Rudolph (Community Manager, OpenClaw Foundation), dated Aug 30, 2026. Quote: "Today we released by far the largest update in the history of OpenClaw." — [Official blog](https://openclaw.ai/blog/openclaw-2-accidentally)
- Release date conflict: blog says Aug 30; GitHub lists Aug 31 UTC (per secondary source); Decrypt says "around Sept. 1", over a weekend; InfoQ article is dated Sep 1 — [dsebastien](https://www.dsebastien.net/2026-10-03-openclaw-2-0-easier-setup-shared-sessions-same-security-defaults/); [Decrypt](https://decrypt.co/377135/openclaw-2-0-is-here-whats-new)
- Also posted about on X by chief architect Vincent Koc: "We shipped the biggest lobster ever. 50% of all PRs since project inception in this one release." Steinberger commented: "Local harnesses feel like relics of the past now." — [InfoQ](https://www.infoq.com/news/2026/09/openclaw-2-release/)
- "Accidental" 2.0: the plan was to simplify installation and rebuild the browser app; cleanup spread across most of the codebase and the team then labeled it 2.0 (per Rudolph) — [dsebastien](https://www.dsebastien.net/2026-10-03-openclaw-2-0-easier-setup-shared-sessions-same-security-defaults/); [Decrypt](https://decrypt.co/377135/openclaw-2-0-is-here-whats-new)
- Scale: 16,977 PRs, 698 direct commits, 987 contributors per release notes (blog/InfoQ/Decrypt say 933 contributors incl. 569 first-timers and "16,000+" PRs, about half of all PRs ever merged) — [Release notes](https://docs.openclaw.ai/releases/2026.8.1); [Official blog](https://openclaw.ai/blog/openclaw-2-accidentally)
- Cadence: 106 releases in 230 days before 2.0, then almost two months (about seven weeks) with no main-line release — [Official blog](https://openclaw.ai/blog/openclaw-2-accidentally)
- Release notes describe it as "a rebuilt web experience, simpler onboarding, stronger memory and session continuity" and "a very large reliability pass" — [Release notes](https://docs.openclaw.ai/releases/2026.8.1)
- Status after 2.0: stable 2026.8.2 (Sep 1) through 2026.9.8 (Oct 3) per secondary source; openclaw.ai (Oct 2026) lists v2026.10.4 for macOS/Linux and v2026.9.8-1 for Windows; GitHub shows 2026.10.4 as "Latest" (16 Oct), with pre-releases 2026.10.5-beta.4 and 2026.10.10-beta.1 (15 Oct) — [openclaw.ai](https://openclaw.ai); [GitHub releases](https://github.com/openclaw/openclaw/releases); [dsebastien](https://www.dsebastien.net/2026-10-03-openclaw-2-0-easier-setup-shared-sessions-same-security-defaults/)
- Version naming is calendar-style (YYYY.M.patch) — inferred from the tags above; no written versioning policy found.
- Press coverage: The Register ("OpenClaw 2.0 pours glitter on slow-burning security dumpster fire", 2026-08-31), CSO Online, SiliconANGLE, InfoQ, Decrypt — [The Register](https://www.theregister.com/ai-and-ml/2026/08/31/openclaw-20-pours-glitter-on-slow-burning-security-dumpster-fire/5293492); [SiliconANGLE](https://siliconangle.com/2026/08/31/openclaw-just-gave-everyone-version-2-0-and-it-comes-with-major-updates/); [CSO Online](https://www.csoonline.com/article/4216969/openclaw-rolls-out-system-wide-overhaul-updates-security-controls-across-agent-platform-2.html) (titles/URLs only; I did not read the Register, SiliconANGLE or CSO articles directly)

### Inferences
- "Redesign" in the task most plausibly means 2.0 (2026.8.1): a UI rebuild plus onboarding, memory and storage rework, not a language rewrite. Nothing sourced indicates a runtime or language change.

### Gaps
- Exact release day (Aug 30 vs 31 vs Sep 1) is inconsistent across sources.
- Contributor count differs (933 vs 987).
- Did not read the Register/SiliconANGLE/CSO articles or X posts directly.
- One secondary source (intelligentliving.co) says a "September 2024 debut"; I could not verify it and it looks wrong against the other timeline details (106 releases in 230 days). Treat as unreliable.

## Full feature list

### Takeaway
2.0 spans installation, Control UI, shared cloud sessions, memory, skills, automations, browser/computer use, plugins, native apps, models and security. Headline items: guided setup that reuses existing subscriptions/keys/local models, a chat-first rebuilt browser UI, and multiplayer sessions.

### Cited Findings
- Installation/onboarding: guided setup detects existing Codex/ChatGPT/Claude CLI sign-ins, API keys, or local models (Ollama, LM Studio) and tests the model responds before saving; most configuration moved out of setup into conversation with the Claw — [dsebastien](https://www.dsebastien.net/2026-10-03-openclaw-2-0-easier-setup-shared-sessions-same-security-defaults/); [Official blog](https://openclaw.ai/blog/openclaw-2-accidentally)
- Platforms: Mac, Linux, Windows, iOS, iPadOS, Android; staged imports from Claude, Codex and Hermes (per Decrypt) — [Release notes](https://docs.openclaw.ai/releases/2026.8.1); [Decrypt](https://decrypt.co/377135/openclaw-2-0-is-here-whats-new)
- Control UI (web): rebuilt around chat with a conversation sidebar (group by project/person/custom); Decrypt adds panels for files, Git diffs, PR status, browser and terminal — [dsebastien](https://www.dsebastien.net/2026-10-03-openclaw-2-0-easier-setup-shared-sessions-same-security-defaults/); [Decrypt](https://decrypt.co/377135/openclaw-2-0-is-here-whats-new); docs: https://docs.openclaw.ai/web/control-ui
- Shared cloud sessions ("multiplayer"): several people join one live session with context intact, hand off work; sessions can run on a paired computer or temporary cloud worker via Crabbox, with Gateway keeping transcripts and credentials; workspaces movable between paired devices/cloud workers; team-hosted instance team.openclaw.ai (Decrypt); user-built dashboards in shared workspaces — [dsebastien](https://www.dsebastien.net/2026-10-03-openclaw-2-0-easier-setup-shared-sessions-same-security-defaults/); [Official blog](https://openclaw.ai/blog/openclaw-2-accidentally); docs: https://docs.openclaw.ai/gateway/cloud-sessions
- Memory: QMD backend retired, replaced by built-in SQLite memory engine; cross-conversation recall across the same agent's private chats; Active Memory on by default for personal installs; background consolidation writes a per-agent "Dream Diary"; automatic learning on by default can propose scanner-approved skills; group/channel chats excluded from default recall; tools to search, inspect, import, remove memory — [intelligentliving](https://www.intelligentliving.co/openclaw-2-0-release/) (secondary); [Release notes](https://docs.openclaw.ai/releases/2026.8.1)
- Skills: create/validate/find/install/call follow one path; "Skill Workshop" tracks proposals, checks, decisions, history — [Release notes](https://docs.openclaw.ai/releases/2026.8.1)
- Automations: "cron" renamed "Automations" across agent, UI, CLI, docs, native apps; `openclaw cron`, existing jobs and schedules still work. Example workflows: inbox monitoring with Telegram alerts, answering iMessage with email context — [dsebastien](https://www.dsebastien.net/2026-10-03-openclaw-2-0-easier-setup-shared-sessions-same-security-defaults/); [Official blog](https://openclaw.ai/blog/openclaw-2-accidentally)
- Browser & Computer Use: signed-in browsing via isolated managed profile or explicitly shared Chrome tabs; Computer Use on paired Macs and explicitly enabled Windows; Linux experimental — [dsebastien](https://www.dsebastien.net/2026-10-03-openclaw-2-0-easier-setup-shared-sessions-same-security-defaults/)
- Plugins/ClawHub/MCP: admins browse, install, enable, disable, remove plugins in the Control UI, plus curated ClawHub skills and vetted MCP connectors — [Release notes](https://docs.openclaw.ai/releases/2026.8.1)
- Native apps: iPhone, iPad, Android, macOS (menu-bar Quick Chat), Wear OS; voice, attachments, model choice, reworked pairing/permission flows — [Release notes](https://docs.openclaw.ai/releases/2026.8.1); [dsebastien](https://www.dsebastien.net/2026-10-03-openclaw-2-0-easier-setup-shared-sessions-same-security-defaults/)
- Models/providers: chat and Models page use the existing catalog; requests stay within intended provider and authorized account order; hosted, subscription, API and local models supported — [Release notes](https://docs.openclaw.ai/releases/2026.8.1); [InfoQ](https://www.infoq.com/news/2026/09/openclaw-2-release/)
- Channels: WhatsApp, Telegram, Discord, Slack, Signal, iMessage remain supported; Telegram/Slack/Discord/native apps keep more context — [InfoQ](https://www.infoq.com/news/2026/09/openclaw-2-release/); [Release notes](https://docs.openclaw.ai/releases/2026.8.1)
- Security items on the feature list (brief; other researchers cover depth): approvals bound to exact request/command/session/person; masked credential requests; Secret Store; opt-in destination proxy; Docker/Podman sandbox (off by default) — [Release notes](https://docs.openclaw.ai/releases/2026.8.1); [intelligentliving](https://www.intelligentliving.co/openclaw-2-0-release/)
- Performance claim (team's, simulated test, via Decrypt): initial JS requests 140 -> 45; startup 1.6 s -> 575 ms — [Decrypt](https://decrypt.co/377135/openclaw-2-0-is-here-whats-new)
- Post-2.0 additions (2026.10.x betas, not 2.0 itself): Gateway DB work moved to worker threads, restart-safe replies, cloud session management, local Gateway in desktop apps, new models (Gemini 4 Argon default Gemini model, Nemotron 3.5 Super VL, xAI Imagine Image 2.0), experimental PostgreSQL engine for the Workboard store, Bun runtime support for standalone executables, Control UI sidebar reorganization; native apps and Control UI require macOS/iOS/Safari 26.2+ — [GitHub releases](https://github.com/openclaw/openclaw/releases) (summary of page; only first 100k of 175k chars read)

### Inferences
- The "Workboard" store and Crabbox are named but not explained in the sources I read.

### Gaps
- The per-area detail pages under docs.openclaw.ai/releases/2026.8.1 were not fetched, so the release notes' full item-level list is not captured. Agent loop internals, ClawHub policy changes and CLI changes beyond `doctor --fix`/`cron` are not covered.

## Architecture changes and rationale

### Takeaway
Documented architecture changes are narrow: sessions/transcripts and memory moved to SQLite, a local Secret Store, and cloud/paired-device workers for sessions. The Gateway-daemon model stays; "one Gateway = one trust domain". No sourced evidence of a language/runtime rewrite, config-format change, or new API. The official blog explicitly gives no architecture details.

### Cited Findings
- Official blog: "does not describe architecture"; says the team grew and work volume "outpaced both the project foundation and the shipping process. Both were reworked" — [Official blog](https://openclaw.ai/blog/openclaw-2-accidentally)
- Sessions and transcripts moved from plain files to SQLite; restoring archived transcripts needs the current CLI — [dsebastien](https://www.dsebastien.net/2026-10-03-openclaw-2-0-easier-setup-shared-sessions-same-security-defaults/); [Release notes](https://docs.openclaw.ai/releases/2026.8.1)
- Gateway daemon separated from the agents it routes to; multi-tenant separation requires separate Gateways ("cells"); docs: "one Gateway equals one trust domain" — [Decrypt](https://decrypt.co/377135/openclaw-2-0-is-here-whats-new); [dsebastien](https://www.dsebastien.net/2026-10-03-openclaw-2-0-easier-setup-shared-sessions-same-security-defaults/); docs: https://docs.openclaw.ai/gateway/security
- Session execution can occur on paired computers or temporary cloud workers (Crabbox); Gateway retains transcripts and credentials — [dsebastien](https://www.dsebastien.net/2026-10-03-openclaw-2-0-easier-setup-shared-sessions-same-security-defaults/)
- Secrets in a local Secret Store separated from agent-readable env; values "not encrypted at rest", rely on state-directory file permissions — [intelligentliving](https://www.intelligentliving.co/openclaw-2-0-release/); [dsebastien](https://www.dsebastien.net/2026-10-03-openclaw-2-0-easier-setup-shared-sessions-same-security-defaults/)
- Why: team used its own multiplayer sessions internally ("build OpenClaw with OpenClaw"); Rudolph says this exposed flaws in the single-user design — [Decrypt](https://decrypt.co/377135/openclaw-2-0-is-here-whats-new); [dsebastien](https://www.dsebastien.net/2026-10-03-openclaw-2-0-easier-setup-shared-sessions-same-security-defaults/)
- Post-2.0 direction: PostgreSQL experimental engine for Workboard store, DB work to worker threads (2026.10.10-beta.1) — [GitHub releases](https://github.com/openclaw/openclaw/releases)
- Competitor context: Hermes Agent (Nous Research) combines loop, tool dispatch and memory in one agent class — [Decrypt](https://decrypt.co/377135/openclaw-2-0-is-here-whats-new)

### Inferences
- The SQLite move plus worker-thread DB work and an experimental Postgres store suggest a trend toward database-backed state, but no source states this as a stated goal.

### Gaps
- No source states language/runtime (TypeScript/Node implied by Bun mention only), process-model, config-format or API changes. No RFC/discussion or design doc found.

## Stability and reliability

### Takeaway
2.0 included "a very large reliability pass", but the upgrade itself was rocky; on Sep 18 the Foundation acknowledged widespread update failures and shipped atomic updates (keep old Gateway running, roll back on failure). Later 10.x releases focus on update reliability and crash/shutdown fixes. No LTS or formal versioning policy found.

### Cited Findings
- Release notes: update paths check the existing install before replacing it; clearer recovery tools (Doctor); accepted messages survive managed restarts — [Release notes](https://docs.openclaw.ai/releases/2026.8.1)
- 6,364 of the changes were maintainer-facing (release/CI work, tests, refactors, docs) — [Release notes](https://docs.openclaw.ai/releases/2026.8.1)
- Community reaction: some upgraded smoothly; others reported migration problems, broken gateways, lost automations, model auth issues — [InfoQ](https://www.infoq.com/news/2026/09/openclaw-2-release/)
- Sep 18 post by Graham McBain (Foundation), interviewing Jason Sy: existing gateway keeps running while the update is prepared; on failure roll back to last working config; always preserve a working agent to diagnose; "The pieces already existed, ordered wrongly"; issue-report button added. Quote: "It should just always leave you with a working claw to at least diagnose what issues happened with the update". Sy said updating is not "completely fixed". Future idea: agent-assisted sidecar handling upgrades. — [Official blog](https://openclaw.ai/blog/shipping-openclaw-updates-that-dont-break)
- That post does not describe testing approach, release channels or versioning policy — [same](https://openclaw.ai/blog/shipping-openclaw-updates-that-dont-break)
- Mislabel incident: npm package `2026.9.1-beta.1` is really `2026.8.1-beta.4`, not newer than stable — [Release notes](https://docs.openclaw.ai/releases/2026.8.1)
- Release channels: stable plus `-beta.N` pre-releases visible on GitHub (e.g. 2026.10.10-beta.1); 2026.10.4 described as a stability patch with no new features or config changes, fixing Gateway sleep/clock recovery, shutdown hangs, Tlon group DM ownership, manual `/compact` — [GitHub releases](https://github.com/openclaw/openclaw/releases)
- 2026.10.5-beta.4: more reliable updates, headless browser sign-in fixes, Gateway access and macOS repair fixes — [GitHub releases](https://github.com/openclaw/openclaw/releases)
- Hacker News (148 pts, 175 comments) lukewarm; critics cited frequent breaking updates (secondary summary, I did not read the thread) — [dsebastien](https://www.dsebastien.net/2026-10-03-openclaw-2-0-easier-setup-shared-sessions-same-security-defaults/)

### Inferences
- The slow 2.0 cycle plus the later atomic-update work indicate the maintainers treated release process as the main stability problem.

### Gaps
- No LTS, support window, deprecation policy, or backward-compat guarantee found. Test/CI details not found.

## Breaking changes and migration path

### Takeaway
Breaking items: SQLite session storage (one-way without backup), OpenProse plugin removed, `codex/*` -> `openai/*` model routes, QMD memory retired. Migration is mainly `openclaw doctor --fix` plus a verified backup beforehand. The official blog lists no breaking changes.

### Cited Findings
- Sessions/transcripts to SQLite: sessions created after migration won't appear on downgrade without a backup; third-party tools reading session files must be updated; recommend verified backup before upgrading — [dsebastien](https://www.dsebastien.net/2026-10-03-openclaw-2-0-easier-setup-shared-sessions-same-security-defaults/); [intelligentliving](https://www.intelligentliving.co/openclaw-2-0-release/)
- QMD backend retired: run `openclaw doctor --fix`; lost: reranking, query expansion, cross-agent transcript search; QMD-backed plugins must be replaced/retired — [dsebastien](https://www.dsebastien.net/2026-10-03-openclaw-2-0-easier-setup-shared-sessions-same-security-defaults/); [intelligentliving](https://www.intelligentliving.co/openclaw-2-0-release/)
- Bundled OpenProse plugin removed — [intelligentliving](https://www.intelligentliving.co/openclaw-2-0-release/); [Decrypt-derived search summary]
- `codex/*` routes renamed `openai/*`; `openclaw doctor --fix` handles it but must be run explicitly — [intelligentliving](https://www.intelligentliving.co/openclaw-2-0-release/)
- Compatibility kept: `openclaw cron` and existing jobs still work — [dsebastien](https://www.dsebastien.net/2026-10-03-openclaw-2-0-easier-setup-shared-sessions-same-security-defaults/)
- Later break (2026.10.10-beta.1, pre-release): native apps and Control UI require macOS/iOS/Safari 26.2+ — [GitHub releases](https://github.com/openclaw/openclaw/releases)
- Staged imports from Claude, Codex, Hermes exist for newcomers (per Decrypt) — [Decrypt](https://decrypt.co/377135/openclaw-2-0-is-here-whats-new)

### Inferences
- Because the official blog/InfoQ list no breaking changes while release-note-derived secondary sources do, users relying on the blog alone could miss them.

### Gaps
- No dedicated official 1.x -> 2.0 migration guide URL found (the details come from release notes sub-pages that I only saw via secondary sources). Sub-pages not fetched.

## Governance and maintainers

### Takeaway
OpenClaw is stewarded by the OpenClaw Foundation, a US 501(c)(3) nonprofit; Steinberger joined OpenAI in Feb 2026 but OpenClaw did not. No sourced evidence that governance changed because of 2.0; the Foundation exists before and is listed as publisher.

### Cited Findings
- Foundation: MIT license, US 501(c)(3) nonprofit steward — [openclaw.ai](https://openclaw.ai)
- Steinberger joined OpenAI in February (2026) to lead personal-agent work; OpenClaw itself did not join OpenAI; Foundation partners listed: OpenAI, Microsoft, GitHub, Nvidia, Atlassian, Tencent — [Decrypt](https://decrypt.co/377135/openclaw-2-0-is-here-whats-new)
- People: Hannes Rudolph (Community Manager), Vincent Koc (chief architect), Jason Sy (Member of Technical Staff), Graham McBain (Foundation author) — sources above
- Blog states the project is not tied to one company, model, or provider — [Official blog](https://openclaw.ai/blog/openclaw-2-accidentally)
- Post-2.0 ecosystem: Microsoft Autopilot built on OpenClaw (announced Sep 25; blog https://openclaw.ai/blog/microsoft-autopilot-openclaw); OpenClaw Enterprise (Sep 29, open-source control plane with multi-tenancy, pilot, 1.0 planned later in 2026; https://openclaw.ai/blog/openclaw-enterprise) — [dsebastien](https://www.dsebastien.net/2026-10-03-openclaw-2-0-easier-setup-shared-sessions-same-security-defaults/); [openclaw.ai](https://openclaw.ai) (home page lists the Sep 29 Enterprise post)

### Inferences
- Enterprise is the multi-tenant answer to the explicit "shared sessions are not tenant isolation" limit in 2.0.

### Gaps
- Foundation's founding date/announcement content not read; whether governance changed with 2.0 is unaddressed in sources (the InfoQ article says it describes no formal governance changes).
- Security-by-default and team features intentionally not covered in depth (other researchers).
