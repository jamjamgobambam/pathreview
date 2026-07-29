# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/82

**Issue title:** Concurrent review requests for the same profile can produce inconsistent results

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
When a user submits two review requests for the same profile at nearly the same
time, `POST /reviews` creates a new `Review` row and schedules `process_review`
as a FastAPI `BackgroundTasks` job for each request — there is no coordination
between the two. Both background jobs independently call `_run_ingestion_pipeline`
against the same `profile_id`, and each opens its own DB session/transaction with
no lock on the profile. If the two ingestion runs interleave, one job's writes
(e.g., re-ingested documents/embeddings for the profile) can be read mid-flight
or overwritten by the other, so the agent/RAG steps downstream of ingestion can
operate on a mixed or stale view of the profile's data. The result is a review
that silently reflects an inconsistent snapshot rather than a clean, of one run.
The fix is to serialize processing per profile — e.g. a per-profile async lock
(or a DB-level advisory lock/row lock) acquired before `_run_ingestion_pipeline`
runs in `process_review`, released after the review finishes — so a second
concurrent request for the same profile waits for the first to complete instead
of interleaving with it. This affects `api/routes/reviews.py` (`create_review_endpoint`,
where the background task is scheduled) and `core/services/review_service.py`
(`process_review` / `_run_ingestion_pipeline`, where the actual race happens).

**Scope reasoning (Is this right for me? checklist):**
- Touches exactly two files with a clear, well-known fix pattern (per-key async
  lock / advisory lock) rather than an open-ended design problem — bounded even
  though it's cross-layer (API route + service).
- The race is concretely reproducible: fire two `POST /reviews` calls for the
  same `profile_id` back-to-back and inspect whether ingestion work is duplicated
  or whether the resulting review reflects mixed state.
- Requires understanding how the background-task/async-session flow works across
  the route and service layer, which is a good showcase of "architectural"
  understanding without requiring new infrastructure or product surface area.
- Estimated effort (6–9h) fits within the module timeline for a single Tier 3
  issue.

**Branch name:** `fix/82-concurrent-review-lock`

**Setup confirmation:** [x] App runs locally at localhost:5173 (carried over from
prior local setup; `.venv`, migrations, and seed data already in place)

**Cohort ledger:** [ ] Issue added to cohort ledger
**Issue claimed publicly:** [ ] Comment posted on #82

---

## Week 7-8 — Reproduction and plan

**Reproduction:** Added `tests/integration/test_review_concurrency.py`, which
fires two `process_review()` calls for the same `profile_id` concurrently
(via `asyncio.gather`, each with its own `AsyncSession`, mirroring two
`BackgroundTasks` jobs from two near-simultaneous `POST /reviews` calls) and
records the start/end time of each call's ingestion step. On the current
(unfixed) code,
`test_concurrent_reviews_for_same_profile_are_not_serialized` **passes**,
proving the two calls' ingestion windows overlap — nothing today prevents two
reviews for the same profile from running at the same time. A companion test,
`test_concurrent_reviews_for_different_profiles_still_run_in_parallel`, also
passes, confirming two *different* profiles legitimately do (and should
continue to) run concurrently — this is the guardrail against overcorrecting
with a global lock.

**Scope note found during reproduction:** `_run_ingestion_pipeline` in
`core/services/review_service.py` constructs `IngestedSource(..., raw_data=...)`,
but `raw_data` isn't a column on the `IngestedSource` model (verified: this
raises `TypeError: 'raw_data' is an invalid keyword argument for
IngestedSource`). This means the real ingestion pipeline currently crashes on
any profile with a `github_username`, `portfolio_url`, or `resume_text`,
independent of concurrency. This is a separate, pre-existing bug, not part of
#82's scope. The reproduction test patches
`_run_ingestion_pipeline`/`_run_agent_orchestration`/
`_run_rag_retrieval_generation`/`_run_safety_checks` so it can isolate the
concurrency question without depending on that unrelated fix. Worth filing as
its own follow-up issue, but out of scope for this PR.

**Fix plan:**
1. Add a per-profile async lock keyed by `profile_id` (e.g. an
   `asyncio.Lock` in a small `dict[str, asyncio.Lock]` registry, or a
   Postgres advisory lock taken at the top of `process_review` and released
   at the end/on exception) so a second `process_review` call for the same
   profile waits for the first to finish instead of interleaving with it.
2. Acquire the lock as early as possible in `process_review` (before the
   ingestion step) and release it in a `finally` block so a failed review
   doesn't leave the profile permanently locked.
3. Do **not** make the lock global — different profiles must keep processing
   concurrently (covered by the sanity test above).
4. Flip `test_concurrent_reviews_for_same_profile_are_not_serialized` to
   assert the two windows do **not** overlap once the lock is in place; keep
   the different-profiles test asserting they still overlap.
5. Add a unit test (or extend the existing one) verifying the lock is
   released even when `process_review` raises, so a failed review doesn't
   permanently block that profile.

---

## Parked — Week 7 (previous pick, not pursued)

Issue #153 (Tier 1, faithfulness checker `None` text crash) was initially
scoped and journaled before switching to #82 for the Tier 3 requirement. That
work is stashed on branch `fix/153-faithfulness-checker-none-text` under a
git stash entry (`wip: issue-153 journal entry`) in case it's picked back up
later.
