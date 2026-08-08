## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/6

**Issue title:** Duplicate embeddings generated when re-ingesting the same repository

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
The ingestion pipeline currently processes a repository again even when that same repository has already been ingested. This creates duplicate vector embeddings for identical source content, which can cause retrieval results to contain repeated chunks and artificially inflated relevance scores. The problem primarily affects `ingestion/pipeline.py` and the ingested-source tracking model in `core/models/ingested_source.py`. A successful fix would detect an existing ingestion before generating embeddings and prevent duplicate vector entries while preserving legitimate re-ingestion behavior when appropriate.

**Selection notes:**
I reviewed the issue description, relevant files, and estimated effort. The issue requires understanding how the ingestion pipeline checks persisted source records before generating and storing embeddings. The scope is limited to the ingestion workflow and associated tests rather than requiring a major application redesign. I should be able to reproduce the duplicate-ingestion behavior locally and verify that repeated ingestion no longer creates duplicate vector entries.

**Branch name:** fix/6-prevent-duplicate-embeddings

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/SingLZ/pathreview/commit/6af19678b07fbc7a7d6189a0de65fcd473d79b00

**Reproduction summary:**
I reproduced the issue with a focused unit test that ingests identical repository metadata twice for the same profile. The embedding processor was invoked twice instead of once, and the second result was not marked as skipped.

**PLAN.md link:** https://github.com/SingLZ/pathreview/blob/fix/6-prevent-duplicate-embeddings/PLAN.md

**Walkthrough video (recommended):** Not recorded.

**Blockers or open questions:**
I still need to confirm whether changed content from the same repository should create a new ingestion or replace the previous repository vectors. I also need to verify all callers before converting the pipeline’s database operations to use the project’s asynchronous SQLAlchemy session.


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented persistent ingestion deduplication using a unique source identifier stored in the `ingested_sources` table. I replaced the placeholder duplicate lookup and recording logic with asynchronous SQLAlchemy operations, normalized repository metadata so volatile metrics do not trigger re-ingestion, and converted the Week 8 reproduction into regression tests.

**Next steps:**
I will run the project-wide checks, document any pre-existing failures, open a draft pull request, and request feedback from a peer or mentor. After addressing relevant feedback, I will mark the pull request ready for review and complete Check-in 2.

**Blockers:**
The repository contains pre-existing type-checking failures outside the files changed for issue #6. I am validating the affected files independently and confirming that this contribution does not introduce additional failures.

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/576

**Branch:** `fix/6-prevent-duplicate-embeddings`

**What you built:**
I implemented persistent deduplication for repository ingestion. The pipeline now checks a stable source ID before generating embeddings and ignores changes to volatile repository metrics.

**Tests added or updated:**
I added `tests/unit/test_ingestion_pipeline_deduplication.py`, which covers identical repository ingestion, changed star counts, and meaningful repository content changes.

**Self-review confirmation:** [x] make check introduces no new failures  [x] make test-unit introduces no new failures

**Draft PR feedback received from:** N/A

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes  [ ] No — still awaiting review

**Summary of feedback:**
A reviewer asked how I derived my implementation because it was similar to another design for the same issue.

**How you responded:**
I explained that I traced the existing ingestion pipeline, found the mismatch between the asynchronous database session and the synchronous duplicate-check logic, and found that successful ingestions were not actually being persisted. I also explained why I used stable repository fields for deduplication and how I tested the behavior.

---

### Reflection

**What was harder than you expected?**
Understanding how one change affected multiple parts of the codebase was harder than I expected. Fixing the duplicate check was not just changing one query. I also had to understand the async SQLAlchemy session, how ingestion records were stored, how source IDs were generated, and how the tests needed to change after the pipeline became asynchronous.

**What did you learn about working in a large codebase?**
I learned that a change that looks small from an issue description can affect several connected files. I had to inspect the database model, ingestion pipeline, migrations, and tests before making the fix. I also learned to keep my PR focused and check the diff carefully so unrelated file changes do not get included.

**How did AI tools help — and where did they fall short?**
AI was most useful for helping me trace unfamiliar code, understand the async database flow, debug test and lint errors, and think through edge cases for deduplication. However, I still needed to verify the suggestions against the actual repository. AI could suggest an implementation quickly, but it could not replace understanding the existing architecture or checking whether the final changes really fit the project.

**What would you do differently if you started over?**
I would spend more time mapping all callers and related database code before beginning implementation. I would also check `git diff` more frequently so unrelated changes are caught earlier, and I would establish the exact deduplication rules before writing the final implementation.

**What are you most proud of from this module?**
I am most proud that I went from reproducing the bug with a failing test to implementing a fix with regression tests that cover both duplicates and legitimate repository changes. I understand the ingestion workflow much better now than when I selected the issue.
