# Research Findings: Context Files for Coding Agents

Source: "Do Context Files Help Coding Agents?" (arxiv.org/abs/2602.11988)

## Key Experimental Results

### LLM-Generated Context Files
- Performance: **-2% to -3%** average decrease in task success
- Cost: **+20-23%** higher inference costs
- Steps: +2.45-3.92 additional steps per task

### Developer-Written Context Files
- Performance: **+4%** average improvement (marginal)
- Cost: up to **+19%** higher inference costs
- Outperformed LLM-generated files across all 4 tested agents

### Context Files with Documentation Removed
- When existing docs (README, etc.) were stripped from repos, LLM-generated context files improved performance by **+2.7%**
- This proves context files work best as **targeted supplements**, not replacements for existing docs

## What Hurts Performance

1. **Repository overviews** — Found in 8/12 developer files and 95-100% of LLM-generated files. Did not help agents navigate faster.
2. **Architecture descriptions** — Agents discover structure fine on their own.
3. **Directory listings / component enumerations** — Redundant with file system exploration.
4. **Duplicating existing documentation** — README content repeated in context files adds cost without benefit.
5. **Excessive length** — Average optimal file: ~640 words. Reasoning tokens increased 14-22% with context files present, suggesting cognitive overload.

## What Helps Performance

1. **Tooling specifications** — Tools mentioned in context were used **2.5x more** frequently. Repository-specific tools used almost exclusively when mentioned.
2. **Build/test commands** — Agents reliably follow exact command specifications.
3. **Environment setup prerequisites** — Non-discoverable setup steps.
4. **Human-written over generated** — Domain expertise matters more than comprehensiveness.

## Optimal File Characteristics

- **~640 words** average length (range: 24-2,003 in study, but shorter correlated with better outcomes)
- **~9.7 sections** average (range: 1-29)
- Content limited to: tooling specs, build/test commands, environment prerequisites
- No architecture overviews, no directory listings, no doc duplication

## Verbatim Conclusion

> "Ultimately, we conclude that unnecessary requirements from context files make tasks harder, and human-written context files should describe only minimal requirements."
