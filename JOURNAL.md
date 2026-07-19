# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `GET /health` endpoint checks that PostgreSQL is reachable by running a probe query, but
it passes the query as a bare Python string — `await db.execute("SELECT 1")` in
`api/routes/health.py`. SQLAlchemy 2.x (pinned `>=2.0.0` in `pyproject.toml`) no longer accepts
raw strings for textual SQL and raises `ArgumentError: Textual SQL expression 'SELECT 1' should
be explicitly declared as text('SELECT 1')`. That error is swallowed by the probe's
`except Exception` block, so Postgres is reported as `"unhealthy"` and the endpoint returns
**503 even when the database is fully reachable**. A successful fix wraps the query in
`sqlalchemy.text()` so the probe runs cleanly, `GET /health` returns `200` with
`postgres: "healthy"` when the DB is up, and still returns `503` when the DB is genuinely down.

**Branch name:** fix/154-health-db-probe-text

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

### "Is this right for me?" checklist reasoning

- **Understand the issue:** Yes — I can explain it in my own words (see summary above): a
  SQLAlchemy 2.x compatibility bug that makes a healthy database report as down.
- **Which part of the app:** The API health route, `api/routes/health.py`, backed by the async
  `AsyncSession` from `core/database.py`. Both files located and read.
- **What "done" looks like:** DB reachable → `200` + `postgres: "healthy"`; DB down → `503`.
  Concrete before/after documented in the prep notes below.
- **Tier fit:** Tier 1. The change is one import + one line in a single file, plus a new unit
  test. No architectural change, no cross-module impact — `grep "SELECT 1"` matches only this
  one line.
- **Codebase readiness:** Found and read the exact line, the `get_db` dependency, and the repo's
  test-mocking convention (`AsyncMock` session in `tests/unit/test_review_service.py`). Note:
  there is currently **no** `test_health.py`, so a new test file is needed for the PR.
- **Scope & time:** Realistic Tier-1 scope (3–6 hrs). No blockers/dependencies.
- **Claims:** Non-exclusive; this issue is popular (open PRs #160, #177, multiple claimants).
  Acceptable, just crowded.

---

## Appendix — Technical prep (Weeks 8–9 planning)

### Acceptance criteria (before / after)

| | Before the fix | After the fix |
|---|---|---|
| DB reachable | Probe raises `ArgumentError`, caught → `postgres: "unhealthy"` | Probe returns a row → `postgres: "healthy"` |
| Overall status | `"unhealthy"` | `"healthy"` (assuming Redis/vector DB ok) |
| HTTP code | `503 Service Unavailable` | `200 OK` |
| DB actually down | `503` (correct, but for the wrong reason) | `503` (correct — real connection error) |

### Planned fix

**Import** (top of `api/routes/health.py`):

```python
from sqlalchemy import text
```

**Probe line:**

```python
# before
await db.execute("SELECT 1")
# after
await db.execute(text("SELECT 1"))
```

### Test plan

No `test_health.py` exists yet, so a new `tests/unit/api/routes/test_health.py` is needed. Using
the repo's `AsyncMock` session convention:

- **Healthy path:** `session.execute` returns a mock; override the FastAPI `get_db` dependency;
  assert `200` and `dependencies.postgres == "healthy"` (patch Redis/vector-DB calls).
- **Unhealthy path:** `session.execute = AsyncMock(side_effect=Exception("boom"))`; assert `503`
  and `dependencies.postgres == "unhealthy"`.
