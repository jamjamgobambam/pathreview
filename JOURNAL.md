# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/27

**Issue title:** Vector store returns stale embeddings after a document is re-ingested

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
The RAG system stores document embeddings in a vector store so the retriever
can find relevant chunks. When a document such as a README is edited and sent
back through the ingestion pipeline, the pipeline writes the new embeddings but
never removes the document's previous ones, so both versions coexist in the
store. Because of this, the retriever can surface outdated chunks that no longer
match the document's current content. A successful fix makes re-ingestion
idempotent — clearing or overwriting a document's existing embeddings before
writing the new ones — so retrieval always reflects the latest version. This
affects the RAG layer, specifically `rag/retriever/vector_store.py` and
`ingestion/pipeline.py`.

**Branch name:** fix/27-vector-store-stale-embeddings-error

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
