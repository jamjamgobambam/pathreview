## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/34

**Issue title:** Implement a re-ranking step that uses an LLM to score retrieved chunks before generation

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
Right now, PathReview's retriever ranks chunks using only vector similarity and keyword overlap scores. This means the final context sent to the generator may include chunks that match on surface keywords but aren't actually relevant to the user's query. The fix is to add an optional re-ranking pass that calls a smaller LLM to score each chunk's relevance before the top-k are handed to the generator. This lives in the rag/retriever module, primarily in a new reranker.py file and integration with hybrid.py. A successful implementation would improve answer quality by filtering out false-positive retrievals.

**Issue selection reasoning (Is this right for me?):**
I can explain the issue without looking at it: the retriever currently ranks chunks by vector and keyword scores alone, but that misses relevance nuance that only an LLM can catch. The fix adds an optional reranker step before generation. I found the relevant files (rag/retriever/hybrid.py exists, reranker.py is new) and read the retriever logic enough to sketch a plan. I checked the test directory and found existing retriever tests I can mirror. I chose Tier 3 because I have prior, though minimal, experience with RAG pipelines and LLM APIs, and the scope is contained to one new module plus one integration point. The 7-10 hour estimate fits within the two-week implementation window given my schedule. No blockers or dependencies on other issues.

**Branch name:** feat/34-setup-&-short-description

**Branch link:** https://github.com/Modeste01/pathreview/tree/feat/34-setup-%26-short-description

**Setup confirmation:** [x] App runs locally at localhost:5173
![alt text](image.png)
![alt text](image-1.png)

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Modeste01/pathreview/commit/80c9bfa

**Reproduction summary:**
I wrote a test that tries to import `ChunkReranker` from `rag.retriever.reranker` and checks whether `HybridRetriever` accepts a reranker parameter. The import fails, confirming the module does not exist. The second test passes, confirming there is no integration point for a reranker in the hybrid retriever. This proves the gap described in issue #34: chunks go straight from blended vector/keyword scoring to the generator with no LLM-based relevance check in between.

**PLAN.md link:** https://github.com/Modeste01/pathreview/blob/feat/34-setup-%26-short-description/PLAN.md

**Walkthrough video (recommended):** (not recorded)

**Blockers or open questions:**
Need to decide which LLM to use for reranking (GPT-3.5-turbo is cheap and fast, but a local model would avoid API costs in tests). Also need to confirm whether batching all chunks in one prompt or scoring them individually gives more reliable results.
