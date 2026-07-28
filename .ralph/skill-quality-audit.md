# Skill Quality Audit — DEV-3

## Goal
Fix all structural compliance issues across 62 skills in scott-cc repo.

## Checklist

### Batch 1: skills/ directory (20 skills)
- [ ] Fix `acceptance-criteria` — description format, add category
- [ ] Fix `c4-diagram` — description format, add category
- [ ] Fix `cli-design` — description format, add category
- [ ] Fix `context-file-optimizer` — description format, add category
- [ ] Fix `context7` — description format, add category
- [ ] Fix `delegate-first` — description format, add category
- [ ] Fix `init` — description format, add category
- [ ] Fix `karpathy-guidelines` — description format, add category
- [ ] Fix `pas-pipeline` — description format, add category
- [ ] Fix `property-based-testing` — add category
- [ ] Fix `python-simplifier` — description format, add category
- [ ] Fix `reck-factory` — description format, add category
- [ ] Fix `skillopt-sleep-learned` — description format, add category
- [ ] Fix `thinking-in-systems` — description format, add category
- [ ] Fix `typescript-simplifier` — description format, add category, split to <500 lines
- [ ] Fix `verified-implementation` — add category
- [ ] Fix `writing-about-engineering` — add category

### Batch 2: plugin skills (42 skills)
- [ ] Fix `humanizer` — add name, description, category (critical)
- [ ] Fix all `review-panel/` skills — description format, add category (30 skills)
- [ ] Fix `browser-automation/` skills — description format, add category (2 skills)
- [ ] Fix `mutation-testing/mutation-test` — description format, add category
- [ ] Fix `security-suite/plan-security-review` — description format, add category
- [ ] Fix `triage/triage-spine` — description format, add category
- [ ] Fix `variant-explorer/explore-variants` — description format, add category

### Cross-skill integrity
- [ ] Verify duplicate tdd skills are intentionally distinct
- [ ] Check all cross-references resolve
- [ ] Check for orphan skills

### Final
- [ ] Re-run audit script to confirm all PASS
- [ ] Commit and push
- [ ] Update DEV-3 issue
