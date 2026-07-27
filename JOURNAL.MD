## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/27]

**Issue title:** [https://github.com/ascherj/pathreview/issues/27]

**Tier:** [ ] Tier 1  [ ] Tier 2  [ X ] Tier 3

**Problem summary:**
When a vector database returns stale embeddings after a document is re-ingested, it means that there are old or stale chunks that don't accurately reflect the new document's chunks. This can lead to incorrect information being retrieved in the retrieval step of the RAG pipeline. this issue takes place in the /rag/retriever/vector_store.py part of the project. 

**Branch name:** [fix/27-vectordb-stale-embeddings]

**Setup confirmation:** [ X ] App runs locally at localhost:5173

**Cohort ledger:** [ X ] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [9455a8f](https://github.com/amalrajn/pathreview/commit/9455a8faa13fb929f2d8904eb88bba4915167f4c)

**Reproduction summary:**
I added an integration test ([tests/integration/test_stale_embeddings_repro.py](https://github.com/amalrajn/pathreview/blob/fix/27-vectordb-stale-embeddings/tests/integration/test_stale_embeddings_repro.py)) that mirrors the pipeline's id scheme — `source_id` embeds the content hash, so an edited README gets a new id, and `VectorStore.delete_by_source_id` is never called. After ingesting a README that says "Flask" and then a re-ingested version that says "FastAPI", I observed both chunks coexisting in the ChromaDB collection and a query returning the stale "Flask" chunk.

**PLAN.md link:** [PLAN.md](https://github.com/amalrajn/pathreview/blob/fix/27-vectordb-stale-embeddings/PLAN.md)

**Walkthrough video (recommended):**

**Blockers or open questions:**
Need to confirm which write path production actually uses — `batch_processor._store_embedding` calls `vector_db.add(...)` directly, while `VectorStore.add_chunks` reads chunk attributes that the `Chunk` dataclass doesn't have — before finalizing the stable-id/delete scheme.