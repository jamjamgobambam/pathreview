## Solution plan

**Issue:** [Duplicate embeddings generated when re-ingesting the same repository](https://github.com/ascherj/pathreview/issues/6)

### Understand

The repository ingestion pipeline calculates a deterministic source identifier from the profile ID, repository name, and repository metadata. It then calls `_check_skip()` before parsing and embedding the repository. However, `_check_skip()` attempts to query the literal string `"IngestedSource"` through a synchronous SQLAlchemy-style `.query()` call, while the application database layer provides an asynchronous `AsyncSession`. The resulting exception is caught and converted into a warning, so ingestion continues instead of being skipped.

The pipeline also calls `_record_ingested_source()` after generating embeddings, but that method currently only writes a log message and does not create an `IngestedSource` database record. Therefore, the second ingestion has no persisted record to find even if the lookup were corrected.

The expected behavior is that ingesting identical repository data for the same profile a second time should return an `IngestResult` with `skipped=True` and should not parse, chunk, generate, or store embeddings again. The current behavior processes both requests and invokes the embedding processor twice, creating duplicate vector entries or attempting to store the same logical chunks again.

### Map

Files expected to be modified:

* `ingestion/pipeline.py`

  * `IngestionPipeline.ingest_repo_metadata()`
  * Potentially `ingest_resume()` and `ingest_readme()` because they use the same broken deduplication helpers
  * `_check_skip()`
  * `_record_ingested_source()`
  * `_hash_content()`, if the full content hash must be retained separately from the vector source identifier

* `core/models/ingested_source.py`

  * Confirm the fields used to identify duplicate sources
  * Potentially add a composite uniqueness constraint for profile, source type, and content hash

* `alembic/versions/<new_migration>.py`

  * Add a database uniqueness constraint if model-level uniqueness is part of the selected solution

* `tests/unit/test_ingestion_pipeline_deduplication.py`

  * Convert the reproduction into passing regression tests
  * Add cases covering legitimate non-duplicate ingestion

Additional files to inspect before implementation:

* `core/database.py`

  * Confirm the intended `AsyncSession` transaction pattern

* Any API route, service, or background task that constructs or calls `IngestionPipeline`

  * Determine whether changing ingestion methods to `async` affects existing callers

### Plan

1. **Define the duplicate identity.**
   Use the existing `IngestedSource` fields to identify an exact duplicate by `profile_id`, `source_type`, and the full SHA-256 `content_hash`. Keep the generated `source_id` for vector chunk identifiers, but do not query a nonexistent `source_id` database column.

2. **Implement a real database lookup.**
   Import the `IngestedSource` model and use SQLAlchemy 2.x `select()` with the project’s `AsyncSession`. Update the ingestion flow to await the lookup before parsing, chunking, or embedding content.

3. **Persist successful ingestion records.**
   Replace the placeholder `_record_ingested_source()` implementation with creation of an `IngestedSource` row containing the profile ID, source type, content hash, source URL or filename when available, and chunk count. Flush or commit through the established transaction convention.

4. **Protect against database duplicates.**
   Evaluate adding a composite unique constraint over `profile_id`, `source_type`, and `content_hash`. If added, create an Alembic migration and handle `IntegrityError` so concurrent duplicate requests do not create multiple database records.

5. **Complete focused regression tests.**
   Update the reproduction test so identical repository input is processed once and skipped on the second call. Add tests showing that changed repository content, a different profile, or a different source type is not incorrectly skipped.

### Inputs & outputs

Inputs:

* `profile_id`: identifies the owner of the repository data
* `repo_data`: repository metadata passed to `ingest_repo_metadata()`
* `source_type`: `"repo"` for repository ingestion
* Derived full SHA-256 content hash
* Optional repository URL extracted from `repo_data`

Expected first-ingestion output:

* `IngestResult.skipped` is `False`
* Repository content is parsed and chunked
* Embeddings are generated and stored once
* One matching `IngestedSource` row is persisted
* `IngestResult.chunk_count` contains the number of stored chunks

Expected duplicate-ingestion output:

* `IngestResult.skipped` is `True`
* `skip_reason` explains that the source was already ingested
* Parsing, chunking, and embedding are not invoked
* No additional vector entries or database records are created
* `chunk_count` remains `0` for the skipped operation

### Risks & unknowns

* `IngestionPipeline` currently exposes synchronous methods, but the database layer uses `AsyncSession`. Converting the pipeline methods to asynchronous methods may require changes to callers that are not identified in the issue description.
* The model stores `content_hash`, while the pipeline currently constructs a separate truncated `source_id`. The implementation must avoid confusing these two identifiers.
* It is not yet confirmed whether updated metadata from the same repository should create a new ingestion, replace the previous vectors, or be skipped based only on repository URL.
* A database record written only after vector storage leaves a concurrency window in which two requests can both generate embeddings. A uniqueness constraint prevents duplicate rows but may not prevent duplicate vector processing by itself.
* If embedding storage succeeds but the database write fails, the vector database and relational database can become inconsistent. The implementation should define appropriate cleanup or retry behavior.
* Existing `IngestedSource` rows may already contain duplicate combinations. A uniqueness migration could fail unless existing data is checked or cleaned first.

### Edge cases

* The exact same repository data is ingested twice for the same profile.
* The same repository data is ingested for two different profiles.
* Repository data changes and therefore produces a different content hash.
* Dictionary ordering or serialization differences produce logically identical repository metadata.
* Repository data has no `name`, URL, description, or language.
* The database lookup raises a temporary error.
* The database insert encounters a concurrent uniqueness conflict.
* Embedding generation fails before the ingestion record is written.
* The database write fails after embeddings have already been stored.
* The source produces zero chunks.
* Resume and README ingestion continue to work because they share the same skip and record helpers.
