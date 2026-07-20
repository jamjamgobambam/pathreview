## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has text: None

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The faithfulness checker combines the text from retrieved context chunks before evaluating an AI-generated statement. When a chunk contains a `text` key whose value is `None`, the current use of `dict.get()` returns `None` instead of the empty-string default. Passing that value to `" ".join()` raises a `TypeError`, causing the evaluation to stop. A successful fix will handle null text safely, preserve valid context text, and pass the related unit test.

**Selection notes:**
The issue has a small and clearly defined scope within the faithfulness checker. It includes a direct reproduction example and an existing related unit test, so I can verify the behavior locally. It does not require a paid API or an architectural change, and success is clearly defined as handling `None` without crashing.

**Branch name:** fix/153-faithfulness-none-context

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger