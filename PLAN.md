## Solution plan

**Issue:** [Implement a re-ranking step that uses an LM to score retrieved chunks before generation](https://github.com/ascherj/pathreview/issues/34)

### Understand

The current `HybridRetriever.retrieve()` in `rag/retriever/hybrid.py` blends vector similarity and BM25 keyword scores into a single `blended_score`, then returns the top-k chunks sorted by that score. The problem is that blended scores are statistical proxies — a chunk with high keyword overlap may not actually answer the query. There is no step that asks a language model "is this chunk truly relevant to what the user is asking?" The fix adds an optional `LLMReranker` that prompts a smaller LLM to score each candidate chunk's relevance (0.0–1.0) and re-sorts the list before the final top-k cut. When the reranker is disabled, behavior is identical to today.

### Map

Files to create:
- `rag/retriever/reranker.py` — new `LLMReranker` class with `rerank(query, chunks)` method

Files to modify:
- `rag/retriever/hybrid.py` — add optional `reranker=None` param to `__init__`, call it in `retrieve()` before the final slice
- `rag/retriever/__init__.py` — export `LLMReranker` alongside existing exports

Files to create (tests):
- `tests/unit/test_reranker.py` — already committed as reproduction; will be made passing

### Plan

1. **Create `rag/retriever/reranker.py`** with `LLMReranker(client, model)`. The `rerank(query, chunks)` method loops over chunks, sends a prompt asking the LLM to rate each chunk's relevance to the query on a 0.0–1.0 scale, parses the float from the response, adds it as `rerank_score` on the chunk dict, and returns the list sorted by `rerank_score` descending. Include robust parsing with a fallback to the original `score` if the LLM response is unparseable.

2. **Update `HybridRetriever.__init__`** to accept `reranker=None`. Store it as `self.reranker`.

3. **Update `HybridRetriever.retrieve()`** to call `self.reranker.rerank(query, results)` after filtering by `min_score` and before the `results[:max_chunks]` slice, but only when `self.reranker is not None`.

4. **Export `LLMReranker` from `rag/retriever/__init__.py`** so callers can do `from rag.retriever import LLMReranker`.

5. **Make all 6 tests in `tests/unit/test_reranker.py` pass** using a mocked LLM client (same `MagicMock` pattern used in `review_generator.py` tests).

### Inputs & outputs

- **Input to `rerank()`:** `query: str`, `chunks: list[dict]` — each dict has at minimum `id`, `text`, and `score` (the blended hybrid score).
- **Output of `rerank()`:** same list with a `rerank_score: float` field added to each chunk, sorted by `rerank_score` descending.
- **Effect on `retrieve()`:** the final `results[:max_chunks]` now reflects LLM-assessed relevance instead of blended statistical scores.

### Risks & unknowns

- **Latency:** scoring N chunks means N sequential LLM API calls. For `max_chunks=10`, that's 10 round-trips before generation even starts. Mitigation: limit re-ranking candidates to the top-20 blended results, not the full pool.
- **LLM response parsing:** the model may return prose instead of a clean float ("This chunk is highly relevant — 0.9"). Need a regex or `float()` try/except with fallback to the original `score`.
- **Cost:** each review request could add 10–20 extra LLM calls. The feature should remain opt-in (reranker defaults to `None`) so existing callers are unaffected.
- **Unknown:** does the project have a shared LLM client factory I should reuse, or should `LLMReranker` accept a raw `openai.OpenAI` client like `ReviewGenerator` does? Need to check `agent/orchestrator.py` before finalizing the constructor signature.

### Edge cases

- Empty chunk list → return `[]` immediately, no LLM calls made.
- Single chunk → skip re-ranking (no ordering decision needed), add `rerank_score=1.0` and return.
- LLM returns unparseable output → log a warning, fall back to original `score` as `rerank_score`.
- LLM returns a score outside 0–1 → clamp to `[0.0, 1.0]`.
- All chunks score 0.0 from reranker → return them in original blended-score order rather than an arbitrary tie-broken order.
