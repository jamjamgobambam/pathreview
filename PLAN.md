## Solution plan

**Issue:** Faithfulness checker crashes when a context chunk has `text: None` — https://github.com/ascherj/pathreview/issues/153

### Understand

**Root cause:** In `FaithfulnessChecker.check()`, context is built with:

```python
context_text = " ".join([
    chunk.get("text", "") for chunk in context_chunks
])
```

`dict.get("text", "")` only uses the default when the key is **missing**. If the key is present and the value is `None`, `.get()` returns `None`. `" ".join(...)` then raises:

`TypeError: sequence item 0: expected str instance, NoneType found`

**Expected:** `check()` returns a float score in `[0.0, 1.0]` and does not crash when a chunk has `"text": None`.

**Actual:** Calling `FaithfulnessChecker().check('Knows Python.', [{'text': None}])` raises `TypeError`. The related unit test `test_none_context_chunk_text` expects graceful handling.

### Map

| File | Role |
|---|---|
| `rag/evaluator/faithfulness_checker.py` | Bug lives here — `check()` join over chunk texts |
| `tests/unit/test_faithfulness_checker.py` | Existing failing case: `test_none_context_chunk_text` |

**Functions involved:** `FaithfulnessChecker.check()` (primary). Downstream `_is_supported()` is fine once `context_text` is a string.

**Files expected to touch:**
1. `rag/evaluator/faithfulness_checker.py` — normalize `None`/non-string chunk text before join
2. `tests/unit/test_faithfulness_checker.py` — only if needed to clarify assertions (test already exists)

### Plan

1. Confirm reproduction: run the issue snippet / `test_none_context_chunk_text` and see `TypeError`.
2. In `check()`, coerce each chunk's text to a string before joining (e.g. treat `None` as `""` via `(chunk.get("text") or "")`, or an explicit `None` check). Keep missing-key behavior the same.
3. Re-run `tests/unit/test_faithfulness_checker.py` (especially `test_none_context_chunk_text` and `test_missing_text_key_in_chunk`) and ensure no regressions.
4. Commit with conventional message: `fix(rag): handle None context chunk text in faithfulness checker` and `Fixes #153`.

### Inputs & outputs

**Inputs:** `feedback: str`, `context_chunks: list[dict]` where a chunk may have `"text"` missing, empty, or `None`.

**Outputs / change:** `check()` returns `float` in `[0.0, 1.0]` instead of raising. Chunks with `None` text contribute nothing to context (same as empty string). Scoring logic otherwise unchanged.

### Risks & unknowns

- Over-coercing non-string values (e.g. numbers) with `str(...)` could change behavior; safest is treat only `None`/falsy text as `""`.
- Need to confirm whether callers ever send non-string `text` besides `None`; for this issue, `None` is the required fix.
- Env note: local run needs project deps installed (`structlog`, etc.) to execute the unit test.

### Edge cases

- `{"text": None}` — must not crash; treat as empty
- Missing `"text"` key — already handled by `.get(..., "")`; must keep working
- Empty string / whitespace-only text
- Mix of valid strings and `None` in the same `context_chunks` list
- Empty `feedback` or empty `context_chunks` — already early-return `0.0`
