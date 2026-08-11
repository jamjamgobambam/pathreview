# Solution plan

**Issue:** [Architecture doc doesn't explain the hybrid retrieval scoring formula](https://github.com/ascherj/pathreview/issues/36)

## Understand

The architecture documentation currently describes hybrid retrieval only as a combination of vector similarity and BM25 keyword search. It does not explain how the two scores are normalized, weighted, blended, filtered, or ranked.

The implementation in `rag/retriever/hybrid.py` normalizes the vector and BM25 scores against the maximum score in each result set. It then calculates a blended score using default weights of 0.7 for vector similarity and 0.3 for keyword relevance. Results below the minimum score threshold are removed, and the remaining results are sorted from highest to lowest blended score.

The expected behavior is for `docs/ARCHITECTURE.md` to clearly explain this process and its default values. The actual behavior is that readers are told which retrieval methods are combined but not how the final ranking is calculated.

## Map

The following files are involved:

- `docs/ARCHITECTURE.md` — the primary file that needs clearer documentation.
- `rag/retriever/hybrid.py` — the source of truth for score normalization, weighting, filtering, and sorting.
- `rag/retriever/vector_store.py` — converts ChromaDB distance values into vector similarity scores.
- `rag/retriever/keyword_search.py` — generates the BM25 keyword scores used by the hybrid retriever.
- `core/config.py` — contains the configured minimum relevance score and should be checked to ensure the documented threshold is accurate.

The expected implementation is documentation-only unless investigation reveals that the documentation and current configuration disagree.

## Plan

1. Review `rag/retriever/hybrid.py`, `rag/retriever/vector_store.py`, `rag/retriever/keyword_search.py`, and `core/config.py` to confirm the current scoring behavior and default values.

2. Add a hybrid retrieval scoring subsection to `docs/ARCHITECTURE.md` that defines the normalized vector score and normalized BM25 score.

3. Document the blended scoring formula:

   `blended_score = (vector_weight * normalized_vector_score) + (keyword_weight * normalized_keyword_score)`

4. Explain the default vector weight of 0.7, keyword weight of 0.3, and minimum score threshold of 0.3.

5. Explain that a chunk appearing in only one retrieval result set receives a score of zero from the missing retrieval method.

6. Add a small worked example showing how vector and keyword scores produce a final blended score.

7. Verify the completed documentation against the implementation and run the repository’s formatting or pre-commit checks before committing the change.

## Inputs & outputs

The scoring process takes the following inputs:

- A user query.
- Vector-search results containing chunk IDs and vector similarity scores.
- BM25 search results containing chunk IDs and BM25 scores.
- The configured vector and keyword weights.
- The minimum blended-score threshold.
- The maximum number of chunks to return.

The process produces:

- A normalized vector score for each chunk.
- A normalized keyword score for each chunk.
- A blended relevance score.
- A filtered and descending-ranked list of chunks.

This issue should change the architecture documentation only. It should not change the retrieval output or runtime behavior.

## Risks & unknowns

- The vector score originates in `rag/retriever/vector_store.py`, where ChromaDB distance is converted to similarity. The documentation must describe this accurately without implying that the raw distance is blended directly.

- The default minimum relevance score also appears in `core/config.py`. I need to verify whether the configured value and the `HybridRetriever.retrieve()` default are always used consistently.

- The normalization behavior depends on the maximum score returned by each retrieval method. The explanation must accurately cover empty result sets and zero maximum scores.

- Default weights could change later, causing the architecture documentation to become outdated. The documentation should identify them as current defaults rather than permanent requirements.

- It is currently unclear whether the issue expects only the formula or also expects a worked scoring example. I will include a concise example to make the explanation easier to verify.

## Edge cases

- A chunk appears in the vector results but not the BM25 results. Its keyword score should be treated as zero.

- A chunk appears in the BM25 results but not the vector results. Its vector score should be treated as zero.

- One or both retrieval methods return no results. Normalization should avoid division by zero and should not produce invalid scores.

- All scores from one retrieval method are zero. The normalized score for that method should remain zero.

- A blended score is exactly equal to the minimum threshold. It should remain in the results because the implementation uses `>=`.

- More qualifying chunks exist than `max_chunks` permits. Only the highest-ranked chunks should be returned.