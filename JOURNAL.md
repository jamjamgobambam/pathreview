## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has text: None

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

This is my first time resolving a bug in a large codebase, so I'm starting with Tier 1, which is a
self-contained fix in one file that I could fully trace and reproduce before claiming it.

**Problem summary:**
The issue occurs in the rag/evaluator/faithfulness_checker.py when a context chunk contains a text field with the value None. The current implementation assumes every text value is a string, so joining the context raises a TypeError instead of handling the missing content gracefully. A successful fix will ensure that None values are treated as empty strings (or otherwise ignored), preventing the crash while allowing the faithfulness check to continue. The related unit test should also pass after the fix.

**Branch name:** fix/153-faithfulness-checker-none-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger