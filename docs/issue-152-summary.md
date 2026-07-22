# Issue #152: Short Claims Marked Unsupported

## Issue Link

https://github.com/ascherj/pathreview/issues/152

## Problem Summary

The PathReview faithfulness checker currently requires at least two meaningful, non-stopword tokens to overlap between a claim and its supporting context.

Because of this requirement, short factual claims such as “Knows Python” may be marked as unsupported even when the context clearly supports them.

For this contribution, I will reproduce the issue, inspect the existing faithfulness-checking logic, and plan a focused solution that correctly handles short claims without weakening support detection for unrelated claims.

## Current Reproduction

```python
from rag.evaluator.faithfulness_checker import FaithfulnessChecker

checker = FaithfulnessChecker()

score = checker.check(
    "Knows Python. Knows SQL.",
    [
        {"text": "python expert"},
        {"text": "sql expert"},
    ],
)

print(score)
```

## Current Behavior

The checker returns:

```text
0.0
```

## Expected Behavior

The checker should recognize that both short claims are supported by the provided context and return an appropriate supported score.
