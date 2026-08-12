## Solution plan

**Issue:** [Add a content hash to detect unchanged documents and skip re-embedding](https://github.com/ascherj/pathreview/issues/13)

### Understand

The ingestion pipeline already computes a SHA-256-based content hash and includes a shortened version of that hash in each `source_id`. However, duplicate detection does not work because `_check_skip()` does not query the actual `IngestedSource` SQLAlchemy model, and `_record_ingested_source()` only logs the ingestion instead of saving a database record. As a result, when the same README is submitted again, the pipeline parses, chunks, and embeds it a second time rather than returning a skipped result. The expected behavior is for the first ingestion to store metadata about the source and for later ingestion attempts with the same profile, source type, repository, and content hash to skip embedding.

### Map

Expected files and code paths involved:

* `ingestion/pipeline.py`

  * `IngestionPipeline.ingest_readme()`
  * `IngestionPipeline._hash_content()`
  * `IngestionPipeline._check_skip()`
  * `IngestionPipeline._record_ingested_source()`
* `core/models/ingested_source.py`

  * Existing `IngestedSource` model
  * Existing `source_url`, `content_hash`, and `chunk_count` fields
* `tests/unit/test_ingestion_pipeline.py`

  * Reproduction test for submitting an identical README twice
  * Additional tests for changed content and database behavior
* Existing service code that shows the caller owns database commits

A database migration is not needed because the `IngestedSource` model and initial Alembic migration already contain the required fields.

### Plan

1. Import and use the actual `IngestedSource` SQLAlchemy model in the ingestion pipeline instead of querying the string `"IngestedSource"`.
2. Compute the full content hash once during ingestion and pass it separately to the duplicate-check and persistence methods.
3. Update `_check_skip()` so it queries for a matching ingested source using `profile_id`, `source_type`, `source_url`, and `content_hash`.
4. Update `_record_ingested_source()` so it creates an `IngestedSource` record and adds it to the database session without committing, because the service or caller layer owns the transaction.
5. Expand `tests/unit/test_ingestion_pipeline.py` so it verifies:

   * the first README ingestion is processed;
   * the second identical README ingestion is skipped;
   * changed README content is processed;
   * the embedding processor is not called for skipped content;
   * ingestion metadata is persisted with the expected hash and chunk count.

### Inputs & outputs

**Inputs:**

* `profile_id`
* repository name
* README content as `str` or `bytes`
* database session
* embedding provider and vector database dependencies

**Outputs and changes:**

* First-time content should be parsed, chunked, embedded, and recorded in `ingested_sources`.
* Identical content submitted again should return an `IngestResult` with:

  * `skipped=True`
  * `chunk_count=0`
  * a clear skip reason
* Changed content should produce a different hash and proceed through embedding normally.
* The database should contain enough metadata to identify previously ingested content.

### Risks & unknowns

* Resolved: the pipeline should call `db_session.add()` but should not call `commit()`, because existing service code owns transaction commits.
* Resolved: README duplicate matching uses `profile_id`, `source_type`, `source_url` with `repo_name`, and the full SHA-256 `content_hash`.
* Resolved: the current `source_id` is not represented as a field on `IngestedSource`, so duplicate lookup relies on real persisted model fields.
* Resolved: importing `IngestedSource` directly into `ingestion/pipeline.py` did not create a circular import.
* Focused tests now confirm unchanged README content is skipped while changed content, different profiles, and different repositories are processed.
* Repository-wide unit and lint failures remain pre-existing and unrelated to Issue #13.

### Edge cases

* Empty README content
* README content provided as bytes instead of a string
* Same content submitted for two different profiles
* Same content submitted for two different repositories
* Changed content for the same profile and repository
* Database lookup failure
* Database persistence failure after embeddings have already been generated
* Existing legacy records with `content_hash=None`
* Duplicate submissions occurring close together before the first transaction is committed
