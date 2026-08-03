# Issue #157 Solution Plan

## Solution plan

**Issue:** [Relevance scorer “partial overlap” test fixture actually has full query overlap](https://github.com/ascherj/pathreview/issues/157)

### Understand

`RelevanceScorer.score()` tokenizes the query and chunk, converts both token
lists to sets, and divides the number of shared tokens by the number of unique
query tokens. The test query contains four tokens—`python`, `django`, `web`,
and `framework`—and the current chunk contains all four, so the actual score
is correctly `4 / 4 = 1.0`. The test describes this input as partial overlap
and expects a score below `0.9`, which conflicts with the data it supplies.
The expected behavior is for the fixture to share only some query tokens and
produce a score strictly between `0.3` and `0.9`.

### Map

- `tests/unit/test_relevance_scorer.py`
  - Update `TestRelevanceScorer.test_query_with_partial_overlap` so its fixture
    represents genuine partial keyword overlap.
- `rag/evaluator/relevance_scorer.py`
  - Review `RelevanceScorer.score()` and `_tokenize()` to confirm the expected
    score, but do not change them unless new evidence shows an implementation
    defect.
- `REPRODUCTION.md`
  - Keep as the recorded baseline demonstrating the original failure.

### Plan

1. Choose fixture text that includes exactly two of the query's four unique
   tokens, producing a deterministic relevance score of `0.5`.
2. Change only the chunk text in
   `test_query_with_partial_overlap`; retain the existing type, range, and
   partial-overlap assertions.
3. Run the targeted test to confirm it changes from failing at `1.0` to
   passing with a middle-range score.
4. Run the complete `tests/unit/test_relevance_scorer.py` file to check that
   the fixture change does not affect the other relevance scenarios.
5. Run the repository's relevant formatting and lint checks, then review the
   final diff to ensure no production scoring logic changed.

### Inputs & outputs

The input remains the query `Python Django web framework` and one chunk of
text. The revised chunk should contain exactly two unique query tokens, such
as `Python` and `Django`, while omitting `web` and `framework`. The scorer
should output `0.5`, which is within the test's required `0.3 < score < 0.9`
range, and the test should pass without changing application behavior.

### Risks & unknowns

- Accidentally retaining all four query tokens in the new fixture would
  preserve the original failure. I will calculate the token intersection
  explicitly before running the test.
- Using only one shared token would yield `0.25`, which would fail the lower
  bound. The fixture therefore needs at least two, but fewer than four,
  shared tokens.
- Punctuation is not stripped by `_tokenize()` in
  `rag/evaluator/relevance_scorer.py`; punctuation attached to a word could
  unintentionally prevent a match. The revised fixture will use plain,
  whitespace-separated words for the intended shared tokens.
- Changing `RelevanceScorer.score()` would expand the scope and could affect
  other tests. Current evidence indicates no production-code change is needed.

### Edge cases

- Zero shared query tokens should continue producing `0.0`.
- One of four shared tokens produces `0.25` and is not suitable for this
  test's asserted middle range.
- Two or three of four shared tokens produce `0.5` or `0.75`, respectively,
  and both represent valid partial overlap.
- All four shared tokens produce `1.0` and must not be used by this fixture.
- Repeated words should not inflate the score because the implementation uses
  token sets.
- Capitalization should not affect overlap because `_tokenize()` lowercases
  both inputs.
