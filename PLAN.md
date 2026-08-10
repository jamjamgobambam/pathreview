# Solution Plan

**Issue:** Faithfulness checker crashes when a context chunk has `text: None`
https://github.com/ascherj/pathreview/issues/153

## Understand

The faithfulness checker combines the text from retrieved context chunks into a single string before evaluating whether the model's response is supported by the retrieved evidence. When one of the chunks contains `text: None`, Python raises a TypeError because `join()` expects strings, causing the evaluation to fail.

## Map

Files involved:

- `rag/evaluator/faithfulness_checker.py`
- `tests/unit/test_faithfulness_checker.py`

## Plan

1. Inspect the failing unit test to understand the expected behavior.
2. Locate where context chunk text is combined in the faithfulness checker.
3. Update the code to safely handle `None` values by treating them as empty strings.
4. Re-run the failing test to verify the crash is resolved.
5. Run the broader faithfulness test suite to ensure no existing behavior is broken.

## Inputs & outputs

**Input:**
A list of retrieved context chunks, where one or more chunks may contain `"text": None`.

**Output:**
The faithfulness checker should ignore or safely handle missing text values instead of crashing.

## Risks & unknowns

I need to confirm whether other parts of the codebase also expect `text` to always be a string. I also want to verify that treating `None` as an empty string matches the intended behavior for the evaluator.

## Edge cases

- Context chunk contains `text: None`
- Context chunk contains an empty string
- Context chunk is missing the `text` field entirely
- Multiple invalid chunks appear in the same request
- All chunks are valid strings (existing behavior should remain unchanged)