## Solution plan

**Issue:** [Relevance scorer “partial overlap” test fixture actually has full query overlap](https://github.com/ascherj/pathreview/issues/157)

### Understand

`RelevanceScorer.score()` finds all four query terms in the fixture, so it returns 1.0 instead of a partial-overlap score.

### Map

- `tests/unit/test_relevance_scorer.py` — `test_query_with_partial_overlap()`

### Plan

1. Remove one query term from the fixture text.
2. Run the relevance scorer tests.
3. Confirm all 19 tests pass.

### Inputs & outputs

The query and chunk should produce a score between 0.3 and 0.9 without changing the scorer.

### Risks & unknowns

In `tests/unit/test_relevance_scorer.py`, the revised text must keep exactly three of the four query terms.

### Edge cases

Zero overlap and full overlap must remain unchanged.
