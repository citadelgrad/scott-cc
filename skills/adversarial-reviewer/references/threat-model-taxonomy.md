# Threat Model and Weakness Coverage

Before candidate generation, record a compact threat model: assets, actors, entry points, trust boundaries, privileges, security objectives, deployment assumptions, abuse cases, unknowns, and out-of-scope surfaces. In unattended mode, proceed with explicit conservative assumptions; do not ask a question nobody can answer. A genuinely non-security prose target may use an explicit not-applicable reason.

Record every taxonomy class as `examined`, `applicable`, `not_applicable`, or `not_assessed` with a reason for the latter two. Coverage is an inspection record, never a quota.

Always assess where relevant:

- authorization and privilege boundaries;
- injection;
- paths/files;
- secrets and sensitive logging;
- deserialization/parsing;
- SSRF/network destinations;
- resource exhaustion;
- races, retries, duplicate requests, and state transitions.

Conditionally assess cryptography, memory safety, supply chain, tenancy/privacy, and agent/tool security. Agentic targets activate prompt injection, tool misuse, memory poisoning, and excessive agency.

Map security findings to CWE identifiers when a useful mapping exists. Use the [2025 CWE Top 25](https://cwe.mitre.org/top25/archive/2025/2025_cwe_top25.html) as prioritization context, not as a requirement to manufacture one issue per category.
