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

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/sujalusa/pathreview/commit/b59487974ded0caedea73a255f2bc3aff84bb3b1

**Reproduction summary:**
I added an xfail unit test (`tests/unit/test_review_cache_reproduction.py`) that
calls `process_review` twice for the same unchanged profile and asserts the
expensive RAG generation step runs only once. It fails today (RAG runs twice),
confirming there is no caching layer: identical submissions re-run the full
pipeline in `core/services/review_service.py`.

**PLAN.md link:** https://github.com/sujalusa/pathreview/blob/feat/32-portfolio-query-cache/PLAN.md

**Walkthrough video (recommended):** [optional — add Loom link if recorded]

**Blockers or open questions:**
Deciding cache scope: hashing the four `Profile` content fields (github_username,
portfolio_url, resume_text, resume_filename) should satisfy "if the portfolio
hasn't changed," but I need to confirm whether ingested-source content must also
be included. Also deciding whether to add a Redis fast path or rely solely on a
`reviews.content_hash` DB lookup for the first pass.
