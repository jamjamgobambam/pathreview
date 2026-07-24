# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `FaithfulnessChecker.check()` method builds its context string by pulling
`text` out of each chunk dict with `chunk.get("text", "")`, assuming that
missing keys are the only case it needs to guard against. But `.get()` only
falls back to the default when the key is absent — if a chunk explicitly has
`"text": None`, `.get()` returns `None`, and the subsequent `" ".join(...)`
call raises a `TypeError` because it can't join a `NoneType` into a string.
In practice this means any upstream chunk that legitimately has a null/empty
text field (rather than a missing one) crashes the faithfulness check instead
of being skipped or treated as empty. A correct fix should coerce `None`
values to an empty string (or filter the chunk out) before joining, so the
checker degrades gracefully instead of raising. This touches
`rag/evaluator/faithfulness_checker.py`, and there's already a failing test,
`test_none_context_chunk_text`, in `tests/unit/test_faithfulness_checker.py`
that should pass once the fix is in.

**Branch name:** fix/153-faithfulness-checker-none-text

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger
