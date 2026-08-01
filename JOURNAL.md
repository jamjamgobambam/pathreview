## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/6

**Issue title:** Duplicate embeddings generated when re-ingesting the same repository

**Tier:** Tier 2  

**Problem summary:**
Right now, the app can ingest the same GitHub repository more than once and store repeated embeddings for the same content. This makes retrieval less reliable because duplicate chunks can show up as if they are more important than they really are. The fix should make repo ingestion recognize already-processed sources and avoid adding duplicate vector entries.

**Tier and scope reasoning:**
This scope feels like a good fit for me because it is focused enough to complete, but still pushes me to trace how data moves through the ingestion pipeline, database model, and vector store. I have already located the main files involved, so I can work from a clear starting point instead of trying to understand the whole app at once. It also feels realistic for the Week 8-9 timeline because the goal is specific: prevent duplicate ingestion and prove the behavior with targeted tests.

**Branch name:** fix/6-duplicate-embeddings-error

**Setup confirmation:** ✅ App runs locally at localhost:5173

**Cohort ledger:** ✅ Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction documentation:** \
I reproduced the issue by calling `IngestionPipeline.ingest_repo_metadata()` twice with the same `profile_id` and the same fake GitHub repo metadata. To keep the reproduction focused, I used the existing `MockEmbeddingProvider`, a fake database session, and a recording fake vector DB that counts every `add()` call. The first ingestion returned `skipped=False` with `chunk_count=1`, which is expected. The second ingestion also returned `skipped=False` with `chunk_count=1` instead of skipping the already-ingested repo. The vector DB recorded two writes for the same embedding ID, confirming that re-ingesting the same repository can create duplicate vector entries.

**Reproduction commit link:** https://github.com/RuiZhangg/pathreview/commit/28a22101

**Reproduction summary:** Refer to above documentation

**PLAN.md link:** https://github.com/RuiZhangg/pathreview/blob/fix/6-duplicate-embeddings-error/PLAN.md

**Blockers or open questions:** None



## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I added a focused unit test for duplicate repository ingestion in `tests/unit/test_ingestion_pipeline.py` and implemented the backend fix in `ingestion/pipeline.py`. The pipeline now serializes repo metadata consistently, checks `IngestedSource` before processing a repo, records a real ingested-source row after a successful first ingestion, and skips the second ingestion instead of writing duplicate embeddings. The targeted test now passes, and `ruff` passes on the touched files.

**Next steps:**
I need to review the final diff, commit only the relevant files for this issue, push the branch, and open the PR with a complete description. After the PR is open, I need to request peer or mentor feedback and then update Check-in 2 with the PR link, testing summary, and feedback source.

**Blockers:**
The full repo checks still have pre-existing failures outside this issue: `make test-unit` still reports 53 known failures, and `make check` still fails on repo-wide lint issues unrelated to `ingestion/pipeline.py` or the new test file. I will document those in the PR notes so reviewers can separate baseline problems from this fix.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/498

**Branch:** `fix/6-duplicate-embeddings-error`

**What you built:**
I fixed duplicate repository ingestion by checking `IngestedSource` before processing repo metadata and recording a real ingested-source row after the first successful ingestion. Re-ingesting the same repo now returns a skipped result instead of writing duplicate embeddings.

**Tests added or updated:**
Added `tests/unit/test_ingestion_pipeline.py`, covering duplicate repo ingestion and verifying the second ingestion does not write another vector entry.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

**Draft PR feedback received from:** none yet
