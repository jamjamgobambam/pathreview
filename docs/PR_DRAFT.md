# PR draft for issue #154

Paste the title and body below when opening the PR on GitHub (against
`ascherj/pathreview:main`), then delete this file from your branch (or leave
it — it's harmless, but it's scratch, not a permanent doc).

## Title

```
fix(api): wrap health check SQL query in text() for SQLAlchemy 2.x
```

## Body

```markdown
## Summary
The `GET /health` endpoint's Postgres probe passed a raw SQL string
(`"SELECT 1"`) directly to `AsyncSession.execute()`. SQLAlchemy 2.x's
`execute()` only accepts `Executable` objects and rejects plain strings
with `ObjectNotExecutableError` (a subclass of `ArgumentError`) before the
query ever reaches the database. The health check's broad
`except Exception` silently caught this, so `/health` always reported
`dependencies.postgres: "unhealthy"` — even when Postgres was fully up and
reachable. The fix wraps the query in `sqlalchemy.text()`, which is what
2.x's unified `execute()` API requires for a raw textual query.

## Issue
Closes #154

## Changes
- `api/routes/health.py`: added `from sqlalchemy import text` and changed
  `await db.execute("SELECT 1")` to `await db.execute(text("SELECT 1"))`.
  Also added an inline `# noqa: B008` on the `health_check(db=Depends(...))`
  line — pre-existing ruff warning, unrelated to #154, but pre-commit lints
  the whole file and this is the first commit in the branch to touch
  `health.py`, so it now blocks any commit here. Suppressed rather than
  fixed repo-wide since the `Depends()` default-argument pattern it flags
  is the standard, intentional FastAPI DI idiom used in ~17 other places.
- `tests/unit/test_health_check.py`: added a `TestHealthCheckPostgresProbe`
  test class with three route-level regression tests (see Testing below),
  fully type-annotated to satisfy the repo's `disallow_untyped_defs` mypy
  config.

## Testing
**Automated:**
- Added `tests/unit/test_health_check.py::TestHealthCheckPostgresProbe`
  (3 tests), on top of the 2 reproduction tests already in that file from
  last week:
  - `test_postgres_probe_executes_text_wrapped_query` — asserts the object
    passed to a mocked `AsyncSession.execute()` is a `TextClause`, not a
    raw `str`. This is the assertion that actually catches a regression to
    the pre-fix code — a mock's `execute()` doesn't raise on a plain string
    the way a real SQLAlchemy engine does, so this had to check the
    argument type directly rather than just the resulting status.
  - `test_postgres_reports_healthy_when_query_succeeds` — confirms
    `dependencies.postgres == "healthy"` when the query succeeds.
  - `test_postgres_reports_unhealthy_when_connection_fails` — confirms a
    genuine connection failure still correctly resolves to `"unhealthy"`
    (the fix doesn't change this path).
  - Ran `make test-unit`: 380 passed (377 pre-existing + 3 new), 53 failed.
    I confirmed by running `make test-unit` on this same branch **before**
    my change that all 53 failures are pre-existing and unrelated (mostly
    `test_review_service.py`, `test_resume_parser.py`, `test_pii_scrubber.py`,
    etc.) — the exact same 53 tests fail with or without this change.
  - Ran `make check` (lint + format + typecheck): pre-existing, unrelated
    issues remain (182 ruff errors repo-wide before my change, 179 after —
    the drop is from cleaning up import order/an unused `timedelta` import
    while I was in this file, not from anything logic-related). I diffed
    `mypy api/routes/health.py` before/after my change line-by-line: it's
    the same 11 errors before and after (2 attr-defined, 1 call-overload,
    7 index, 1 no-untyped-def), just shifted line numbers from the import
    reordering — my change adds zero new mypy errors but doesn't resolve
    any either, since none of the 11 are on the line it touches. The
    remaining errors in this file are pre-existing and out of scope: a
    `B008` `Depends()` default-argument lint warning (same pattern used in
    17 other places across `api/routes/`), and the separate Redis config
    bug noted below.
  - `black --check` passes with no changes needed.

**Manual verification:**
1. `docker compose up -d db` (Postgres becomes healthy)
2. `uvicorn api.main:app --port 8000`
3. `curl http://localhost:8000/health`
   - **Before this fix:** `503`,
     `"dependencies":{"postgres":"unhealthy",...}`, with the server log
     showing `postgres_health_check_failed error="Textual SQL expression
     'SELECT 1' should be explicitly declared as text('SELECT 1')"`.
   - **After this fix:** `dependencies.postgres` is `"healthy"`. (The
     endpoint still returns `503` overall — see the Redis note below — but
     the Postgres-specific bug this issue is about is fixed.)
4. Stop Postgres (`docker compose stop db`) and re-run the curl — confirms
   `dependencies.postgres` correctly still reports `"unhealthy"` for an
   actually-down database, so the fix doesn't mask real failures.

## Notes for Reviewers
- **This PR intentionally does not fix a second, pre-existing bug in the
  same endpoint.** The Redis probe (`api/routes/health.py:44-46`) reads
  `settings.redis_host` / `settings.redis_port`, but `core/config.py` only
  defines `redis_url` — this raises `AttributeError` on every request,
  caught by the same broad `except Exception`, so `dependencies.redis` (and
  therefore the overall `status`/HTTP code) is always `"unhealthy"`
  regardless of this fix. I verified this is a separate, unrelated issue
  (confirmed via the server log: `redis_health_check_failed error="'Settings'
  object has no attribute 'redis_host'"`) and scoped this PR to #154 only,
  rather than scope-creeping the Redis fix in here too. Happy to file a
  follow-up issue for it if that's the preferred process.
- The three broad `except Exception` blocks in this endpoint are a
  contributing factor to how #154 went unnoticed (catch-log-mark-unhealthy
  hides the actual error from callers). I didn't change that pattern here
  since it's a bigger, separate refactor, but flagging it in case it's
  worth a follow-up issue.
- Reviewers verifying manually: after step 3 above, the HTTP status will
  still be `503` because of the Redis bug — check
  `dependencies.postgres` in the JSON body specifically, not the top-level
  `status` or HTTP code.
```
