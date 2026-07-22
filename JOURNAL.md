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