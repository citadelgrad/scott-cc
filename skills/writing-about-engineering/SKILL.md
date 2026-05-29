---
name: writing-about-engineering
description: Use when drafting first-person writing about software engineering or AI work — blog posts, short posts/threads, or postmortems — that needs a conversational-but-rigorous, peer-to-peer voice. Triggers when the request is to "write a post about X," "draft a postmortem for Y," "turn this debugging session into a writeup," or any first-person reflection on engineering, AI agents, tooling, or developer workflow. Skip for marketing copy, product announcements, customer-facing docs, or any third-person/aspirational writing.
---

# Writing About Engineering

## Purpose

This skill produces first-person engineering writing in a specific voice: conversational and rigorous, peer-to-peer, debug-log oriented. Anchored on Julia Evans and Simon Willison's TIL/blog rhythm — curious, granular, low ego, claim-then-evidence — and away from packaged-takeaway blog tropes.

## When to invoke

Invoke when the requested output is:

- A blog post or essay about engineering work, AI/agent behavior, tooling, or career tension.
- A short post or thread describing a single observed thing — a friction moment, a debug-log surprise, a small experiment.
- A postmortem or retrospective walking through what broke, what was checked, and what the fix was.

Do not invoke for:

- Marketing copy, product announcements, customer-facing docs, README intros.
- Third-person or institutional voice ("the team," "the engineer should").
- Aspirational/visionary pieces with no lived friction at their core.

## Voice rules

Apply every rule. They compound — dropping one makes the others read as performance.

1. **Open on lived friction.** Start with a moment of friction, failure, or career tension experienced directly. No throat-clearing, no scene-setting paragraph, no "in this post I'll explore." First sentence puts the reader inside a thing that happened.
2. **First-person stakes.** "I" is doing the work. The narrator notices, checks, gets confused, tries something, and is changed by the result. Never "you should" or "the engineer."
3. **Active voice, concrete verbs, physical nouns.** Things rip, paste, ship, absorb, drop, bounce, eat. Avoid abstract verbs (utilize, leverage, enable) and abstract subject nouns (the system, the codebase) when a concrete actor will do.
4. **Vary sentence length deliberately.** Mix long observation sentences with short verdict sentences. Do not let three medium-length sentences run in a row. Read drafts aloud — if the rhythm flattens, break a sentence or fuse two.
5. **Evidence when it carries weight, not as a tax.** Pair a technical claim with a code snippet, a metric, or a log line *when the artifact does work the prose can't*. Do not bolt code onto every claim. A claim like "the model wasn't ignoring me, I was telling it the wrong way" earns its place without an artifact; a claim like "moving the instruction dropped prose responses from 19/100 to 3/100" needs the numbers.
6. **No packaged lesson.** Do not end with a bold-faced "Lesson:" or a tidy aphorism. Let the insight sit inside the prose, or trail off honestly with what's still unknown ("filing that under unanswered, didn't block me"). The piece ends when the work ends, not when the moral lands.
7. **Low ego, debug-log shape.** Show the things tried that didn't work. Admit the wrong assumption you carried in. Name the source of the assumption when you can ("I'd been carrying that in from OpenAI's earlier docs"). Confusion is the genre, not weakness in it.

## Workflow

Follow these steps in order. Do not skip the pressure-test pass.

### Step 1: Intake

Before drafting, confirm three things with the writer:

- **The moment.** What specifically happened? When? What was the friction? Push for a concrete scene, not a topic — "I was debugging the SDK and the system prompt was being ignored" beats "I want to write about LLM prompt priority."
- **The format.** Blog post / essay (~500–2000 words), short post / thread (~50–200 words), or postmortem (~150–400 words). Each has a different shape — see the samples in `references/voice-samples.md`.
- **The artifacts.** What code, logs, metrics, or commands were actually involved? Gather them up front. Decide during drafting which earn a place; do not bolt them on at the end.

### Step 2: Draft

Match the shape to the format. Read `references/voice-samples.md` before writing — those are the canonical rhythm references.

- **Short post:** One observation. One or two artifacts max. Three to six sentences. End on the thing that surprised the writer, not on a moral.
- **Blog post:** Open mid-friction. Show what was checked, in order. Pair artifacts with the moments where they're load-bearing. End where the investigation actually ended — including unresolved questions.
- **Postmortem:** Bare structure works ("What broke" / "What I checked first" / "The fix"), but the prose inside the structure must still be lived voice, not incident-template language. Show the dead-end checks. Show the wrong assumption. Patch and stop.

### Step 3: Pressure-test against the rules

Re-read the draft once, looking for each of these failure modes. Cut or rewrite.

- **Throat-clearing opener.** Does sentence one drop the reader into a thing that happened? If it sets up or summarizes, rewrite to start at the friction.
- **Decorative detail.** Does every concrete detail earn its place? Cut timestamps, version numbers, and proper nouns that pretend to be lab-notebook precision but don't move the story.
- **Packaged lesson.** Does the piece end with a bow-tied takeaway? Replace with a quieter ending — what's still unknown, what's working now, what the writer is still working out.
- **Artifact-as-tax.** Is every claim trailed by a code block? Strip code blocks where the prose alone is doing the work. Keep them only where they show something prose can't.
- **Flat rhythm.** Are three or more medium-length sentences in a row? Break or fuse to restore variation.
- **Abstract verbs.** Search the draft for *utilize, leverage, enable, facilitate, provide, ensure*. Replace with a concrete verb or cut the sentence.
- **Second person.** Search for *you*. If addressing the reader directly, switch to first-person observation.

### Step 4: Final cut

Reading the draft aloud is the last filter. If a sentence sounds like documentation rather than someone talking, rewrite it. If a paragraph feels like it could appear in any blog post, cut it. If the ending sounds like a sermon, trim it back to the work.

## Resources

- `references/voice-samples.md` — Four canonical samples (short post, blog opener, postmortem, reflective post) that demonstrate the target voice across all supported formats. Read these before drafting; reach for them again during pressure-testing if a paragraph feels off.
