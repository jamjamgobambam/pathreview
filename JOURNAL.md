## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`health.py` passes a simple query to the database to check it is working. The query must be sent through a specific method, but the execute call receives it as a plain string, which raises an error. As a result, the health endpoint cannot tell whether the database is actually working. Wrapping the query in the required method would let the endpoint report the real database status.

**Branch name:** fix/154-health-db-probe-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**"Is this right for me?" reasoning:**
This is my first open source contribution. So, I have chosen Tier 1. The issue 154 publisher has already described the cause of the problem and the affected file explicitly. I fully understood what is wrong with the endpoint. This fix is isolated to a single file, so the scope is small enough for me to handle.


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/rarepig/pathreview/tree/bf543f02befa8a2ab5295f35a600eed55b58b62c

**Reproduction summary:**
Reproduced manually. With the Docker Postgres container confirmed running and
healthy (`docker ps` → `Up (healthy)` on port 5433), calling `GET /health`
returned `"postgres": "unhealthy"`. Since the database is reachable, this is a
false negative caused by the raw `"SELECT 1"` probe in `api/routes/health.py`
(line 31), which raises `ArgumentError` under SQLAlchemy 2.x and is swallowed by
the surrounding `except`.

**Why no existing test catches this:**
There is no test covering `api/routes/health.py`. The project's unit tests mock
the DB session with `AsyncMock` (see `tests/unit/test_review_service.py`), so a
mocked `execute()` never raises the real SQLAlchemy `ArgumentError` — the bug is
invisible to that pattern. Reproducing it requires a live session, as the issue
author notes, which is why I reproduced it manually via `GET /health` + `docker ps`.

**PLAN.md link:** https://github.com/rarepig/pathreview/blob/fix/154-health-db-probe-text/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]