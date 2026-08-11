## Solution plan

**Issue:** [Architecture doc doesn't explain the hybrid retrieval scoring formula — #36](https://github.com/ascherj/pathreview/issues/36)

### Understand

PathReview's architecture documentation explains that hybrid retrieval combines semantic vector search with BM25 keyword search, but it does not explain how the scores are normalized or combined. The implementation in `rag/retriever/hybrid.py` normalizes each result's vector and keyword score against the highest score returned by the corresponding retriever. It then calculates a weighted sum using default weights of 0.7 for vector retrieval and 0.3 for keyword retrieval.

The expected behavior is for `docs/ARCHITECTURE.md` to accurately explain the implemented scoring process, including normalization, default weights, treatment of results that appear in only one retriever, score filtering, and a worked numerical example. The current behavior is that readers are told the scores are blended but are not given enough information to reproduce or reason about the ranking.

### Map

The following files are involved in understanding the issue:

* `docs/ARCHITECTURE.md`

  * The documentation file that will be updated.
* `rag/retriever/hybrid.py`

  * Defines score normalization, default weights, weighted blending, minimum-score filtering, sorting, and result limits.
* `rag/retriever/vector_store.py`

  * Shows how ChromaDB distances are converted into vector similarity scores.
* `rag/retriever/keyword_search.py`

  * Shows that keyword relevance is calculated using BM25 scores.

I expect to modify only:

* `docs/ARCHITECTURE.md`

I may update `PLAN.md` or `JOURNAL.md` as my understanding changes, but no production code should be required for this issue.

### Plan

1. Locate the existing hybrid retrieval section in `docs/ARCHITECTURE.md` and determine the most appropriate location for the scoring explanation.
2. Document how the vector retriever converts a returned distance into a similarity score using `1 / (1 + distance)`.
3. Explain how vector and BM25 scores are normalized by dividing each score by the highest score returned by its respective retrieval method.
4. Add the weighted hybrid scoring formula and document the default vector weight of 0.7 and keyword weight of 0.3.
5. Add a worked numerical example and explain how missing retriever scores, the minimum-score threshold, sorting, and the result limit affect the final output.
6. Review the documentation against the implementation and run the project's documentation or formatting checks before submitting the pull request.

### Inputs & outputs

The scoring process takes the following inputs:

* A query string.
* A query embedding.
* Results returned by vector search.
* Results returned by BM25 keyword search.
* Configurable vector and keyword weights.
* A minimum accepted score.
* A maximum number of chunks to return.

The documentation change should produce:

* A clear explanation of vector-score conversion.
* The vector and keyword normalization formulas.
* The weighted hybrid scoring formula.
* The default weights of 0.7 and 0.3.
* An explanation of how chunks appearing in only one result set are scored.
* A worked example showing normalization and weighted blending.
* An explanation of score filtering, descending sorting, and the maximum-result limit.

The fix should not alter runtime behavior or modify retrieval code.

### Risks & unknowns

* The vector collection is configured to use cosine distance, while a comment in `rag/retriever/vector_store.py` refers generally to Euclidean distance. The documentation should avoid describing the distance as Euclidean unless the implementation or maintainers confirm that wording.
* BM25 scores can theoretically be zero or negative depending on the corpus and query. The current normalization logic only checks whether the maximum score is greater than zero, so the documentation should describe the implemented behavior without claiming that BM25 scores are always positive.
* The vector and keyword weights are configurable and are not explicitly validated to sum to 1. The documentation should describe 0.7 and 0.3 as defaults rather than stating that all valid configurations must total 1.
* `HybridRetriever.retrieve()` fetches all chunks but does not index them inside that method. Keyword indexing may happen elsewhere in the application. This behavior is outside the scope of the documentation issue unless it affects the accuracy of the architecture explanation.
* The existing architecture document may already use terminology that should be preserved for consistency.

### Edge cases

* A chunk appears in vector results but not keyword results. Its keyword score is treated as zero.
* A chunk appears in keyword results but not vector results. Its vector score is treated as zero.
* One of the retrievers returns no results.
* The maximum score from a retrieval method is zero, causing normalized scores for that method to remain zero.
* A blended score falls below the default minimum score of 0.3 and is removed.
* More qualifying chunks are produced than the default maximum of 10, so only the highest-scoring chunks are returned.
* Custom weights are supplied instead of the default 0.7 and 0.3 values.
