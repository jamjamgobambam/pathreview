## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/34

**Issue title:** Implement a re-ranking step that uses an LLM to score retrieved chunks before generation #34

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
The current retriever ranks document chunks by combining vector and keyword scores. However, these initial scores don't always accurately reflect how relevant a chunk is to the user's query. Adding an optional re-ranking step in `rag/retriever/reranker.py` will prompt a smaller LLM to score each chunk's actual relevance before passing the top-k chunks to the generator. This will make the retrieved context more accurate and improve the overall feedback quality.

**Selection notes / "Is this right for me?" checklist reasoning:**
- **Estimated effort:** 7–10 hours (Tier 3), which fits well within my project timeline.
- **Affected files:** `rag/retriever/hybrid.py` and creating `rag/retriever/reranker.py`.
- **Reason for selection:** This issue has a clear focus on the RAG retrieval logic. It allows me to work on backend search and LLM scoring cleanly without requiring frontend or database changes.

**Branch name:** `feat/34-llm-reranker`

**Setup confirmation:** [x] App runs locally at localhost:5173
