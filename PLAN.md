## Solution plan

**Issue:** [Faithfulness checker crashes when a context chunk has `text: None` (#153)](https://github.com/ascherj/pathreview/issues/153)

### Understand

**Root cause.** `FaithfulnessChecker.check` builds one big context string by
joining the `text` field of every retrieved chunk:

```python
context_text = " ".join([chunk.get("text", "") for chunk in context_chunks])
```

`dict.get("text", "")` only falls back to the `""` default when the `"text"`
key is **absent**. When a chunk explicitly contains `{"text": None}` — a real
shape produced by retrieval when a stored chunk has a null body — `.get`
returns `None`, and `str.join` refuses to join a `None`:

```
TypeError: sequence item 0: expected str instance, NoneType found
```

**Expected vs. actual.**
- *Expected:* a null-text chunk contributes no text and scoring proceeds
  normally over the remaining chunks; the method still returns a float in
  `[0.0, 1.0]`.
- *Actual:* the whole `check` call raises `TypeError` and the evaluation
  aborts, so a single bad chunk poisons the entire faithfulness score.

### Map

Files/functions involved:

- [rag/evaluator/faithfulness_checker.py](rag/evaluator/faithfulness_checker.py) — `FaithfulnessChecker.check`, the `" ".join([...])` list comprehension at line ~44. **Primary fix site.**
- [tests/unit/test_faithfulness_checker.py](tests/unit/test_faithfulness_checker.py) — already contains `test_none_context_chunk_text` and `test_missing_text_key_in_chunk`, which currently fail/pass respectively; these become the regression tests. **Test site.**
- [rag/evaluator/eval_suite.py](rag/evaluator/eval_suite.py) and [scripts/run_evals.py](scripts/run_evals.py) — callers that feed real retrieval chunks into the checker; used to sanity-check that the fix behaves in the actual eval pipeline (read-only, likely no edits).

### Plan

1. **Fix the coercion in `check`.** Replace `chunk.get("text", "")` with a form
   that treats both missing keys and explicit `None` as empty string, e.g.
   `str(chunk.get("text") or "")`, or filter non-string/empty texts out before
   the join. Keep it a single, localized change in `faithfulness_checker.py`.
2. **Guard the return path.** Confirm that after coercion, an all-`None`/empty
   context still returns a valid float (claims found but zero support → `0.0`)
   rather than dividing by zero or returning `None`.
3. **Turn the existing None test green.** Ensure `test_none_context_chunk_text`
   passes, and add explicit assertions (score is a float in `[0.0, 1.0]`) plus
   a mixed case: some chunks `None`, some real, verifying the real chunks still
   count toward the score.
4. **Add regression coverage for adjacent shapes.** Add tests for a chunk whose
   `text` is a non-string (e.g. `{"text": 123}`) and for a mix of missing-key
   and `None`-value chunks, to lock the coercion behavior.
5. **Run the full unit suite + linters.** `pytest tests/unit/test_faithfulness_checker.py`
   and the pre-commit hooks (ruff/black/mypy) to confirm no regressions.

### Inputs & outputs

- **Input (unchanged signature):** `check(feedback: str, context_chunks: list[dict]) -> float`.
  The behavioral change is that `context_chunks` may now contain items where
  `chunk["text"]` is `None`, missing, or a non-string, and these are tolerated
  instead of raising.
- **Output:** still a `float` faithfulness score in `[0.0, 1.0]`. For inputs
  that previously raised `TypeError`, the output changes from *(exception)* to a
  well-defined score computed from the surviving text (or `0.0` if no supporting
  text remains).
- **No change** to public API, return type, or the scoring semantics for
  well-formed chunks.

### Risks & unknowns

- **`str(x or "")` over-coercion.** `x or ""` also turns falsy values like `0`
  or `False` into `""`. For a `text` field that's acceptable, but I should
  confirm in `eval_suite.py`/`run_evals.py` that `text` is only ever expected to
  be a string, so coercion doesn't silently mask a different upstream bug.
- **Should bad chunks be skipped or emptied?** Emptying (`""`) keeps chunk
  count/order; filtering changes the effective context. I'll pick emptying to
  stay minimal, but need to verify no caller relies on a positional mapping
  between `context_chunks` and the joined text.
- **Silent data-quality loss.** Coercing `None`→`""` hides that retrieval
  produced null chunks. Open question: should the fix also `logger.warning`
  when a chunk has null/missing text, matching the existing `structlog` logging
  style in this file? Leaning yes.
- **Non-string non-None texts** (e.g. numbers) are an unverified assumption
  about real data; the `str(...)` wrapper handles them defensively but I haven't
  confirmed they occur.

### Edge cases

The fix must handle each of these gracefully (return a valid float, no raise):

1. A single chunk `{"text": None}` (the reported crash).
2. A mix of `{"text": None}` and `{"text": "real content"}` — real chunks still
   contribute to the score.
3. A chunk missing the `text` key entirely, e.g. `{"content": "..."}` (already
   covered by `test_missing_text_key_in_chunk`).
4. All chunks have `None`/empty text → claims exist but nothing supports them →
   score `0.0`, not an exception.
5. A chunk whose `text` is a non-string (e.g. `{"text": 123}`) — coerced, not
   crashed.
6. Empty string text `{"text": ""}` — treated as no support, consistent with
   the existing empty-input handling.
