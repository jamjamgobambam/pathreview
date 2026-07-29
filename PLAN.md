## Solution plan

**Issue:** [Relevance scorer “partial overlap” test fixture actually has full query overlap](https://github.com/ascherj/pathreview/issues/157)

### Understand

`RelevanceScorer.score()` tokenizes the query and each chunk, then divides the
number of matching unique query tokens by the number of unique query tokens.
The query in `test_query_with_partial_overlap` contains four tokens, and the
original chunk contains all four, so the actual and correct score is `1.0`.
The test expects a partial-match score between `0.3` and `0.9`, so the fixture—not
the scoring implementation—is the root cause. The expected behavior is for the
chunk to contain only some of the query tokens and produce a middle-range score.

### Map

Files involved:

- `tests/unit/test_relevance_scorer.py`
  - `TestRelevanceScorer.test_query_with_partial_overlap`
- `rag/evaluator/relevance_scorer.py`
  - `RelevanceScorer.score()` provides the behavior being tested but should not
    require modification.

### Plan

1. Preserve the four-token query so the test remains easy to understand.
2. Change the chunk fixture to retain `Python` and `Django` while omitting the
   query terms `web` and `framework`.
3. Confirm the scorer returns `0.5`, representing two matching tokens out of
   four unique query tokens.
4. Run `pytest tests/unit/test_relevance_scorer.py -q` and confirm the partial
   overlap assertion and the rest of the scorer tests pass.
5. Review the diff to ensure no production scoring behavior changed.

### Inputs & outputs

The test passes the query `"Python Django web framework"` and a single chunk
dictionary containing natural-language text. The revised fixture should match
exactly two of the four unique query tokens, causing `score()` to return `0.5`.
The test file should pass without changes to `RelevanceScorer`.

### Risks & unknowns

- Adding either `web` or `framework` back to the chunk would raise the score to
  `0.75`, which still passes but makes the intended 50% overlap less explicit.
- Punctuation is not stripped by `_tokenize()`, so punctuation attached to a
  query word could accidentally turn an intended match into a non-match.
- The focused test requires `pytest` and `structlog` in the local environment.
- No production-code changes are expected; a production change would expand
  the issue beyond its stated scope.

### Edge cases

- The revised chunk should continue to demonstrate case-insensitive matching.
- Extra non-query words in the chunk must not affect the coverage calculation.
- Empty queries and chunks, zero overlap, full overlap, and multiple chunks are
  already covered by neighboring tests and should remain unchanged.
