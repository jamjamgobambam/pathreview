# Solution plan

## Issue
#18 Add end-to-end ingestion test with a sample resume fixture  
https://github.com/ascherj/pathreview/issues/18

## Understanding
**Root Cause:** The project is missing a end-to-end test suite for ingestion pipeline, even though there are unit tests for individual parsers.

**Expected Behavior:** A complete integration test suite exists at `tests/integration/test_ingestion_pipeline.py` and stress-tests the document ingestion features. This test suite uses `pytest` and follows the code patterns and convenions that are set by the existing test suites in `tests/unit`

**Actual Behavior:** The ingestion pipeline is untested and could produce undetected bugs due to the absence of end-to-end integration test suite.


## Map
**Files involved:**
- `tests/integration/test_ingestion_pipeline.py` (new file for test suite)
- Sample data in `tests/fixtures/sample_resumes/`
- `ingestion/pipeline.py`

**Core modules under test:**
- `ingestion/pipeline.py:IngestionPipeline` (main class with `ingest_resume()`, `ingest_readme()`, `ingest_repo_metadata()` methods)
- `ingestion/pipeline.py:IngestResult` (return type)
- `ingestion/embeddings/batch_processor.py:BatchEmbeddingProcessor` (called during ingestion)
- `ingestion/embeddings/provider.py:EmbeddingProvider` (dependency)
- `ingestion/parsers/resume_parser.py:ResumeParser` (used internally)
- `ingestion/chunking/strategy_selector.py:StrategySelector` (used internally)


## Plan
1. **Set up test fixtures:** Create fixtures in `tests/fixtures/sample_resumes/` if they don't exist.
2. **Create mock dependencies:** Mock `vector_db`, `db_session`, and `EmbeddingProvider` to avoid real API calls and database writes
3. **Test resume ingestion:** Write test cases for `ingest_resume()` covering the full flow: parse → chunk → embed → store
4. **Test readme ingestion:** Write test cases for `ingest_readme()` with the same end-to-end validation
5. **Test repository metadata ingestion**: Write test cases for `ingest_repo_metadata()` with dictionary input
6. **Test deduplication logic:** Verify `_check_skip()` correctly skips already-ingested sources
7. **Validate all outputs:** Assert `IngestResult` contains correct `source_id`, `chunk_count`, and `skipped` status


## Inputs & Outputs
**Test Inputs:**
- Sample resume content (string or bytes)
- Sample README content (markdown string)
- Repository metadata (dict)
- Profile ID (string)

**Expected Outputs:**
- `IngestResult` with `source_id`, `chunk_count`, `skipped`, and optional `skip_reason`
- Mocked `vector_db` receives chunk embeddings via `batch_processor.process()`
- Mocked `db_session` records ingested source via `_record_ingested_source()`


## Risks & unknowns
**Risks:**
- Mocking the `BatchEmbeddingProcessor` and `EmbeddingProvider` correctly to avoid real API calls
- Ensuring the mock database session captures the calls to `_record_ingested_source()` without a real ORM

**Unknowns:**
- The exact structure of `ParseResult` returned by parsers (need to verify metadata fields)
- The exact signature of `batch_processor.process()` and what it expects
- Whether `db_session.query()` in `_check_skip()` can be mocked directly or if it needs a spy


## Edge cases
- **Ingested source:** Resume ingested twice should return `skipped=True` on second call
- **Empty content:** Should handle gracefully by raising exception or skipping
- **Mixed content types:** Resume as bytes vs. string should both work
- **Deduplication by hash:** Different content with same `profile_id` should get different `source_ids`
- **Parser errors:** Invalid resume format should be caught and logged
- **Batch processor failures:** Embedding generation failure should propagate as exception