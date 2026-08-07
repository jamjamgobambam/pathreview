# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/109

**Issue title:** Test coverage for `core/services/review_service.py` is below 40%

**Tier:** [x] Tier 2  [ ] Tier 1  [ ] Tier 3

**Problem summary:**
`core/services/review_service.py` orchestrates the entire review workflow —
creating a review, fetching it back while checking ownership, and listing a
user's reviews — but most of its code paths currently have no test coverage.
The existing test file only covers a handful of happy-path cases, so failure
handling (a review that never finishes generating, a partially-completed
review, a lookup for a review that doesn't belong to the requesting user) is
unverified even though this is described as the most critical service in the
application. A successful fix adds unit tests targeting the success,
partial-failure, and full-failure paths through `create_review`, `get_review`,
and `list_reviews`, using the existing mocked async DB session pattern already
present in `tests/unit/test_review_service.py`.

**Branch name:** test/109-review-service-test-coverage

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/darylcarter2006/pathreview/commit/9c83385

**Reproduction summary:**
Ran `pytest tests/unit/test_review_service.py --cov=core.services.review_service --cov-report=term-missing` in a local venv (no Docker needed — the tests mock the DB session). Observed actual coverage of 22% (worse than the ~40% the issue implies), with `process_review`, `_run_ingestion_pipeline`, and `_run_safety_checks` — the functions covering the success/partial-failure/full-failure workflow — at 0% coverage. Also discovered 13 of the 19 existing tests in that file are already failing from an unrelated `AsyncMock` misconfiguration bug (tracked separately as issue #158), which affects how I need to write new tests.

**PLAN.md link:** https://github.com/darylcarter2006/pathreview/blob/test/109-review-service-test-coverage/PLAN.md

**Walkthrough video (recommended):** (not recorded)

**Blockers or open questions:**
Docker/Node aren't installed on my machine yet, so I've only run the backend unit tests directly in a venv, not the full `make setup && make run` app — that's fine for this test-only issue since `process_review` and friends don't need the frontend or a live DB, but I still need real Docker/Node installed before Week 9 if I want to sanity-check the app end-to-end. Also watching issue #158 (claimed by other students) since it touches the same test file and could conflict with my new tests if their fix lands first.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented all six sub-tasks from `PLAN.md`: added a `make_execute_result` helper that builds mocked `db.execute()` return values as plain `Mock()` objects (avoiding the `AsyncMock` auto-mocking trap behind issue #158), then added 17 new tests to `tests/unit/test_review_service.py` covering `process_review`'s success path, its two partial-failure branches (profile not found, safety checks failed), its full-failure branch (including the nested exception in the recovery block), `_run_ingestion_pipeline`'s per-source-type branches and error isolation, and `_run_safety_checks`'s four rejection conditions plus its own exception handler. Ran `pytest --cov=core.services.review_service --cov-report=term-missing`: coverage is now 95%, up from the 22% baseline. Also captured a `make check`/`make test-unit` baseline before touching any code and confirmed after my changes that the exact same 53 pre-existing test failures and the same categories of pre-existing lint/format/typecheck issues remain — my changes introduce no new failures (and net-fixed a few pre-existing lint issues in this file via `black`/`ruff --fix` while formatting my additions).

**Next steps:**
Open a draft PR against `ascherj/pathreview` for peer/mentor feedback, then address any feedback and mark it ready for review before the deadline.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/942

**Branch:** test/109-review-service-test-coverage

**What you built:**
17 new unit tests for `core/services/review_service.py` covering `process_review`'s success/partial-failure/full-failure paths, `_run_ingestion_pipeline`'s per-source-type branches, and `_run_safety_checks`'s rejection branches — no production code changes, per the issue's scope.

**Tests added or updated:**
`tests/unit/test_review_service.py` — added a `make_execute_result` mock helper and 17 new test methods; raises module coverage from 22% to 95%. Did not modify the existing 19 tests (13 of which still fail due to the separately-tracked issue #158).

**Self-review confirmation:** [x] make check passes (no new failures vs. documented pre-existing baseline)  [x] make test-unit passes (same 53 pre-existing failures as baseline; all 17 new tests pass)

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No feedback came in. Reviewer feedback isn't enabled for the Summer 2026
cohort, so this is expected rather than a sign the PR was overlooked.

**How you responded:**
N/A — no feedback to respond to. PR #942 remains open against
`ascherj/pathreview` for issue #109 in case it's picked up later.

---

### Reflection

**What was harder than you expected?**
Writing tests against `process_review` exposed a subtlety I hadn't
anticipated: the shared `mock_db_session` fixture builds an `AsyncMock()`
for the DB session, and since `result.scalars()` is called synchronously
(not awaited) in the production code, mocking `result` itself as an
`AsyncMock` silently returns an unawaited coroutine instead of the
configured return value. That's the root cause of the 13 pre-existing
failures tracked in issue #158. Once I understood it, writing new tests
that used a plain `Mock()` for the execute-result object (while keeping
`db.execute` itself as an `AsyncMock`) was straightforward, but diagnosing
*why* the pattern in the existing tests was broken took longer than
writing the actual test bodies.

**What did you learn about working in a large codebase?**
The biggest difference from my own projects (like AcademiqHQ) is that
correctness here is bounded by scope, not just by "does it work." I found
a second, undocumented bug while writing tests — `IngestedSource(...,
raw_data=...)` always raises `TypeError` because the real model has no
`raw_data` field, so every ingestion source silently fails in production
today. Fixing it would have been a two-line change, but it was out of
scope for a test-coverage issue, so I documented it in the PR instead of
touching production code. In my own codebase I'd have just fixed it on
the spot; here, staying inside the issue's stated boundary mattered more
than being thorough.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful for the mechanical parts: tracing the
`AsyncMock`/`scalars()` interaction across the file, generating the
repetitive mock-setup boilerplate for 17 test cases, and running
`black`/`ruff --fix` loops to keep formatting clean as the file grew. It
fell short on judgment calls that needed project context I had to supply
myself — deciding the `IngestedSource` bug was out of scope rather than
something to fix, and deciding how to represent per-branch error
isolation in `_run_ingestion_pipeline` without leaning on a broken test
premise (my first attempt at that test was actually wrong, and I had to
identify why before rewriting it against a real code path).

**What would you do differently if you started over?**
I'd install Docker and Node earlier — I did all of this against the
backend unit tests in a bare venv and never ran the full app end-to-end,
which was fine for a test-only issue but would have been risky if the fix
had touched anything user-facing. I'd also read `_run_ingestion_pipeline`
line-by-line before Week 8 instead of during Week 9, since that's where
the `raw_data` bug was hiding and I could have flagged it a week earlier.

**What are you most proud of from this module?**
Getting `core/services/review_service.py` from 22% to 95% coverage while
leaving the exact same 53 pre-existing failures untouched — proving that
with a before/after diff rather than eyeballing pass counts — feels like
the real deliverable, more than the PR itself. It's the difference between
"I added tests" and "I added tests without breaking anything or hiding
whether I broke anything."
