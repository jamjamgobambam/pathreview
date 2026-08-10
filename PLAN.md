## Solution plan

**Issue:** [Relevance scorer “partial overlap” test fixture actually has full query overlap #157](https://github.com/ascherj/pathreview/issues/157)

### Understand

The issue is in the test fixture for `test_query_with_partial_overlap`.

The query is `"Python Django web framework"`, and the test chunk is `"Django is a Python web framework for rapid development"`. Because the chunk contains all four query terms, the relevance scorer returns `1.0`.

The scorer is behaving correctly. The problem is that the test data represents full overlap even though the test is supposed to measure partial overlap.

Expected behavior: the test chunk should contain only some of the query terms and return a score between the zero-overlap and full-overlap results.

Actual behavior: the chunk contains all query terms, so the score is `1.0`, which fails the assertion `0.3 < score < 0.9`.

### Map

The main file involved is:

- `tests/unit/test_relevance_scorer.py`
  - Contains `TestRelevanceScorer`
  - Contains `test_query_with_partial_overlap`
  - Contains the incorrect query and chunk fixture
  - Contains the failing score assertion

The scoring implementation is located in:

- `rag/evaluator/relevance_scorer.py`
  - Contains the `RelevanceScorer` class
  - Contains the `score` method used by the test

I expect the fix to modify only:

- `tests/unit/test_relevance_scorer.py`

The implementation file should only be reviewed to confirm the current behavior and should not need to be changed.

### Plan

1. Inspect `test_query_with_partial_overlap` and compare it with the perfect-match and zero-overlap tests.

2. Review `rag/evaluator/relevance_scorer.py` to confirm how query terms are tokenized and how overlap affects the final score.

3. Update the chunk in `test_query_with_partial_overlap` so that it contains only some of the query terms instead of all four.

4. Run the single affected test and verify that the score falls inside the expected partial-overlap range.

5. Run the complete `tests/unit/test_relevance_scorer.py` file to confirm that all relevance scorer tests pass and no regressions are introduced.

### Inputs & outputs

**Inputs:**

- Query: `"Python Django web framework"`
- A chunk containing only some of the query terms
- The relevance scorer's keyword-matching logic

**Expected output:**

- A floating-point relevance score between `0.0` and `1.0`
- A partial-overlap score greater than `0.3` and less than `0.9`
- A passing `test_query_with_partial_overlap`
- No failures in the other relevance scorer unit tests

The fix should only change the test fixture and should not change the behavior or public interface of the relevance scorer.

### Risks & unknowns

- Removing too many query terms may cause the score to fall below `0.3`.
- Leaving too many matching terms may keep the score above `0.9`.
- The scorer may consider tokenization, punctuation, or common words in ways that affect the final score.
- A replacement chunk could accidentally duplicate the purpose of the perfect-match or zero-overlap tests.
- I need to confirm whether the current score range is appropriate after the fixture is corrected.
- The pre-commit hook is currently failing locally because of a corrupted virtualenv cache, so documentation commits may require `--no-verify` until the environment issue is repaired.

### Edge cases

The corrected test should remain distinct from these cases:

- All query terms appear in the chunk
- No query terms appear in the chunk
- Only one query term appears in the chunk
- Query terms use different capitalization
- Query terms contain punctuation
- Query terms are repeated
- The query is empty
- The chunk text is empty
- The chunk is missing the `text` key
- The chunk has high semantic similarity but only partial exact keyword overlap## Solution plan

**Issue:** [Relevance scorer “partial overlap” test fixture actually has full query overlap #157](https://github.com/ascherj/pathreview/issues/157)

### Understand

The issue is in the test fixture for `test_query_with_partial_overlap`.

The query is `"Python Django web framework"`, and the test chunk is `"Django is a Python web framework for rapid development"`. Because the chunk contains all four query terms, the relevance scorer returns `1.0`.

The scorer is behaving correctly. The problem is that the test data represents full overlap even though the test is supposed to measure partial overlap.

Expected behavior: the test chunk should contain only some of the query terms and return a score between the zero-overlap and full-overlap results.

Actual behavior: the chunk contains all query terms, so the score is `1.0`, which fails the assertion `0.3 < score < 0.9`.

### Map

The main file involved is:

- `tests/unit/test_relevance_scorer.py`
  - Contains `TestRelevanceScorer`
  - Contains `test_query_with_partial_overlap`
  - Contains the incorrect query and chunk fixture
  - Contains the failing score assertion

The scoring implementation is located in:

- `rag/evaluator/relevance_scorer.py`
  - Contains the `RelevanceScorer` class
  - Contains the `score` method used by the test

I expect the fix to modify only:

- `tests/unit/test_relevance_scorer.py`

The implementation file should only be reviewed to confirm the current behavior and should not need to be changed.

### Plan

1. Inspect `test_query_with_partial_overlap` and compare it with the perfect-match and zero-overlap tests.

2. Review `rag/evaluator/relevance_scorer.py` to confirm how query terms are tokenized and how overlap affects the final score.

3. Update the chunk in `test_query_with_partial_overlap` so that it contains only some of the query terms instead of all four.

4. Run the single affected test and verify that the score falls inside the expected partial-overlap range.

5. Run the complete `tests/unit/test_relevance_scorer.py` file to confirm that all relevance scorer tests pass and no regressions are introduced.

### Inputs & outputs

**Inputs:**

- Query: `"Python Django web framework"`
- A chunk containing only some of the query terms
- The relevance scorer's keyword-matching logic

**Expected output:**

- A floating-point relevance score between `0.0` and `1.0`
- A partial-overlap score greater than `0.3` and less than `0.9`
- A passing `test_query_with_partial_overlap`
- No failures in the other relevance scorer unit tests

The fix should only change the test fixture and should not change the behavior or public interface of the relevance scorer.

### Risks & unknowns

- Removing too many query terms may cause the score to fall below `0.3`.
- Leaving too many matching terms may keep the score above `0.9`.
- The scorer may consider tokenization, punctuation, or common words in ways that affect the final score.
- A replacement chunk could accidentally duplicate the purpose of the perfect-match or zero-overlap tests.
- I need to confirm whether the current score range is appropriate after the fixture is corrected.
- The pre-commit hook is currently failing locally because of a corrupted virtualenv cache, so documentation commits may require `--no-verify` until the environment issue is repaired.

### Edge cases

The corrected test should remain distinct from these cases:

- All query terms appear in the chunk
- No query terms appear in the chunk
- Only one query term appears in the chunk
- Query terms use different capitalization
- Query terms contain punctuation
- Query terms are repeated
- The query is empty
- The chunk text is empty
- The chunk is missing the `text` key
- The chunk has high semantic similarity but only partial exact keyword overlap
