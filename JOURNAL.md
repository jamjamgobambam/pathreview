## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The RAG faithfulness checker (`rag/evaluator/faithfulness_checker.py`) builds its
context by calling `chunk.get("text", "")` on each retrieved chunk. The default
only applies when the `"text"` key is missing — if the key exists but its value
is `None`, `.get()` returns `None`, and the following `" ".join(...)` raises a
`TypeError` because `None` isn't a string. So one malformed chunk crashes the
whole faithfulness evaluation. A successful fix makes `check()` treat a `None`
text value like an empty/missing one so the checker keeps running, and it turns
the existing failing test `test_none_context_chunk_text` green.

**Is this right for me? — checklist reasoning:**
- Scope is tiny: one function, one file, a well-understood Python `dict.get`
  gotcha. No cross-module or schema/API/frontend changes.
- Verifiable "done": the issue ships a 3-line repro and names the failing test
  `tests/unit/test_faithfulness_checker.py::test_none_context_chunk_text`, so
  success is objective (test passes, `make test-unit` stays green).
- Good intro to the RAG evaluator without needing the whole pipeline first.
- Note: heavily claimed in the shared cohort repo; I'm completing it in my own
  fork for practice, and my branch is my graded deliverable.

**Branch name:** fix/153-faithfulness-none-context-chunk

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 - Reproduction & solution planning

**Reproduction commit link:** https://github.com/skyler-hall/pathreview/commit/9705c63

**Reproduction summary:**
Ran the unit test test_none_context_chunk_text against a chunk of {"text": None}. It raised
TypeError: sequence item 0: expected str instance, NoneType found at
rag/evaluator/faithfulness_checker.py:34, confirming that chunk.get("text", "") returns None
(not "") when the key exists with a None value, and " ".join(...) then rejects the None. Bug
reproduced reliably.

**PLAN.md link:** https://github.com/skyler-hall/pathreview/blob/fix/153-faithfulness-none-context-chunk/PLAN.md

**Walkthrough video (recommended):** N/A - not recorded

**Blockers or open questions:**
None blocking. Noted for Week 9: the unit suite has 3 pre-existing failures
(test_partial_support_returns_middle_score, test_multiple_context_chunks,
test_multiple_claims_varying_support) that fail on main and are unrelated to #153
(they stem from the _is_supported >=2-token overlap threshold). My fix targets only
test_none_context_chunk_text; I will not touch those.
