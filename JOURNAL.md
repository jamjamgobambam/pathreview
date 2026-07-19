# Module 3 Journal

> Running record of my progress on **PathReview** throughout Module 3.
> A new section is added each week.
> Fork: https://github.com/arunkasala-open/pathreview

---

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/28

**Issue title:** Generator produces duplicate feedback sections when a user has multiple projects in the same tech stack

**Tier:** [ ] Tier 1 [ ] Tier 2 [x] Tier 3

**Problem summary:**
The review generator treats each of a user's projects independently, so when
someone has several projects built with the same stack (for example three
Python projects), it produces almost the same skills feedback for each one and
the overall review ends up repetitive and padded. The current
`_consolidate_feedback` step in `rag/generator/review_generator.py` only removes
duplicates by section name, not by the actual content of the feedback, so
repeated observations across similar projects still slip through. A successful
fix would detect when the same observation applies to multiple same-stack
projects and consolidate those into a single, cross-project comment. The result
should be a review that reads as a cohesive assessment of the portfolio rather
than a per-project checklist, affecting the RAG generation layer
(`rag/generator/review_generator.py` and `rag/generator/output_parser.py`).

**Branch name:** fix/28-duplicate-feedback-sections-when-multiple-projects

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
