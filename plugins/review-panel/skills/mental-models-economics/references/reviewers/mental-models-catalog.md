# Mental Models Catalog

Source material: the ~70 mental models catalogued at [fs.blog/mental-models](https://fs.blog/mental-models/),
grouped there into General Thinking Tools, Systems Thinking, Mathematics, Economics, and Art. Model
names and one-line definitions on that page are the inspiration; every "reframed as a code-review
question" line below is authored fresh for this plugin, not copied from the source. See
[CREDITS.md](../CREDITS.md) for the attribution note.

Not all ~70 models reframe usefully against code — most of the Art category (Melody, Genre,
Character, Plot, Setting, Performance, Audience) and several General Thinking Tools items
(Thermodynamics, Reciprocity, Alloying, Catalysts, Activation Energy, Ecosystems, Self-Preservation,
Replication) don't map to a concrete review question and are deliberately excluded. This catalog
curates the subset that does, split across four review vectors, each backing one skill in this
plugin. A model that fits more than one vector's frame is listed once, under the vector where it's
most actionable — don't duplicate a finding across vectors for the same underlying model.

Each vector's skill (`skills/mental-models-<vector>/SKILL.md`) points here rather than repeating
this list, so the model definitions stay in one place.

## Adversarial/Risk — backs `skills/mental-models-adversarial/`

Pressure-tests the *reasoning* behind a change — assumptions, incentives, systemic risk — as
opposed to `adversarial-reviewer`'s attack on the code as written (bugs, exploits, hostile input).

| Model | Reframed as a code-review question |
|---|---|
| Inversion | What would have to be true for this change to make things worse? Design backward from failure instead of forward from intent. |
| Second-Order Thinking | What happens after the immediate effect — to callers, to load patterns, to the next engineer who copies this pattern? |
| Probabilistic Thinking | Is the common case being treated as certain when it's actually a distribution? What's the tail behavior? |
| Margin of Safety | Does this have slack for being wrong — retry budget, capacity headroom, a rollback path — or does it assume the estimate is exact? |
| Multiply by Zero | Is there one single point whose failure zeroes out everything else (one retry, one validator, one credential), no matter how well everything else is built? |
| Regression to the Mean | Was this justified by one exceptional benchmark or incident, when the typical case will regress back toward average? |
| Incentives | What does this code or config actually reward or penalize, versus what it intends to? Will people or systems game it? |
| Hanlon's Razor | Is a defense being built against malice where the real risk is an honest mistake (or vice versa) — is the threat model matched to the real cause? |
| Circle of Competence | Does this assume expertise (in a domain, a library's internals, a protocol) the team doesn't actually have, and is that assumption visible anywhere? |
| Surface Area | Every new public method, endpoint, or config knob is more surface for misuse — has the integration/attack surface grown more than the diff's stated purpose requires? |

## Simplifier — backs `skills/mental-models-simplifier/`

Questions the *frame*, not the syntax — whether this is even the right problem being solved, and
whether effort is aimed at the actual constraint. Distinct from `ponytail-review`'s mechanical
delete/stdlib/native/yagni/shrink pass over the diff as literally written.

| Model | Reframed as a code-review question |
|---|---|
| Occam's Razor | Of the approaches on the table, is the simplest one that fits being chosen, or is complexity being justified by an unlikely edge case? |
| First Principles Thinking | Was this built by decomposing the actual requirement, or by analogy to a similar-looking but different problem? |
| Law of Diminishing Returns | Is more effort or complexity being spent past the point where it buys meaningful correctness or performance — e.g. handling a 0.001% case with the same rigor as the 99% case? |
| Irreducibility | Does a claim that "this could be simplified further" actually hold, or is the remaining complexity inherent to the problem's essence rather than this implementation? |
| Trade-offs | Is a trade-off (e.g. consistency for latency) being made silently, instead of as an explicit, examinable choice? |
| Global vs Local Maxima | Is this optimizing the piece directly in front of us at the expense of the whole — a locally-clever fix that makes the overall design worse? |
| Optimization | Is effort being spent optimizing a dimension (speed, memory, DX) that isn't actually the constraint that matters here? |

## Systems/Boundaries — backs `skills/mental-models-systems/`

Evaluates *dynamic, runtime* behavior — feedback, load, interaction across components — as opposed
to `design-review`'s funnel, which evaluates *static* module/abstraction quality.

| Model | Reframed as a code-review question |
|---|---|
| Feedback Loops | Does this create or break a feedback loop (retries feeding retries, alerts silencing alerts, cache invalidation triggering more invalidation) — is it damping or amplifying? |
| Equilibrium | What steady state does this converge to under sustained load, and is that state stable, or does a small perturbation run away? |
| Bottlenecks | What's the actual constraint this system hits first under scale, and does this change move or hide the bottleneck rather than remove it? |
| Critical Mass | Is there a threshold (queue depth, connection count, cache size) past which this stops behaving the way it does at small scale? |
| Emergence | Each component looks correct in isolation — but what behavior arises only from the combination (two independent retriers hammering the same downstream, two caches disagreeing) that no single component's logic shows? |
| Hierarchical Organization | Is a decision being made at the wrong layer (a leaf reaching up to orchestrate, or a top layer micromanaging a leaf's internals) instead of where the necessary information or authority actually lives? |
| Interdependence | How many other components does this now implicitly depend on, and what happens when one of them changes independently? |
| Scale | Does the design's core assumption hold at 10x or 100x current volume, or does it only work at today's size? |
| Algorithms | Is behavior actually deterministic and reproducible the way the code implies, or does hidden state or ordering make it nondeterministic under concurrency? |

## Economics/Debt — backs `skills/mental-models-economics/`

Frames the change as a resource-allocation decision — technical debt, build-vs-buy, vendor lock-in,
deferred work — a lens no other seat in this plugin applies.

| Model | Reframed as a code-review question |
|---|---|
| Scarcity | What's the actually scarce resource here (engineer time, on-call attention, database connections), and does this change spend it wisely? |
| Trade-offs | Was an alternative with a better cost/benefit ratio available and not considered, or is this the cheapest-now, most-expensive-later option? |
| Debt | Is debt being taken on knowingly with an explicit payoff plan (a TODO with an owner/ticket), or silently — or is "debt" language being used to excuse something that's just wrong? |
| Specialization | Is this reinventing something a specialized library or service already does well, at the cost of ongoing maintenance no one signed up for? |
| Efficiency | Is effort proportional to value delivered, or is this gold-plating a low-value path while a high-value path stays neglected? |
| Creative Destruction | Is this patching an approach that should be replaced outright, extending the life of something actively worse than starting over? |
| Monopoly and Competition | Does this create a single point of dependency on one vendor, library, or team with no viable alternative, and is that lock-in acceptable given the switching cost? |
| Gresham's Law | Is a quick, low-quality pattern here going to get copy-pasted because it's the path of least resistance, driving out the better pattern that takes more effort to replicate? |
