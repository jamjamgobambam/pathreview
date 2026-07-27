## Solution plan

**Issue:** Faithfulness checker can never mark short claims as supported (#152)
https://github.com/ascherj/pathreview/issues/152

### Understand

_is_supported() requires at least 2 non-stopword tokens to overlap between a claim and its context before counting it as supported. Short factual claims ("Knows Python") only ever have 1-2 content words total, so they can never reach that bar even when fully correct, pulling whole feedback scores to 0.0. Confirmed locally: 3 tests fail exactly this way(test_partial_support_returns_middle_score, test_multiple_context_chunks, test_multiple_claims_varying_support).

While reproducing, I also found tokens aren't stripped of punctuation before comparison, so list-style claims like "Python, JavaScript, and Docker" lose real matches ("python," != "python"). This quietly kills 2 of 3 expected matches in test_multiple_context_chunks, before the threshold rule even applies.

### Map
- rag/evaluator/faithfulness_checker.py — _is_supported() (core fix), check() (aggregation, may need updating too)
- tests/unit/test_faithfulness_checker.py — 3 failing tests define target behavior; ~18 passing tests define what must NOT break

### Plan

1. Strip punctuation before tokenizing both claim and context in _is_supported()

2. Scale the overlap requirement to the claim's own meaningful-token count instead of a flat "always need 2", so a 1-2 word claim needs less overlap to count as supported

3. Decide whether _is_supported() stays boolean or returns a partial score, since some failing tests expect scores in the 0.2-0.8 range, not just 0.0/1.0. If it becomes a score, check() needs to average scores instead of counting booleans

4. Re-run the 3 target tests plus the full suite (pytest tests/unit/test_faithfulness_checker.py -v) to confirm the fix works and nothing that currently passes breaks

5. Add a regression test for the punctuation case specifically, since none of the existing tests isolate it

### Inputs & outputs

**Input:** a claim string + concatenated context string.
**Output:** currently bool (True/False). Likely needs to become a float support score per claim, which check() then averages across all claims for the final 0.0-1.0 result.

### Risks & unknowns

- Scaling the threshold down for short claims could reintroduce false positives on generic overlapping words. Example: "This developer is an expert in Rust..." vs. context about "The developer has Python..." only share the word "developer", but that's currently correctly scored as unsupported because it can't clear 2. A threshold of 1 would wrongly pass it.
- Unclear if support should stay boolean or move to continuous scoring, this changes check()'s aggregation logic, not just _is_supported()
- Must confirm the fix doesn't change currently-passing tests, especially test_feedback_fully_supported_by_context and test_is_supported_without_keywords

### Edge cases
- Claim with exactly 1 meaningful token vs. a context with only 1 coincidental (non-supporting) matching word
- Claims with commas/lists where punctuation sits directly against words
- A claim whose only "meaningful" tokens are generic/reused words that appear in unrelated contexts (the "developer" example above)