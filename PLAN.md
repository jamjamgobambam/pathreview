## Solution plan
**Issue:** Implement a re-ranking step that uses an LLM to score retrieved chunks before generation #34

### Understand
The current hybrid retriever combines vector and keyword search scores but lacks a secondary filtering layer. This can result in noisy context windows being passed to the generator. The expected behavior is an optional re-ranking pass where a smaller LLM evaluates each chunk's relevance to the query, allowing only the top-k highest-scoring chunks to reach the generator.

### Map
The changes will involve the following files:
* `rag/retriever/reranker.py` (New file to implement the LLM scoring logic)
* `rag/retriever/hybrid.py` (Modify the hybrid retrieval pipeline to integrate the reranker)
* `tests/unit/test_reranker.py` (New or updated unit tests for validation)

### Plan
1. Create `rag/retriever/reranker.py` with a core scoring function/class that prompts a lightweight LLM to evaluate chunk relevance against a user query.
2. Update `rag/retriever/hybrid.py` to ingest the retrieval results, invoke the new re-ranking step conditionally or directly, and filter down to the top-k chunks.
3. Write unit tests to mock the LLM responses and verify that chunks are correctly re-sorted and filtered by score.

### Inputs & outputs
* **Input:** A query string and a list of retrieved document chunks (from hybrid search).
* **Output:** A re-sorted and filtered list of top-k document chunks with updated relevance scores.

### Risks & unknowns
* **Latency overhead:** Adding an LLM call into the retrieval pipeline will increase response time. Mitigation: Ensure a small, fast model configuration is used.
* **Prompt output parsing:** The LLM might return malformed scores. Mitigation: Implement robust fallback parsing or default scoring if the LLM output is unstructured.

### Edge cases
* Empty retrieval results list (should handle gracefully without invoking the LLM).
* Fewer retrieved chunks than the requested top-k limit.
* LLM API failure or rate limit during re-ranking (should fall back to original hybrid ranking).