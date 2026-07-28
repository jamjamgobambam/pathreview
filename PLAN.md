## Solution plan

**Issue:** [#153 — Faithfulness checker crashes when a context chunk has `text: None`](https://github.com/jamjamgobambam/pathreview/issues/153)

### Understand

**Root cause.** In `FaithfulnessChecker.check`, the context string is built with:

```python
context_text = " ".join([
    chunk.get("text", "") for chunk in context_chunks
])
```

`dict.get("text", "")` only falls back to `""` when the `"text"` key is
*missing*. When the key is *present but set to `None`* (e.g. `{"text": None}`),
`get` returns `None`, and `" ".join([None, ...])` raises:

```
TypeError: sequence item 0: expected str instance, NoneType found
```

**Expected vs. actual.**
- *Expected:* a chunk whose `text` is `None` is treated the same as an empty
  or missing chunk — it contributes nothing to the context and the checker
  returns a valid float score in `[0.0, 1.0]`.
- *Actual:* the checker raises an unhandled `TypeError` and the faithfulness
  score is never produced, which can crash the evaluation path that calls it.

### Map

Files/functions involved:

- **`rag/evaluator/faithfulness_checker.py`** — `FaithfulnessChecker.check`
  (the context-concatenation line, ~line 40 after the reproduction comment).
  This is the only line that needs to change.
- **`tests/unit/test_faithfulness_checker.py`** —
  `test_none_context_chunk_text` (already present, currently failing) is the
  regression signal. I may add a companion test for a *mixed* chunk list
  (`None` alongside a valid chunk) to prove valid chunks still score.

Files I expect to touch:
1. `rag/evaluator/faithfulness_checker.py` (the fix)
2. `tests/unit/test_faithfulness_checker.py` (strengthen coverage)

### Plan

1. **Coerce `None` to empty string** in the context concatenation. Replace
   `chunk.get("text", "")` with a form that also handles a present-but-`None`
   value, e.g. `chunk.get("text") or ""` (treats `None`, missing, and `""`
   identically). Remove the `BUG(#153)` reproduction comment as part of the fix.
2. **Confirm the existing regression test passes** —
   `test_none_context_chunk_text` should go from failing to passing.
3. **Add a mixed-chunk test** — a list containing `{"text": None}` and a valid
   chunk, asserting the score reflects only the valid chunk (proves `None` is
   skipped, not that scoring silently breaks).
4. **Run the full faithfulness test module** and confirm no regressions in the
   normal-chunk tests (scoring behavior for valid input must be unchanged).

### Inputs & outputs

- **Input:** `feedback: str` and `context_chunks: list[dict]`, where a chunk's
  `"text"` value may be a normal string, an empty string, missing entirely, or
  `None`.
- **Output:** a `float` faithfulness score in `[0.0, 1.0]`. After the fix, a
  `None` (or missing) text value contributes an empty string to the context
  instead of raising. Scores for all-valid input are byte-for-byte unchanged.

### Risks & unknowns

- **Behavioral equivalence of `None` and missing.** Using `chunk.get("text") or
  ""` also collapses `0`/`False`-y values, but `text` is expected to be a
  string, so this is safe here. Risk is low; I'll keep the change to the single
  line.
- **Unrelated pre-existing failures.** Three other tests in the same module
  (`test_partial_support_returns_middle_score`, `test_multiple_context_chunks`,
  `test_multiple_claims_varying_support`) currently fail due to the scoring
  *heuristic* returning `0.0`, **not** the `None` bug. My fix must not touch
  those thresholds; I'll verify my change leaves their behavior untouched and
  call out that they are out of scope for #153.
- **Callers.** Unknown whether any caller relies on the crash as a signal
  (unlikely). I'll grep for `FaithfulnessChecker(` / `.check(` usages to confir
  no caller expects an exception.

### Edge cases

- `{"text": None}` — the reported case; must not crash.
- Missing `"text"` key (`{"content": "..."}`) — already handled; must stay
  handled (`test_missing_text_key_in_chunk`).
- `{"text": ""}` — empty string, should contribute nothing and not crash.
- Mixed list: `[{"text": None}, {"text": "valid content"}]` — valid chunk still
  contributes; score computed from it.
- All chunks `None`/empty — context is empty; claims find no support and the
  method returns a valid low score rather than raising.
