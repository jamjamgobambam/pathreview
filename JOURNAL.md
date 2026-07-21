## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/152

**Issue title:** Faithfulness checker can never mark short claims as supported

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
FaithfulnessChecker._is_supported() (rag/evaluator/faithfulness_checker.py) marks a claim as supported only if it shares at least two non-stop-word tokens with the retrieved context. Short claims like "Good indentation" have just two or three content words total, so nearly every token must match the context to hit the threshold. If there were any small thing to break it, like a plural, tense change, or synonym, it drops the overlap to one and fails the claim even when it's true. This fixed threshold makes it so short correct claims can structurally never clear. A fix should scale the required overlap to claim length rather than using a flat >= 2 cutoff.

**Branch name:** fix/152-faithfulness-short-claims-not-supported

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
