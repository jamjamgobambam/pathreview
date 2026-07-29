## Solution plan

**Issue:** Faithfulness checker can never mark short claims as supported
https://github.com/ascherj/pathreview/issues/152

### Understand
`_is_supported()` in `rag/evaluator/faithfulness_checker.py` requires at
least 2 non-stopword tokens to overlap between a claim and its supporting
context before marking the claim as supported. Short factual claims (e.g.
"Knows Python.") often share only 1 meaningful token with a fully supporting
context (e.g. "python expert"), so they always fail this threshold and get
scored as unsupported -- even when they're correct. Expected behavior: a
short claim with strong single-token overlap (especially on a distinctive,
non-generic term) should be able to score as supported. Actual behavior:
any claim with fewer than 2 overlapping tokens is unconditionally scored
unsupported, producing false negatives and dragging faithfulness scores to
0.0 for otherwise-correct short feedback.

### Map
- rag/evaluator/faithfulness_checker.py -- contains _is_supported() and
  the overlap-counting logic; this is the primary file to change
- tests/unit/test_faithfulness_checker.py -- contains the three currently
  failing tests (test_partial_support_returns_middle_score,
  test_multiple_context_chunks, test_multiple_claims_varying_support)
  that should pass once the fix is in
- [confirm] any tokenizer/stopword-list helper file, if overlap counting
  relies on a shared utility elsewhere in rag/evaluator/ or rag/utils/

### Plan
1. Read _is_supported() fully and confirm exactly how the 2-token
   threshold is applied (hardcoded constant vs. computed threshold)
2. Adjust the overlap requirement to scale with claim length -- e.g.
   require overlap of min(2, len(non_stopword_tokens)) tokens instead of
   a flat 2, so 1-token claims can pass on a single strong match
3. Re-run the three named failing tests and confirm they pass
4. Re-run repro_152.py and confirm it now returns a supported score
   instead of 0.0
5. Check other existing passing tests in the same file still pass, to
   confirm the change doesn't loosen the check too far (e.g. no false
   positives on genuinely unsupported short claims)

### Inputs & outputs
Input: a claim string and a list of context chunks (dicts with a
text field). Output: a faithfulness score/classification indicating
whether the claim is supported. The fix changes only how the
supported/unsupported decision is computed for short claims -- it doesn't
change the function signature or the overall scoring pipeline.

### Risks & unknowns
- Loosening the threshold for short claims could increase false positives
  (marking genuinely unsupported short claims as supported) -- need to test
  against a clearly-unsupported short claim, not just the ones in the bug
  report, to make sure the fix doesn't overcorrect
- [confirm] whether the 2-token threshold is used anywhere else in the
  codebase (e.g. reused by a different checker) -- a shared helper function
  would mean this fix affects more than just this one class
- Unsure yet whether "claim length" should be measured in raw tokens or
  non-stopword tokens only -- need to look at how stopwords are defined to
  avoid an off-by-one when scaling the threshold

### Edge cases
- A claim with exactly 1 non-stopword token that has zero overlap with any
  context (genuinely unsupported) -- should still score unsupported
- A claim with 0 non-stopword tokens (e.g. just punctuation or stopwords)
  -- need to confirm this doesn't divide-by-zero or crash
- Multiple context chunks where a short claim overlaps partially with more
  than one chunk -- confirm scoring picks the best match rather than
  summing/double-counting
- Very long claims, to confirm the existing 2-token threshold behavior is
  preserved for cases where it already worked correctly
