## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/27

**Issue title:** Vector store returns stale embeddings after a document is re-ingested

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
When a README is edited and re-ingested, the ingestion pipeline adds new embeddings for the updated content but never removes the embeddings from the prior version. Both the old and new chunks end up coexisting in the vector store under the same source, since nothing currently deletes stale entries before or after a re-ingest. As a result, the retriever can return outdated chunks — content that no longer matches the current document — alongside or instead of the up-to-date version. This affects the ingestion pipeline (`ingestion/pipeline.py`) and the vector store layer (`rag/retriever/vector_store.py`), which currently lacks a way to delete existing chunks by source before adding new ones. A successful fix would ensure re-ingesting a source clears its old embeddings first, so only the current version is ever retrievable.

**"Is this right for me?" checklist reasoning:**

*Part 1 — Understanding the issue:* I can explain the problem without re-reading it: re-ingesting a README adds new embeddings but never deletes the old ones, so the vector store accumulates stale chunks and the retriever can surface outdated content. "Done" means re-ingestion clears prior embeddings for that source before adding the new ones, leaving only current content retrievable.

*Part 2 — Tier fit:* This is my first formal contribution to this codebase, which per the checklist would normally point me to Tier 1. I'm choosing Tier 3 anyway because I already work with this exact class of problem professionally as an Analytics Engineer — Slowly Changing Dimensions (SCD Type 2) solve the same underlying issue in a data warehouse context: when a record is updated, the old version must be closed out or removed rather than left alongside the new one, or queries can return stale data. I've built and maintained pipelines that explicitly guard against this. The unfamiliarity the checklist guards against is with this specific codebase, not the underlying concept — I recognize this bug pattern immediately from professional experience, which narrows the real risk to codebase navigation rather than domain knowledge.

*Part 3 — Codebase readiness:* I've read both `ingestion/pipeline.py` and `rag/retriever/vector_store.py` in full, including the specific ingestion function and the vector store's storage/query methods, and can sketch a rough plan for the fix: add a delete-by-source-id method to `vector_store.py`, and call it at the start of the re-ingest flow in `pipeline.py` before new chunks are added.

*Part 4 — Scope and time:* I've checked the issue comments and the ledger's Claims column and confirmed the current claim count and no open blockers. I'm targeting completion well before the Week 9 deadline, with Week 10 held as buffer rather than my actual estimate.

**Branch name:** fix/27-stale-vectordb-embeddings

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger`