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

### Selection notes — "Is this right for me?"

- **Do I understand the problem?** [x] Yes. I can point to the exact cause: the
  generator scores each project in isolation and `_consolidate_feedback` in
  `rag/generator/review_generator.py` only dedupes by section name, not by
  content, so same-stack projects produce repeated observations.
- **Is the scope appropriate (not too big, not trivial)?** [x] Yes. It's a
  Tier 3 issue estimated at ~7–10 hours in the issues manifest. It's contained
  to the RAG generation layer (two files: `review_generator.py` and
  `output_parser.py`) rather than spanning ingestion, API, and frontend, so the
  blast radius is bounded and reviewable.
- **Is it in a part of the codebase I can navigate?** [x] Yes. I've already read
  the generator and parser modules while setting up, and the logic is
  self-contained Python with clear entry points (`generate_full_review`,
  `_consolidate_feedback`).
- **Can I test/verify the fix?** [x] Yes. The behavior is deterministic given a
  fixed set of chunks, so I can write unit tests under `tests/unit/` that feed a
  profile with multiple same-stack projects and assert that overlapping
  observations are consolidated into a single cross-project comment.
- **Does the effort fit my available time this module?** [x] Yes. A ~7–10 hour
  Tier 3 item is a realistic single-issue commitment for Module 3.
- **Is it unclaimed / not already in progress?** [x] Yes. Confirmed against the
  cohort ledger before claiming, and recorded my name there.

**Scope reasoning:** I'm deliberately limiting this fix to consolidation *within
the generator output* — detecting and merging duplicate cross-project
observations. I am **not** changing the retrieval layer, the prompt templates,
or the review data model, since those are out of scope for this issue and would
expand the blast radius. If deduplication turns out to need richer metadata
(e.g. per-project tech-stack tags), I'll note that as a follow-up rather than
widen this issue.
