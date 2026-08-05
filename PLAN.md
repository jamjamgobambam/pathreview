## Solution plan

**Issue:** Faithfulness checker crashes when a context chunk has `text: None` — https://github.com/jamjamgobambam/pathreview/issues/153

### Understand
**Root cause.** `FaithfulnessChecker.check()` concatenates the context by reading
each chunk with `chunk.get("text", "")`. The `""` default only applies when the
`"text"` **key is missing**. When the key is present but its value is `None`
(a real case for retrieved chunks that were stored with a null body),
`.get("text", "")` returns `None`. That `None` is then passed into
`" ".join([...])`, and since `str.join` only accepts strings, Python raises
`TypeError: sequence item 0: expected str instance, NoneType found`.

**Expected vs. actual.**
- Expected: a chunk with `text: None` is treated the same as an empty/missing
  text — it contributes nothing to the context and the scoring continues.
- Actual: the whole `check()` call crashes with a `TypeError`, so any retrieved
  context containing a null-text chunk aborts the faithfulness evaluation.

### Map
Files/functions involved:
- `rag/evaluator/faithfulness_checker.py` — `FaithfulnessChecker.check()`,
  specifically the context concatenation at lines 34–36. **(the fix)**
- `tests/unit/test_faithfulness_checker.py` — already contains
  `test_none_context_chunk_text` (line 231, currently failing) and
  `test_missing_text_key_in_chunk` (line 244, passing). **(verification)**

Files I expect to touch:
- `rag/evaluator/faithfulness_checker.py` (the one-line-ish fix)
- Possibly `tests/unit/test_faithfulness_checker.py` (only if I add a
  multi-chunk mixed None/valid case to strengthen coverage)

### Plan
1. **Confirm the failing test** reproduces the `TypeError`
   (`pytest tests/unit/test_faithfulness_checker.py::TestFaithfulnessChecker::test_none_context_chunk_text`).
2. **Fix the coercion** in `check()`: change the list comprehension so a `None`
   text is coerced to `""` (e.g. `chunk.get("text") or ""`), treating null the
   same as empty/missing.
3. **Run the targeted test** and confirm it now passes and returns a float
   in `[0.0, 1.0]`.
4. **Run the full faithfulness test module** to confirm no regressions
   (all existing passing tests stay green).
5. **Optionally add** a test with mixed chunks (one `None`, one valid) to lock
   in the behavior that a null chunk doesn't wipe out valid context.

### Inputs & outputs
- **Input:** `feedback: str` and `context_chunks: list[dict]`, where a chunk may
  have `text` missing, `text: None`, or `text: <string>`.
- **Output:** a faithfulness score `float` in `[0.0, 1.0]`. After the fix, a
  chunk with `text: None` contributes no text (like `""`) instead of raising,
  so `check()` always returns a valid score for well-formed chunk lists.

### Risks & unknowns
- **Silent data loss vs. crash:** coercing `None → ""` hides that a chunk had no
  body. That's the behavior the issue asks for, but I should confirm no upstream
  code relies on the crash to surface bad ingestion data. (Low risk — the issue
  explicitly wants graceful handling.)
- **`or ""` vs. `if ... is not None`:** using `chunk.get("text") or ""` also
  coerces other falsy values (e.g. empty string stays `""`, which is fine). No
  numeric/text falsy edge cases are expected here since `text` should be a
  string, but I'll note this in the fix.
- **Non-dict chunks:** the signature is `list[dict]`, so I'll assume dicts; I am
  not planning to defend against non-dict chunk entries unless a test requires
  it.

### Edge cases the fix should handle gracefully
- Chunk with `text: None` → treated as empty, no crash.
- Chunk with `text` key missing → already handled (`""` default), stays working.
- Multiple chunks where some are `None` and some valid → valid text still counts.
- All chunks have `None`/empty text → context is empty; scoring proceeds and
  returns a valid float (unsupported claims → low score).
- Empty `context_chunks` list → already returns `0.0` early (unchanged).
