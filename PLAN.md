# Solution Plan — Issue #153

## Issue

**Title:** Faithfulness checker crashes when a context chunk has `text: None`
**Link:** https://github.com/ascherj/pathreview/issues/153
**Branch:** `fix/153-faithfulness-none-context`

## Problem

`FaithfulnessChecker.check()` combines retrieved context text using `" ".join()`. It currently reads each value with `chunk.get("text", "")`. The default empty string handles a missing key, but it does not handle a key that exists with the value `None`. As a result, `" ".join()` receives a `None` value and raises a `TypeError` instead of returning a faithfulness score.

## Local reproduction

### Environment

- macOS on Apple Silicon
- Python 3.11.15
- pytest 9.1.1
- Working branch: `fix/153-faithfulness-none-context`

### Reproduction command

```bash
.venv/bin/pytest tests/unit/test_faithfulness_checker.py::TestFaithfulnessChecker::test_none_context_chunk_text -v
```

### Test input

The failing test calls the checker with:

```python
feedback = "Has Python skills"
context_chunks = [{"text": None}]
```

### Observed behavior

The test fails in `rag/evaluator/faithfulness_checker.py` with:

```text
TypeError: sequence item 0: expected str instance, NoneType found
```

The failure occurs on this context-building operation:

```python
context_text = " ".join([
    chunk.get("text", "") for chunk in context_chunks
])
```

### Expected behavior

The checker should treat a missing or null text value as empty context. It should complete the evaluation without crashing and return a float between `0.0` and `1.0`.

## Root cause

`dict.get("text", "")` uses the empty-string default only when the `"text"` key is missing. If the key exists with the value `None`, `dict.get()` returns `None`.

The `" ".join()` operation accepts only strings. When it receives `None`, it raises a `TypeError`.

## Code-path analysis

1. `test_none_context_chunk_text` creates a context chunk containing `{"text": None}`.
2. The test calls `FaithfulnessChecker.check()`.
3. `check()` extracts claims from the supplied feedback.
4. It reads the `"text"` value from each context chunk.
5. The current expression returns `None` for the null text value.
6. `" ".join()` attempts to combine the values into one context string.
7. The join operation raises a `TypeError`.
8. The checker never calculates or returns the faithfulness score.

`EvalSuite.run()` also calls `FaithfulnessChecker.check()`. Therefore, an exception in the checker can prevent the full evaluation suite from calculating its overall result.

## Files involved

### File to modify

- `rag/evaluator/faithfulness_checker.py`
  - Normalize missing or `None` chunk text to an empty string before joining the context.
  - Preserve valid string values.
  - Keep the existing claim extraction and scoring behavior unchanged.

### Test file used for validation

- `tests/unit/test_faithfulness_checker.py`
  - Use the existing `test_none_context_chunk_text` as regression coverage.
  - Verify that `test_missing_text_key_in_chunk` continues passing.
  - Run the complete test file to detect regressions.

## Proposed solution

Update the context concatenation in `FaithfulnessChecker.check()` so that both a missing `"text"` key and a `"text"` value of `None` are normalized to an empty string.

The implementation should:

- Pass only strings to `" ".join()`.
- Treat `None` as empty context rather than converting it to the literal string `"None"`.
- Preserve all valid context strings.
- Avoid changing the existing scoring algorithm.

## Implementation steps

1. Modify the context-building expression in `FaithfulnessChecker.check()`.
2. Normalize missing and null text values to an empty string.
3. Run the targeted regression test.
4. Run the full faithfulness checker test file.
5. Review the diff to ensure the change remains narrowly scoped.
6. Run the project’s linting, formatting, and type checks.
7. Run the complete unit-test suite.
8. Commit the implementation using the project’s commit convention.

## Edge cases

- A chunk has no `"text"` key.
- A chunk has `"text": None`.
- All chunks contain missing or null text.
- Valid and null chunks appear together.
- `context_chunks` is empty.
- Valid string chunks continue producing the same results.

## Risks and scope

- The fix must not convert `None` into the string `"None"`, because that would introduce false context.
- The change must not modify claim extraction, keyword matching, or scoring thresholds.
- Valid text from other chunks must not be discarded when one chunk contains `None`.
- `RelevanceScorer` has a similar assumption about chunk text, but it is outside the scope of issue #153.
- Unexpected truthy non-string values are not part of the reported issue and should not cause unnecessary scope expansion.

## Validation commands

Run the targeted regression test:

```bash
.venv/bin/pytest tests/unit/test_faithfulness_checker.py::TestFaithfulnessChecker::test_none_context_chunk_text -v
```

Run all faithfulness checker tests:

```bash
.venv/bin/pytest tests/unit/test_faithfulness_checker.py -v
```

Run the required project checks:

```bash
make check
make test-unit
```

## Definition of done

- The reported `None` input no longer raises a `TypeError`.
- `test_none_context_chunk_text` passes.
- The missing-key test continues passing.
- All faithfulness checker tests pass.
- Project linting, formatting, type checking, and unit tests pass.
- The implementation remains limited to issue #153.