## Solution plan

**Issue:** Faithfulness checker crashes when a context chunk has text: `None` (https://github.com/ascherj/pathreview/issues/153)

### Understand
Root cause: In `FaithfulnessChecker.check()`, context text is built with:
`" ".join([chunk.get("text", "") for chunk in context_chunks])`.
If a chunk contains `{"text": None}`, `chunk.get("text", "")` returns `None` (because the key exists), and `join` raises a `TypeError`.

Expected behavior: `check()` should treat missing/`None` chunk text as empty text and return a valid float score in `[0.0, 1.0]`.
Actual behavior: `check()` crashes before scoring.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

- `rag/evaluator/faithfulness_checker.py` (`FaithfulnessChecker.check`)
- `tests/unit/test_faithfulness_checker.py` (existing coverage; may add/adjust tests for non-string text values)
- `JOURNAL.md` (Week 8 reproduction evidence)

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. Reproduce the bug with the focused pytest command and save output in journal notes.
2. Update context text normalization in `FaithfulnessChecker.check()` so `None` (and optionally other non-string values) are safely coerced to empty strings or strings before joining.
3. Keep/expand unit tests for `None` and missing `text` keys, and optionally add a test for non-string `text` values.
4. Run targeted tests for `test_none_context_chunk_text` and related faithfulness tests.
5. Run the full unit test subset for evaluator modules to catch regressions.

### Inputs & outputs
What does your fix take as input? What should it produce or change?

- Inputs: `feedback: str`, `context_chunks: list[dict]` where chunk dictionaries may have absent, `None`, or unexpected `text` values.
- Output: A `float` faithfulness score between `0.0` and `1.0`.
- Behavioral change: No exception when chunk `text` is `None` or missing; scoring continues normally.

### Risks & unknowns
What could go wrong? What are you still unsure about?

- Coercing all non-string values to `str(...)` could introduce noisy tokens; coercing to empty string may hide malformed upstream data.
- Need to confirm team preference for strict sanitization (`None` only) versus broader defensive handling (all non-strings).
- If scoring semantics change slightly due to sanitization, some threshold-based tests could need updates.

### Edge cases
What inputs or states should your fix handle gracefully?

- `context_chunks = [{"text": None}]`
- `context_chunks = [{"content": "..."}]` (missing `text` key)
- Mixed valid and invalid chunk text values in one request
- Empty feedback or empty chunk list (already returns `0.0`)
- Feedback that yields zero extracted claims (should still return neutral/default score path)