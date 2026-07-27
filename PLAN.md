## Solution plan

**Issue:** [Implement a re-ranking step that uses an LLM to score retrieved chunks before generation](https://github.com/ascherj/pathreview/issues/34)

### Understand

The hybrid retriever (rag/retriever/hybrid.py) ranks chunks using a weighted blend of vector similarity and BM25 keyword scores. This is a purely statistical ranking that can surface false positives: chunks that share surface-level keywords with the query but don't actually answer what was asked. There is no semantic relevance check before the top-k chunks are passed to the generator.

Expected behavior: an optional re-ranking pass sits between retrieval and generation, where a smaller LLM scores each chunk's actual relevance to the query. Only chunks that pass this second check are forwarded to the generator. This should be opt-in so the system still works without it (for speed or cost reasons).

### Map

Files involved:
- `rag/retriever/hybrid.py` — current retriever that produces blended results; will call the reranker if enabled
- `rag/retriever/reranker.py` — new file; contains the LLM reranking logic
- `rag/retriever/__init__.py` — will export the new reranker class
- `rag/generator/review_generator.py` — downstream consumer; expects chunks with `text`, `metadata`, and `score` fields (no changes needed here, the reranker output matches this shape)
- `tests/unit/test_reranker.py` — new test file for the reranker

### Plan

1. **Create `rag/retriever/reranker.py`** — implement a `ChunkReranker` class that takes a list of retrieved chunks and a query, prompts a smaller LLM (e.g., GPT-3.5-turbo or a local model) to score each chunk's relevance on a 0-10 scale, normalizes scores, and returns the top-k chunks sorted by LLM relevance score.

2. **Integrate into `hybrid.py`** — add an optional `reranker` parameter to `HybridRetriever.__init__`. If provided, call `reranker.rerank(query, results)` after blending but before returning. If not provided, behavior is unchanged (backward compatible).

3. **Define the scoring prompt** — write a concise prompt template that asks the LLM to rate chunk relevance given a query. The prompt should produce a numeric score that can be parsed reliably (JSON output format preferred).

4. **Write unit tests** — create `tests/unit/test_reranker.py` with mocked LLM responses. Test: normal reranking, chunks that get filtered out, empty input, LLM response parsing errors, and that the reranker gracefully falls back if the LLM call fails.

5. **Add configuration** — expose a config flag or environment variable to enable/disable reranking and set the model name, so the feature is opt-in and the model can be swapped without code changes.

### Inputs & outputs

**Input to the reranker:**
- `query` (str): the user's original query
- `chunks` (list[dict]): retrieved chunks from the hybrid retriever, each with `id`, `text`, `metadata`, `score`
- `top_k` (int): how many chunks to return after reranking

**Output from the reranker:**
- list[dict]: top-k chunks re-sorted by LLM relevance score. Each chunk retains its original fields plus a new `rerank_score` field. The `score` field is updated to the normalized LLM score so the generator can use it as-is.

### Risks & unknowns

- **Latency**: calling an LLM for each chunk adds latency. Mitigation: batch all chunks into a single prompt or use async calls. If the retriever returns 20 candidate chunks, a single batched prompt is better than 20 individual calls.
- **LLM output parsing**: the model might not return a clean numeric score. Mitigation: use structured output (JSON mode) and fall back to the original hybrid score if parsing fails for a chunk.
- **Cost**: reranking every query adds API cost. Mitigation: make it opt-in via config, and only rerank when the number of candidate chunks exceeds a threshold.
- **Model availability**: if the LLM call fails entirely (rate limit, network error), the system should fall back to returning the original hybrid-ranked results without crashing.

### Edge cases

- Query returns zero chunks from hybrid retrieval (nothing to rerank, return empty list)
- All chunks score below the relevance threshold after reranking (return empty or fall back to top-k by original score)
- LLM returns malformed output for some chunks (use original score for those chunks, log a warning)
- Very long chunks that exceed the LLM's context window (truncate chunk text in the scoring prompt)
- Reranker is enabled but the configured model is unavailable (fall back gracefully to hybrid scores)
