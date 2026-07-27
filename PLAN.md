# PLAN.md

## Solution plan

**Issue:** Faithfulness checker can never mark short claims as supported
https://github.com/ascherj/pathreview/issues/152

### Understand

The faithfulness checker evaluates generated feedback by extracting claims and determining whether each claim is supported by the retrieved context.

I reproduced Issue #152 locally by running:

```bash
make test-unit
```

The faithfulness checker tests failed, including:

* `test_partial_support_returns_middle_score`
* `test_multiple_context_chunks`
* `test_multiple_claims_varying_support`

The logs showed:

```text
faithfulness_checked
claims_count=2
supported_count=0
score=0.0
```

This confirms that short supported claims are currently being evaluated as unsupported.

From reading the issue and reproducing the failure, the likely root cause is that the current support-checking logic requires at least **two meaningful overlapping tokens** between a claim and its supporting context.

For example:

Claim:

```
Knows Python
```

After removing stopwords, the only meaningful token is:

```
python
```

Even when the context contains:

```
python expert
```

there is only one overlapping meaningful token, so the checker incorrectly marks the claim as unsupported.

**Expected behavior**

A claim containing one meaningful token should be considered supported when that token appears in the retrieved context.

Longer claims should continue requiring stronger supporting evidence so the checker does not introduce false positives.

---

### Map

The primary files involved are:

**rag/evaluator/faithfulness_checker.py**

* `FaithfulnessChecker.check()`
* claim extraction
* context concatenation
* support-checking logic
* token overlap calculation

**tests/unit/test_faithfulness_checker.py**

Existing failing tests:

* `test_partial_support_returns_middle_score`
* `test_multiple_context_chunks`
* `test_multiple_claims_varying_support`

This file will also receive new regression tests to verify the fix.

I also created:

```
docs/issue-152-reproduction.md
```

to document how the issue was reproduced locally.

---

### Plan

1. Trace how `FaithfulnessChecker.check()` extracts claims and determines whether each claim is supported.

2. Understand how meaningful tokens are generated after stopword removal.

3. Identify where the current overlap threshold is enforced.

4. Add regression tests for short supported claims before modifying the implementation.

5. Modify the overlap logic so that claims with only one meaningful token can be supported by one matching token.

6. Verify that longer claims still require stronger evidence and are not incorrectly classified as supported.

7. Run the faithfulness checker tests.

8. Run the complete unit test suite.

9. Run linting and formatting checks.

---

### Inputs & outputs

**Input**

The checker receives:

* generated feedback text
* retrieved context chunks

Example:

```python
feedback = "Knows Python. Knows SQL."

context_chunks = [
    {"text": "python expert"},
    {"text": "sql expert"},
]
```

Current output:

```
0.0
```

because both claims are considered unsupported.

Expected output:

Both claims should be considered supported because each meaningful token appears in the supplied context.

The resulting faithfulness score should reflect complete support.

---

### Risks & unknowns

Possible risks include:

* Lowering the overlap threshold too much could introduce false positives.
* Longer claims should not pass because of only one shared word.
* Claims containing only stopwords should not automatically become supported.
* Changes to support detection could affect existing partial-support scores.
* Multiple context chunks must continue working correctly.
* I still need to confirm the exact intended overlap rule by reading the implementation in `faithfulness_checker.py`.

---

### Edge cases

The implementation should correctly handle:

* one meaningful token that appears in the context
* one meaningful token that does not appear in the context
* multiple short claims
* multiple context chunks
* supported and unsupported claims together
* empty feedback
* empty context
* empty context text
* `None` context text
* claims containing only stopwords
* punctuation
* uppercase/lowercase differences
* repeated words
* longer claims with only one incidental matching word
