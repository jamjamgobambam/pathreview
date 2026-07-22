# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/32

**Issue title:** Implement a caching layer for repeated identical portfolio queries

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
The review pipeline does no work-deduplication: every time a portfolio is
submitted, the full RAG pipeline runs from scratch, even when the exact same
profile was reviewed moments earlier with no changes. This wastes compute and
adds latency (and LLM cost) for a result that is guaranteed to be identical.
The fix introduces a caching layer keyed on a hash of the profile's content, so
an unchanged portfolio short-circuits to the previously stored review instead of
regenerating it. Success means a repeated identical submission returns the cached
review quickly, while any change to the portfolio content produces a new hash and
triggers a fresh generation. This work touches the RAG generator
(`rag/generator/review_generator.py`) and the review service
(`core/services/review_service.py`).

**Branch name:** feat/32-portfolio-query-cache

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
