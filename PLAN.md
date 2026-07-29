## Solution plan

**Issue:** #153 — Faithfulness checker crashes when a context chunk has `text: None`
(https://github.com/ascherj/pathreview/issues/153)

> _This is a living document — I'll update it in Week 9 as my understanding evolves._

### Understand

**Root cause.** In `rag/evaluator/faithfulness_checker.py`, `FaithfulnessChecker.check()` builds the
context string with:

```python
context_text = " ".join([
    chunk.get("text", "") for chunk in context_chunks
])
```

`dict.get("text", "")` only returns the `""` default when the **key is absent**. When the key is
present but its value is `None` (i.e. `{"text": None}`), `.get()` returns `None`, and `str.join()`
rejects a `None` element, raising `TypeError: sequence item 0: expected str instance, NoneType found`.

**Expected vs. actual.**
- _Expected:_ a chunk whose text is `None` is treated as empty and scoring proceeds normally
  (a float 0.0–1.0 is returned; typically 0.0 if there is no supporting context).
- _Actual:_ the entire `check()` call raises `TypeError`, which crashes the evaluation step that
  calls it (`rag/evaluator/eval_suite.py:43`).

The repo already encodes the expected behavior in `tests/unit/test_faithfulness_checker.py`
(`test_none_context_chunk_text`, line 231) — that test currently **fails** with this crash, which is
how I reproduced the issue.

### Map

Files I expect to touch:

- **`rag/evaluator/faithfulness_checker.py`** — `FaithfulnessChecker.check()`, the list
  comprehension on lines 34–36. This is the single site of the crash and where the fix goes.
- **`tests/unit/test_faithfulness_checker.py`** — `test_none_context_chunk_text` (line 231) already
  asserts graceful handling and currently fails; `test_missing_text_key_in_chunk` (line 244) already
  passes. I'll confirm both pass after the fix and may tighten the `None` test to assert the exact
  score (`== 0.0`) rather than just a valid range.

Related but **out of scope for #153** (same `chunk.get("text", "")` / `chunk["text"]` pattern, would
crash on the same input — noted for awareness, not changing unless a mentor asks for the broader fix):

- `rag/evaluator/relevance_scorer.py:32`
- `rag/generator/review_generator.py:157`
- `rag/retriever/keyword_search.py:25` (uses `chunk["text"]` directly)

### Plan

1. **Reproduce first (done).** Call `check("Has Python skills", [{"text": None}])` and confirm the
   `TypeError` at `faithfulness_checker.py:34`. Confirm the control case (missing `text` key) does
   **not** crash — proving the bug is specific to an explicit `None`.
2. **Apply the fix.** Change the comprehension to coerce a null/missing value to an empty string:
   `(chunk.get("text") or "")`. This handles `None`, a missing key, and `""` uniformly while leaving
   real text untouched.
3. **Verify tests.** Run the unit tests for this module
   (`make test-unit`, or `pytest tests/unit/test_faithfulness_checker.py -v`) and confirm
   `test_none_context_chunk_text` and `test_missing_text_key_in_chunk` now pass with nothing else
   broken.
4. **Tighten the assertion (optional).** Update `test_none_context_chunk_text` to assert
   `score == 0.0`, making the expected behavior explicit rather than just "some valid float."
5. **Quality gate.** Run `make check` (ruff + black + mypy) to confirm lint, formatting, and types
   are clean before opening the PR.

### Inputs & outputs

**Function I'm changing:** `check(feedback: str, context_chunks: list[dict]) -> float`

- **Existing happy path:** chunks with real text → float in `[0.0, 1.0]` (unchanged).
- **New behavior (the bug case):** `context_chunks = [{"text": None}]` → returns a float (`0.0`), no
  exception. The null chunk contributes empty text to the concatenated context instead of crashing.
- **Also covered by the same fix:** `[{"text": ""}]` and `[{"content": "..."}]` (missing key) →
  float, no crash.

**Test that defines "done":** `test_none_context_chunk_text` passes (currently fails), asserting a
valid float (and, after step 4, `score == 0.0`).

### Risks & unknowns

1. **`or ""` also swallows other falsy values.** For a `text` field that's realistically a string or
   `None`, `chunk.get("text") or ""` is correct. But a non-string *truthy* value (e.g. an `int`)
   would still crash `join`. I'll check what upstream actually stores in `text` — the retriever
   (`rag/retriever/hybrid.py:85`) pulls it from ChromaDB documents, which are strings — so `None` is
   the realistic bad input. If non-str values are possible I'll switch to `str(chunk.get("text") or "")`.
2. **Scope creep.** The identical pattern in `relevance_scorer.py`, `review_generator.py`, and
   `keyword_search.py` would crash on the same input. I'm unsure whether the issue owner wants those
   fixed under #153 or in a separate issue. I'll ask in Slack / office hours and keep this PR minimal
   unless told otherwise.
3. **Semantics: empty vs. drop.** Whether a null chunk should contribute empty text or be dropped
   entirely produces the same score here (empty adds nothing to keyword overlap). I'll go with
   "treat as empty" to match the existing `get("text", "")` default semantics.

### Edge cases

- `{"text": None}` — treated as empty, no crash (the reported case).
- `{"content": "..."}` (missing `text` key) — already empty via the default; still no crash.
- `{"text": ""}` — empty, no crash.
- Mixed list `[{"text": None}, {"text": "Python skills"}]` — only the real text contributes; score is
  computed normally over the non-null chunk.
- All chunks null/empty → concatenated context is empty → no claims supported → returns `0.0`
  (a valid score, not a crash).
