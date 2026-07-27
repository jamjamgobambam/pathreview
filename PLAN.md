## Solution plan

**Issue:** [Implement a re-ranking step that uses an LLM to score retrieved chunks before generation](https://github.com/ascherj/pathreview/issues/34)

### Understand

**How the pipeline works today:**
PathReview is a portfolio review tool. A user submits their profile (resume, GitHub, repos) via the web dashboard. The service layer (`core/services/review_service.py`) orchestrates ingestion, agent analysis, and RAG-based feedback generation. The RAG step is where the retriever and generator live:

1. The service formulates internal queries (not typed by the user) for each review dimension, like "What frontend frameworks does this candidate use?" or "How complete is this candidate's work experience?"
2. The hybrid retriever (`rag/retriever/hybrid.py`) searches stored profile chunks using vector similarity (70% weight) and BM25 keyword matching (30% weight), blends the scores, and returns top-k chunks.
3. The generator (`rag/generator/review_generator.py`) takes those chunks as context and prompts an LLM to write structured feedback.

**What's wrong:**
The retriever ranks chunks using only statistical signals. A chunk can score high simply by containing keywords from the query, even when it's not semantically relevant. For example, if the query is about "frontend frameworks," a chunk mentioning "Flask REST API framework" scores high on the keyword "framework" despite being about backend tech. These false positives then get fed to the generator, which writes feedback based on partially irrelevant context.

**What a fix looks like:**
An optional re-ranking pass sits between steps 2 and 3. A smaller LLM scores each candidate chunk's actual relevance to the query (e.g., 0-10). The chunks get re-sorted by that LLM relevance score, and only the truly relevant top-k are passed to the generator. This should be opt-in so the system still works without it (for speed or cost reasons).

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
