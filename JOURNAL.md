## Week 7 — Issue selection

**Issue link:** [Issue Link](https://github.com/ascherj/pathreview/issues/6)

**Issue title:** Duplicate embeddings generated when re-ingesting the same repository

**Tier:** Tier 2

**Problem summary:**

The `pipeline.py` doesn't check whether the file has already been ingested, so when a Github repo is re-ingested, the pipeline generates the same vector entries repeatedly. This issue might inflate the scores of the repeated chunks.

A successful fix would avoid ingestion when a repeated file is detected, signal the situation, and simply return the existing result.

Affected files:
`ingestion/pipeline.py`
`core/models/ingested_source.py`

**Selection notes:**
This isn't my first open-source contribution, so I’m choosing Tier 2 for a better fit. I am comfortable tracing how multiple modules interact in the codebase. I’ve found the relevant code/file and understand the surrounding code well enough.

**Branch name:** fix/6-duplicate-embeddings-issue

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/AnniecTW/pathreview/commit/bf1777157e1fd93cd9dba9636eddfd93207b6366

**Reproduction summary:**
I used pytest to reproduce the issue. In the test I created a fake VectorDB and AsyncSession to stand in for the real vector store and database session, then ingested the same README twice with the same `profile_id` and `repo_name` to check whether the second call would be skipped (`skipped=True`). Instead it still returned `skipped=False`, confirming the broken behavior, and the same vector ids were written twice (duplicate entries).

**PLAN.md link:** https://github.com/AnniecTW/pathreview/blob/fix/6-duplicate-embeddings-issue/plan.md

**Blockers or open questions:**
Running the pre-commit hooks, mypy flagged missing type annotations in several existing `ingestion/*` files (the repo sets `disallow_untyped_defs`, and mypy follows imports into them). That's pre-existing starter code rather than anything my reproduction added, so I left it as-is and committed the test with `--no-verify`. Fixing those annotations feels out of scope for the reproduction step.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Finished steps 1–4 of the fix; now on step 5 (adjusting the tests).

**Next steps:**
Finish step 5, commit the fix and tests, and open the PR for review.

**Blockers:**
None for the fix itself. Worth noting though, that `make check` and `make test-unit` already fail on a clean checkout — 53 pre-existing unit-test failures in files I didn't touch, plus repo-wide ruff/mypy errors. My changes leave that count unchanged (the 4 new tests pass) and my edited files are ruff/black clean, so nothing new is introduced.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/AnniecTW/pathreview/pull/1

**Branch:** `fix/6-duplicate-embeddings-issue`

**What you built:**
Fixed the deduplication in `ingestion/pipeline.py`. `_check_skip` now queries the `ingested_sources` table and returns a skipped result when a match exists, while `_record_ingested_source` actually persists a row after each successful ingest. As a result, re-ingesting the same README/resume/repo is skipped instead of re-embedding and writing duplicate vectors.

**Tests added or updated:**
`tests/unit/test_pipeline_dedup.py` — four tests covering that re-ingesting the same README/resume/repo is skipped with no duplicate vectors, plus one confirming different content is still ingested. The vector store and database are mocked with fakes, and the fake session filters records using the WHERE clause, so duplicate detection behaves like it would against a real database.

**Self-review confirmation:** [x] my changed files pass ruff/black; my new tests pass
(make check / make test-unit have pre-existing failures unrelated to this change. See Blockers)

**Draft PR feedback received from:** "none"

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes [x] No — still awaiting review

**Summary of feedback:**
No review came in.

**How you responded:**

---

### Reflection

**What was harder than you expected?**
The setup surprised me the most. I expected a project's package versions and coding style to be consistent, but here some code used non-modern syntax or even contradicted itself .The declared versions didn't always match how the code was actually written, so it was up to my own judgment what to change and how far to go. Running `make check` at the end also showed the starter already had many errors, so I had to clearly separate the pre-existing ones from those my own changes introduced (e.g. mypy requires type annotations the existing `ingestion/*` files never had, and the code still uses `Optional[X]` instead of the modern `X | None`).

**What did you learn about working in a large codebase?**
As above, working in a large codebase takes both comprehension and judgment. I learned to use AI tools to understand the whole codebase faster, and through back and forth discussion I gradually built a clear mental model of its architecture. Talking through trade-offs, edge cases, and graceful degradation before writing code helped steer the direction and raise the quality. For example, I chose the existing `content_hash` as the dedup key instead of adding a `source_id` column, since it avoids a schema change, keeps the diff small, and is easier to get merged.

**How did AI tools help — and where did they fall short?**
AI was most useful for understanding the codebase and speeding up iteration: it helped me locate the relevant files, explained things I wasn't familiar with, and helped me write the reproduction test, plan the fix, and even catch two mistakes in my own fix. But a lot still came down to my own judgment: the fake session I first wrote for simplicity couldn't actually catch condition-level bugs, and I only realized and upgraded it after some back-and-forth.

**What would you do differently if you started over?**
I'd push the fix closer to production-ready. Beyond blocking exact-duplicate content, I'd handle the case where a repo is re-fetched with slightly changed metadata — deleting the old vectors before writing new ones to avoid stale data — add a unique constraint on `(profile_id, source_type, content_hash)` to guard against concurrent duplicate writes, and add a real Postgres integration test to cover the condition-level behavior the fake session in the unit tests can't.

**What are you most proud of from this module?**
What I'm most proud of isn't just getting the fix to pass, but making the tests solid and honest. My first fake session would have passed as long as any record existed, which doesn't actually verify the dedup logic; I later upgraded it to really match the `WHERE` conditions and added a negative test ("different content should not be skipped") so the tests genuinely hold. I also cared about honestly separating pre-existing failures from ones I introduced, and documenting that clearly in the PR.
