## Solution plan

**Issue:** Add end-to-end ingestion test with a sample resume fixture ([#18](https://github.com/ascherj/pathreview/issues/18))

### Understand

There are unit tests for each parser on its own (`test_resume_parser.py`, `test_readme_parser.py`), but nothing tests the full flow a real resume goes through: upload, parse, chunk, embed, and store. `tests/integration/` was empty before this issue.

Expected behavior: calling `IngestionPipeline.ingest_resume()` on a new resume should parse it, chunk it, generate embeddings, and store them, and the result should reflect that (`skipped=False`, `chunk_count > 0`).

Actual behavior, confirmed by reproduction: with a mocked `db_session` (the same way every existing test mocks it), the pipeline reports `skipped=True, chunk_count=0` on a brand new profile. `_check_skip()` in `pipeline.py` queries `db_session.query("IngestedSource")` with a string instead of the model class, so a mocked session's `.first()` always returns a truthy `Mock`, and the pipeline thinks a match already exists before it ever parses anything.

### Map

- `tests/integration/test_ingestion_pipeline.py` - the test file itself. Already has one test from the Week 8 reproduction; extending it past that.
- `tests/fixtures/sample_resumes/` - already exists with `resume.txt` (added for the reproduction commit); will add at least one more fixture to cover a resume with no clear sections (mirrors the case already covered in `test_resume_parser.py`).
- `ingestion/pipeline.py` - read-only reference for `IngestionPipeline.ingest_resume()`, the method under test, including `_check_skip()` and `_record_ingested_source()`.
- `ingestion/parsers/resume_parser.py` - parsing step.
- `ingestion/chunking/strategy_selector.py` - chunking step.
- `ingestion/embeddings/batch_processor.py` + `ingestion/embeddings/provider.py` (`MockEmbeddingProvider`) - embedding step. Confirmed `vector_db.add(...)` is the actual call to assert against.
- `tests/conftest.py` - has an existing `sample_resume_text` fixture I can reuse instead of reading from a file directly; may add a fixture here for the fixtures directory path if more than one test file ends up needing it.

### Plan

1. Configure the mocked `db_session` explicitly in the test to get past the `_check_skip()` bug without touching `pipeline.py`. This turns the current failing reproduction test into a real passing test.
2. Add assertions that the pipeline actually did the work, not just that it didn't skip: `result.chunk_count > 0`, `result.skipped is False`, and that `vector_db.add` was actually called (proves embeddings were "stored", not just that chunking happened).
3. Add a second fixture resume with no clear section headers (mirrors `test_resume_parser.py`'s "no work experience" case) and a second test asserting the pipeline still produces chunks for it instead of failing.
4. Add a test for the skip path itself: call `ingest_resume()` twice with the same content and a `db_session` mock configured to return a match on the second call, asserting the second call reports `skipped=True`. Without this, the workaround from step 1 means the skip logic is never actually exercised by any test.
5. Clean up test file: rename/reframe docstring now that this is the real test, not just a reproduction, and confirm `pytest tests/integration/` passes green end to end.

### Inputs & outputs

Input: resume content (str or bytes), a `profile_id`, and a `filename`, passed to `IngestionPipeline.ingest_resume()`.

Output: an `IngestResult` (`source_id`, `chunk_count`, `skipped`, `skip_reason`), plus the side effect of `vector_db.add(...)` being called once per chunk with the chunk's embedding, metadata, and text.

### Risks & unknowns

- Working around `_check_skip()` by pre-configuring the mock's `.query().filter_by().first()` chain ties the test to an internal implementation detail. If `pipeline.py`'s query logic changes later (e.g. someone fixes the placeholder), this mock setup will need to change too.
- Our fixtures are plain text, not real PDF bytes. `ResumeParser` has PDF-handling logic (per `tests/unit/test_resume_parser.py`) that our integration test won't exercise. Open question: is a `.txt`/`.md` fixture enough for this issue, or does "sample resume fixture" imply a real PDF should be included too.
- Haven't yet confirmed what chunk count a short mock resume actually produces, small fixtures might only yield 1 chunk, which is a weak signal for "chunking works." May need a longer fixture to meaningfully test multi-chunk behavior.

### Edge cases

- Very short resume content that produces only one chunk (or zero, if below the chunker's minimum).
- Resume with no detectable sections (no "Experience"/"Skills" headers) - `ResumeParser` already handles this gracefully per its unit tests, but the pipeline as a whole hasn't been checked against it.
- The exact same resume ingested twice for the same profile - should legitimately skip the second time, and this needs its own test since the workaround in step 1 otherwise hides that behavior entirely.
