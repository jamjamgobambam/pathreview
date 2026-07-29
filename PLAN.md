## Solution plan

**Issue:** [#6 — Duplicate embeddings generated when re-ingesting the same repository](https://github.com/ascherj/pathreview/issues/6)

### Understand

Reuploading identical content creates duplicate vector entries and skews retrieval. Reproduction (`tests/unit/test_pipeline_repro.py`) confirms two independent, stacked bugs. Both need fixing.

1. **`_check_skip()` fails.** calls `self.db_session.query("IngestedSource").filter_by(source_id=source_id).first()`, the old sync SQLAlchemy 1.x API. The real session (`core/database.py`, `AsyncSessionLocal`, built with `class_=AsyncSession`) has no `.query()` method. The `AttributeError` is caught by a broad `except Exception`, logged as a warning, and `_check_skip()` returns `None`. That means "proceed," every time. Confirmed: both calls in the reproduction hit this warning, and `batch_processor.process` runs twice for identical content.

2. **The query targets a column that doesn't exist.** `filter_by(source_id=source_id)` assumes a `source_id` column. `core/models/ingested_source.py` has `profile_id` and `content_hash` (both indexed), no `source_id`. `source_id` is built in memory at call time (`f"resume_{profile_id}_{hash}"`), never persisted. A correct query needs to filter on `profile_id` + `content_hash` instead.

3. **`_record_ingested_source()` writes nothing.** only calls `logger.info(...)`. No `IngestedSource(...)`, no `db.add()`, no `commit()`. Even a fixed query would have nothing to find.

`ingest_resume`, `ingest_readme`, and `ingest_repo_metadata` all share these two helpers, so one fix covers all three ingestion paths.

**Expected behavior:** re-ingesting content with the same `(profile_id, content_hash)` should return `IngestResult(skipped=True, ...)` before parsing, chunking, or embedding. New or changed content (different hash) should still process normally.

### Map

- **`ingestion/pipeline.py`**: `_check_skip()` (line 280) and `_record_ingested_source()` (line 310) get the fix. `ingest_resume`, `ingest_readme`, `ingest_repo_metadata` (lines 55, 126, 201) call both and need to become async.
- **`core/models/ingested_source.py`**: confirms the real schema. No model changes needed.
- **`core/database.py`**: confirms `db_session` is an `AsyncSession` (line 21-27). This is why `.query()` fails and why the fix needs `select(...)` + `await db.execute(...)`.
- **`core/services/profile_service.py`, `core/services/review_service.py`**: the existing async pattern to follow: `select(Model).where(...)`, `await db.execute(stmt)`, `result.scalars().first()`/`.all()` for reads; `db.add(...)`, `await db.commit()` for writes. Confirmed by grep.
- **`tests/unit/test_batch_processor.py`, `tests/unit/test_review_service.py`**: mocking conventions to follow (`Mock`/`AsyncMock`, `@pytest.mark.asyncio`).
- **`tests/conftest.py`**: no DB-session fixtures exist yet, confirmed. Will add one if more than one test file needs it.
- **`api/routes/profiles.py`**: parses resumes inline, never calls `IngestionPipeline`. Confirmed by grep across the repo: zero call sites for `IngestionPipeline(`, `ingest_resume(`, `ingest_readme(`, `ingest_repo_metadata(`. The pipeline is currently unwired from any live route. Wiring it in is a separate task, out of scope here.

### Plan

1. Confirm the production session type and query idiom (done, see Map).
2. Rewrite `_check_skip()` as `async def _check_skip(self, profile_id: str, source_type: str, content_hash: str) -> Optional[IngestResult]`. Query with `select(IngestedSource).where(IngestedSource.profile_id == profile_id, IngestedSource.content_hash == content_hash)`, then `await self.db_session.execute(stmt)`, then `result.scalars().first()`. Narrow the except so a real error gets logged loudly instead of treated as "proceed."
3. Rewrite `_record_ingested_source()` to actually persist: build `IngestedSource(profile_id=..., source_type=..., content_hash=..., filename=..., chunk_count=...)`, `self.db_session.add(record)`, `await self.db_session.commit()`.
4. Convert `ingest_resume`, `ingest_readme`, `ingest_repo_metadata` to `async def` and await the two helper calls. Compute `content_hash` once and pass it through, instead of re-deriving it from `source_id`.
5. Re-run the reproduction test, adapted to await the now-async pipeline. Confirm it flips from failing to passing.
6. Extend `tests/unit/test_pipeline.py` (new file): changed content does not skip; `_record_ingested_source` calls `db.add`/`db.commit` with correct fields; a profile with no prior rows proceeds normally.
7. Run `make test-unit` and `make check` before calling it done.
8. Note in the PR whether wiring `IngestionPipeline` into a route is in scope. Default: out of scope, follow-up issue.

### Inputs & outputs

**Methods changing:**
- `_check_skip(self, profile_id: str, source_type: str, content_hash: str) -> Optional[IngestResult]`. Was `(self, source_id: str, source_type: str)`, sync.
- `_record_ingested_source(self, profile_id: str, source_type: str, content_hash: str, filename: str | None, chunk_count: int) -> None`. Was sync and non-persisting.
- `ingest_resume`, `ingest_readme`, `ingest_repo_metadata`: become `async def`. Breaking change in principle, but zero call sites today, confirmed.

**Happy path:** new content in, `IngestResult(skipped=False, chunk_count=N)` out, embeddings stored, one new `IngestedSource` row written.

**Duplicate path (the fix):** content with an existing `(profile_id, content_hash)` match returns `IngestResult(skipped=True, chunk_count=0, skip_reason="Source already ingested")`. `batch_processor.process` never runs. No new row.

### Risks & unknowns

1. **Async signature change.** Confirmed zero call sites today via grep. Will re-check right before opening the PR.
2. **Mock pitfall, confirmed while reproducing.** A bare `Mock()` for `db_session` does not reproduce this bug: `Mock().query(...).filter_by(...).first()` returns a truthy `Mock`, so `_check_skip` falsely succeeds on the first call. Only `Mock(spec=AsyncSession)` raises the real `AttributeError` (confirmed in the reproduction log). `test_pipeline.py` needs the same spec, or it tests a fiction.
3. **Dedup scope is ambiguous.** Should `content_hash` be scoped per `profile_id`, or global? Two users uploading the same README template would hash identically. Scoping per-profile for now, matching the model's FK, but flagging this in the PR.
4. **Vector store behavior on repeated IDs is unconfirmed.** Haven't checked whether ChromaDB's `.add()` errors, overwrites, or duplicates on a repeated `embedding_id`. Will check before calling the fix done.
5. **Narrowing the except could turn a transient DB error into a hard failure**, where today it silently (wrongly) proceeds. Failing loudly seems like the right tradeoff, but need to confirm it doesn't break some other expected fallback path.
6. **Found, but out of scope: a separate bug in `core/services/review_service.py`.** `_run_ingestion_pipeline()`, called from the live `POST /reviews` background task, constructs `IngestedSource(profile_id=..., source_type=..., raw_data=json.dumps(...))`. model has no `raw_data` column, so this likely fails silently every time (caught by a bare except). This function also has no dedup check at all. Not fixing this here: issue #6 is filed as Tier 2, scoped to `ingestion/pipeline.py` + `core/models/ingested_source.py`, and this is a different module with a different bug. Also confirmed `_run_agent_orchestration` and `_run_rag_retrieval_generation` are stub functions returning hardcoded data (comment: "In production, this would: 1. Embed ingested content..."), so no real embedding generation happens on the live path today either way. Flagging this as a candidate follow-up issue in the PR.

### Edge cases

- Same profile re-ingests identical content: should skip, zero new embeddings. Covered by the reproduction test.
- Same profile re-ingests changed content (different hash): should not skip, should add a new row. Open question tied to risk 3: replace the old row, or keep both? No versioning logic exists elsewhere in the codebase, so defaulting to "add new" unless told otherwise.
- Two different profiles upload identical content: per risk 3, current plan does not skip this, since the query is scoped by `profile_id`.
- Brand-new profile with no prior rows: query returns nothing, proceeds normally. This is the "first call" case in the reproduction.
- DB query fails for an unrelated reason (connection drop): per risk 5, should now fail loudly instead of silently proceeding. Need to confirm this doesn't regress any expected fallback behavior.