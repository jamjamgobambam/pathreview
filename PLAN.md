# Solution plan

**Issue:** Relevance scorer "partial overlap" test fixture actually has full query overlap

https://github.com/ascherj/pathreview/issues/157

## Understand

The unit test `test_query_with_partial_overlap` is intended to verify behavior when only some query terms appear in a document chunk. However, the current fixture contains all of the query terms, so the relevance scorer correctly returns a score of 1.0. The failing assertion is caused by incorrect test data rather than a bug in the scoring algorithm.

## Map

Expected files to examine:

- tests/unit/test_relevance_scorer.py
- relevance scorer implementation (only if needed to confirm expected behavior)

Primary file expected to change:

- tests/unit/test_relevance_scorer.py

## Plan

1. Run the failing unit test to reproduce the issue.
2. Locate `test_query_with_partial_overlap` and inspect the query and fixture text.
3. Modify the fixture so that it contains only a subset of the query terms.
4. Re-run the unit test to verify the assertion passes.
5. Run any related relevance scorer tests to ensure no other tests are affected.

## Inputs & outputs

### Input

- Query text
- Test fixture text
- Existing relevance scoring function

### Output

- Updated unit test fixture representing true partial overlap
- Passing unit test without changing the scoring algorithm

## Risks & unknowns

- The scorer may intentionally normalize scores differently than expected, so I want to verify that only the fixture—not the production code—needs modification.
- Other tests in `tests/unit/test_relevance_scorer.py` may rely on similar fixture wording, so I will check for consistency after making the change.

## Edge cases

- Query terms all present (full overlap) should continue producing a score of 1.0.
- Only some query terms present should produce a lower relevance score.
- No query terms present should continue producing a very low score.