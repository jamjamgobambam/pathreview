# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/28

**Issue title:** Generator produces duplicate feedback sections when a user has multiple projects in the same tech stack

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
When a user has several projects built with the same tech stack (e.g. three Python projects), the review generator writes a nearly identical "Python skills" paragraph for each one instead of noticing the overlap. The feedback ends up repetitive rather than useful, because the generator treats every project independently instead of looking across projects for shared observations. A fix needs to deduplicate and consolidate these cross-project observations, most likely in `rag/generator/review_generator.py` and `rag/generator/output_parser.py`, so a user with multiple same-stack projects gets one consolidated skills section instead of several near-copies.

**Branch name:** fix/28-duplicate-feedback-sections

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
