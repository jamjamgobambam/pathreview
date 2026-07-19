# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has text: None

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`FaithfulnessChecker.check()` builds the context string by calling
`chunk.get("text", "")` on each retrieved chunk. That default only applies when
the `"text"` key is missing entirely — if the key exists but is explicitly set
to `None`, `.get()` returns `None` instead of falling back to `""`. The
resulting list of chunk texts then gets passed to `" ".join(...)`, which
raises a `TypeError` because `join` requires every item to be a string. A
successful fix will coerce a `None` (or otherwise falsy/non-string) `"text"`
value to an empty string before joining, so a single malformed chunk no
longer crashes the whole evaluation run. This affects
`rag/evaluator/faithfulness_checker.py`.

**Branch name:** fix/153-faithfulness-checker-none-context-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
