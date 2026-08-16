## Solution plan

**Issue:** Hybrid retriever over-weights keyword results when query contains technology names [https://github.com/ascherj/pathreview/issues/24]

### Understand
The hybrid retriever combines normalized vector similarity and BM25 keyword scores. A chunk containing repeated technology keywords such as “Python” can receive a large keyword boost and rank above a chunk that is more semantically relevant to the user’s query.

The expected behavior is for semantically relevant chunks to rank above unrelated chunks that only share common technology terms. The actual behavior is that a weaker or keyword-only result can outrank a stronger semantic result after the vector and keyword scores are combined.

The issue appears to be in the score normalization and weighted blending logic inside HybridRetriever.retrieve().

One discrepancy is that the issue description says the retriever uses equal vector and keyword weights, but the current `HybridRetriever` constructor defaults to `0.7` for vector search and `0.3` for keyword search. Even with these unequal weights, the reproduction tests show that normalized keyword scores can still cause less relevant chunks to rank too highly.

### Map
### Map

The main scoring logic is located in:

* `rag/retriever/hybrid.py`

  * `HybridRetriever.__init__()` defines the vector and keyword weights.
  * `HybridRetriever.retrieve()` normalizes the vector and BM25 scores, combines them, sorts the results, and applies the minimum-score filter.

The reproduction and regression tests are located in:

* `tests/unit/test_hybrid.py`

  * Contains tests showing that keyword-only or keyword-boosted chunks can outrank stronger semantic matches.
  * These tests will be updated or extended to verify that the final scoring change fixes the issue without breaking existing behavior.

I currently expect to modify only `rag/retriever/hybrid.py` and `tests/unit/test_hybrid.py`. Other retriever files may be reviewed for context, but they should not need changes unless further investigation reveals that the raw scores are produced incorrectly.

### Plan
1. Review the current normalization and blending logic in HybridRetriever.retrieve() and trace how each vector and BM25 score contributes to the final score.
2. Compare possible score-combination strategies, including:
    * weighted rank-based fusion, where vector ranking has more influence than BM25 ranking;
    * capping or saturating the BM25 contribution;
    * reducing the keyword boost for chunks with weak or missing vector relevance.
3. Select the smallest approach that prevents common technology keywords from overpowering semantic relevance while still preserving useful exact-keyword matches.
4. Implement the selected scoring change in rag/retriever/hybrid.py.
5. Run the tests in tests/unit/test_hybrid.py and confirm that:
    * the two reproduced ranking failures pass;
    * chunks found by both retrievers still receive a useful boost;
    * empty results, min_score, and max_chunks still work correctly.
6. Run the broader retriever test suite to check for regressions before finalizing the implementation.

### Inputs & outputs
The retriever takes the following inputs:
* text query;
* a profile or collection identifier;
* a query embedding;
* vector search results containing similarity scores;
* BM25 search results containing keyword scores;
* optional values such as max_chunks and min_score.

The retriever should produce:

* one merged list of unique chunks;
* chunks ordered by overall relevance;
* semantically relevant chunks ranked above unrelated keyword-only matches;
* an additional benefit for chunks that are relevant in both vector and keyword search;
* no more than the requested number of chunks;
* no results below the configured minimum score.

### Risks & unknowns
* The issue description says equal weights are used, but the implementation currently uses 0.7 for vector search and 0.3 for keyword search. I still need to confirm whether another part of the application overrides these defaults.
* Weighted rank-based fusion would avoid comparing raw score scales directly, but it may be a larger change than necessary.
* Capping or saturating BM25 scores requires selecting and justifying a threshold or constant.
* Penalizing keyword-only results too strongly could hurt queries where exact keyword matching is important.
* A solution that passes the current reproduction tests may still behave differently with real vector and BM25 result distributions.
* The final approach may require testing several queries and score combinations before choosing appropriate weights or constants.

### Edge cases
The fix should handle:

* no vector results;
* no keyword results;
* no results from either retriever;
* a chunk found only by vector search;
* a chunk found only by keyword search;
* a chunk found by both retrievers;
* repeated technology terms such as “Python Python Python”;
* very large BM25 scores;
* equal final scores;
* duplicate chunk IDs across both result lists;
* results below min_score;
* max_chunks values smaller than the number of available results;
* zero or missing score values.

