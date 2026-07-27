# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
In the RAG system, the faithfulness checker assumes every retrieved context chunk has string text, so a chunk with `text: None` throws an error instead of being handled. A successful fix would skip or safely handle null-text chunks so the check runs without crashing.

**Branch name:** fix/153-faithfulness-none-text-crash

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

### Is this right for me?
- Scope is small and isolated to one RAG check, so it fits a Tier 1 effort.
- The bug is a clear null-handling case with an obvious success condition (no crash).
