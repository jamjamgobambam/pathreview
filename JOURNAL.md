## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/34

**Issue title:** Implement a re-ranking step that uses an LLM to score retrieved chunks before generation

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
Right now, PathReview's retriever ranks chunks using only vector similarity and keyword overlap scores. This means the final context sent to the generator may include chunks that match on surface keywords but aren't actually relevant to the user's query. The fix is to add an optional re-ranking pass that calls a smaller LLM to score each chunk's relevance before the top-k are handed to the generator. This lives in the rag/retriever module, primarily in a new reranker.py file and integration with hybrid.py. A successful implementation would improve answer quality by filtering out false-positive retrievals.

**Branch name:** feat/34-setup-&-short-description

**Branch link:** https://github.com/Modeste01/pathreview/tree/feat/34-setup-%26-short-description

**Setup confirmation:** [x] App runs locally at localhost:5173
![alt text](image.png)
![alt text](image-1.png)

**Cohort ledger:** [x] Issue added to cohort ledger
