## Solution plan

**Issue:** Faithfulness checker can never mark short claims as supported
https://github.com/ascherj/pathreview/issues/152

### Understand
`_is_supported()` in rag/evaluator/faithfulness_checker.py requires
len(meaningful_overlap) >= 2 -- at least 2 non-stopword tokens must overlap
between a claim and the concatenated context text before a claim is marked
supported. Short factual claims (e.g. "Knows Python") often share only 1
meaningful token with a fully supporting context (e.g. "python expert"), so
they always fail this hardcoded threshold and are scored unsupported even
when correct. Expected behavior: a short claim with strong single-token
overlap on a distinctive term should be able to score as supported. Actual
behavior: any claim under the 2-token threshold is unconditionally
unsupported, dragging faithfulness scores toward 0.0 for short, valid
feedback.

Additionally, reproduction surfaced a related issue in _extract_claims():
it filters out any sentence with len(s.strip()) <= 10 characters. In the
repro case ("Knows Python. Knows SQL."), "Knows SQL" (9 chars) is silently
dropped before scoring even begins, which is why only 1 claim was counted
instead of 2. This is a separate bug from the one reported in #152 and is
noted here as a related risk, not something this fix will change unless
scoped in.

### Map
- rag/evaluator/faithfulness_checker.py -- contains _is_supported()
  (the overlap threshold to fix) and _extract_claims() (the related
  length-filter issue, noted but out of scope for this fix)
- tests/unit/test_faithfulness_checker.py -- contains the three currently
  failing tests (test_partial_support_returns_middle_score,
  test_multiple_context_chunks, test_multiple_claims_varying_support)
  that should pass once the fix is in

### Plan
1. Confirm via tests that the fix should target the hardcoded
   `>= 2` in _is_supported(), scoped only to that method
2. Change the threshold to scale with claim length -- e.g.
   min(2, len(claim_tokens - stop_words)) instead of a flat 2, so a
   1-meaningful-token claim can pass on a single strong match
3. Re-run the three named failing tests and confirm they pass
4. Re-run repro_152.py and confirm it returns a supported score instead
   of 0.0
5. Run the full test_faithfulness_checker.py suite to confirm no
   previously-passing tests regress (i.e. no new false positives on
   genuinely unsupported short claims)

### Inputs & outputs
Input: a claim string and a list of context chunks (dicts with a text
field), consumed by _is_supported(claim, context) as a string pair.
Output: a boolean supported/unsupported per claim, which check() converts
into a 0.0-1.0 faithfulness ratio. The fix changes only the threshold
logic inside _is_supported() -- it doesn't change check()'s signature,
_extract_claims(), or the overall scoring pipeline.

### Risks & unknowns
- Loosening the threshold for short claims could increase false positives
  on genuinely unsupported short claims -- need a test case with a short
  claim that shares 1 token with context but is NOT actually supported,
  to confirm the fix doesn't overcorrect
- The related _extract_claims() length filter (dropping claims <=10 chars)
  affects the repro's claim count and could mask or interact with test
  results if not accounted for -- flagging it, not fixing it, unless the
  issue scope is confirmed to include it
- Need to decide whether "claim length" for the scaled threshold should be
  measured in raw tokens or only non-stopword tokens, to avoid an
  off-by-one when very short claims are entirely stopwords

### Edge cases
- A claim with exactly 1 non-stopword token with zero context overlap
  (genuinely unsupported) -- should still score unsupported
- A claim with 0 non-stopword tokens (e.g. all stopwords) -- confirm
  meaningful_overlap and the scaled threshold don't produce a
  divide-by-zero or a false "supported" result
- Claims under the 10-character _extract_claims() filter (like "Knows
  SQL") -- confirmed these are dropped before scoring; noted as a known
  gap, not silently patched
- Multiple context chunks where a short claim partially overlaps more
  than one chunk -- confirm the concatenated-context approach still
  works correctly with the new threshold
- Longer claims (3+ meaningful tokens) -- confirm existing correct
  behavior is preserved and not affected by the scaled threshold
