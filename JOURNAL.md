## Week 7 — Issue selection

**Issue link:** (https://github.com/ascherj/pathreview/issues/153)

**Issue title:** Faithfulness checker crashes when a context chunk has text: None

**Tier:** [✅] Tier 1

**Problem summary:**
The FaithfulnessChecker in the RAG eval suite (rag/evaluator/faithfulness_checker.py) joins the text of every context chunk into one string using chunk.get("text", ""), which only guards against a missing key — not a chunk whose text is explicitly None. When a None-text chunk appears, the " ".join(...) call throws a TypeError and crashes the entire faithfulness check. A successful fix treats None text as empty so the checker skips it and keeps scoring the remaining chunks.

**Branch name:** fix/153-faithfulness-checker-none-chunk-text

**Setup confirmation:** [✅] App runs locally at localhost:5173

**Cohort ledger:** [✅] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [bc4f381](https://github.com/GolamMortuzaSourov/pathreview/commit/bc4f381fe68b74729b027504661a31e93a00e8f9)

**Reproduction summary:**
Ran the existing unit test `tests/unit/test_faithfulness_checker.py::TestFaithfulnessChecker::test_none_context_chunk_text` against a chunk of `{"text": None}` and it fails with `TypeError: sequence item 0: expected str instance, NoneType found` at `rag/evaluator/faithfulness_checker.py:34` — confirming the `" ".join([chunk.get("text", "") ...])` crash, because `dict.get("text", "")` returns `None` (not `""`) when the key exists but is explicitly `None`.

Exact reproduction:

```
$ .venv/bin/python -m pytest \
    tests/unit/test_faithfulness_checker.py::TestFaithfulnessChecker::test_none_context_chunk_text -x -q

>       context_text = " ".join([
            chunk.get("text", "") for chunk in context_chunks
        ])
E       TypeError: sequence item 0: expected str instance, NoneType found
rag/evaluator/faithfulness_checker.py:34: TypeError
1 failed in 0.72s
```

(Note: 3 other tests in that file — `test_partial_support_returns_middle_score`, `test_multiple_context_chunks`, `test_multiple_claims_varying_support` — also fail, but for an unrelated `_is_supported` scoring-threshold reason, not the `None` crash. They are out of scope for issue #153.)

**PLAN.md link:** [PLAN.md](https://github.com/GolamMortuzaSourov/pathreview/blob/fix/153-faithfulness-checker-none-chunk-text/PLAN.md)

**Walkthrough video (recommended):**

**Blockers or open questions:**
Need to read `rag/evaluator/eval_suite.py` to confirm whether context chunks can ever carry a non-`str`, non-`None` `text` value (e.g. an `int`), which would decide whether the fix should coerce with `str(...)` or just coalesce `None`/missing to `""`.