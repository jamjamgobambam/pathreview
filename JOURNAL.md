## Week 7 — Issue selection

**_Issue link:_** https://github.com/ascherj/pathreview/issues/152

**_Issue title:_** Faithfulness checker can never mark short claims as supported

**_Tier:_** [X] Tier 1 [ ] Tier 2 [ ] Tier 3

**_Problem summary:_**
Short, accurate claims get scored 0.0 by the faithfulness evaluator. The problem is in `_is_supported()`: it only counts a claim as supported if it shares at least two non-stopword tokens with the context chunks. Short claims often have just one. So feedback like "the candidate knows Python" has a single matching token, falls under the threshold, and gets flagged as unsupported even though it's true. The fix has to score these one-token claims correctly without weakening the check for longer, multi-token claims.

**_Branch name:_** fix/152-short-claims-faithfulness

**_Setup confirmation:_** [X] App runs locally at localhost:5173

**_Cohort ledger:_** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ocabezas95/pathreview/commit/6f60da3e705d350cee6fc50ab66c1e8bf4fa267c

**Reproduction summary:** Reproduced short claims faithfulness scoring issues locally by running `pytest tests/unit/test_faithfulness_checker.py`. Observed assertions failing where `FaithfulnessChecker.check()` returned `0.0` or raised a `TypeError` on short claims/chunks, failing to parse single/short sentence claims correctly.

**PLAN.md link:** https://github.com/ocabezas95/pathreview/blob/fix/152-short-claims-faithfulness/PLAN.md

**Walkthrough video (recommended):** None

**Blockers or open questions:** None

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:** I have fully implemented the fix for Issue #152. I updated `faithfulness_checker.py` to handle `None` context chunks safely and refactored `_extract_claims` and `_is_supported` to correctly parse and score short claims. All `PLAN.md` sub-tasks are complete, and `make test-unit` (including a new short claim test) and `make check` pass successfully.

**Next steps:** Open a draft PR on GitHub to get feedback, refine if necessary, and then submit the final Pull Request by the Sunday deadline.

**Blockers:** None at this time!

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/377

**Branch:** `fix/152-short-claims-faithfulness`

**What you built:** I fixed an issue where short claims were being incorrectly discarded and evaluated as 0.0. I updated the context string concatenation to safely handle `None` values and refactored the claim extraction and overlap logic to scale down required token matches for short sentences.

**Tests added or updated:** Added `test_short_claims_retained_and_evaluated` to `tests/unit/test_faithfulness_checker.py` to ensure concise claims are preserved and scored correctly.

**Self-review confirmation:** [x] make check passes [x] make test-unit passes

**Draft PR feedback received from:** none
