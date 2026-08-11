# Solution Plan

**Issue:** [Faithfulness checker crashes when a context chunk has `text: None`](https://github.com/ascherj/pathreview/issues/153)

## Understand

The faithfulness checker combines the text from every retrieved context chunk into one string before evaluating whether the generated feedback is supported by the context. The current implementation uses `chunk.get("text", "")`, which handles a missing `text` key but does not handle a key whose value is explicitly `None`.

When a context chunk contains `{"text": None}`, the expression returns `None`. The `" ".join(...)` operation then raises a `TypeError` because it expects every item to be a string. The expected behavior is for the checker to treat a missing or `None` text value as an empty string and continue without crashing.

## Map

The primary files involved are:

- `rag/evaluator/faithfulness_checker.py`
  - Contains `FaithfulnessChecker.check()`.
  - Builds the combined context string from the context chunks.
  - Contains the expression responsible for the crash.

- `tests/unit/test_faithfulness_checker.py`
  - Contains the unit tests for the faithfulness checker.
  - Includes `test_none_context_chunk_text`, which reproduces the issue.
  - Will be used to verify that the fix handles `None` safely without changing existing behavior.

- `REPRODUCTION.md`
  - Documents the command, input, observed failure, and expected behavior for Issue #153.

## Plan

1. Update the context text extraction in `FaithfulnessChecker.check()` so that both missing `text` keys and explicit `None` values are converted to empty strings.

2. Run `test_none_context_chunk_text` and confirm that the checker no longer raises a `TypeError`.

3. Review the existing faithfulness checker tests to determine whether additional cases are needed for missing text, empty strings, or mixed valid and invalid context chunks.

4. Run the complete `tests/unit/test_faithfulness_checker.py` test file to confirm that the change does not break existing faithfulness behavior.

5. Run the repository's formatting, linting, and relevant test commands before committing the final implementation.

## Inputs and Outputs

The fix takes a list of context chunk dictionaries as input. Each dictionary may contain a `text` key with a normal string, an empty string, a `None` value, or no `text` key at all.

Before the fix, an explicit `None` value causes the checker to raise a `TypeError` while joining the context text.

After the fix, missing and `None` text values should be treated as empty strings. Valid string values should remain unchanged, and the method should return a numeric faithfulness score instead of crashing.

## Risks and Unknowns

- Treating `None` as an empty string could result in an empty combined context when every chunk has missing text. I need to verify how the checker handles that situation and what score it should return.

- Other unexpected non-string values, such as integers, lists, or nested dictionaries, could still cause `" ".join(...)` to fail. Issue #153 specifically concerns `None`, so supporting every possible invalid type may be outside the intended scope.

- Removing empty values before joining might produce cleaner context, but it could be a broader behavioral change than simply normalizing `None`. I will keep the implementation targeted unless existing tests indicate otherwise.

- The test already exists and currently fails, so I need to verify that its expected score accurately represents the intended behavior after the crash is resolved.

## Edge Cases

The solution should handle the following cases gracefully:

- A context chunk with `{"text": None}`
- A context chunk with no `text` key
- A context chunk with `{"text": ""}`
- A list containing both valid text chunks and `None` text chunks
- Multiple context chunks whose text values are all `None`
- An empty context chunk list
- Empty feedback
- Normal context chunks containing valid strings

The change should not alter the behavior of valid context chunks or existing faithfulness calculations.
