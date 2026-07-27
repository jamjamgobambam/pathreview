## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `check()` method in `FaithfulnessChecker` builds its context by calling
`chunk.get("text", "")` on each context chunk, assuming this will fall back to
an empty string if text is missing. However, `.get()` only applies its default
when the key itself is absent — if a chunk has `"text": None`, `.get()` returns
`None` instead. This value then gets passed into a `" ".join(...)` call, which
raises a `TypeError` because `join()` expects a list of strings, not `None`.
The fix involves handling the case where `text` is present but `None`, likely
by falling back to an empty string in that case too. This affects the
`rag/evaluator/faithfulness_checker.py` module.

**Branch name:** fix/153-faithfulness-checker-none-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
