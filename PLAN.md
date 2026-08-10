## Solution plan

**Issue:** [Add end-to-end ingestion test with a sample resume fixture (#18)](https://github.com/ascherj/pathreview/issues/18)

### Understand

This is a **missing-coverage** issue, not a runtime bug. The ingestion module
already works, but every automated test exercises a single component in
isolation (`tests/unit/test_resume_parser.py`, `test_semantic_chunker.py`,
`test_batch_processor.py`, …). Nothing drives the orchestrator
`IngestionPipeline.ingest_resume()` in `ingestion/pipeline.py`, which chains the
whole flow: **parse → chunk → embed → store → record**.

- **Expected:** an integration test proves that a sample resume, fed in as it
  would be on upload, flows through all stages and lands as stored embeddings —
  so a regression at any *seam between components* (e.g. metadata dropped
  between parser and chunker, wrong text passed to the embedder) is caught.
- **Actual:** `tests/integration/` contains only `__init__.py` and collects
  **0 tests**; there is no `tests/fixtures/` directory at all. Verified in the
  Week 7 reproduction commit.

### Map

Files involved (read during research; the pipeline and its collaborators are
**not** being modified — the fix is test-only):

| File | Role |
|------|------|
| `ingestion/pipeline.py` | Orchestrator under test — `ingest_resume()` |
| `ingestion/parsers/resume_parser.py` | Markdown/PDF → text + `detected_sections` |
| `ingestion/chunking/strategy_selector.py` → `semantic_chunker.py` | Resume uses the semantic chunker; adds `chunk_index`, `char_start/end` |
| `ingestion/embeddings/batch_processor.py` | Batches chunks, calls provider, `vector_db.add(ids, embeddings, metadatas, documents)` |
| `ingestion/embeddings/provider.py` | Ships `MockEmbeddingProvider` — deterministic 1536-dim vectors, offline |

**Files I expect to create:**
- `tests/fixtures/sample_resumes/sample_resume.md` — realistic markdown resume fixture.
- `tests/integration/test_ingestion_pipeline.py` — the end-to-end test.
- (Possibly) a small fixture/helper in the test file: a `FakeVectorDB` spy and a
  configured mock `db_session`.

No production code changes are planned.

### Plan

1. **Add the fixture.** Create `tests/fixtures/sample_resumes/sample_resume.md`
   with clearly detectable sections (Experience, Education, Skills, Projects) so
   the parser's `detected_sections` and the chunker have real structure to work
   on. Resolve its path in the test relative to `__file__` (not the cwd).
2. **Build offline test doubles.** Use the existing `MockEmbeddingProvider`
   (real class, no network). Add a tiny `FakeVectorDB` spy that records every
   `add(...)` call. Configure a mock `db_session` so
   `query(...).filter_by(...).first()` returns `None` — otherwise `_check_skip`
   treats the source as already ingested and the pipeline no-ops.
3. **Write the happy-path e2e test.** Instantiate `IngestionPipeline`, call
   `ingest_resume(profile_id, content=<fixture text>, filename="sample_resume.md")`,
   and assert on the returned `IngestResult` **and** the side effects captured by
   the spy (see Inputs & outputs).
4. **Add seam/behavior assertions.** Verify the data actually threaded through:
   stored `documents` are non-empty chunk texts, each embedding is 1536-dim,
   every stored metadata carries `source_id`, `profile_id`, `source_type ==
   "resume"`, and `chunk_index`; embedding IDs follow
   `{source_id}_chunk_{index}`.
5. **Mark and wire in.** Decorate with `@pytest.mark.integration` so it runs
   under `make test-integration` (`pytest -m integration`), confirm it passes
   locally, and confirm the previously-empty suite now collects ≥1 test.

### Inputs & outputs

**Input:** a sample resume read from `tests/fixtures/sample_resumes/` (markdown
string), plus a `profile_id` and `filename`, passed to
`IngestionPipeline.ingest_resume()` with mocked embedding/storage/DB
collaborators.

**Output / what changes:** new test + fixture files only. The test *asserts on*
(does not change) these pipeline outputs:
- Returns `IngestResult(source_id=…, chunk_count>=1, skipped=False,
  skip_reason=None)`.
- `FakeVectorDB.add` called ≥1 time; total stored IDs == `chunk_count`.
- Each stored embedding has dimension 1536; each metadata dict contains
  `source_id`, `profile_id`, `filename`, `source_type="resume"`, `chunk_index`,
  and the parser's `detected_sections`.

### Risks & unknowns

- **Do NOT assert an exact `chunk_count`.** De-risk run showed the semantic
  chunker merges a short resume into a **single** chunk. Assert `>= 1` and length
  invariants, not a magic number, so the test isn't brittle to chunker tuning.
- **A real ChromaDB collection would reject this metadata.** `detected_sections`
  is a **list**, and ChromaDB only accepts scalar metadata values. Confirmed
  reason to use an in-memory `FakeVectorDB` spy rather than a live client —
  which also keeps the test hermetic (the `integration` marker is documented as
  "require Docker services", but a fully-mocked ingestion test needs none).
- **`_check_skip` mock shape.** If the mock `db_session` isn't configured to
  return `None` from `.first()`, the pipeline silently skips and the test would
  assert against a no-op. Configured explicitly (verified in de-risk run).
- **PDF fixture (stretch).** A `.pdf` fixture would exercise the `pypdf` path
  too, but committing binary + generating deterministic PDF text is extra
  surface. Plan: ship markdown first; add PDF only if time allows, as a second
  parametrized case.

### Edge cases

- **Duplicate ingestion / skip path:** a second test where `.first()` returns a
  truthy row asserts `IngestResult.skipped is True` and that `vector_db.add` is
  **not** called.
- **Empty / whitespace-only resume:** should not crash; `BatchEmbeddingProcessor`
  already short-circuits on an empty chunk list — assert graceful handling.
- **Metadata propagation:** `profile_id`/`filename` supplied at the top must
  survive all the way into every stored chunk's metadata (the core "seam" this
  test exists to protect).
- **Determinism:** `MockEmbeddingProvider` is hash-seeded, so identical input
  yields identical vectors — assertions on embeddings stay stable across runs.
