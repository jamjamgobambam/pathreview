## Week 7 - Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `check()` method in `rag/evaluator/faithfulness_checker.py` builds
its context by calling `chunk.get("text", "")` on each context chunk,
assuming this will always yield a string. However, `.get()`'s default
value only kicks in when the key is missing entirely - if a chunk
dictionary has the key `"text"` present but explicitly set to `None`,
`.get()` returns `None` instead of the default empty string. This
`None` then gets passed into `" ".join(...)`, which raises a
`TypeError` since `join` expects a list of strings. A successful fix
will make the checker handle `None` values gracefully (coercing them
to empty strings before joining) so it can process context chunks
with missing or null text without crashing.

**Branch name:** fix/153-faithfulness-checker-none-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger