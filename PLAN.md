# Issue #152 Solution Plan

## Issue

https://github.com/ascherj/pathreview/issues/152

## Problem Summary

The faithfulness checker incorrectly marks short factual claims as unsupported
when the supplied context contains evidence for them.

The current matching logic requires at least two meaningful overlapping tokens.
A short claim such as "Knows Python" may contain only one meaningful token,
`python`, after stopwords are removed. Therefore, the claim cannot reach the
current threshold even when `python` appears directly in the context.

## Reproduction

I ran the project's unit tests using:

make test-unit

The test suite completed and reproduced the reported issue.

The following tests currently fail:

- test_partial_support_returns_middle_score
- test_multiple_context_chunks
- test_multiple_claims_varying_support

The logs show:

faithfulness_checked
claims_count=2
supported_count=0
score=0.0

This confirms that short supported claims are incorrectly evaluated as unsupported.

### Command

```bash
python scripts/reproduce_issue_152.py