# Voice Samples

These are the canonical rhythm references for the `writing-about-engineering` skill. They were drafted, edited, and approved as exemplars of the target voice. Read them before drafting; return to them when pressure-testing a paragraph that feels off.

Each sample is annotated with the moves it demonstrates. The annotations are for skill use only — they do not appear in final output.

---

## Sample 1 — Short post

**Format:** Short post / thread (~80 words). One observation, low ego, ends on the surprise.

> I noticed Claude Code was re-reading the same file three times per turn in one of my sessions. I added a hook to log every Read call. Confirmed: same path, same offset, three reads. Turns out I had three subagents in parallel and each one re-reads from disk — there's no shared cache between them. Reasonable! Just not what I expected. I'd been blaming context bloat for something that was just three processes doing their jobs.

**Moves to notice:**

- Opens on a noticed friction ("I noticed... three times per turn") — no throat-clearing.
- "Confirmed:" + colon is a debug-log move; it does the work three sentences of prose would do.
- Ends on the realignment of the writer's assumption, not on a moral. No "Lesson:" line.
- "Reasonable! Just not what I expected" carries the entire takeaway. Plain language, no swagger.

---

## Sample 2 — Blog opener

**Format:** Blog post opener (~260 words). Lab-notebook rhythm, two artifacts that earn their place, ends on what's still unresolved.

> I've been trying to figure out why Claude sometimes ignores the system prompt when I use the SDK with `tools=[...]`. The behavior I keep seeing: I write "always respond in JSON" in the system prompt, and the model responds in JSON about 80% of the time. The other 20%, it writes prose.
>
> First thing I checked was temperature. It was 1.0. I set it to 0.0 and re-ran 100 calls.
>
> ```
> prose:  19/100
> json:   81/100
> ```
>
> So temperature isn't the variable. Same ~20% prose rate either way.
>
> Next I tried moving the JSON instruction from the system prompt into the user message. Re-ran 100 calls.
>
> ```
> prose:   3/100
> json:   97/100
> ```
>
> Big jump. So the instruction *is* being followed — it just follows the user turn more reliably than the system prompt when tools are present. That's not what I would have guessed.
>
> I poked at this for a while and went back to the docs. The docs don't actually promise the system prompt is higher-priority than the user turn for tool-using requests. I'd been carrying that assumption in from OpenAI's earlier docs. Different model, different rules.
>
> I haven't tested whether `tools=[...]` itself changes the priority, because once I moved the instruction the problem went away and I had other work to do. Filing that under "unanswered, didn't block me." If anyone has a clean isolating test case I'd love to see it.

**Moves to notice:**

- Opens inside the active investigation, not on a topic intro.
- Two code blocks that compare configurations — load-bearing, not decorative. The point of the piece *is* the comparison.
- "I'd been carrying that assumption in from OpenAI's earlier docs" names the source of the wrong assumption. Low ego, locates the mistake.
- Ends with an unresolved question and an open invitation, not a tidy takeaway.
- Sentence rhythm varies: long setup ("I've been trying to figure out..."), short verdict ("Big jump."), reflective close.

---

## Sample 3 — Postmortem

**Format:** Postmortem / retrospective (~210 words). Bare structure inside lived voice. Shows dead-end checks. Patches and stops.

> A scheduled job that's been running fine for three months silently stopped producing output last week. The job runs daily and writes a digest file to S3.
>
> I didn't notice for three days because the only consumer of that file is me, reading it on weekdays.
>
> What I checked first:
>
> - CloudWatch logs for the Lambda → exit 0, no errors.
> - IAM policy → unchanged in git for over a month.
> - S3 bucket policy → unchanged.
> - The output path itself → empty.
>
> Then I re-read the Lambda code, which I wrote, and noticed:
>
> ```python
> key = f"digests/{datetime.now().strftime('%Y-%m-%d')}.json"
> ```
>
> Fine. The Lambda was definitely writing the file — I added a `head_object` call right after the `put_object` and it returned 200.
>
> Eventually I checked the bucket's lifecycle rules and found one I'd set up four months ago: `Prefix: digests/, Days: 0`. I'd written `Days: 0` thinking it meant "never expire." It means "expire immediately." The Lambda was writing the files. The bucket was eating them within seconds.
>
> Patched to `Days: 30`. Files are sticking now.

**Moves to notice:**

- Postmortem structure is present but unobtrusive — a single section header, a bulleted check list, then prose.
- "Which I wrote" — owns the source of the mistake without performing humility.
- Dead-end checks (CloudWatch, IAM, bucket policy) are shown. They're the texture of real debugging.
- Two short verdict sentences carry the diagnosis: "The Lambda was writing the files. The bucket was eating them within seconds." No "Lesson:" follows.
- Ends with the patch and the present state ("Files are sticking now."), not a takeaway about lifecycle units or about reading docs more carefully.
- No decorative precision — earlier draft included "May 14, 03:00 UTC" timestamps that were cut for not carrying weight.

---

## Sample 4 — Reflective post (no artifacts)

**Format:** Reflective / essay-style short post (~180 words). No code, no metric. Demonstrates the voice without artifacts when the story doesn't need them.

> I've been writing skills for Claude Code for about six weeks. The first three I wrote read like documentation — a list of things you can do, organized under headers, verbs all in second person. They worked, in the sense that Claude could follow them, but I noticed Claude wasn't really *using* them. It was reading them and then doing whatever it would have done anyway.
>
> I changed two things. I rewrote them in imperative form — "do this" instead of "you should do this" — and I moved the most important rule to the top instead of burying it under "best practices." The next three I wrote, Claude actually leaned on.
>
> It's a strange thing to notice. You spend years learning that good documentation is voiced for a reader who will skim, take what they need, and leave. Skills aren't read like that. The model reads the whole thing, in order, every time. Knowing that should change how you write, and I'm still working out how.

**Moves to notice:**

- No code, no metric — the comparison ("read like documentation" vs. "Claude actually leaned on") is observational, not measured. That's appropriate for the story being told.
- "It was reading them and then doing whatever it would have done anyway" is a concrete observation about behavior, doing the work a metric might otherwise do.
- Opens on first-person stakes ("I've been writing skills...") and frames the friction in the second sentence ("read like documentation").
- Ends mid-thought: "Knowing that should change how you write, and I'm still working out how." No takeaway, no morale, no tidy frame.
- This sample is the dial-check: when an idea is reflective rather than diagnostic, do not force in code or metrics.

---

## Cross-sample patterns

Common moves that appear across all four:

- **Open on a noticed thing, not a topic.** Every sample's first sentence describes something that happened to the writer.
- **Locate the wrong assumption.** Samples 1, 2, and 4 all name where the writer's prior belief came from and why it was off.
- **End where the work ends.** No sample closes with a lesson. They close with a present state, an open question, or the surprise itself.
- **Short verdict sentences punctuate long observation sentences.** "Big jump." / "Files are sticking now." / "Reasonable!" — each carries a paragraph's worth of weight on its own.
- **Concrete verbs throughout.** Files are eaten, instructions are moved, code is re-read, hooks are added. No utilizing, leveraging, or enabling.
