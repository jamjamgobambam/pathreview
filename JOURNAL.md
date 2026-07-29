## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has text: None

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The faithfulness checker combines the text from retrieved context chunks before evaluating an AI-generated statement. When a chunk contains a `text` key whose value is `None`, the current use of `dict.get()` returns `None` instead of the empty-string default. Passing that value to `" ".join()` raises a `TypeError`, causing the evaluation to stop. A successful fix will handle null text safely, preserve valid context text, and pass the related unit test.

**Selection notes:**
The issue has a small and clearly defined scope within the faithfulness checker. It includes a direct reproduction example and an existing related unit test, so I can verify the behavior locally. It does not require a paid API or an architectural change, and success is clearly defined as handling `None` without crashing.

**Branch name:** fix/153-faithfulness-none-context

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


## Week 8 — Issue reproduction and solution planning

**Reproduction status:** [x] Issue reproduced locally

**Reproduction command:**

```bash
.venv/bin/pytest tests/unit/test_faithfulness_checker.py::TestFaithfulnessChecker::test_none_context_chunk_text -v
```

**Observed result:**
The test failed with `TypeError: sequence item 0: expected str instance, NoneType found` in `rag/evaluator/faithfulness_checker.py`.

**Expected result:**
The checker should handle a context chunk containing `{"text": None}` without crashing and return a valid float score.

**Root cause:**
`chunk.get("text", "")` returns the empty-string default when the key is missing, but it returns `None` when the key exists with a null value. The resulting list is passed to `" ".join()`, which only accepts strings. This causes the checker to crash before calculating its score.

**Files investigated:**

- `rag/evaluator/faithfulness_checker.py`
- `tests/unit/test_faithfulness_checker.py`
- `rag/evaluator/eval_suite.py`
- `rag/evaluator/relevance_scorer.py`

**Solution plan:** [PLAN.md](./PLAN.md)

**Planned scope:**
Normalize missing or null context text inside `FaithfulnessChecker.check()` while preserving valid text and leaving the scoring algorithm unchanged. The similar behavior in `RelevanceScorer` is outside the scope of issue #153.

**Walkthrough video:** [ ] Optional video completed