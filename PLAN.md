## Solution plan

**Issue:** [#18 — Add end-to-end ingestion test with a sample resume fixture](https://github.com/ascherj/pathreview/issues/18)

### Understand
There are unit tests for individual parsers (`tests/unit/test_resume_parser.py`, etc.) but nothing that exercises the full ingestion chain together: parse → chunk → embed → store. During reproduction I confirmed `IngestionPipeline.ingest_resume()` (in `ingestion/pipeline.py`) does work correctly end-to-end when called directly — it produced 1 chunk from a sample resume, generated a mock embedding, and stored it in a real ChromaDB collection (`collection.count()` returned 1). Expected behavior per the issue is a repeatable integration test proving this chain works; actual current state is that no such test exists, and the chain has only ever been exercised manually.

I also found the pipeline is not wired into the actual API: `api/routes/profiles.py`'s upload endpoint parses resumes itself via raw `PyPDF2` and never calls `IngestionPipeline`. This means the e2e test can't realistically go through the HTTP upload endpoint — it needs to call `IngestionPipeline.ingest_resume()` directly, since that's the only place the full parse → chunk → embed → store chain actually exists today.

### Map
- `tests/integration/test_ingestion_pipeline.py` — where the new test will live (currently only contains reproduction notes)
- `ingestion/pipeline.py` — `IngestionPipeline.ingest_resume()`, the method under test
- `ingestion/parsers/resume_parser.py` — parsing step
- `ingestion/chunking/strategy_selector.py` — chunking step
- `ingestion/embeddings/batch_processor.py` + `ingestion/embeddings/provider.py` (`MockEmbeddingProvider`) — embedding step
- `tests/conftest.py` — existing `sample_resume_text` fixture I can reuse; may need to add fixture files here too
- `tests/fixtures/sample_resumes/` — does not exist yet, needs to be created with at least one sample resume file (PDF and/or markdown) per the issue's instructions

### Plan
1. Create `tests/fixtures/sample_resumes/` and add at least one real sample resume file (a markdown resume, and ideally a PDF, to match `ResumeParser`'s supported input types)
2. Write a real ChromaDB test collection setup (using `chromadb.Client()` in-memory, as verified during reproduction) and a `MockEmbeddingProvider` instance as pipeline dependencies, replacing the ad-hoc `FakeSession` from my repro with a proper test double or the app's real test DB session fixture if one exists
3. Write the core test: call `IngestionPipeline.ingest_resume()` with the fixture content, assert the returned `IngestResult` has the expected `chunk_count` and `skipped=False`, and assert the vector DB collection actually contains the stored embedding(s)
4. Add a second test case for the skip/dedupe path (`_check_skip`), documenting that it currently always returns `None` (proceeds) against a real session because the placeholder query will raise and be silently caught — decide whether to assert this current (possibly unintended) behavior or mark it with a `# TODO` noting the known gap
5. Mark the test with `@pytest.mark.integration` to match the existing marker convention in `pyproject.toml`

### Inputs & outputs
**Input:** a sample resume file's raw content (markdown text and/or PDF bytes) plus a `profile_id` and `filename`, fed into `IngestionPipeline.ingest_resume()`.
**Output:** an `IngestResult` (source_id, chunk_count, skipped, skip_reason) returned by the pipeline, and as a side effect, one or more embeddings actually persisted in the ChromaDB collection — verified by querying `collection.count()` and/or `collection.get()` after ingestion.

### Risks & unknowns
- `IngestionPipeline._check_skip()` (in `ingestion/pipeline.py`) queries with a placeholder string instead of a real ORM model (`db_session.query("IngestedSource")`), which will raise against any real SQLAlchemy session. It's currently caught by a try/except, so it silently no-ops rather than failing loudly — my test needs to account for this rather than assume dedupe actually works.
- `IngestionPipeline._record_ingested_source()` only logs and does not persist anything to Postgres, despite its docstring implying it does. My test can't assert on any real DB row for this — only on the vector DB side of storage.
- No real Postgres-backed `db_session` fixture currently exists in `tests/conftest.py` for integration tests; I'll need to investigate whether one should be added (e.g., using the app's existing test DB setup) or whether a lightweight fake/mock session is acceptable for this specific test's scope.
- `tests/fixtures/sample_resumes/` doesn't exist yet — I need to create realistic sample files (not just inline strings) to match the issue's explicit instruction to use fixtures from that path.

### Edge cases
- A resume with no detectable sections (e.g., no Experience/Skills headers) — confirm the pipeline still produces at least one chunk and doesn't error, per `test_parse_resume_no_work_experience` in `tests/unit/test_resume_parser.py`.
- A PDF resume input (bytes) vs. a markdown/text resume input (str) — confirm both content types flow through `ingest_resume()` correctly, since `ResumeParser.parse()` branches on type.
- Calling `ingest_resume()` twice with identical content for the same profile — given `_check_skip()`'s known placeholder bug, document what actually happens (currently: re-ingests and re-embeds rather than skipping) rather than assuming the ideal dedupe behavior.
