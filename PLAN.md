## Solution plan

**Issue:** [Relevance scorer “partial overlap” test fixture actually has full query overlap](https://github.com/ascherj/pathreview/issues/157)

### Understand

The failing test is intended to verify that partial keyword overlap produces a relevance score between a zero-overlap score and a full-match score.

The test query is `Python Django web framework`, while the fixture chunk is `Django is a Python web framework for rapid development`. The chunk contains all four meaningful query terms: `python`, `django`, `web`, and `framework`.

Because the fixture represents full query coverage rather than partial overlap, the relevance scorer correctly returns `1.0`. The actual issue is in the test fixture, not necessarily in the production scoring implementation.

The expected behavior is for the fixture to contain only some of the query terms and produce a score satisfying the existing assertion:

`0.3 < score < 0.9`

### Map

The main file expected to change is:

- `tests/unit/test_relevance_scorer.py`
  - `TestRelevanceScorer.test_query_with_partial_overlap`

The production implementation should be reviewed to confirm the scoring behavior, but it is not expected to change:

- `rag/evaluator/relevance_scorer.py`
  - `RelevanceScorer.score`
  - `RelevanceScorer._tokenize`

No frontend, API, database, migration, or configuration files are expected to change.

### Plan

1. Review `RelevanceScorer.score` and `RelevanceScorer._tokenize` to confirm how query and chunk tokens are normalized and compared.
2. Update the chunk text in `test_query_with_partial_overlap` so it contains only a subset of the meaningful query terms.
3. Keep the existing assertion `0.3 < score < 0.9` so the test continues to verify a genuine middle-range partial-overlap score.
4. Run the individual failing test to confirm the corrected fixture now passes.
5. Run the full `tests/unit/test_relevance_scorer.py` file and relevant project checks to confirm no other relevance scorer tests regress.

### Inputs & outputs

The test input consists of:

- A query string containing multiple meaningful keywords
- A list containing a chunk dictionary with a `text` field

The corrected fixture should contain some, but not all, query keywords.

The expected output is a floating-point score between `0.0` and `1.0`. For the partial-overlap test specifically, the score should be greater than `0.3` and less than `0.9`.

The final implementation should change only the test fixture and should not alter production scoring behavior unless further investigation reveals an actual implementation defect.

### Risks & unknowns

- A replacement chunk could accidentally still contain every query token.
- A replacement chunk with too little overlap could produce a score of `0.3` or below.
- Token normalization may treat punctuation or capitalization differently than expected.
- Changing the assertion instead of the fixture could weaken the purpose of the test.
- The focused test may pass while another relevance scorer test fails, so the full scorer test file must also be run.
- The repository may contain unrelated failing tests; only failures connected to issue #157 should affect the scope of this fix.

### Edge cases

- The replacement fixture contains zero query terms rather than partial overlap.
- The replacement fixture contains all query terms in a different order.
- Capitalization differences affect matching unexpectedly.
- Punctuation attached to keywords changes tokenization.
- Repeating one matching keyword is mistaken for matching multiple distinct query terms.
- The resulting score is exactly `0.3` or `0.9`, which would fail because the assertion uses strict inequalities.
