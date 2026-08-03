# Issue #152 Reproduction

## Issue

**Faithfulness checker can never mark short claims as supported**

https://github.com/ascherj/pathreview/issues/152

## Environment

The issue was reproduced locally from the working branch:

`fix/faithfulness-short-claims`

The project dependencies were installed in a Python virtual environment, and the unit tests were executed from the repository root.

## Reproduction command

```bash
make test-unit
```

A more focused reproduction can be run with:

```bash
pytest tests/unit/test_faithfulness_checker.py -v
```

## Observed failures

The following faithfulness-checker tests failed:

* `test_partial_support_returns_middle_score`
* `test_multiple_context_chunks`
* `test_multiple_claims_varying_support`

The test output included:

```text
faithfulness_checked
claims_count=2
supported_count=0
score=0.0
```

## Actual behavior

Short claims that are supported by the provided context are counted as unsupported. This causes the checker to return a faithfulness score of `0.0`, including cases where at least some or all of the claims should be recognized as supported.

## Expected behavior

A short claim should be considered supported when its meaningful content appears in the supplied context.

For example, a claim such as `Knows Python` should be supported by context containing `python`, even though the claim may contain only one meaningful non-stopword token.

## Scope note

The complete unit suite currently contains other unrelated failures. This contribution is limited to the failures associated with Issue #152 in:

* `rag/evaluator/faithfulness_checker.py`
* `tests/unit/test_faithfulness_checker.py`
