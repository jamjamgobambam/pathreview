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

**Selection reasoning:**
I chose this as a Tier 3 issue because I am still building my comfort with the
RAG layer, and this bug is well-scoped rather than open-ended. It is isolated to
two files (`rag/retriever/vector_store.py` and `ingestion/pipeline.py`), it has a
clear reproduction path (edit and re-ingest a document, then observe stale chunks
in retrieval), and the maintainer's 6–9 hour estimate suggests a fix that is
ambitious enough to stretch me but bounded enough to finish within Module 3. It
also lines up with what I want to learn this module — how ingestion and vector
storage interact — so the scope fits both my current skill level and my goals.

**Branch name:** fix/27-vector-store-stale-embeddings-error

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
