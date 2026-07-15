## Week 7 — Issue selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/152

**Issue title:** Faithfulness checker can never mark short claims as supported

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**

The faithfulness checker currently requires at least two meaningful overlapping words between a claim and the retrieved context before marking the claim as supported. This causes short factual claims, such as "Knows Python.", to be incorrectly classified as unsupported even when the context clearly contains supporting information. The issue affects the `rag/evaluator/faithfulness_checker.py` component. A successful fix will allow short claims to be recognized as supported while preserving stricter matching for longer, more detailed claims.

**Branch name:** `fix/152-short-claim-support`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger