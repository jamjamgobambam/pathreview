# PathReview Contribution Journal

## Week 7 — Issue selection

**Issue link:** [#152 — Faithfulness checker can never mark short claims as supported](https://github.com/ascherj/pathreview/issues/152)

**Issue title:** Faithfulness checker can never mark short claims as supported

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview's faithfulness evaluator decides whether generated feedback is supported by retrieved context by comparing meaningful words in each claim with words in the context. Its `_is_supported()` method currently requires at least two non-stopword matches, so a short factual claim such as “Knows Python” is rejected even when the context clearly says “Python expert.” As a result, several fully or partially supported short claims can incorrectly produce a faithfulness score of `0.0`. A successful fix will let short claims receive credit when the available evidence supports them while preserving low scores for claims that have no meaningful support.

**Selection notes:**
I chose this Tier 1 issue because I am still getting comfortable with the PathReview codebase and wanted a focused bug with a clear reproduction case. The affected behavior is contained in `rag/evaluator/faithfulness_checker.py`, and the issue identifies related unit tests in `tests/unit/test_faithfulness_checker.py`, so I can understand and verify the change without modifying unrelated APIs, database models, or frontend code. The scope fits my current skill level: I am comfortable with Python, sets, token filtering, and pytest, but the task will still help me practice reasoning about scoring rules and regression tests in an unfamiliar project. I will consider the fix successful only if short supported claims score appropriately, unsupported claims remain unsupported, and the relevant unit tests pass.

**Branch name:** `fix/152-faithfulness-short-claims`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
