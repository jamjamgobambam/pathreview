## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/151

**Issue title:** Bias detector patterns are too narrow to match common phrasings

**Tier:** Tier 1

**Summary:**
PathReview’s bias detector currently uses regex patterns that require language to closely match a small number of predefined phrases. Because of this, the detector misses natural variations of dismissive statements about educational background and assumptions related to age. The problem affects the patterns and is demonstrated by nine failing tests. A successful fix will recognize the intended variations while keeping the patterns narrow enough to avoid flagging unrelated language.

**Selection notes**
This issue has a clearly identified implementation file, reproducible examples, and existing tests that define the expected behavior. Its scope is limited, so it does not require redesigning the application. I should be able to reproduce the failure and verify the solution using the provided unit tests.

**Branch name:** `fix/151-expand-bias-detection-patterns`

**Setup confirmation:** App runs locally at localhost:5173

**Cohort ledger:** Issue added to cohort ledger
