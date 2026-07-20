## Solution plan

**Issue:** [#13 — Add a content hash to detect unchanged documents and skip re-embedding](https://github.com/jamjamgobambam/pathreview/issues/13)

### Understand

The ingestion pipeline re-embeds every document it receives, including documents whose content has not changed since the last ingest. Each re-ingest costs embedding API calls and processing time that produce identical vectors.

The deduplication machinery is half-built. `IngestionPipeline._hash_content()` already computes a SHA256 digest of the content, and the `IngestedSource` model already carries an indexed `content_hash` column sized for a full SHA256 (`String(64)`). The two halves are never joined:

- `_check_skip()` calls `self.db_session.query("IngestedSource")`, passing a string literal where the ORM model class belongs, and filters on `source_id`, which is not a column on `IngestedSource`. Verified against the live schema: the table has `id`, `profile_id`, `source_type`, `source_url`, `filename`, `content_hash`, `chunk_count`, `ingested_at`. Two independent failures in one query.
- `_record_ingested_source()` performs no database work at all. It logs the values it was given and returns.

Both failures are silent. `_check_skip()` wraps its query in `try/except` that logs a warning and returns `None`, which the caller reads as "proceed with ingestion." So the pipeline behaves exactly as if deduplication had never been requested.

A third failure sits underneath: `core/database.py` builds an async engine and an `async_sessionmaker` with `class_=AsyncSession`, and `get_db()` yields an `AsyncSession`. `AsyncSession` has no `.query()` method, so the placeholder query would raise `AttributeError` even if the model class and column name were correct.

Expected behavior after the fix: ingesting a document records an `IngestedSource` row carrying its content hash, and re-submitting identical content for the same profile returns `IngestResult(skipped=True)` without calling the embedding provider. Changed content ingests normally.

### Map

Files expected to change:

- `ingestion/pipeline.py` — `_check_skip()`, `_record_ingested_source()`, `_hash_content()`, and the three public entry points `ingest_resume()`, `ingest_readme()`, `ingest_repo_metadata()`
- `tests/unit/test_ingestion_pipeline.py` — new file; no unit test currently covers `IngestionPipeline`

Files read and depended on, not expected to change:

- `core/models/ingested_source.py` — the target model; column set confirmed against the live table via `psql -c '\d ingested_sources'`
- `core/database.py` — establishes that every session the application can supply is an `AsyncSession`
- `ingestion/embeddings/batch_processor.py` — the call being skipped

Out of scope, noted for the reviewer: `core/services/review_service.py` runs a second, unrelated ingestion path (`_run_ingestion_pipeline`) that constructs `IngestedSource` with a `raw_data=` keyword matching no column on the model. It never calls `IngestionPipeline`. Fixing it is a separate issue and would widen this diff beyond the two files named in #13.

### Plan

1. **Convert the pipeline's database access to async.** Change `_check_skip()` and `_record_ingested_source()` to `async def`, and propagate `async`/`await` up through `ingest_resume()`, `ingest_readme()`, and `ingest_repo_metadata()`. This matches the only session type the application produces.

2. **Rewrite `_check_skip()` against the real model.** Replace the string literal and the `.query()` call with `select(IngestedSource)` filtered on `content_hash`, `profile_id`, and `source_type`, executed via `await self.db_session.execute(...)` and read with `.scalars().first()`. Scoping by profile and source type prevents one profile's content from suppressing another's ingest. Change the signature to accept the content hash, since `source_id` is not queryable.

3. **Implement `_record_ingested_source()`.** Construct an `IngestedSource` with `profile_id`, `source_type`, `content_hash`, and `chunk_count`, add it to the session, and commit. Add a `content_hash` parameter to the signature; the current parameters (`source_id`, `source_type`, `profile_id`, `chunk_count`) do not include the value the issue is about.

4. **Widen `_hash_content()` to the full digest.** It currently truncates to 16 hex characters while the column holds 64. Return the full `hexdigest()` for storage and keep a truncated slice where `source_id` is assembled, so chunk metadata in the vector store keeps its current shape.

5. **Write unit tests in `tests/unit/test_ingestion_pipeline.py`.** Cover the skip path, the changed-content path, and the profile-isolation case, using a mocked async session and a stub embedding provider so the suite makes no network calls.

6. **Narrow the exception handling.** The current bare `except Exception` in `_check_skip()` is what hid this bug. Catch database errors specifically, and let programming errors surface.

### Inputs and outputs

**Inputs.** `_check_skip(content_hash: str, profile_id: str, source_type: str)` replaces the current `(source_id, source_type)` signature. `_record_ingested_source(...)` gains a `content_hash: str` parameter. The three public entry points keep their existing arguments (`profile_id`, `content`, and a filename or repo identifier) but become coroutines.

**Outputs.** Behavior changes rather than return types. On unchanged content, `IngestResult(skipped=True, chunk_count=0, skip_reason="Source already ingested")` is returned and `BatchEmbeddingProcessor.process()` is never called. On new or changed content, `IngestResult(skipped=False)` is returned as today and one row is written to `ingested_sources`.

**Side effects.** A row per successful ingest, where previously none was written. `content_hash` is populated with a 64-character digest.

### Risks and unknowns

- **No existing caller constructs `IngestionPipeline`.** `grep -rn "IngestionPipeline(" --include=*.py` returns nothing across the repository. Nothing breaks when the methods become coroutines, but nothing validates the choice either, so the unit tests are the only consumer of the new contract. If a caller is added later expecting synchronous methods, this decision is what it will collide with.
- **`content_hash` has no unique constraint.** The live schema shows an index but no uniqueness. Two concurrent ingests of the same content can both pass the skip check and write duplicate rows. The read side handles it with `.first()`; a database-level constraint would be a schema change beyond this issue's scope.
- **`profile_id` type mismatch.** `IngestionPipeline` annotates `profile_id` as `str` while the column is `UUID(as_uuid=False)`. Whether SQLAlchemy coerces a plain string on insert and on comparison needs confirming against Postgres, not assumed. This is the same class of assumption that produced the `raw_data` bug in `review_service.py`.
- **Commit ownership is unsettled.** Committing inside `_record_ingested_source()` may conflict with a caller managing its own transaction. `flush()` instead would leave durability to the caller, but with no caller in existence there is nothing to match. Committing is the choice here because it makes the pipeline self-contained; it is worth flagging in the pull request.
- **Mocking an `AsyncSession` is easy to get wrong.** `execute()` is awaitable while `.scalars().first()` is not, so a naive `AsyncMock` produces coroutines where the code expects values, and a test can pass for the wrong reason.
- **`make test-unit` filters on a marker.** The target runs `pytest tests/unit -v -m unit`, so a new test module without `pytestmark = pytest.mark.unit` is silently deselected and never runs. Verified: the reproduction file was reported as "5 deselected" until the marker was added.
- **Neither project gate passes on main.** `make test-unit` reports 53 failures before any change to this branch, across `test_bias_detector.py`, `test_pii_scrubber.py`, `test_resume_parser.py`, `test_skill_extractor.py`, `test_review_service.py`, and others. `make check` fails at its first step, `ruff check .`, with 183 errors. Neither baseline is caused by this work, and neither can be made green within the scope of this issue. The contribution standard has to be met by showing no new failures rather than a clean run.
- **`ingestion/pipeline.py` carries 4 pre-existing lint errors.** Editing the file surfaces them alongside the real changes, forcing a decision about whether fixing them belongs in this diff or stays out of scope.
- **The unit suite does not pass on `main`.** Running `make test-unit` against an unmodified checkout produces 53 failures across `test_bias_detector.py`, `test_pii_scrubber.py`, `test_resume_parser.py`, `test_skill_extractor.py`, `test_review_service.py`, and others. None are in files this fix touches. The contribution standard therefore has to be met by showing no new failures against a recorded baseline rather than by a green run.
- **`make test-unit` filters on a marker.** The target runs `pytest tests/unit -v -m unit`, so any test module without `pytestmark = pytest.mark.unit` is silently deselected and reports as passing work that never executed. A bare `MagicMock` is worse: `db_session.query(...).filter_by(...).first()` returns a truthy object, so the skip check appears to work against entirely unfixed code. Specifying `spec=AsyncSession` is what prevents both.
- **The unit suite does not pass on `main`.** A baseline run before any change to production code produced 53 failures across `test_bias_detector.py`, `test_pii_scrubber.py`, `test_resume_parser.py`, `test_skill_extractor.py`, `test_review_service.py`, `test_tech_detector.py`, and others, none of which this issue touches. `make test-unit` therefore cannot report green, and the contribution standard has to be demonstrated as a baseline comparison: 53 failures before, no new failures after, none in the files changed here.
- **`make test-unit` filters on a pytest marker.** The target runs `pytest tests/unit -v -m unit`, so any new test module without `pytestmark = pytest.mark.unit` is silently deselected rather than reported as skipped. A test file can appear to be passing when it never ran at all.

### Edge cases

- **Identical content re-submitted for the same profile.** Must skip and must make zero embedding calls. Asserting the call count, not just the `skipped` flag, is what proves the API saving.
- **Content changed by a single character.** Produces a different digest, so the pipeline must ingest normally rather than skip.
- **Same content under two different profiles.** Must ingest for both. A skip check keyed on `content_hash` alone would wrongly suppress the second profile.
- **Same content ingested as two different source types**, for example a README also submitted as resume text. Scoping by `source_type` keeps these independent.
- **Existing rows with `content_hash` set to NULL.** The column is nullable and other code paths write rows without it, so a NULL must never compare equal to a computed hash and trigger a false skip.
- **`str`/`bytes` content for the same document.** `_hash_content()` encodes strings before hashing, so a README passed as text and as bytes must yield the same digest and skip on the second pass.
- **`ingest_repo_metadata` hashes `str(repo_data)`.** Dictionary ordering changes the string form, so semantically identical metadata can hash differently and defeat the skip. Serializing with sorted keys is the likely correction.
- **Embedding succeeds but the row write fails.** The next run re-embeds. Wasteful but not corrupting, and preferable to recording a source whose vectors were never stored.
