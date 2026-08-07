## Solution plan

**Issue:** Faithfulness checker crashes when a context chunk has `text: None` — [#153](https://github.com/ascherj/pathreview/issues/153)

### Understand

**Root cause.** `FaithfulnessChecker.check()` concatenates context using:

```python
context_text = " ".join([
    chunk.get("text", "") for chunk in context_chunks
])
```

`dict.get("text", "")` only supplies the `""` default when the `"text"` **key is absent**. When the key is *present but explicitly `None`* — e.g. `{"text": None}` — `.get()` returns `None`, and `str.join()` raises `TypeError: sequence item 0: expected str instance, NoneType found`. This crashes the entire faithfulness check even when other chunks in the list have valid text.

**Expected vs. actual.**
- *Expected:* a `None`-text chunk is treated as empty text and skipped, and the checker keeps scoring the remaining chunks, returning a float in `[0.0, 1.0]`.
- *Actual:* the whole `check()` call raises `TypeError` and the caller (eval suite) crashes.

### Map

Files / functions involved:

- **`rag/evaluator/faithfulness_checker.py`** — `FaithfulnessChecker.check()`, the `" ".join(...)` at lines 34–36. **This is the only production file I expect to touch.**
- **`tests/unit/test_faithfulness_checker.py`** — `test_none_context_chunk_text` (line 231) already asserts graceful handling; it currently fails, which is the reproduction. I may add an assertion that a valid chunk alongside a `None` chunk is still scored (mixed list).
- **`rag/evaluator/eval_suite.py`** — caller of `FaithfulnessChecker.check()`; read-only, to confirm no upstream change is needed and understand how `context_chunks` are produced.

### Plan

1. **Guard the value, not just the key.** Replace `chunk.get("text", "")` with a coalescing expression that maps both missing keys *and* explicit `None` to `""`, e.g. `(chunk.get("text") or "")`. Consider also coercing non-str values defensively (`str(...)`) if the eval suite can emit them — decide after reading `eval_suite.py`.
2. **Strengthen the test.** Keep `test_none_context_chunk_text`, and add a mixed-list case (`[{"text": None}, {"text": "Python skills demonstrated"}]`) asserting the valid chunk still contributes to the score — proving we *skip* `None` rather than abort.
3. **Run the targeted tests** (`pytest tests/unit/test_faithfulness_checker.py::...::test_none_context_chunk_text` and the mixed case) to confirm they pass.
4. **Run the full faithfulness test file** to confirm no regressions from my change (noting the 3 pre-existing scoring-threshold failures are out of scope for #153).
5. **Update JOURNAL.md** Week 9 entry with the fix commit and test evidence.

### Inputs & outputs

- **Input:** `feedback: str`, `context_chunks: list[dict]` where any chunk may have `text` missing, `None`, or a valid string.
- **Output:** unchanged public contract — a `float` faithfulness score in `[0.0, 1.0]`. The only behavioral change is that a `None`/missing `text` chunk no longer raises; it contributes empty text and the remaining chunks are scored normally.

### Risks & unknowns

- **Non-string, non-None `text` values** (e.g. an `int` or a list) would still break `str.join`. Unknown whether `eval_suite.py` can produce these — need to read it to decide whether to coerce with `str(...)` or leave out of scope.
- **`or ""` also collapses falsy-but-valid values** like `0` or empty string — acceptable here since `text` is meant to be a string, but worth a comment so the intent is clear.
- **Pre-existing failures** (`test_partial_support_returns_middle_score`, `test_multiple_context_chunks`, `test_multiple_claims_varying_support`) fail due to `_is_supported` threshold sensitivity, *not* this bug. Risk of scope creep — I will explicitly leave them out of #153.
- Small risk the fix silently masks upstream data-quality problems (chunks arriving with `None` text); mitigated by keeping the existing `logger.info` observability and considering a debug log when a chunk is skipped.

### Edge cases

- `{"text": None}` — the reported crash; must return a float, not raise.
- `{"content": "..."}` (missing `text` key) — already handled; keep it working (`test_missing_text_key_in_chunk`).
- Mixed list `[{"text": None}, {"text": "valid text"}]` — valid chunk must still be scored.
- All chunks `None`/empty — should behave like empty context (score derived from zero overlap, i.e. low/`0.0`), not crash.
- Empty `context_chunks` list — already short-circuits to `0.0` before the join (unchanged).
