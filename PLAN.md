## Solution plan

**Issue:** Test coverage for core/services/review_service.py is below 40%
(https://github.com/ascherj/pathreview/issues/109)

### Understand
Root cause of failures: existing tests mock the SQLAlchemy result object
(`mock_result`) as an `AsyncMock`, but `.scalars()` and `.first()/.all()` are
synchronous methods called on the *result* of an already-awaited `db.execute()`.
This makes every call to `.scalars()` return an un-awaited coroutine instead of
a mock value, causing `AttributeError: 'coroutine' object has no attribute 'first'`.
Expected behavior: every early-return path (review missing, profile missing, safety check failing) and every exception path should reliably set status="failed" and never crash the caller; actual behavior: 22% coverage due to failing tests.

### Map
core/services/review_service.py — no production changes expected; this is a test-only issue (the file itself works, the tests calling it are broken/missing)
tests/unit/test_review_service.py — main file to fix (mock setup) and extend (new test cases for process_review and its helpers)
core/models/review.py, core/models/profile.py, core/models/ingested_source.py — reference these to build accurate Profile/Review fixtures
api/schemas/review.py (FeedbackSection) — needed since process_review builds these objects from RAG output
Possibly tests/unit/conftest.py — if I add a shared, correctly-typed mock_db_session fixture so the AsyncMock/MagicMock fix only has to happen in one place

### Plan
1. Fix the broken mock pattern. Change every mock_result = AsyncMock() to mock_result = MagicMock() across the 13 failing tests, since only db.execute() itself is async — .scalars(), .first(), and .all() are synchronous calls on the returned result object. Re-run the suite to confirm all 19 existing tests pass before adding anything new.
2. Add tests for process_review's happy path. Mock the four private helpers (_run_ingestion_pipeline, _run_agent_orchestration, _run_rag_retrieval_generation, _run_safety_checks) to succee
3. Add tests for process_review's early-return and failure branches.
4. Add tests for the private helper functions directly: _run_ingestion_pipeline (all sources present, none present, one source raising while others succeed) and _run_safety_checks (empty sections, missing fields, out-of-range confidence, valid input).
5. Re-run coverage and close remaining gaps. 

### Inputs & outputs
Input: the real review_service.py source (already reviewed), a corrected mocking pattern (MagicMock for result objects, AsyncMock only for db.execute), and Profile/Review fixtures matching the actual model fields.
Output: a tests/unit/test_review_service.py where all existing tests pass and new tests cover process_review's success/partial-failure/full-failure paths plus its helper functions, verified by a coverage report showing the file comfortably above 40%. No changes to review_service.py itself unless a genuine bug turns up while testing (would be called out separately, not folded silently into this fix).

### Risks & unknowns
Since the same broken mock pattern appears in ~13 places, there's a real risk of missing one instance when fixing them

The four private helper functions currently contain placeholder logic rather than real integrations

### Edge cases
confidence values exactly at the boundaries (0 and 1).
Multiple ingestion sources failing simultaneously while at least one succeeds.