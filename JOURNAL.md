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
