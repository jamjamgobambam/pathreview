## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The faithfulness checker's `check()` method builds its context string using
`chunk.get("text", "")`, which only substitutes an empty string when the
`text` key is missing — not when it's present but set to `None`. When a
context chunk has `text: None`, `.get()` returns `None`, and the subsequent
`" ".join()` call raises a `TypeError`, crashing the safety-layer's
faithfulness check entirely. A successful fix normalizes `None` values to
empty strings at this boundary, since the checker sits in the RAG
evaluation layer and shouldn't assume its inputs are always well-formed.

**Branch name:** fix/153-faithfulness-checker-none-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger