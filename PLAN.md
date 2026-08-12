## Solution plan

**Issue:** Explain hybrid retrieval scoring logic in `docs/ARCHITECTURE.md` — https://github.com/ascherj/pathreview/issues/36

### Understand

The RAG System section in `docs/ARCHITECTURE.md` states that the application uses hybrid retrieval by combining vector similarity and BM25 keyword retrieval. However, it does not explain the scoring formula, the default weights, the normalization process, or provide a worked example.

The expected documentation should explain that vector and BM25 scores are normalized separately and then combined using a weighted sum. The default weights are 0.7 for vector similarity and 0.3 for BM25 keyword relevance.

The current documentation does not provide enough information for a reader to understand or reproduce the final ranking score.

### Map

Files and modules involved:

- `docs/ARCHITECTURE.md` — contains the incomplete hybrid retrieval description and will be updated.
- `rag/hybrid.py` — contains the hybrid retrieval logic, score normalization, default weights, filtering, and sorting.
- `rag/vector_store.py` — converts ChromaDB distance values into vector similarity scores.
- `rag/keyword_search.py` — calculates and returns BM25 keyword scores.

The primary file expected to change is:

- `docs/ARCHITECTURE.md`

The files in `rag/` will be used as the source of truth but are not expected to require changes.

### Plan

1. Document how `rag/vector_store.py` converts vector distance into a similarity score using `1 / (1 + distance)`.
2. Explain how `rag/hybrid.py` normalizes vector and BM25 scores by dividing each score by the maximum score returned by its retrieval method.
3. Add the weighted scoring formula to `docs/ARCHITECTURE.md`, using the default weights of 0.7 for vector similarity and 0.3 for BM25 relevance.
4. Add a worked numerical example showing how normalized vector and keyword scores produce a final hybrid score.
5. Review the new documentation against `rag/hybrid.py`, `rag/vector_store.py`, and `rag/keyword_search.py` to confirm accuracy.

### Inputs & outputs

The hybrid retrieval process takes:

- a text query
- a query embedding
- vector similarity search results
- BM25 keyword search results
- a vector weight, defaulting to 0.7
- a keyword weight, defaulting to 0.3
- a minimum score threshold, defaulting to 0.3
- a maximum number of chunks, defaulting to 10

The retrieval process produces a ranked list of chunks containing:

- the chunk ID
- chunk text
- metadata
- final blended score
- normalized vector score
- normalized keyword score

The documentation change should produce a clear explanation of the formula, defaults, normalization process, and a complete example.

### Risks & unknowns

- Vector and BM25 scores use different numerical scales, so the documentation must clearly explain that they are normalized separately.
- The vector store collection uses cosine space, while a comment in `rag/vector_store.py` states that ChromaDB distances are Euclidean by default. The documentation should describe the implemented conversion without making unsupported claims about the exact distance type.
- The weights can be overridden when `HybridRetriever` is created, so the documentation must distinguish default values from required values.
- The code does not verify that the two weights add up to 1.0.
- Normalization depends on the maximum score in the current result set, so normalized scores may change depending on which documents are returned.
- Results with a final score below the default minimum threshold of 0.3 are removed.

### Edge cases

The documentation should account for:

- no vector search results
- no keyword search results
- a maximum vector or keyword score of zero
- a document appearing in only one retrieval method
- one component receiving a weight of zero
- custom weights that do not add up to 1.0
- documents with equal blended scores
- blended scores below the minimum threshold