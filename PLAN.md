## Solution plan

**Issue:** [Duplicate embeddings generated when re-ingesting the same repository](https://github.com/ascherj/pathreview/issues/6)

### Understand

The repo ingestion path builds a stable `source_id` for a repository, but it does not actually use the `IngestedSource` model to prevent repeat work. `_check_skip()` currently queries a placeholder string and filters on `source_id`, which is not a field on `IngestedSource`. `_record_ingested_source()` also only logs the completed ingestion, so there is no saved record for the next run to find.

Expected behavior: if the same profile ingests the same repository again, the pipeline should return a skipped result and avoid chunking, embedding, or writing to the vector DB. 

Actual behavior: the second ingestion still runs and writes the same embedding ID again.

**Root cause:** `ingestion/pipeline.py` has incomplete deduplication logic, and it is not correctly connected to `core/models/ingested_source.py`.

### Map

Files I expect to touch:

- `ingestion/pipeline.py` — update `ingest_repo_metadata()`, `_check_skip()`, and `_record_ingested_source()` so repo ingestion checks and records real `IngestedSource` rows.
- `core/models/ingested_source.py` — confirm whether the existing fields are enough for deduplication; add a uniqueness constraint or index only if needed.
- `tests/unit/test_ingestion_pipeline.py` — add focused tests for first ingestion, repeated ingestion, and skip behavior.

Files I may read but probably will not change:

- `ingestion/embeddings/batch_processor.py` — confirms where vector DB writes happen.
- `ingestion/parsers/repo_analyzer.py` — confirms what repo metadata becomes before chunking.

### Plan

1. Add a failing unit test that reproduces the current bug by ingesting the same repo twice and asserting that the vector DB is written only once.
2. Replace the placeholder query in `_check_skip()` with a real query against `IngestedSource`, scoped by `profile_id`, `source_type`, and a stable repo identifier such as `content_hash` and/or `source_url`.
3. Update `_record_ingested_source()` so it creates an `IngestedSource` record after successful ingestion instead of only logging.
4. Adjust `ingest_repo_metadata()` to pass the needed deduplication fields into the skip and record helpers.
5. Run the targeted ingestion pipeline tests, then run the relevant unit test suite to make sure the change does not break resume or README ingestion.

### Inputs & outputs

**Function I am changing:** `ingest_repo_metadata(profile_id: str, repo_data: dict) -> IngestResult`

Existing behavior:

- Input: same `profile_id` and same repo metadata twice.
- Output: both runs return `skipped=False`, and the vector DB receives duplicate embedding writes.

New behavior:

- Input: same `profile_id` and same repo metadata twice.
- Output: first run stores chunks, embeddings, and an `IngestedSource` record. Second run returns `skipped=True` and does not call the parser, chunker, embedding provider, or vector DB.

Test I will write:

- `test_ingest_repo_metadata_skips_duplicate_repo()` will ingest the same fake repo twice, then assert that the second result is skipped and the fake vector DB only received the first write.

### Risks & unknowns

1. The pipeline uses a sync-style `db_session.query(...)`, while other parts of the app use async SQLAlchemy sessions. I need to confirm the expected session type before choosing the final query style.
2. `IngestedSource` has `content_hash` and `source_url`, but not `source_id`. I need to decide whether to store the current hash in `content_hash`, use the repo URL as the stable key, or add a small model change.
3. The current source ID hashes `str(repo_data)`, which can change if dictionary ordering or metadata fields change. I may need to make the repo deduplication key more stable than the raw string form.

### Edge cases

- Same repo ingested twice for the same profile should skip the second run.
- Same repo ingested for a different profile should still be allowed.
- Same repo name with a different URL should not be treated as the same source.
- Repo metadata with no `html_url` should still use a stable fallback, such as repo name plus content hash.
- If database recording fails after vector storage, the error should not be silently hidden in a way that allows future duplicate embeddings.
