## Solution plan

**Issue:** Relevance scorer "partial overlap" test fixture actually has full query overlap ([Issue #157](https://github.com/ascherj/pathreview/issues/157))

### Understand
The root cause is in the unit test fixture, not in `RelevanceScorer.score`. The test named `test_query_with_partial_overlap` expects a middle-range score, but the chunk text contains all four query tokens: `python`, `django`, `web`, and `framework`. Because `RelevanceScorer.score` calculates relevance as `overlap / len(query_tokens)`, the actual score is `4 / 4 = 1.0`, which conflicts with the assertion `0.3 < score < 0.9`.

### Map
The main files involved are:
- `tests/unit/test_relevance_scorer.py`
- `rag/evaluator/relevance_scorer.py`

I expect the actual code change to be limited to `tests/unit/test_relevance_scorer.py`, while `rag/evaluator/relevance_scorer.py` is the reference implementation I will verify against.

### Plan
1. Confirm the intended behavior by tracing how `RelevanceScorer.score` tokenizes the query and chunk text and computes overlap.
2. Replace the current chunk fixture in `test_query_with_partial_overlap` with text that omits at least one query token while still remaining clearly relevant.
3. Re-run the focused relevance scorer unit tests to verify the partial-overlap test now lands in the expected middle range without breaking the nearby scoring tests.
4. Review adjacent tests in `tests/unit/test_relevance_scorer.py` to make sure the new fixture still fits the suite’s assumptions about tokenization and score bounds.

### Inputs & outputs
The fix takes the existing query string and a corrected chunk fixture as input. It should produce a test case where the token overlap is partial rather than complete, causing `RelevanceScorer.score` to return a value strictly between the existing lower and upper bounds in the assertion.

### Risks & unknowns
One risk is choosing a replacement chunk that accidentally still matches every query token because of simple whitespace tokenization in `rag/evaluator/relevance_scorer.py`. Another is selecting a fixture whose score is technically partial but too close to the test boundary, which would make the test fragile if tokenization behavior changes later. I also still need the local Python test environment available to run the focused unit test and verify the exact score instead of relying only on static code tracing.

### Edge cases
The updated fixture should avoid accidental full overlap from punctuation or repeated words, since `_tokenize` currently just lowercases and splits on whitespace. It should also remain semantically relevant enough that the test still represents a real partial match rather than drifting into the "zero overlap" scenario already covered elsewhere in the file.
