# Reproduction: Issue #109 — review_service.py test coverage below 40%

## How I reproduced it

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest tests/unit/test_review_service.py -v -m unit \
  --cov=core.services.review_service --cov-report=term-missing
```

No Docker/Postgres/Redis needed — `test_review_service.py` mocks the async DB
session directly, so this runs against the venv alone.

## What I observed

```
Name                              Stmts   Miss  Cover   Missing
---------------------------------------------------------------
core/services/review_service.py     135    105    22%   68-79, 98-194, 202-279, 288, 323, 369-390
---------------------------------------------------------------
TOTAL                               135    105    22%

13 failed, 6 passed, 1 warning in 0.41s
```

Actual coverage is **22%**, worse than the 40% the issue title states.

The uncovered ranges map to real functions with zero test coverage:
- `68-79`: tail of `list_reviews` (the paginated-results query path)
- `98-194`: all of `process_review` — the entire success / partial-failure /
  full-failure workflow this issue asks to cover
- `202-279`: all of `_run_ingestion_pipeline`, including its three independent
  per-source-type try/except branches (github, portfolio, resume)
- `369-390`: all of `_run_safety_checks`, including its three failure branches
  (no sections, incomplete section, invalid confidence) and its own
  exception handler

**Unexpected finding:** 13 of the 19 existing tests in this file are already
failing, independent of coverage. Example:

```
count_result = await db.execute(count_stmt)
total = len(count_result.scalars().all())
AttributeError: 'coroutine' object has no attribute 'all'
```

Root cause: the `mock_db_session` fixture builds `db.execute` as an
`AsyncMock`. Any attribute accessed off the *return value* of an `AsyncMock`
call is auto-specced as another `AsyncMock`, so `count_result.scalars()` —
which is a synchronous SQLAlchemy call in real code — comes back as an
unawaited coroutine instead of a `ScalarResult`, and `.all()` blows up.

This is the exact bug tracked separately in
[issue #158](https://github.com/ascherj/pathreview/issues/158) ("review_service
unit tests misconfigure async mocks — 13 of 19 tests fail"), which several
other students have already claimed. It lives in the same test file I'm
adding coverage to, so my new tests need to use a mock pattern that doesn't
have this problem (see `PLAN.md`) rather than copying the existing fixture
as-is.
