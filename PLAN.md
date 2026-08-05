Solution plan

Issue: Faithfulness checker can never mark short claims as supported

Understand

The faithfulness checker extracts claims from generated feedback and determines whether each claim is supported by the retrieved context. The current implementation requires at least two meaningful overlapping words before a claim can be marked as supported.

This causes short factual claims such as “Knows Python” or “Knows SQL” to fail even when the context clearly contains matching evidence such as “python expert” or “sql expert.” The direct reproduction returned a score of 0.0, and several existing unit tests also fail with the same behavior.

The reproduction log also showed claims_count=1 for the input “Knows Python. Knows SQL.” This suggests that claim extraction may also be filtering or combining short sentences, so both claim extraction and support matching need to be investigated before changing the implementation.

Map

The main files and functions involved are:

rag/evaluator/faithfulness_checker.py

check() calculates the final faithfulness score.

_extract_claims() determines which sentences count as claims.

_is_supported() checks meaningful token overlap between a claim and the context.

tests/unit/test_faithfulness_checker.py

Contains tests for fully supported, partially supported, and unsupported claims.

Contains the failing partial-support, multiple-context, and varying-support test cases.

Will likely need new or updated tests for short supported claims.

I expect the main implementation change to stay inside rag/evaluator/faithfulness_checker.py, with test updates in tests/unit/test_faithfulness_checker.py.

Plan

Inspect _extract_claims() to determine why “Knows Python. Knows SQL.” is logged as only one extracted claim.

Inspect _is_supported() and confirm how the minimum two-token overlap causes short claims to fail.

Update the support logic so short factual claims can be supported by one meaningful matching token while longer claims continue to require stronger evidence.

Add or update unit tests for fully supported short claims, unsupported short claims, multiple context chunks, and mixed supported and unsupported claims.

Run the focused faithfulness-checker test file and the broader test suite to confirm that the fix does not introduce regressions.

Inputs & outputs

The checker receives:

Generated feedback text containing one or more claims.

A list of context dictionaries containing supporting text.

Example input:

generated_text = "Knows Python. Knows SQL."
contexts = [
    {"text": "python expert"},
    {"text": "sql expert"},
]

Current output:

0.0

Expected behavior:

Both short claims should be recognized as separate claims.

Each claim should be marked as supported because its meaningful term appears in the context.

The final faithfulness score should reflect full support according to the checker’s existing scoring rules.

Unsupported claims with no meaningful overlap should still receive no support.

Risks & unknowns

Lowering the overlap requirement globally from two tokens to one could create false positives for longer or vague claims.

A common single word could appear in both the claim and context without proving that the entire claim is supported.

_extract_claims() may have a minimum-length rule that removes short but valid claims.

Changing claim extraction could affect the number of claims used to calculate scores in existing tests.

Changes in rag/evaluator/faithfulness_checker.py could alter expected scores in other parts of the application.

The separate None context failure should not be included in Issue #152 unless the issue scope or instructor guidance allows it.

Edge cases

The fix should handle:

A short claim with one meaningful token that clearly appears in the context.

A short claim whose meaningful token does not appear in any context.

Multiple short claims supported by separate context chunks.

A mixture of supported and unsupported claims.

Claims containing only stopwords or punctuation.

Empty generated text.

Empty context lists.

Case differences such as Python versus python.

Repeated words in a claim or context.

Longer claims that share only one weak or incidental token with the context.

Short claims separated by periods that should be extracted as separate claims.