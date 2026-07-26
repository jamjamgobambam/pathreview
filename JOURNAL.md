# PathReview Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3

**Problem summary:**

The faithfulness checker builds a combined context string from the text stored in each retrieved context chunk. The current implementation provides an empty-string default only when the `text` key is missing, but it does not handle cases where the key exists and its value is `None`. As a result, the checker attempts to join a `None` value into a string and raises a `TypeError`. A successful fix will normalize `None` values to empty strings so that malformed or incomplete context chunks do not crash the faithfulness evaluation process.

**Selection notes:**

This issue is appropriately scoped because the failure has a clear reproduction case, identifies the affected faithfulness checker, and points to a related unit test. It is limited to safely handling one edge case rather than redesigning the RAG evaluation system. I can reproduce the failure locally, make a targeted change, and validate the behavior using unit tests. The issue is labeled Tier 1 and good first issue, making it suitable for my first contribution to this codebase.

**Branch name:** `fix/153-handle-none-context-text`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
