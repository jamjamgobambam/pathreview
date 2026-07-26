## Solution plan 

**Issue:** Faithfulness checker crashes when a context chunk has `text: None` — [paste GitHub issue #153 URL here]

### Understand
The root cause is a misuse of `dict.get()` in `FaithfulnessChecker.check()`. The
context-building step calls `chunk.get("text", "")`, but a default only applies
when the key is *missing*. When the key is present with value `None` (i.e.
`{"text": None}`), `.get()` returns `None`, which then flows into `" ".join(...)`.
`str.join` requires every element to be a string, so it raises
`TypeError: sequence item 0: expected str instance, NoneType found`.
Expected behavior: the checker handles a null text value gracefully and returns a
float in `[0.0, 1.0]`. Actual behavior: it crashes with a TypeError.

### Map
- `rag/evaluator/faithfulness_checker.py` — the `check()` method, specifically the
  context concatenation on line 34 (`" ".join([chunk.get("text", "") ...])`).
  This is the only source file that needs to change.
- `tests/unit/test_faithfulness_checker.py` — `test_none_context_chunk_text`
  already exists and exercises this case; no test changes needed. The sibling
  `test_missing_text_key_in_chunk` must also stay green.

### Plan
1. Change the context-building expression from `chunk.get("text", "")` to
   `chunk.get("text") or ""`, coercing any falsy value (including `None`) to an
   empty string before it reaches `join`.
2. Run `test_none_context_chunk_text` to confirm it now passes.
3. Run `test_missing_text_key_in_chunk` to confirm the missing-key case still
   passes (the same expression covers it).
4. Run the full `test_faithfulness_checker.py` suite to confirm no regressions.

### Inputs & outputs
- Input: `feedback` (str) and `context_chunks` (list of dicts, where a chunk's
  `text` value may be a string, `None`, or absent entirely).
- Output: unchanged contract — a faithfulness score as a float in `[0.0, 1.0]`.
  The fix only changes how null/missing text is handled during context assembly;
  it does not alter scoring for well-formed input.

### Risks & unknowns
Very low risk — a one-line, single-cause change with an existing test. The
expression `x or ""` is standard and readable. One thing to be aware of: if a
chunk's `text` were a non-string *truthy* value (e.g. a number or a list),
`" ".join` would still raise, because `or ""` only catches falsy values. That is
outside the scope of this issue and not covered by any current test, so it is
noted here as a known limitation rather than fixed.

### Edge cases
- `{"text": None}` → coerced to `""` (the reported bug).
- `{"content": "..."}` (missing `text` key) → `.get("text")` is `None` → `""`.
- `{"text": ""}` → already empty, passes through unchanged.
- `{"text": "Python skills"}` → normal path, unaffected.
