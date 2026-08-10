## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/158

**Issue title:** review_service unit tests misconfigure async mocks — 13 of 19 tests fail

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The unit tests for `review_service` configure the mocked database session incorrectly. The service correctly awaits `db.execute()`, but the mock result returns a coroutine from `scalars()` instead of a normal result object. This causes calls such as `scalars().first()` and `scalars().all()` to fail even though the service implementation is correct. A successful fix will update the test mocks so that `execute` is asynchronous while the returned result and scalar methods behave like normal synchronous SQLAlchemy result objects.

**Selection notes — “Is this right for me?” checklist reasoning:**
This issue has a limited scope because it primarily affects one unit test file and does not require changes to the application’s production behavior. The failure is reproducible with a single pytest command, and the expected result is clearly defined: all existing `review_service` tests should execute correctly. The issue involves Python unit testing, `AsyncMock`, and `MagicMock`, which are skills I can investigate and test locally. Because it is labeled Tier 1 and does not appear to require major architectural changes, I believe it is a realistic issue for me to complete within the module timeline.

**Branch name:** test/158-review-service-async-mocks

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Ariunlag/pathreview/commit/c4132846d5324d6ee3ea4a9b07b553d8e4476ce0

**Reproduction summary:**
I reproduced issue #158 by running:

`pytest tests/unit/test_review_service.py -q`

The test suite produced 13 failed tests and 6 passed tests. The `get_review()` tests fail with `AttributeError: 'coroutine' object has no attribute 'first'`, while the `list_reviews()` tests fail with `AttributeError: 'coroutine' object has no attribute 'all'`.

The failures occur because the tests configure the result returned by `db.execute()` as an `AsyncMock`. The service correctly awaits `db.execute()`, but then uses `scalars().first()` and `scalars().all()` synchronously.

**PLAN.md link:** [PLAN.md](https://github.com/Ariunlag/pathreview/blob/test/158-review-service-async-mocks/PLAN.md)

**Walkthrough video (recommended):**
Not recorded

**Blockers or open questions:**
I need to verify how the mocked SQLAlchemy Result object should behave and how to handle the two `db.execute()` calls made by `list_reviews()`.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix for issue #158 in `tests/unit/test_review_service.py`. The tests now keep `db.execute()` as an `AsyncMock`, while the SQLAlchemy result objects returned from it use `MagicMock` so that synchronous calls such as `scalars().first()` and `scalars().all()` behave correctly.

The `list_reviews()` tests were also updated to represent its two database executions separately: one result for the count query and one for the paginated query. An existing assertion was updated to reflect that `list_reviews()` correctly calls `db.execute()` twice.

The issue-specific test file now passes completely:

`19 passed, 1 warning`

The full unit test suite improved from:

`53 failed, 375 passed, 1 warning`

to:

`40 failed, 388 passed, 1 warning`

This resolves 13 failures, matching the 13 failures originally reproduced for issue #158.

The changed test file also passes both Ruff and Black checks.

Implementation commit:

`cf3a6c0 — test(api): fix async mocks in review service tests`

**Next steps:**
Push the implementation and journal updates, open a Draft PR, request peer or mentor feedback, address any review comments, and then complete the final Week 9 check-in before marking the PR ready for review.

**Blockers:**
Repository-wide quality checks have pre-existing failures outside the scope of issue #158. Ruff reports 174 errors across unrelated files, Black reports 51 files that would require reformatting, and mypy stops with five errors related to missing or untyped dependencies and type-stub/toolchain compatibility. The changed `review_service` test file itself passes Ruff, Black, and all 19 targeted tests.


### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/445

**Branch:** test/158-review-service-async-mocks

**What you built:**
Fixed the async mock configuration in `tests/unit/test_review_service.py`. `db.execute()` remains an `AsyncMock`, while the SQLAlchemy result objects returned from it use `MagicMock`. The `list_reviews()` tests now model the count query and paginated query separately.

**Tests added or updated:**
Updated the existing `review_service` unit tests to correctly model synchronous SQLAlchemy result behavior. The targeted test file passes with `19 passed, 1 warning`. The full unit suite improved from `53 failed, 375 passed, 1 warning` to `40 failed, 388 passed, 1 warning`, resolving the 13 failures associated with issue #158.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

Repository-wide checks still contain failures outside the scope of this change. The modified test file passes Ruff, Black, and all 19 targeted tests. The remaining repository-wide failures are documented in the PR description.

**Draft PR feedback received from:** No feedback received before final submission.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer feedback was received on the GitHub PR. The Summer 2026 course notes indicate that reviewer feedback is not provided as a course feature this term.

**How you responded:**

---

### Reflection

**What was harder than you expected?**
The hardest part was determining whether the failures came from the production service or from the tests themselves. The error messages involved coroutines, so initially it was possible to suspect that the service was incorrectly handling asynchronous database operations.

After tracing the service code, I found that `db.execute()` is correctly awaited, but the SQLAlchemy result returned from that awaited operation is consumed synchronously through calls such as `scalars().first()` and `scalars().all()`. The tests incorrectly used `AsyncMock` for both layers.

Another unexpected detail was that `list_reviews()` performs two database executions: one for the total count and another for the paginated results. That required two separate synchronous result mocks using `side_effect`, rather than one shared result.

The repository-wide quality state was also more complicated than I expected. Fixing my issue did not make the entire repository green because unrelated Ruff, Black, mypy, and unit-test failures already existed. I had to separate failures caused by my change from failures that were outside the scope of issue #158.

**What did you learn about working in a large codebase?**
I learned that working in an existing codebase requires verifying assumptions before changing code. In my own projects, I can often change implementation and tests together. In someone else's codebase, I need to first understand the existing contract and determine which side is actually incorrect.

For this issue, the production implementation did not need to change. Reading the service code carefully showed that the mocks were the problem. Changing production code just to make the tests pass could have introduced a real bug.

I also learned the importance of baseline measurements. I reproduced 13 failures before implementation and finished with all 19 targeted tests passing. The full unit suite changed from `53 failed, 375 passed` to `40 failed, 388 passed`, which provided strong evidence that the 13 issue-specific failures were resolved.

The Week 9 grading feedback also showed me that this baseline discipline should be applied more consistently to repository-wide quality checks. I documented the remaining Ruff, Black, and mypy failures, but a stronger process would have recorded the exact before-and-after state of each repository-wide command.

**How did AI tools help — and where did they fall short?**
AI tools were most useful for helping me reason about `AsyncMock` versus `MagicMock`, interpret coroutine-related failures, understand how the mocked SQLAlchemy result should behave, and organize the Git and pull request workflow.

AI also helped me think through why an asynchronous method can return an object whose later methods are synchronous. That distinction was central to solving the issue.

However, AI could not determine the actual state of the repository without me running the code. I still needed to execute the targeted tests, full unit suite, Ruff, Black, and mypy locally and compare the results. AI could suggest what to investigate, but the actual evidence had to come from the repository and test results.

I also needed to verify that suggested changes matched the real production implementation instead of applying them simply because they sounded reasonable.

**What would you do differently if you started over?**
I would establish a more complete baseline before changing any code.

I would record:
- the targeted test results,
- the full unit-test results,
- repository-wide lint results,
- formatting results,
- type-checking results,

and then run the exact same commands after implementation.

For this issue, I captured the targeted and full-unit-test comparison well, but the Week 9 grading feedback showed that I should have done the same before-and-after comparison for every repository-wide quality command. That would make it easier for a reviewer or grader to verify that my change introduced no new problems.

I would also inspect the complete execution flow of `list_reviews()` earlier. Recognizing immediately that it calls `db.execute()` twice would have made the correct mock structure obvious sooner.

**What are you most proud of from this module?**
I am most proud that I identified the actual source of the failure instead of changing production code just to make the tests pass.

The final implementation preserved the existing service behavior and corrected the tests so that the mocks reflected the real asynchronous and synchronous boundaries. The 13 failures I initially reproduced were all resolved, and the targeted test file finished with 19 passing tests.

I am also proud that I documented the remaining repository-wide failures rather than claiming that checks passed when they did not. Even though the repository was not completely green, the final documentation accurately described what my contribution fixed and what remained outside the scope of issue #158.