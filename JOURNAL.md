## Week 7 — Issue selection

**Issue link:** [[paste link here](https://github.com/ascherj/pathreview/issues/152)]

**Issue title:** [Faithfulness checker can never mark short claims as supported
#152]

**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3

**Problem summary:**
This is an issue with the RAG. The faithfulness checker is not able to check if claims written with few characters are suported

**Branch name:** [fix/152-faithfulness-checker]

**Reproduction notes:**

- Confirmed locally in the repository HEAD version that `_is_supported("The candidate knows Python.", "Python experience with Flask.")` returned `False`.
- Confirmed that the faithfulness score for "The developer shows Python expertise and Kubernetes knowledge." against a context with only Python support returned `0.0`.
- These reproductions prove the bug exists in the core short-claim support logic.

**Setup confirmation:** [ ] App runs locally at localhost:5173 -- it acually runs on localhost:5174

**Cohort ledger:** [X] Issue added to cohort ledger
