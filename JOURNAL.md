## Week 7: Issue Selection

**Issue link:** https://github.com/ascherj/pathreview/issues/6

**Issue title:** Duplicate embeddings generated when re-ingesting the same repository

**Tier:** [x] Tier 2
Touches both ingestion pipeline and database model layer, rather than simply one file. The estimated duration for the issue is 4-6 hours, which falls within the window of Weeks 7-9. I'd worked with SQLAlchemy models previously, so a cross-module problem seemed manageable.

**Problem summary:**
When you submit the same repository twice, PathReview doesn't recognize that it has previously been completed; instead, it repeats the whole embedding process. There is a safeguard for this: the 'IngestedSource' has an indexed 'content_hash' column. But it's broken in two places. Skip check never executes because `_check_skip()` in `ingestion/pipeline.py` accesses the database incorrectly and fails quietly, captured by a broad try/except. And even if the query was successful, there would be nothing to verify against because `_record_ingested_source()` merely records a message and never stores a row. As a result, each re-ingestion accumulates duplicate embeddings, skewing retrieval in favor of the duplicate. Fix: Make ingestion idempotent. Check the content hash, disregard everything that has already been consumed, still process what's new or changed.

**Branch name:** `fix/6-duplicate-embeddings-reingest`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/jl17500/pathreview/commit/3c400a53c9061d235847a6983e59e74c171c2b51

**Reproduction summary:**
Created a test that runs `ingest_resume()` twice with the same content after instantiating the real `IngestionPipeline` with a `db_session` mock spec'd to `AsyncSession` (the actual session type used in `core/database.py`). Because `AsyncSession` lacks a `.query()` function, it verifies that `_check_skip()` raises `AttributeError: 'Mock' object has no attribute 'query'`; the error is silently consumed, and `batch_processor.process` runs twice rather than once for identical input.

**PLAN.md link:** https://github.com/jl17500/pathreview/blob/fix/6-duplicate-embeddings-reingest/PLAN.md

**Walkthrough video (recommended):** [not recorded]

**Blockers or open questions:**
While mapping call sites, discovered a second unrelated error in 'core/services/review_service.py': '_run_ingestion_pipeline()' creates 'IngestedSource(..., raw_data=...)' with a kwarg that the model lacks, which is quietly swallowed by a broad unless. It's on a live path ('POST /reviews'), but it's not relevant to problem #6, which only focuses on the pipeline and model layer. Flagging it for a possible follow-up issue rather than fixing it now.