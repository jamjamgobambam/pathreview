## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/34

**Issue title:** Implement a re-ranking step that uses an LLM to score retrieved chunks before generation #34

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
The current retriever ranks chunks using vector similarity and keyword scores. This issue adds an optional re-ranking step where a smaller LLM scores each retrieved chunk's relevance to the query before passing the top-k chunks to the generator. This affects the RAG retrieval pipeline in `rag/retriever/` (`hybrid.py` and a new `reranker.py`).

**Branch name:** `feat/34-llm-reranker`

**Setup confirmation:** [x] App runs locally at localhost:5173
