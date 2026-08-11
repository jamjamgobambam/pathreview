# Issue #153 Reproduction

## Issue

Faithfulness checker crashes when a context chunk has `text: None`.

Issue link: https://github.com/ascherj/pathreview/issues/153

## Environment

- Branch: `fix/153-handle-none-context-text`
- Test framework: pytest
- Affected module: `rag/evaluator/faithfulness_checker.py`
- Relevant test: `tests/unit/test_faithfulness_checker.py::TestFaithfulnessChecker::test_none_context_chunk_text`

## Reproduction command

pytest tests/unit/test_faithfulness_checker.py::TestFaithfulnessChecker::test_none_context_chunk_text -v

## Input

The test calls the faithfulness checker with the following input:

- Feedback: `"Has Python skills"`
- Context chunks: `[{"text": None}]`

## Observed behavior

The test fails with:

`TypeError: sequence item 0: expected str instance, NoneType found`

The failure occurs when `FaithfulnessChecker.check()` combines the context chunk values using `" ".join(...)`.

## Expected behavior

The checker should handle a context chunk whose `text` value is `None` without crashing. The `None` value should be treated as an empty string, allowing the checker to return a valid faithfulness score.
