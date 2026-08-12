## Solution plan

**Issue:** Faithfulness checker crashes when a context chunk has text: None
(https://github.com/ascherj/pathreview/issues/153)

### Understand
`FaithfulnessChecker.check()` builds a combined context string by calling
`chunk.get("text", "")` on each chunk. The default value `""` only applies
when the `"text"` key is missing entirely. When a chunk has `"text": None`
explicitly, `.get()` returns `None` instead of falling back to the default.
The subsequent `" ".join(...)` call then raises `TypeError` because `None`
is not a string. Expected behavior: chunks with missing or `None` text
should be treated as empty strings and not crash the checker.

### Map
- `rag/evaluator/faithfulness_checker.py` — `check()` method, line ~34,
  where `context_text` is built via `.join()`
- `tests/unit/test_faithfulness_checker.py` — contains
  `test_none_context_chunk_text`, the existing failing test that
  documents expected behavior

### Plan
1. Change `chunk.get("text", "")` to `chunk.get("text") or ""` so both
   missing keys and explicit `None` values normalize to an empty string.
2. Run `test_none_context_chunk_text` to confirm it passes.
3. Run the full test file (`pytest tests/unit/test_faithfulness_checker.py`)
   to make sure no other tests regress.
4. Check for similar `.get(key, default)` patterns elsewhere in the file
   (or nearby evaluator files) that could have the same bug, since this
   may be a repeated pattern across the codebase.
5. Add/verify a docstring or comment clarifying that `None` text values
   are treated as empty context.

### Inputs & outputs
- Input: `feedback: str`, `context_chunks: list[dict]` where each dict may
  have `"text"` missing, `None`, or a real string.
- Output: a faithfulness score (float 0.0–1.0) without raising an exception,
  regardless of which of those three states each chunk's `"text"` is in.

### Risks & unknowns
- Unsure whether `chunk.get("text") or ""` could unintentionally treat
  other falsy-but-valid values (e.g. an empty string that's meaningfully
  different from `None`) the same way — need to confirm the codebase
  doesn't distinguish between "empty" and "missing" context elsewhere.
- Need to check if `_extract_claims()` or other methods in the same file
  have similar unguarded `.get()` calls that could crash on `None`.
- Possible that PR #162 (already linked to this issue) fixes it differently
  — worth comparing approaches, since multiple people are working on #153.

### Edge cases
- `context_chunks = [{"text": None}]` — single chunk, explicit None (the
  reported bug)
- `context_chunks = [{}]` — chunk missing the `"text"` key entirely
- `context_chunks = [{"text": None}, {"text": "real text"}]` — mixed valid
  and None chunks
- `context_chunks = []` — empty list (already handled by the early
  `if not context_chunks` check)
- `context_chunks = [{"text": ""}]` — explicit empty string (should behave
  the same as None, since both mean "no usable context")