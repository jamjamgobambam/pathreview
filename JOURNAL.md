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

**Reproduction summary:**
Reproduced short claims faithfulness scoring issues locally by running `pytest tests/unit/test_faithfulness_checker.py`.
Observed assertions failing where `FaithfulnessChecker.check()` returned `0.0` or raised a `TypeError` on short claims/chunks (e.g., `"Python expert. Knows Rust. Skilled with Docker."`), failing to parse single/short sentence claims correctly.
