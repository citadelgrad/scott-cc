---
name: polyglot-idiom
description: >-
  Use when a diff, branch, or PR touches Java, C++, C#, Ruby, or PHP code and needs
  per-language idiom and code-review checkpoints, grounded in the language-checkpoint
  reference tables of the Gemini "Code Quality Review Research" PDF. Deliberately
  excludes Python, TypeScript/JavaScript, Go, Rust, and Swift, which have
  dedicated simplifier skills (python-simplifier, typescript-simplifier, go-simplifier,
  rust-simplifier, swift-simplifier) — do not use this skill for those five languages.
  Also runnable directly via /scott-cc:polyglot-idiom for an explicit standalone pass.
license: MIT
metadata:
  category: technique
  triggers: [code-review, java, c++, csharp, ruby, php, polyglot]
---

# Polyglot Idiom Review

This skill applies idiom and architecture checkpoints for five languages that do not
have a dedicated `*-simplifier` skill: **Java, C++, C#, Ruby, and PHP**. It is grounded
in the per-language "Code Review Checkpoints and Idioms" sections of the Gemini deep-research
PDF `Code Quality Review Research - Google Docs.pdf`.

## Scope Boundary

**In scope:** Java, C++, C#, Ruby, PHP only.

**Out of scope:** Python, TypeScript/JavaScript, Go, Rust, and Swift. These languages
have dedicated `python-simplifier`, `typescript-simplifier`, `go-simplifier`,
`rust-simplifier`, and `swift-simplifier` skills.
If the target code is in one of those five languages, stop and point the user to the
matching simplifier skill instead of proceeding here.

## How This Differs From review-panel, adversarial-reviewer, thermo-nuclear, and google-standard

- The other four review commands apply one lens or doctrine across *any* language.
  **polyglot-idiom** is the only one that applies *language-specific* idiom checklists —
  it knows what "good Java" and "good Ruby" each look like, rather than a
  language-agnostic principle.
- It is a checklist reviewer, not a structural-doctrine reviewer (unlike thermo-nuclear)
  and not a code-health-bar reviewer (unlike google-standard). It exists to fill the
  idiom-coverage gap for languages this plugin otherwise has no dedicated eyes on.
- This skill can be invoked automatically by the model, or by another orchestrating
  skill or agent (e.g. review-panel), whenever a diff touches Java, C++, C#, Ruby, or
  PHP — it is not limited to explicit invocation via its slash command, though that
  remains available for a standalone pass.

## Per-Language Checkpoints

### Java

Java relies on disciplined, contract-driven object-oriented design. Enterprise
frameworks (e.g. Spring Boot) should separate concerns: thin web controllers handling
HTTP transport, domain services owning business logic, and repository interfaces
isolating persistence.

- **Thin handlers and DTO isolation** — controllers must never contain business logic or
  directly expose persistence entities; request/response payloads must use explicit DTOs
  or immutable record types.
- **Interface segregation** — question concrete class dependencies; require injection
  via interfaces for loose coupling and testability.
- **Explicit exception handling** — custom exceptions must extend the appropriate
  runtime/checked base; prohibit swallowing exceptions or returning raw `null`; use
  `Optional<T>` for nullable returns.
- **Immutability and modern features** — favor `record` classes for immutable data,
  pattern matching for `instanceof`, and local variable type inference (`var`) where it
  preserves readability.

### C++

Modern C++ (C++20/C++23) prioritizes deterministic resource management, type safety,
compile-time computation, and RAII (Resource Acquisition Is Initialization).

- **Deterministic resource management (RAII)** — reject raw `new`/`delete`; all
  resources (memory, file descriptors, locks) must be managed via RAII wrappers or smart
  pointers (`std::unique_ptr`, `std::shared_ptr`).
- **Type constraints via Concepts** — require C++20 Concepts for generic template
  parameters instead of complex SFINAE, for clearer diagnostics and explicit contracts.
- **Const correctness and `constexpr`** — enforce `const` on member functions, variables,
  and parameters; prefer `constexpr`/`consteval` for compile-time-evaluable logic.
- **Dangling references and lifetimes** — inspect lambda captures, `std::string_view`,
  and `std::span` to confirm referenced objects outlive their consumers.

### C#

C# combines object-oriented enterprise patterns with modern functional features (LINQ,
records, pattern matching, nullability).

- **Nullable reference types (NRT)** — enforce `#nullable enable`; ban unvalidated
  property access or returning bare nulls without explicit `T?` annotation.
- **Async/await usage** — flag synchronous blocking over async operations (`.Result`,
  `.Wait()`), which risks threadpool starvation and deadlocks; ensure
  `CancellationToken` propagates down async call stacks.
- **LINQ efficiency** — review for multiple enumerations of `IEnumerable<T>` or complex
  logic executed inside database query projections.
- **Dependency injection lifetimes** — verify service registrations match intended
  lifetimes (Transient, Scoped, Singleton) to avoid memory leaks or captive dependencies.

### Ruby

Ruby treats everything as an object, leaning on message passing, dynamic dispatch, and
block-based collection processing; web architecture (e.g. Rails) follows MVC enriched
with plain old Ruby objects (POROs).

- **Background job hygiene** — asynchronous workers (e.g. Sidekiq jobs) must be
  idempotent and keep payloads small (pass entity IDs, not serialized objects).
- **Controlled metaprogramming** — flag `method_missing`, `eval`, or dynamic
  `define_method` unless required by framework internals; metaprogramming obscures call
  graphs and complicates debugging.
- **Skinny controllers and focused models** — controllers handle only parameters and
  responses; business logic belongs in service objects or domain models.
- **Idiomatic Enumerable patterns** — favor built-in `Enumerable` methods (`map`,
  `select`, `reduce`, `flat_map`) over manual `each` loop constructs.

### PHP

Modern PHP (8.2+) is a strongly typed, class-based object-oriented platform; modern
frameworks (Symfony, Laravel) follow Domain-Driven Design with DI containers,
attribute-based routing, and explicit object mappers.

- **Strict type declarations** — every PHP file must begin with
  `declare(strict_types=1);`; parameters, return values, and class properties need
  explicit type declarations.
- **Compliance with PSR standards** — enforce PSR-12 (formatting), PSR-4 (autoloading),
  and PSR-7 (HTTP message interfaces) as applicable.
- **DTO hydration** — reject unsafe raw `$_GET`/`$_POST` parsing; requests must be
  validated and hydrated into strongly typed DTOs.
- **Separation of legacy procedural code** — block legacy procedural patterns, global
  variables (`global $db`), or inline execution scripts from entering modern code.

## Review Process

1. **Resolve the target** — a `base..head` range, branch, PR, or (if none given) the
   current working-tree diff against `HEAD`.
2. **Identify the language(s) touched.** If any touched file is Python,
   TypeScript/JavaScript, Go, Rust, or Swift, exclude it from this review and note that
   it is out of scope per the Scope Boundary above — do not apply this skill's checklists
   to it.
3. For each remaining file, select its language's checkpoint list above and walk every
   item against the code.
4. Categorize each finding by severity (blocking vs. advisory) and by which checkpoint it
   violates.
5. Produce the report: findings grouped by language and checkpoint, and a summary of any
   files excluded as out of scope.

## What NOT to Do

1. **Don't apply Java checkpoints to C# code (or vice versa)** — the five languages have
   distinct idioms; match the checklist to the actual language of each file.
2. **Don't silently review out-of-scope languages** — if a diff is entirely Python, Go,
   Rust, TypeScript, or Swift, say so and stop instead of guessing at checkpoints this
   skill doesn't own.
3. **Don't invent checkpoints beyond the five lists above** — if a real issue doesn't map
   to a documented checkpoint, note it as a general finding rather than fabricating a new
   "rule" attributed to this skill's source material.

## When to Use

- Runnable directly via `/scott-cc:polyglot-idiom`, or automatically by the model or an
  orchestrating skill/agent (e.g. review-panel) when a diff touches one of its five
  in-scope languages.
- Use for Java, C++, C#, Ruby, or PHP code specifically.
- For Python, TypeScript/JavaScript, Go, Rust, or Swift, use the matching dedicated
  `*-simplifier` skill instead.

## Limitations

- Covers exactly five languages (Java, C++, C#, Ruby, PHP). It is not a general-purpose
  reviewer for any language outside that list.
- Grounded in the Gemini deep-research PDF's language-checkpoint tables as captured on
  2026-07-31 — a secondary-research source, not each language's own official style guide.
  For binding style decisions, defer to the language's official style guide over this
  skill's summaries.
- Does not check security holes or hostile-input handling — use `adversarial-reviewer`
  for that.
- Stop and ask for clarification if the diff, PR, or branch target cannot be resolved
  unambiguously, or if a file's language cannot be determined from its extension/content.
