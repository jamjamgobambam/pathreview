### Solution Plan

**Issue:** #24 — Hybrid retriever over-weights keyword results when queries contain technology names
https://github.com/ascherj/pathreview/issues/24

### Understand

HybridRetriever.retrieve() currently combines vector similarity and BM25 scores using a fixed 70/30 weighted sum. Before combining them, each score is normalized against the highest score in the current result batch.

The problem is that BM25 scores can become very large when a chunk repeats query terms. A keyword-stuffed README such as "Python React Python React..." can become the highest BM25 result and therefore receive a normalized score of 1.0, even if it is not actually relevant. A genuinely relevant chunk that mentions each term normally can then rank below it.

There is also a tokenizer issue. _tokenize() only lowercases and splits on whitespace, so "Python," does not match "python". This can reduce keyword scores for otherwise relevant chunks.

**Root cause:**

Per-batch max-score normalization lets BM25 outliers dominate.
Tokenization fails to match terms next to punctuation.

The existing regression test confirms the issue: the irrelevant, keyword-stuffed readme_1 ranks above the relevant resume_1.

I also considered reducing the weight of terms that appear across many chunks, but that does not solve this case because the problem is repetition within one chunk, not across multiple chunks.

### Map
* rag/retriever/hybrid.py — replace max-score normalization with weighted RRF.
* rag/retriever/keyword_search.py — improve _tokenize() to handle punctuation.
* tests/unit/test_hybrid_retriever.py — remove the xfail from the regression test.
* tests/unit/test_keyword_search.py — verify existing special-character tests still pass.

### Plan
1. Add a helper in hybrid.py that converts scored results into {chunk_id: rank}, with rank 1 being the highest result and deterministic tie-breaking.
2. Replace the current 70/30 score blend with Weighted Reciprocal Rank Fusion (RRF):
score = vector_weight / (k + vector_rank) + keyword_weight / (k + keyword_rank).
3. Start with k=10. Chunks missing from one result set should receive the worst possible rank for that side.
4. Update _tokenize() to remove leading/trailing punctuation while preserving internal characters such as c++ and node.js.
5. Remove the xfail from test_relevant_chunk_outranks_keyword_stuffed_irrelevant_chunk and verify it passes.
6. Run the hybrid retriever and keyword search test suites.
7. Add a test where keyword matching should win, such as a rare identifier with weak vector similarity, to ensure RRF does not overcorrect toward vector results.

### Inputs & Outputs

The retrieve() interface and inputs remain unchanged:

* query
* profile_id
* query_embedding
* max_chunks
* min_score

The output structure also remains the same, but score will now be an RRF score rather than a 0–1 blended score. vector_score and keyword_score may also need to become rank-derived values. Nothing outside the hybrid retriever tests currently appears to depend on their existing scale.

### Risks & Unknowns
* min_score: The current default of 0.3 assumes a 0–1 score. RRF scores are much smaller, so this threshold will need to change or be replaced with a rank-based cutoff.
* RRF k: Testing with k=60, 20, 10, 5 fixed the reproduction case. k=10 produced the clearest margin, but it should be tested against more realistic data.
* Loss of score magnitude: RRF uses rank rather than the actual similarity score, so two results with very different scores can be treated similarly if they have the same rank.
* Tokenizer regression: Punctuation stripping must not break tokens such as c++ or node.js.
* Keyword indexing: retrieve() does not currently call keyword_searcher.index(). This is a separate issue and is outside the scope of #24.

### Edge Cases

The implementation should handle:

* Empty vector or keyword results.
* Queries with no keyword matches or all-zero BM25 scores.
* Single-chunk corpora.
* Queries containing only stopwords.
* Tied scores, while preserving the current deterministic ordering.
* Chunks that appear in only one of the two result sets.