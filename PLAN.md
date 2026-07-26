## Solution plan

**Issue:** [#154 — Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x](https://github.com/ascherj/pathreview/issues/154)

### Understand

`GET /health` verifies PostgreSQL is reachable by running a `SELECT 1` liveness probe. In
`api/routes/health.py`, the probe passed the query as a **bare Python string** to an async
session:

```python
await db.execute("SELECT 1")   # original
```

SQLAlchemy 2.x (pinned `sqlalchemy>=2.0.0` in `pyproject.toml`) no longer accepts raw strings as
textual SQL. Instead of running, `execute()` raises at argument-validation time:

```
ArgumentError: Textual SQL expression 'SELECT 1' should be explicitly declared as text('SELECT 1')
```

The probe is wrapped in a broad `except Exception` block, so that `ArgumentError` is **swallowed**
and treated identically to a real outage: `dependencies.postgres` is set to `"unhealthy"`, the
overall `status` flips to `"unhealthy"`, and the endpoint raises `HTTPException(503)`. The net
effect: **`/health` returns 503 even when PostgreSQL is fully up.**

**Root cause:** Missing SQLAlchemy 2.x-compatible query construction in `api/routes/health.py` —
a raw string is passed where a `text()` clause is now required. It is *not* a database, engine, or
session-config problem; `core/database.py` is correct.

**Expected vs. actual:**

| Scenario | Actual (buggy) | Expected (fixed) |
|---|---|---|
| DB reachable | `ArgumentError` swallowed → `postgres: "unhealthy"`, HTTP **503** | probe returns a row → `postgres: "healthy"`, HTTP **200** |
| DB genuinely down | HTTP 503 (right answer, wrong reason) | HTTP 503 (right answer, real connection error) |

### Map

Files I expect to touch:

- **`api/routes/health.py`** — `health_check()`, the PostgreSQL probe line (`await
  db.execute(...))`, ~line 31). This is the only place `SELECT 1` appears in the repo
  (`grep -r "SELECT 1"` → one hit), so the blast radius is a single line + one import. **This is
  the core fix.**
- **`tests/unit/test_health.py`** — **new file.** No health test exists today. Tests live *flat*
  in `tests/unit/` (there is no `api/routes/` subdirectory), following names like
  `test_review_service.py`. Must be marked `@pytest.mark.unit` so `make test-unit` (`-m unit`)
  collects it.

Files I read to confirm the fix location but do **not** need to change:

- **`core/database.py`** — owns `get_db()` / `AsyncSessionLocal` / `create_async_engine`. The
  session and engine are correct 2.x async; only the caller's query form is wrong.
- **`api/main.py`** — confirms `app.include_router(health.router)` with no app-level prefix, so
  the endpoint is `GET /health` (router prefix `/health`).

### Plan

1. **Confirm the fix is in place and correct.** `api/routes/health.py` already imports
   `from sqlalchemy import text` and calls `await db.execute(text("SELECT 1"))` (committed early
   in `ae88d0e`). Re-read the file to confirm no regression.
2. **Reproduce the original bug on the real stack** (see Inputs & outputs). `docker compose up -d
   db redis vector-db`; on a throwaway branch, revert the line to the raw string; `make run`;
   `curl -i http://127.0.0.1:8000/health` → capture the **503 + `ArgumentError`** in the uvicorn
   log. Restore the fix; re-`curl` → **200 / `postgres: "healthy"`**. Commit the captured evidence
   into JOURNAL as the reproduction artifact.
3. **Write `tests/unit/test_health.py`** with two cases, using the repo's `AsyncMock` convention:
   - *Healthy path:* override `get_db` with a session whose `execute` is an `AsyncMock`; patch
     Redis + vector-DB so the test stays pure/unit → assert `200` and
     `dependencies.postgres == "healthy"`.
   - *Unhealthy path:* `session.execute = AsyncMock(side_effect=Exception("boom"))` → assert
     `503` and `dependencies.postgres == "unhealthy"`.
4. **Run `make test-unit`** — confirm the suite (incl. the new test) is green.
5. **Run `make check`** (ruff + black + mypy) and resolve the pre-existing `health.py` lint/type
   findings *minimally* (see Risks) so CI passes before the Week 9 PR.

### Inputs & outputs

**Function under change:** `health_check(db=Depends(get_db))` in `api/routes/health.py`.

**The fix (input → output):**
- *Input:* an `AsyncSession` from `get_db()` against a reachable Postgres.
- *Output change:* `text("SELECT 1")` executes cleanly (returns a row) instead of raising
  `ArgumentError`, so `dependencies.postgres = "healthy"`, overall `status = "healthy"`, response
  **200** (assuming Redis/vector-DB are also up).
- The DB-down path is unchanged: a real connection error still lands in the `except` block → 503.

**Reproduction (input → observed output):**
- *Input:* pre-fix code (`db.execute("SELECT 1")`) + real Postgres running.
- *Observed:* `curl -i http://127.0.0.1:8000/health` → `HTTP/1.1 503`, body
  `dependencies.postgres: "unhealthy"`, log line `postgres_health_check_failed … should be
  explicitly declared as text('SELECT 1')`.

**Test I'll write (drafted):**

```python
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from api.main import app
from core.database import get_db

@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_reports_postgres_healthy_when_probe_succeeds():
    """/health returns 200 + postgres 'healthy' when the SELECT 1 probe runs."""
    session = AsyncMock()
    session.execute = AsyncMock()                      # awaited → AsyncMock
    app.dependency_overrides[get_db] = lambda: session
    with patch("redis.Redis") as r:
        r.return_value.ping.return_value = True
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            resp = await c.get("/health")
    app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert resp.json()["dependencies"]["postgres"] == "healthy"

@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_reports_postgres_unhealthy_when_probe_raises():
    """/health returns 503 + postgres 'unhealthy' when the DB probe errors."""
    session = AsyncMock()
    session.execute = AsyncMock(side_effect=Exception("boom"))
    app.dependency_overrides[get_db] = lambda: session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://t") as c:
        resp = await c.get("/health")
    app.dependency_overrides.clear()
    assert resp.status_code == 503
    assert resp.json()["detail"]["dependencies"]["postgres"] == "unhealthy"
```

I'll adjust the exact client wiring to whatever `api/main.py` exposes; if the ASGI transport
proves fiddly I'll fall back to calling `health_check()` directly as an async function with a
mocked `db`.

### Risks & unknowns

1. **A mocked test does not prove the real fix.** An `AsyncMock` `execute` accepts *any* argument,
   so both the raw string and `text("SELECT 1")` would "pass" the unit test. The unit test guards
   the 200/503 branching logic; the *actual* SQLAlchemy-2.x behavior is only proven by the live
   reproduction (Plan step 2). I will not claim the test alone validates the fix.
2. **Pre-existing lint/type failures in `health.py`** (present on upstream `main`, *not*
   introduced by me): `B008` (`Depends(get_db)` in an argument default — standard FastAPI idiom
   ruff dislikes) and mypy inferring `health_status` as `dict[str, object]`, which errors on every
   indexed assignment. The early fix commit used `--no-verify`. Before the Week 9 PR, `make check`
   must pass — I'll annotate `health_status: dict[str, Any]` and add a scoped `# noqa: B008` (or
   the repo's preferred ignore), keeping changes minimal and not refactoring the module.
3. **No existing route test uses `TestClient`/`AsyncClient`.** I may be introducing a new test
   pattern; the direct-function-call fallback avoids that if the ASGI wiring fights me.
4. **Redis/vector-DB in the test.** The route also probes Redis and the vector DB; if I don't
   patch them the "healthy" case could flip to 503 for an unrelated reason. The test must isolate
   Postgres by patching or satisfying the other two probes. **Confirmed during reproduction:** the
   Redis probe references `settings.redis_host`/`settings.redis_port`, which don't exist on
   `Settings` (only `REDIS_URL` does) — so Redis *always* reports `"unhealthy"` and overall
   `/health` never returns 200. This is a **separate pre-existing bug, out of scope for #154**;
   I'll flag it in the PR but not fix it here. It's precisely why my healthy-path *unit* test must
   patch Redis rather than rely on the live route returning 200.
5. **Crowded issue.** Open PRs #160 and #177 target the same fix with multiple claimants. It's
   non-exclusive, but I'll review their diffs for prior art before opening mine.

### Edge cases

- **DB reachable but slow / transient error:** a real connection error must still yield 503
  (`postgres: "unhealthy"`) — the fix must not swallow genuine outages, only stop manufacturing a
  fake one.
- **DB up, Redis or vector-DB down:** overall `status` should still be `"unhealthy"` → 503, with
  `postgres: "healthy"` and the *other* dependency flagged. The Postgres fix must not mask other
  dependencies' state.
- **`vector_db_url` unset:** current code reports `"unavailable"` (not `"unhealthy"`) and does not
  trip 503 — I'll leave that behavior untouched (out of scope for #154).
- **Repeated/concurrent `/health` hits** (load balancers poll it): the probe must be idempotent
  and side-effect-free — `SELECT 1` is, and `text()` doesn't change that.

---

> Living document. I'll update **Understand** if reproduction reveals a different root cause, and
> add to **Map** if `make check` forces me to touch a file I didn't anticipate.
