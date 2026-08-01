# System Analysis Anti-Patterns

Common failure modes when analyzing or designing systems. Flag these explicitly whenever you spot them — whether in an existing system being analyzed or in a proposed design.

| Anti-pattern | What it looks like | Correct response |
|---|---|---|
| **Element fixation** | Analysis focuses on visible parts (people, buildings, budgets) while ignoring interconnections | Redirect to flows and feedback loops |
| **Goal displacement** | Stated purpose and actual behavior have diverged; metrics being gamed | Name the real purpose; redesign the metric |
| **Delay blindness** | Assuming cause and effect are close in time and space | Map every delay explicitly; estimate lag |
| **Single-variable fix** | Proposing to change one number while the rest of the structure stays the same | Check for compensating feedback loops that will neutralize the fix |
| **Resilience sacrifice** | Optimizing for efficiency by eliminating redundancy | Name what breaks when the single path fails |
| **Paradigm lock** | Proposing only technical fixes for a problem rooted in a shared mental model | Escalate to leverage points 2–3 |
| **Short-term symptom addiction** | Repeated application of a fix that works briefly but worsens the root cause | Name the reinforcing loop being created; identify structural alternative |

Flag any anti-pattern you spot throughout the live analysis — not just during the final review pass.
