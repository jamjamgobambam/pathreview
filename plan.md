## Solution plan

**Issue:** [Duplicate embeddings generated when re-ingesting the same repository](https://github.com/ascherj/pathreview/issues/6)

### Understand

`pipeline.py` doesn't check whether the file has already been ingested, so when a Github repo is re-ingested, the pipeline duplicates vector entries, which can inflate the retrieval scores of the duplicated chunks.

An expected behavior would skip ingestion when a repeated file is detected, signal that it was a duplicate, and simply retur the existing result.

Digging in, I found the deduplication is really two unfinished placeholders. First, `_check_skip` calls `self.db_session.query("IngestedSource")`, which is the old synchronous Query API — but this project runs on an `AsyncSession` that doesn't even have a `.query()` method. So the call throws, the surrounding `except` quietly swallows it, and the function returns `None`, meaning ingestion always proceeds. Second, `_record_ingested_source` only writes a log line; it never actually inserts an `IngestedSource` row. So even if the lookup worked, there would be nothing in the database to match against.

### Map

Both halves need to be made real. I'll rewrite `_check_skip` and `_record_ingested_source` in `pipeline.py` to use the `IngestedSource` model through the async session, which means `select(...)` with `await session.execute(...)` rather than the sync `.query()`.

### Plan

Step 1 — Decide what identifies a duplicate. There are two reasonable keys. The lighter one reuses the `content_hash` column that already exists on `IngestedSource`, matched alongside `profile_id` and `source_type`, so there's no schema change. The cleaner one adds a dedicated `source_id` column that stores the composite id the pipeline already builds, making the lookup a single-key match but costing a migration. I'm leaning toward `content_hash`.

Step 2 — Fix `_check_skip`. Replace the placeholder so it selects an existing `IngestedSource` by the chosen key, and when it finds one, returns `IngestResult(skipped=True, ...)` instead of re-ingesting.

Step 3 — Implement `_record_ingested_source`. Make it genuinely record a row (`session.add(...)` followed by `await session.commit()`) once an ingest succeeds, so there's actually something for Step 2 to find.

Step 4 — Make the ingest methods async. Because Steps 2 and 3 now `await`, the three `ingest_*` methods have to become `async def`.

Step 5 — Turn the reproduction test into a regression test. Flip `tests/unit/test_pipeline_dedup.py` to assert the fixed behaviour (second call skipped, no duplicate vectors).

### Inputs & outputs

Input: the fix works inside the existing `ingest_*` calls, taking a `profile_id` plus the content itself as input.

Output: the first call ingests normally and records one `IngestedSource` row, and any later call with the same content returns a skipped result, writes no new vectors, and adds no new row.

### Risks & unknowns

Turning the ingest methods async is technically a signature change, so I'll call it out in the PR even though there are no callers to break yet. There's also a concurrency corner: two simultaneous ingests of the same source could both pass the check before either records, so a unique constraint on the dedup key is the real safeguard there.

### Edge cases

The happy case is identical content being re-ingested, which should now skip. I want to be careful not to over-skip, though: if a repo's metadata shifts slightly (a new star count or `pushed_at`), the hash legitimately changes and it should ingest as fresh, not be treated as a duplicate. And if an ingest fails partway through, it must not record an `IngestedSource` row, so a retry can still succeed.
