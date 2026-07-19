## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/27]

**Issue title:** [https://github.com/ascherj/pathreview/issues/27]

**Tier:** [ ] Tier 1  [ ] Tier 2  [ X ] Tier 3

**Problem summary:**
When a vector database returns stale embeddings after a document is re-ingested, it means that there are old or stale chunks that don't accurately reflect the new document's chunks. This can lead to incorrect information being retrieved in the retrieval step of the RAG pipeline. this issue takes place in the /rag/retriever/vector_store.py part of the project. 

**Branch name:** [fix/27-vectordb-stale-embeddings]

**Setup confirmation:** [ X ] App runs locally at localhost:5173

**Cohort ledger:** [ X ] Issue added to cohort ledger