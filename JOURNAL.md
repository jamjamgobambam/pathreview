## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The faithfulness checker verifies that generated claims are actually supported
by the retrieved context, but it crashes when a context chunk has `None` as
its text value instead of an empty string. The code uses
`chunk.get("text", "")` to build the combined context string, which only
falls back to the default when the "text" key is missing entirely — if the
key exists but is explicitly `None`, `.get()` returns `None`, and joining a
list containing `None` with a string raises a TypeError. This affects the
`rag` module's faithfulness-scoring logic, and the fix would involve safely
coercing a `None` text value to an empty string before concatenation.

**Branch name:** fix/153-faithfulness-checker-none-text-crash

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger 