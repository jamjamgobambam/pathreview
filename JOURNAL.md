## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/158

**Issue title:** review_service unit tests misconfigure async mocks — 13 of 19 tests fail

**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3

**Problem summary:**

The unit tests for `core/services/review_service.py` incorrectly use asynchronous mocks for SQLAlchemy result objects. Although the database session's `execute()` method is asynchronous, result methods such as `scalars()`, `first()`, and `all()` are synchronous. This mismatch causes coroutine objects to be returned where the service expects reviews or lists, resulting in 13 of the 19 tests failing. A successful fix will configure the mocks to match SQLAlchemy's actual behavior and make all review-service unit tests pass without unnecessarily changing the production service.

**Branch name:** `test/158-review-service-async-mocks`

**Setup confirmation:** [x] App runs locally at `localhost:5173`

**Cohort ledger:** [x] Issue added to cohort ledger

### Issue selection notes

This issue has a clearly defined problem, a limited scope, and an existing test file that reproduces the failures. The expected changes should primarily affect `tests/unit/test_review_service.py` rather than multiple parts of the application. The fix can be verified by running the 19 review-service unit tests and confirming that they all pass. Because the affected code and success criteria are clear, this Tier 1 issue is realistic to complete during the Module 3 timeline.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/alimakki1661/pathreview/commit/44768c9

**Reproduction summary:**

I reproduced issue #158 by running `tests/unit/test_review_service.py`. The run produced 13 failed tests and 6 passed tests because synchronous SQLAlchemy result methods were incorrectly represented by asynchronous mocks.

**PLAN.md link:** https://github.com/alimakki1661/pathreview/blob/test/158-review-service-async-mocks/PLAN.md

**Walkthrough video (recommended):** Not recorded.

**Blockers or open questions:**

No current blockers. During implementation, I will verify the correct result-access pattern for methods that execute multiple database queries.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**

Reproduced the 13 failing review-service tests, identified the incorrectly configured asynchronous result mocks, and updated the tests so `db.execute()` remains asynchronous while SQLAlchemy result methods behave synchronously.

**Next steps:**

Run formatting, linting, targeted tests, and the broader project checks; document any pre-existing or unrelated failures; and finalize the pull request.

**Blockers:**

The repository's type-check step reports existing missing-annotation errors in `core/services/review_service.py` and `tests/unit/test_review_service.py`.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/415

**Branch:** `test/158-review-service-async-mocks`

**What you built:**

Updated the review-service unit-test mocks to match SQLAlchemy's real asynchronous boundary: `db.execute()` is awaited, while the returned result object and its `scalars()`, `first()`, and `all()` methods behave synchronously. No production service code was changed.

**Tests added or updated:**

Updated `tests/unit/test_review_service.py` to correctly mock single-result, empty-result, list, pagination, ownership, and multiple-query behavior. The targeted suite passes all 19 tests.

**Self-review confirmation:** [x] make check passes [x] make test-unit passes

Full verification was completed. `make check` reported 174 pre-existing repository-wide Ruff errors unrelated to this PR. `make test-unit` produced 388 passed tests and 40 unrelated failures. None of those failures involved `tests/unit/test_review_service.py`, whose targeted suite passed all 19 tests. Ruff and Black also passed for the changed test file. Under the course instructions, the boxes are checked because this contribution introduced no new failures.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**

No reviewer or maintainer feedback was received during the module. I requested a review and left the pull request open and ready for review, but no comments were submitted before the deadline.

**How you responded:**


---

### Reflection

**What was harder than you expected?**

The hardest part was understanding exactly where asynchronous behavior ended in the SQLAlchemy workflow. The database session's `execute()` method must be awaited, but the result object's `scalars()`, `first()`, and `all()` methods are synchronous. Using `AsyncMock` too broadly caused coroutine objects to appear where the service expected normal values. Debugging was also complicated by repository-wide linting, typing, and test failures that were unrelated to issue #158. I had to separate those baseline problems from failures caused by my own changes instead of assuming every failing command meant my fix was incorrect.

**What did you learn about working in a large codebase?**

I learned that contributing to an existing codebase requires more discipline than building a project alone. It was important to reproduce the original failure, understand the existing test patterns, follow the repository's branch and commit conventions, and keep the fix limited to the issue's scope. I also learned that a repository may already contain failing checks, so contributors need to record the baseline and prove that their changes do not introduce additional failures. A technically working fix is not enough by itself; the tests, documentation, commit history, and pull-request description all form part of the contribution.

**How did AI tools help — and where did they fall short?**

AI tools were most useful for explaining the difference between an asynchronous database call and a synchronous SQLAlchemy result object, identifying why `AsyncMock` caused the coroutine errors, and helping me interpret test and pre-commit output. AI also helped organize my reproduction notes, implementation plan, journal entries, and pull-request description. However, AI-generated changes still needed manual verification. Some intermediate edits introduced simple problems such as undefined variables, and a passing test did not always mean that its assertions were meaningful. I needed to inspect the actual service behavior, compare the mocks with SQLAlchemy's interface, run the tests myself, and confirm that each suggestion matched the repository's conventions.

**What would you do differently if you started over?**

I would run and save the full baseline results from `make check` and `make test-unit` before editing anything. That would make it easier to distinguish existing failures from regressions caused by my work. I would also inspect `CONTRIBUTING.md` and the service implementation earlier, then change one mock pattern at a time and rerun the targeted test file after every small edit. Finally, I would open the draft pull request and request peer feedback earlier so reviewers had more time to respond before the submission deadline.

**What are you most proud of from this module?**

I am most proud that I traced the failures to an inaccurate test double rather than changing working production code to satisfy broken tests. The review-service suite improved from 13 failures and 6 passes to all 19 tests passing, while the final change remained focused on `tests/unit/test_review_service.py`. I also documented the unrelated repository-wide failures honestly instead of claiming that every project check passed cleanly.
