## Solution plan

**Issue:** Faithfulness checker crashes when a context chunk has `text: None` https://github.com/ascherj/pathreview/issues/153

### Understand
The faithfulness checker currently concatenates context chunk text with `chunk.get("text", "")`. That works only when the `text` key is missing; if the key exists with value `None`, the join receives a `None` item and raises `TypeError`. Expected behavior is for `FaithfulnessChecker.check()` to treat missing or `None` chunk text as empty text and continue scoring normally.

### Map
- `rag/evaluator/faithfulness_checker.py`
- `tests/unit/test_faithfulness_checker.py`

### Plan
1. Update `FaithfulnessChecker.check()` so chunk text is normalized safely to a string before joining.
2. Ensure `None` values and missing `text` keys both become `""`.
3. Run or update the existing unit test `test_none_context_chunk_text` to verify the crash is fixed.
4. Optionally add a small regression test or assertion to cover the normalization behavior explicitly.

### Inputs & outputs
Input: `feedback` string and `context_chunks` list of dictionaries, where each chunk may have `text=None`, missing `text`, or valid string text.
Output: A valid float faithfulness score, never crashing due to `None` chunk text.

### Risks & unknowns
- The fix is small and low risk, but it should not alter scoring semantics for valid text values.
- Need to confirm no other evaluator paths assume chunk text is always a string.

### Edge cases
- `context_chunks` contains `{"text": None}`
- `context_chunks` contains chunks with missing `text` keys
- `context_chunks` contains empty strings, whitespace-only strings, or non-string values in `text`
- `feedback` is empty or `context_chunks` is empty already handled by current logic