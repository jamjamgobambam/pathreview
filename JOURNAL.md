# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness check

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
This issue addresses an edge case in the faithfulness checker when a context chunk contains `{"text": None}`. The current implementation uses the chunk’s `text` value when building the combined context, but `None` is not a string and causes `join()` to raise a `TypeError`. A successful fix will normalize `None` text values into a safe string value while preserving existing behavior for valid context chunks.

**Branch name:** feat/153-faithfulness-check

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger