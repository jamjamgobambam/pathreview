## Solution plan

**Issue:** [Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x](https://github.com/ascherj/pathreview/issues/154)

### Understand

SQLAlchemy 2.x stopped accepting bare strings in `execute()`; the text has to go through `text()` first, or it throws `ObjectNotExecutableError`. `await db.execute("SELECT 1")` (`api/routes/health.py:31`) is still a raw string. The health check's own `try/except` catches that exception and treats it exactly like a real connection failure, so `/health` returns HTTP 503 and reports postgres as unhealthy, even when the database is sitting there healthy and reachable. Expected behavior: postgres reachable → `dependencies.postgres: "healthy"`, overall HTTP 200. What actually happens: postgres reachable → still `"unhealthy"`, HTTP 503, because the query itself never got the chance to run.

### Map

`api/routes/health.py`: The `health_check()` function, specifically the postgres branch at line 31. Two changes: import `text` from `sqlalchemy`, then wrap the string. `core/database.py` defines the `AsyncSession`/engine this all runs through, but nothing there needs to change.

### Plan

1. Add `from sqlalchemy import text` to `api/routes/health.py`.
2. Change line 31 to `await db.execute(text("SELECT 1"))`.
3. Restart the API and re-run the repro (`curl -i localhost:8000/health`) to confirm postgres flips to `"healthy"`.
4. Grep the rest of the codebase for other unguarded `.execute("...")` calls — if this slipped through once, it's worth checking whether it happened elsewhere too.
5. Add a regression test that hits the postgres branch directly, so a future SQLAlchemy bump can't quietly reintroduce this.

### Inputs & outputs

Input: `GET /health` - no request body or params. The only input that matters is the `AsyncSession` handed in through the `get_db()` dependency.
Output: changes from `dependencies.postgres: "unhealthy"` / HTTP 503 to `dependencies.postgres: "healthy"` / HTTP 200, assuming postgres is actually up.

### Risks & unknowns

Found something during reproduction that's related but out of scope: the redis branch of this same endpoint fails too, for a completely different reason (`health.py` reads `settings.redis_host`/`redis_port`, but `core/config.py` only defines `redis_url`). That's a separate bug. It means even after this fix ships, `/health` will probably still return HTTP 503 overall until someone fixes redis too — worth calling out in the PR description so a reviewer doesn't think the fix didn't work. Still need to grep for other raw-string `.execute()` calls elsewhere in the repo (ingestion scripts, migrations) to make sure this isn't a wider pattern.

### Edge cases

Postgres genuinely down or unreachable — the fix has to keep reporting that as `"unhealthy"`, not swallow real connectivity errors along with the fixed syntax error. Worth double-checking once a test client gets added that the fix behaves the same under a sync `TestClient` as it does under `curl`.
