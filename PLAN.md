## Solution plan

**Issue:** Faithfulness check — https://github.com/ascherj/pathreview/issues/153

### Understand
The root cause of this issue is that `FaithfulnessChecker.check()` assumes that every context chunk contains a string value under the `text` field. When a context chunk contains `{"text": None}`, the current implementation uses `chunk.get("text", "")`, which returns `None` because the key exists. This `None` value is then passed into `" ".join()`, causing a `TypeError` because `join()` only accepts strings.

The expected behavior is for the faithfulness checker to handle `None`-valued context text gracefully without crashing. Valid text values should continue to be concatenated and evaluated normally.

### Map
The main files involved are:

- `rag/evaluator/faithfulness_checker.py`
  - `FaithfulnessChecker.check()`
  - Context extraction and text concatenation logic where `context_text` is generated.

- `tests/unit/test_faithfulness_checker.py`
  - `TestFaithfulnessChecker.test_none_context_chunk_text`
  - Existing tests covering faithfulness evaluation behavior.

Expected files to touch:
- `rag/evaluator/faithfulness_checker.py`
- Potentially `tests/unit/test_faithfulness_checker.py` if additional regression coverage is needed.

### Plan
1. Reproduce the current failure by running `test_none_context_chunk_text` and confirm that `None` values in context chunks cause a `TypeError`.
2. Update the context text extraction logic in `FaithfulnessChecker.check()` to normalize `None` values into a safe string representation before joining.
3. Run the existing `test_none_context_chunk_text` test to confirm the issue is resolved.
4. Run the full faithfulness checker test suite to ensure the change does not affect existing behavior.
5. Review edge cases and commit the implementation after confirming the fix.

### Inputs & outputs

Input example:

```python
feedback = "Has Python skills"
context_chunks = [{"text": None}]
```

Current behavior:
- The function extracts `None` as the context text.
- `" ".join()` receives a non-string value.
- The function raises a `TypeError`.

Expected behavior:
- `None` text values are handled safely.
- The function completes without crashing.
- Valid string context continues to work as before.

### Risks & unknowns
- It is unclear whether the `text` field is guaranteed to only contain `str` or `None`.
- A broad fallback approach may hide unexpected invalid data types.
- Empty context after filtering invalid values may affect later faithfulness scoring logic.
- Additional validation may belong upstream depending on the intended data flow.

### Edge cases
The fix should handle:

- Empty context:
  - `[]`

- Missing text field:
  - `[{}]`

- None text value:
  - `[{"text": None}]`

- Empty string:
  - `[{"text": ""}]`

- Mixed valid and invalid chunks:
  - `[{"text": None}, {"text": "Valid context"}]`

- Multiple valid chunks:
  - `[{"text": "First"}, {"text": "Second"}]`