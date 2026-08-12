## Solution plan

**Issue:** [Add a performance benchmark for the ingestion pipeline to detect regressions](https://github.com/ascherj/pathreview/issues/112)

### Understand
This is a feature gap, not a bug. there is no reproduction, only a missing test. `tests/benchmarks/` currently contains only an empty `__init__.py`; no `test_ingestion_performance.py` exists, and `pytest-benchmark` (already listed in `pyproject.toml` dev deps) is not used anywhere in the codebase. There is also no existing "ingest a full portfolio" helper anywhere — `IngestionPipeline` (`ingestion/pipeline.py`) only exposes three per-source methods (`ingest_resume`, `ingest_readme`, `ingest_repo_metadata`); the API layer's `_run_ingestion_pipeline` in `core/services/review_service.py` is a placeholder stub that doesn't call the real pipeline at all. So "expected behavior" is: a new pytest-benchmark test that drives `IngestionPipeline` through a representative workload (1 resume + 5 repos, each with a README + metadata) and fails the test if mean runtime exceeds 30 seconds. "Actual behavior" today: no such check exists, so a regression (e.g., an accidental O(n²) loop in chunking, or a change that removes batching) would go undetected until a user notices slow ingestion in production.

Every parser/chunker touched by the pipeline (`ResumeParser`, `ReadmeParser`, `RepoAnalyzer`, `SemanticChunker`, `StructuralChunker`) is pure CPU work (regex + `tiktoken` encoding) with no network or disk I/O — the only I/O boundary is `EmbeddingProvider.embed()` and the `vector_db.add()` call, both of which the codebase already has clean seams to mock (`MockEmbeddingProvider` in `ingestion/embeddings/provider.py`, already used in `tests/unit/test_batch_processor.py`). This means a 30s budget is generous and the benchmark is really a regression tripwire on the pipeline's own logic, not a test of network latency.

### Map
- `tests/benchmarks/test_ingestion_performance.py` — new file, the benchmark itself (the file the issue names).
- `ingestion/pipeline.py` — `IngestionPipeline.ingest_resume`, `.ingest_readme`, `.ingest_repo_metadata` are what gets benchmarked.
- `ingestion/embeddings/provider.py` — `MockEmbeddingProvider`, used so the benchmark measures pipeline overhead, not real OpenAI network calls.
- `ingestion/pipeline.py:_check_skip` (line 280) — **gotcha**: it calls `self.db_session.query("IngestedSource").filter_by(...).first()`. If `db_session` is a bare `Mock()`, `.first()` returns a truthy `Mock` object, so every call gets silently short-circuited as "already ingested" (`skipped=True`, 0 chunks) and the benchmark would measure almost nothing. The mock session's `.first()` must be wired to return `None`.
- `tests/conftest.py` — existing `sample_resume_text` / `sample_readme_text` fixtures; benchmark will need its own fixtures for 5 distinct repo payloads (`repo_data` dicts) sized like real GitHub API responses.
- `pyproject.toml` — `pytest-benchmark>=4.0.0` already declared under `[project.optional-dependencies].dev`; `benchmark` marker already registered in `[tool.pytest.ini_options]`.
- `Makefile` — no `test-benchmark` target exists yet; will add one alongside `test-unit`/`test-integration` for discoverability (not required by the issue, but consistent with repo conventions).

### Plan
1. Add fixtures representing a "large portfolio": one multi-section resume (markdown, since PDF parsing is exercised elsewhere) and five distinct repo payloads, each with realistic `repo_data` (matching the shape `RepoAnalyzer.parse` expects: `name`, `description`, `language`, `stargazers_count`, `file_structure`, etc.) plus a README of a few hundred words.
2. Build the pipeline under test with `MockEmbeddingProvider`, a `Mock()` vector DB, and a `Mock()` db_session whose `query(...).filter_by(...).first()` explicitly returns `None` so every source is actually processed, not skipped.
3. Write the benchmarked function: ingest the resume, then loop over the 5 repos calling `ingest_repo_metadata` + `ingest_readme` for each, wrapped via `pytest-benchmark`'s `benchmark()` fixture (or `benchmark.pedantic` if setup/teardown needs to be excluded from timing).
4. Assert on `benchmark.stats.stats.mean < 30` (seconds) so the test fails outright on regression, in addition to pytest-benchmark's normal reporting — per the issue, "fails if mean ingestion time exceeds the threshold."
5. Wire it up for discoverability: add a `make test-benchmark` target (`pytest tests/benchmarks -v -m benchmark`) mirroring `test-unit`/`test-integration`; leave it out of the default CI `test-unit`/`test-integration` jobs since benchmark timing is noisy on shared CI runners (note this as a deliberate scope decision, confirm with maintainer if it should be wired into `ci.yml` instead).

### Inputs & outputs
**Input:** a synthetic "large portfolio" fixture — 1 resume (markdown text) + 5 repos (each a `repo_data` dict + README markdown string) — fed through `IngestionPipeline` with mocked embedding/storage/db boundaries.
**Output:** a new `tests/benchmarks/test_ingestion_performance.py` that (a) runs under `pytest-benchmark` and produces timing stats, and (b) asserts mean ingestion time < 30s, failing CI/local runs on regression. Possibly a small `Makefile` addition.

### Risks & unknowns
- The `_check_skip` mock gotcha above is easy to get wrong silently (test "passes" but measures ~0 real work) — need an explicit assertion that `chunk_count > 0` / `skipped is False` for each result, not just the timing assertion, so a broken mock fails loudly instead of just looking suspiciously fast.
- 30s is generous for CPU-only mocked work, so the benchmark may always be far under threshold on dev/CI hardware — need to double check that it would actually catch a real regression (e.g. temporarily introduce an O(n²) chunking bug locally and confirm the test fails) rather than being a check that can never trip.
- pytest-benchmark's calibration (multiple rounds/iterations) could make a single "ingest everything" benchmark run for a while during autotuning; may need `benchmark.pedantic(..., rounds=..., iterations=1)` to keep it fast and deterministic given ingestion has side effects (mock call counts) that shouldn't accumulate across rounds.
- Unsure whether maintainers want this gated in `ci.yml` (currently it only runs `test-unit` and `test-integration`) or left as a local/manual check — flagging this as an open question rather than assuming.

### Edge cases
- Empty/near-empty README or resume section (chunkers already have `if not text or not text.strip(): return []` guards — worth confirming the benchmark fixtures don't accidentally hit this and undercount work).
- A repo with a very large README (`section_tokens > SECTION_TOKEN_LIMIT` triggers `StructuralChunker` falling back to `SemanticChunker` sub-chunking) — include at least one oversized README among the 5 to exercise that path, since it's the more expensive branch.
- Ensure the benchmark is marked `@pytest.mark.benchmark` (marker already registered) so it can be selected/excluded independently of `test-unit`/`test-integration`.
