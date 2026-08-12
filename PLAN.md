## Solution plan

**Issue:** Faithfulness checker crashes when a context chunk has `text: None` — https://github.com/ascherj/pathreview/issues/153

### Understand

`FaithfulnessChecker.check()` in [rag/evaluator/faithfulness_checker.py](rag/evaluator/faithfulness_checker.py) builds a combined context string with:

```python
context_text = " ".join([
    chunk.get("text", "") for chunk in context_chunks
])
```

`dict.get(key, default)`'s default only applies when the key is **missing**. If a chunk is `{"text": None}` (key present, value null), `.get("text", "")` returns `None`, not `""`. That `None` lands in the list passed to `" ".join(...)`, which raises `TypeError: sequence item 0: expected str instance, NoneType found` because `join` requires every item to be a string.

- **Expected behavior:** a chunk with a null `text` field is treated as empty context and `check()` still returns a normal float score in `[0.0, 1.0]`.
- **Actual behavior:** `check()` raises an unhandled `TypeError`, crashing the whole faithfulness evaluation (and therefore `EvalSuite.run()`, which calls it unconditionally).

Null `text` happens in practice when a retrieved chunk failed to embed/extract content or is a placeholder record — this isn't a synthetic edge case.

### Map

- [rag/evaluator/faithfulness_checker.py:34-36](rag/evaluator/faithfulness_checker.py#L34-L36) — the `" ".join(...)` list comprehension where the crash originates. This is the only line that needs to change.
- [tests/unit/test_faithfulness_checker.py:231-242](tests/unit/test_faithfulness_checker.py#L231-L242) — `test_none_context_chunk_text`, the existing failing test that pins down the expected fix. No new test should be needed.
- [tests/unit/test_faithfulness_checker.py:244-255](tests/unit/test_faithfulness_checker.py#L244-L255) — `test_missing_text_key_in_chunk`, a sibling test that already passes today (missing-key case works because `.get`'s default *does* apply there); must keep passing after the fix.
- [rag/evaluator/eval_suite.py:43](rag/evaluator/eval_suite.py#L43) — the only caller of `FaithfulnessChecker.check()`, via `EvalSuite.run()`. Not touched directly, but it's why this crash is user-facing: any chunk with null text anywhere in the retrieval pipeline takes down the whole eval run, not just the faithfulness sub-score.

### Plan

1. Reproduce the crash locally with `pytest tests/unit/test_faithfulness_checker.py -k test_none_context_chunk_text -v` and confirm the `TypeError` and stack trace match the issue (done — see reproduction commit).
2. Fix line 34-36 in `faithfulness_checker.py` to coerce a `None` text value to `""` before joining, e.g. `chunk.get("text") or ""` (treats both a missing key and an explicit `None` the same way), instead of `chunk.get("text", "")`.
3. Re-run `test_none_context_chunk_text` and `test_missing_text_key_in_chunk` to confirm both pass with the one-line change.
4. Run the full `tests/unit/test_faithfulness_checker.py` file and diff the failure list against the pre-fix baseline to confirm the fix touches only the target test and introduces no new failures.
5. Run the broader test suite (`pytest tests/`) once to check nothing outside this file depends on the current (buggy) behavior.

### Inputs & outputs

- **Input:** `context_chunks: list[dict]`, where each dict may have a `"text"` key that is a non-empty string, an empty string, `None`, or absent entirely. Chunks arrive this way from the retrieval layer that feeds `EvalSuite.run()`.
- **Output:** `check()` must always return a `float` in `[0.0, 1.0]` (or raise only for truly invalid input types, which is out of scope here) — it must never raise `TypeError` due to a chunk's `text` being `None`.
- No change to the public signature of `check()` or to `EvalSuite`.

### Risks & unknowns

- **Scope creep risk:** running the full test file today shows 3 *other* pre-existing failures (`test_partial_support_returns_middle_score`, `test_multiple_context_chunks`, `test_multiple_claims_varying_support`) caused by unrelated scoring-threshold behavior in `_is_supported`. These are not part of issue #153 and must not be "fixed" as a drive-by — noting them so the baseline diff in step 4 isn't misread as new regressions I introduced.
- **Chunk shape assumption:** the fix assumes every item in `context_chunks` is a `dict`. If a chunk itself could be `None` or a non-dict (not currently tested or seen in `eval_suite.py`), `chunk.get(...)` would still raise `AttributeError`. Need to confirm during implementation whether the retrieval layer ever produces non-dict chunks — if not, this is out of scope.
- **`or ""` vs explicit `is None` check:** `chunk.get("text") or ""` also collapses a legitimately empty string `""` to `""` (a no-op) but would also collapse falsy-but-valid values if `text` were ever something other than a string (not expected here). Worth double-checking there's no case where `text` is a non-string falsy value before finalizing the fix.

### Edge cases

- `{"text": None}` — must not crash; treated as empty context (covered by `test_none_context_chunk_text`).
- `{"content": "..."}` (missing `"text"` key) — must keep working as before (covered by `test_missing_text_key_in_chunk`).
- `{"text": ""}` — already works today; must keep returning a valid score.
- Mixed list with some `None`-text chunks and some valid-text chunks — the valid chunks' text must still be joined and contribute to `context_text` normally.
- All chunks have `None` text — `context_text` becomes an all-empty-string join (`""`), and `check()` should return a low/neutral score rather than crashing, same code path as `test_empty_context_chunks_returns_zero` but arriving via a different input shape.
