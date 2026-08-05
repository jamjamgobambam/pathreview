# Solution plan

**Issue:** [#6 — Duplicate embeddings generated when re-ingesting the same repository](https://github.com/ascherj/pathreview/issues/6)

## Understand

The ingestion pipeline is supposed to be idempotent — re-ingesting a source it has already processed should be a recorded no-op — but every piece of the dedup mechanism is broken, in three distinct ways:

1. **The skip-check can never succeed.** `_check_skip()` (`ingestion/pipeline.py:280`) calls `self.db_session.query("IngestedSource")` — passing the *string* `"IngestedSource"`, not the model class — filtered on a `source_id` column that doesn't exist on the model, and wraps it all in a catch-all `except` that downgrades the failure to a warning and proceeds. With the app's real session the call fails every single time (reproduced: `'AsyncSession' object has no attribute 'query'`), so nothing is ever skipped, and the bug hides itself in a log line nobody reads.
2. **Nothing is ever recorded.** `_record_ingested_source()` (`ingestion/pipeline.py:310`) says it in its own comment: "This is a placeholder for actual database recording." It only logs. Reproduced: after four ingests, `select count(*) from ingested_sources` returns **0**.
3. **The repo dedup key is built from volatile data.** `ingest_repo_metadata()` (`ingestion/pipeline.py:217`) hashes `str(repo_data)`, which includes fields like `stargazers_count` and `pushed_at` that change between GitHub fetches. The "same repo" therefore gets a new `source_id` on every re-fetch, which flows into new Chroma chunk IDs (`batch_processor.py:108`).

**Expected behavior:** the second ingest of unchanged content returns `skipped=True` with zero embedding calls and no vector-store writes.
**Actual behavior (reproduced locally with `scripts/repro_issue_6.py`):** a byte-identical README ingested twice returns `skipped=False` both times and calls the embedding provider again (double cost; the Chroma count stays flat only because the colliding chunk IDs are silently dropped by `add()`). The same repo re-fetched with a star-count change goes from 4 to 5 vectors, and a retrieval query then returns the same repo text twice — 2 of the top 5 hits — under two different `source_id`s.

## Map

Files I expect to touch:

- `ingestion/pipeline.py` — implement `_check_skip()` and `_record_ingested_source()` for real; fix `ingest_repo_metadata()` hashing; likely convert the three `ingest_*` methods to `async` (see Risks)
- `core/models/ingested_source.py` — add the dedup key: a unique `source_id` column (the model already has `content_hash`, but the pipeline queries `source_id`; the two need reconciling)
- `alembic/versions/003_*.py` — new migration for the column + unique constraint, following the `001_initial_schema.py` / `002_add_error_message_to_reviews.py` patterns
- `tests/unit/test_pipeline.py` — new unit test file, modeled on the mock patterns in `tests/unit/test_batch_processor.py`
- `tests/integration/` — one integration-marked test against the dockerized Postgres
- Read-only reference: `ingestion/embeddings/batch_processor.py` (chunk ID scheme), `core/database.py` (session factory), `tests/conftest.py` (fixtures)

## Plan

1. **Reconcile the schema with the pipeline's dedup key.** Add `source_id: Mapped[str]` (unique, indexed) to `IngestedSource`; store the full SHA-256 in `content_hash` (the model comments says SHA-256 but the pipeline truncates to 16 hex chars — keep the truncated form only inside the human-readable `source_id`). Write Alembic migration 003. Safe to add as unique: the table is provably empty everywhere, because recording never worked.
2. **Implement `_record_ingested_source()`.** Construct and commit a real `IngestedSource` row (profile_id, source_type, source_id, content_hash, chunk_count, filename/source_url where available). Catch `IntegrityError` and treat it as "another worker recorded it first" (concurrent-ingest race → behave like a skip, don't crash).
3. **Implement `_check_skip()`.** Real SQLAlchemy 2.0 `select(IngestedSource).where(IngestedSource.source_id == ...)`. On DB error: log at **error** level (not warning) and proceed with ingestion — availability over dedup, but loudly. This requires resolving the sync/async mismatch (see Risks) — most likely converting `ingest_resume/readme/repo_metadata` to `async def` since the app is async end-to-end and nothing calls the pipeline yet.
4. **Stabilize the repo hash.** Replace `self._hash_content(str(repo_data))` with a canonical `json.dumps(stable_fields, sort_keys=True)` over identity-relevant fields only (`name`, `description`, `language`, `languages`, `topics`) so a star-count or timestamp change no longer changes the dedup key — while a real description/topic change still triggers re-ingestion.
5. **Tests.** Unit: second identical ingest returns `skipped=True`, embedding provider **not** called again, `vector_db.add` **not** called again; repo hash stable across volatile-field changes but sensitive to stable-field changes; DB-error path proceeds and logs. Integration (`@pytest.mark.integration`): ingest twice against real Postgres, assert exactly one `ingested_sources` row and unchanged vector count. Run `make check && make test-unit` before the PR.

## Inputs & outputs

- **Inputs (unchanged):** `ingest_resume(profile_id, content, filename)`, `ingest_readme(profile_id, repo_name, content)`, `ingest_repo_metadata(profile_id, repo_data)`. The only signature change is the likely `async def` conversion (callers must `await`) — acceptable because the pipeline currently has no production caller.
- **Outputs:** `IngestResult` keeps its shape. First ingest of new content: `skipped=False`, `chunk_count=N`, one new `ingested_sources` row, N vectors written. Re-ingest of unchanged content: `skipped=True`, `chunk_count=0`, `skip_reason="Source already ingested"`, **zero** embedding-provider calls, **zero** vector writes, no new rows.
- **Side-effect contract:** for any source, `ingested_sources` holds at most one row per (`profile_id`, `source_type`, dedup hash), and the Chroma collection's count is stable across repeated ingestion of unchanged content.

## Risks & unknowns

- **Sync/async session mismatch (the riskiest part).** `core/database.py` only exposes an `AsyncSession` factory, but the pipeline's methods are sync. Converting `ingest_*` to `async def` is the app-consistent fix (`pytest-asyncio` is already a dev dependency), but it changes the public API of `IngestionPipeline` and every test that touches it. Investigation path: confirm nothing outside `scripts/` and tests instantiates `IngestionPipeline` (`grep -rn IngestionPipeline --include='*.py'`) before committing to the conversion.
- **Chroma `add()` silently ignores duplicate IDs** (`batch_processor.py:111`) — this masked half the bug. If I only fix hashing, previously-duplicated vectors from old volatile `source_id`s remain in the store. Cleaning up historical duplicates overlaps with issue #27 (stale embeddings) and stays **out of scope**; I'll note it in the PR.
- **Choice of stable fields for the repo hash.** Too narrow (name only) and genuine updates stop re-ingesting; too wide and the bug returns. Unknown until I check what `RepoAnalyzer.parse()` (`ingestion/parsers/repo_analyzer.py`) actually reads — the hash should cover exactly the fields that feed the generated text.
- **Migration on non-empty tables.** If any deployment somehow has `ingested_sources` rows, a unique constraint could fail to apply. Mitigation: migration 003 is written against the observed reality (recording never persisted anything) and the PR will call this out.
- **The mypy pre-commit hook fails on pre-existing upstream errors.** Committing any Python file that imports `ingestion.*` makes mypy follow the imports and report 13 pre-existing errors in 7 upstream files (e.g. `ingestion/pipeline.py:30` untyped `__init__`, `ingestion/pipeline.py:233` passing a `dict` to `RepoAnalyzer.parse()` which is annotated `str | bytes`, `ingestion/chunking/structural_chunker.py:81`). Until those are fixed upstream, commits touching this package need `SKIP=mypy`. For Week 9 I'll add annotations to the functions my diff actually touches so my own code is clean, and flag the rest in the PR.
- **`review_service._run_ingestion_pipeline()` is a placeholder** that never calls `IngestionPipeline` (and passes a nonexistent `raw_data` kwarg to `IngestedSource` in `core/services/review_service.py`). Wiring the HTTP layer to the pipeline is explicitly out of scope; my fix is verified at the pipeline level, same as every existing component test.

## Edge cases

1. **Same repo, volatile metadata changed** (stars 41→42, new `pushed_at`) → must skip. This is the reproduced core case.
2. **Same repo, stable metadata changed** (description or topics edited) → must **not** skip; new hash, full re-ingest.
3. **Same resume content, different filename** → must skip (dedup is content-based; filename is metadata only, and the recorded row keeps the first filename).
4. **Two different profiles ingest identical content** → must **not** cross-deduplicate; `source_id` embeds `profile_id`, and the uniqueness key is scoped per profile.
5. **Concurrent ingest of the same source** (two workers race past `_check_skip`) → second `_record_ingested_source()` hits the unique constraint; catch `IntegrityError` and return normally instead of crashing.
6. **DB unavailable during `_check_skip`** → proceed with ingestion (availability over dedup) but log at error level; never silently swallow like today.
7. **Empty or whitespace-only content** → hash still computes; chunker may return zero chunks; record the row with `chunk_count=0` so re-uploads of the same empty file still skip.
8. **Stale stats inside a skipped repo chunk.** `RepoAnalyzer.parse()` embeds volatile stats directly in the text it hands the embedder (`ingestion/parsers/repo_analyzer.py:78-80` emit `Stars:`, `Forks:`, `Open Issues:`), so once a re-fetch is correctly skipped, the stored chunk keeps the star count it was first ingested with. Accepted deliberately: refreshing stats is a re-ingestion *policy* question adjacent to #27, not part of making ingestion idempotent. Called out in the PR rather than silently widening scope.
9. **Recording fails for a non-race reason** (FK violation on an unknown `profile_id`, DB down mid-commit) → must not be disguised as the benign concurrent-ingest path. Inspect the `IntegrityError`'s SQLSTATE: only `23505` (unique violation) is the race; anything else is logged at error level, and because no row was persisted, the next ingest correctly re-ingests instead of skipping.
