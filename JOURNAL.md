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

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [b3894e2 — document issue #152 reproduction](https://github.com/stardess/pathreview/commit/b3894e28238873dbf1ab3a44d214d52075bd5256)

**Reproduction summary:**
I reproduced the issue by checking `Knows Python. Knows SQL.` against context containing `python expert` and `sql expert`; the checker returned `0.0` even though the context supports both technologies. The three unit tests named in issue #152 also failed with `0.0`, confirming the problem in my local environment.

**PLAN.md link:** [Solution plan for issue #152](https://github.com/stardess/pathreview/blob/fix/152-faithfulness-short-claims/PLAN.md)

**Walkthrough video (recommended):** Not recorded

**Blockers or open questions:**
I need to confirm whether the fix should also change `_extract_claims()`'s minimum-length rule, which currently removes valid short statements such as `Knows SQL`, or remain limited to the support calculation. I also need to choose between splitting compound claims and returning graded support per claim so partial evidence produces a middle score without increasing false positives.
