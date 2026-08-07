## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/158

**Issue title:** review_service unit tests misconfigure async mocks — 13 of 19 tests fail

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The unit test suite for the review service subsystem is currently broken because the mock database session is returning asynchronous coroutines where synchronous result objects are expected. Specifically, the production code in `core/services/review_service.py` properly awaits `db.execute()`, but the subsequent chained calls to `.scalars().first()` or `.scalars().all()` crash because the test setup incorrectly applies `AsyncMock` to the resulting database response object. This causes 13 out of 19 CRUD tests to fail with an `AttributeError`. A successful fix will reconfigure the test fixtures and mock structures so that `db.execute` correctly returns a synchronous mock object, allowing the existing service assertions to pass without modifying the underlying production logic.

**Selection Notes & Scope Reasoning:**
I selected this issue because it is categorized as Tier 1, meaning it is strictly scoped to a single file (`tests/unit/test_review_service.py`) and does not require complex cross-module architectural updates. As a data professional working with asynchronous testing environments, this is an excellent fit for my current skill level; it allows me to resolve a blocking test environment issue without changing core application workflows.

* **Part 1 — Understanding the Issue:** Verified. I can clearly explain the asynchronous mock regression in plain words. I have located the target test file and confirmed that the explicit goal is to get the 13 failing unit tests passing by matching the mock behavior to what the production CRUD methods expect.
* **Part 2 — Tier Fit:** Verified. This is a Tier 1 issue because it is an isolated, self-contained test environment bug. It is a highly realistic match for orienting myself in the PathReview codebase during the first week of the module.
* **Part 3 — Codebase Readiness:** Verified. I have opened, read, and successfully run the test suite for `tests/unit/test_review_service.py` locally in my environment, reproducing the precise `AttributeError` tracebacks. I understand the mock configuration patterns currently in use.
* **Part 4 — Scope and Time:** Verified. The scope is tight and well-defined, taking an estimated 2–4 hours of focused work. This is perfectly achievable around my ongoing professional and graduate coursework commitments, and there are no external engineering blockers.

**Branch name:** fix/158-review-service-async-mocks
**Setup confirmation:** [x] App runs locally at localhost:5173
**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**[Reproduction commit](https://github.com/rdv-chio/pathreview/commit/2d4aaad8205d7b3ab9adb5ff55ee6f6c49e07ab3)**

**Reproduction summary:**
I reproduced the issue locally in my environment by running `pytest tests/unit/test_review_service.py -v`. I observed exactly 13 failures out of 19 tests, all throwing an `AttributeError` because the production code attempts to chain synchronous `.scalars().first()` and `.all()` methods onto an improperly returned asynchronous coroutine mock object.

**[PLAN.md](https://github.com/rdv-chio/pathreview/blob/fix/158-review-service-async-mocks/PLAN.md)**

**Blockers or open questions:**
None. The error behavior perfectly mirrors the issue description, and the resolution path is entirely isolated to the test configuration script.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I successfully refactored the database return mock structures within `tests/unit/test_review_service.py`. Sub-tasks 1, 2, and 3 from `PLAN.md` are completely implemented, converting the recursively chaining mock result objects from `AsyncMock` layers to clean, synchronous `Mock` components that exactly align with what the production code expects.

```bash
ai201) rociodv@WIN-MU9C0LJD9CM:~/code/pathreview$ pytest tests/unit/test_review_service.py -v
================================================= test session starts ==================================================
platform linux -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0 -- /home/rociodv/anaconda3/envs/ai201/bin/python3.11
cachedir: .pytest_cache
hypothesis profile 'default'
benchmark: 5.2.3 (defaults: timer=time.perf_counter disable_gc=False min_rounds=5 min_time=0.000005 max_time=1.0 calibration_precision=10 warmup=False warmup_iterations=100000)
rootdir: /mnt/d/code/pathreview
configfile: pyproject.toml
plugins: anyio-4.14.2, asyncio-1.4.0, hypothesis-6.156.6, cov-7.1.0, pytest_httpserver-1.1.5, benchmark-5.2.3
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 19 items

tests/unit/test_review_service.py::TestReviewService::test_create_review_returns_review_with_pending_status PASSED [  5%]
tests/unit/test_review_service.py::TestReviewService::test_get_review_returns_review_for_correct_owner PASSED    [ 10%]
tests/unit/test_review_service.py::TestReviewService::test_get_review_returns_none_for_wrong_user PASSED         [ 15%]
tests/unit/test_review_service.py::TestReviewService::test_list_reviews_returns_paginated_results PASSED         [ 21%]
tests/unit/test_review_service.py::TestReviewService::test_list_reviews_page_2_returns_correct_offset PASSED     [ 26%]
tests/unit/test_review_service.py::TestReviewService::test_list_reviews_returns_tuple PASSED                     [ 31%]
tests/unit/test_review_service.py::TestReviewService::test_create_review_calls_db_add PASSED                     [ 36%]
tests/unit/test_review_service.py::TestReviewService::test_create_review_calls_db_commit PASSED                  [ 42%]
tests/unit/test_review_service.py::TestReviewService::test_create_review_calls_db_refresh PASSED                 [ 47%]
tests/unit/test_review_service.py::TestReviewService::test_get_review_uses_select_and_join PASSED                [ 52%]
tests/unit/test_review_service.py::TestReviewService::test_list_reviews_default_pagination PASSED                [ 57%]
tests/unit/test_review_service.py::TestReviewService::test_list_reviews_custom_page_size PASSED                  [ 63%]
tests/unit/test_review_service.py::TestReviewService::test_create_review_with_uuid_ids PASSED                    [ 68%]
tests/unit/test_review_service.py::TestReviewService::test_get_review_verifies_ownership PASSED                  [ 73%]
tests/unit/test_review_service.py::TestReviewService::test_list_reviews_counts_total PASSED                      [ 78%]
tests/unit/test_review_service.py::TestReviewService::test_list_reviews_returns_reviews_list PASSED              [ 84%]
tests/unit/test_review_service.py::TestReviewService::test_review_sections_and_score_initially_none PASSED       [ 89%]
tests/unit/test_review_service.py::TestReviewService::test_get_review_with_valid_uuid PASSED                     [ 94%]
tests/unit/test_review_service.py::TestReviewService::test_list_reviews_ordered_by_created_at PASSED             [100%]

=================================================== warnings summary ===================================================
core/config.py:7
  /mnt/d/code/pathreview/core/config.py:7: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class Settings(BaseSettings):

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
============================================ 19 passed, 1 warning in 0.84s =============================================
```


**Next steps:**
I am running automated styling and type checker regression validations across the suite via static code tools, tracking any pre-existing mypy errors, and generating a live, public Pull Request for final evaluation.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**[PR link](https://github.com/ascherj/pathreview/pull/186)
**[Branch](https://github.com/rdv-chio/pathreview/tree/fix/158-review-service-async-mocks)

**What you built:**
I modified the unit test configuration topology inside `tests/unit/test_review_service.py` so that the awaited database engine execution path returns a traditional synchronous `Mock` representing an active SQLAlchemy result set instead of an `AsyncMock`. This enables smooth, chained evaluation of synchronous methods like `.scalars().first()` and `.all()` inside the core service files, clearing the previous failures.

**Tests added or updated:**
Updated `tests/unit/test_review_service.py`. The modifications directly remediated the mock layout across all 13 failing unit test methods (including `test_get_review_returns_review_for_correct_owner` and `test_list_reviews_returns_paginated_results`), checking successful paths, pagination parameters, filters, and missing record scenarios.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes (Note: Rerun via `pytest tests/unit -v -m unit` due to custom Conda profile environment layout).

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
As noted in the Summer 2026 course guidelines, official maintainer review feedback was not provided for this cohort session. No external pull request comments were received by the closing date.

**How you responded:**
N/A (no feedback received).

---

### Reflection

**What was harder than you expected?**
The subtle mechanics of Python's `unittest.mock` library when mixing asynchronous coroutines with synchronous chained method calls caught me off guard. Initially, diagnosing why `result = await db.execute(stmt)` succeeded while `result.scalars().first()` threw an `AttributeError` required stepping through how `AsyncMock` recursively generates coroutine children for every accessed attribute. Disentangling the `AsyncMock` execution layer from the synchronous `Mock` result container required carefully inspecting the exact SQLAlchemy query execution pipeline.

**What did you learn about working in a large codebase?**
Working in a multi-module repository like PathReview reinforced that fixing a bug rarely requires touching production application code if the problem is localized to the test harness. I learned that reading existing test patterns and understanding fixture scope in `tests/unit/test_review_service.py` is far more valuable than blindly refactoring functions. Additionally, navigating pre-existing static type errors in un-related modules taught me the importance of maintaining an isolated diff that doesn't attempt to fix the whole codebase at once.

**How did AI tools help — and where did they fall short?**
AI tools were incredibly useful for quickly analyzing the stack trace of the 13 failing unit tests and pinpointing why `AsyncMock` was causing `.scalars()` to return an unawaited coroutine. They helped draft the initial synchronous `Mock` replacement strategy and structured the markdown planning documents. However, AI fell short when accounting for service-level query counts; it assumed `db.execute` was called once in `test_list_reviews_ordered_by_created_at`, failing to realize the service layer runs two queries (one for the total pagination count and one for the data array), which required manual debugging.

**What would you do differently if you started over?**
If I started over, I would immediately run `pytest` on the specific test module before doing any environment setup or dependency installs to establish an accurate failure baseline faster. I would also write out the explicit mock object hierarchy on paper during the Week 8 planning phase before touching any code. This would have helped me catch the pagination dual-query requirement in `list_reviews` much earlier in the process.

**What are you most proud of from this module?**
I am most proud of systematically taking a broken test suite with 13 failing unit tests and bringing it to 100% green (19 passed) while keeping my pull request diff completely surgical. Isolating the issue strictly to `tests/unit/test_review_service.py` without introducing regression side-effects or dirtying unrelated repository files felt like a true production-grade contribution.