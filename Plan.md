# Solution plan

**Issue:** [Faithfulness checker crashes when a context chunk has text: None](https://github.com/ascherj/pathreview/issues/153)

## Understand

The root cause of this issue is that `FaithfulnessChecker.check()` uses `chunk.get("text", "")`. This works when the text key is missing because `.get()` returns an empty string by default. However, if the text key exists and its value is `None`, `.get("text", "")` returns `None` instead of the default empty string. Later, when the checker tries to join the chunks into a single string using `" ".join(...)`, Python raises a TypeError because `" ".join(...)` expects a string where None is.
The faithfulness checker should handle a chunk with `text: None` without crashing and return a valid faithfulness score. Instead, it raises `TypeError: sequence item 0: expected str instance, NoneType found`.

## Map

The main files involved are:

- `rag/evaluator/faithfulness_checker.py`
- `tests/unit/test_faithfulness_checker.py`

The main function involved is:

- `FaithfulnessChecker.check()`

## Plan

- Inspect `rag/evaluator/faithfulness_checker.py` and find where the context chunks join to create the context string.
- Update the context text extraction so that a chunk with `text: None` produces a valid string value, treating it as an empty string.
- Run `test_none_context_chunk_text` to confirm the bug is fixed.
- Run the full faithfulness checker test in `test_faithfulness_checker.py` to confirm nothing broke.

## Inputs & outputs

Input for `check()` function:

- Claim string extracted from feedback | `"Knows Python."`
- List of context chunks | `{"text": None}]`

Expected output after the fix:

- The checker should complete without raising a `TypeError`.
- `None` text value should be handled as an empty or unusable context.
- Normal context chunks with valid text should continue behaving the same way as before.

## Risks & unknowns

One risk is accidentally changing the meaning of empty or missing context. If None becomes an empty string, the checker may treat that chunk as no context, which makes sense in theory, but I need to confirm that this matches with the existing behavior.

## Edge cases

The fix should handle these cases gracefully:

- A context chunk has `{"text": None}`
- A context chunk is missing a `text` key
- A context chunk has `{"text": ""}`
- Multiple context chunks are provided, and only one has `text: None`
- Valid context chunks with normal string text should still work exactly as before
