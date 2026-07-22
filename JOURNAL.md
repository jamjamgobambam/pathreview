# PathReview — Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint is supposed to report whether PostgreSQL, Redis, and the
vector DB are reachable, but it always reports Postgres as `unhealthy` even when
the database is working fine. The cause is in `api/routes/health.py`: the probe
calls `await db.execute("SELECT 1")` with a bare string, and SQLAlchemy 2.x no
longer accepts raw strings — textual SQL has to be wrapped in `text()`. So the
call raises an exception, the handler marks Postgres unhealthy, and the whole
endpoint returns HTTP 503. A successful fix wraps the query in `sqlalchemy.text()`
(adding the import) so the probe actually runs, `/health` reports Postgres
healthy when the DB is up, and the endpoint can return 200 when all real
dependencies are available. This affects the API layer's monitoring/health path.

**Branch name:** fix/154-health-check-raw-sql

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

### "Is this right for me?" checklist — scope reasoning

- **Well-defined?** Yes. The issue names the exact file, the failing line, and the
  expected behavior, so there's no ambiguity about what "done" means.
- **Scope small enough for a first contribution?** Yes. The fix is a one-line
  change plus an import in a single file (`api/routes/health.py`), with no
  cross-module or architectural impact.
- **Do I understand the code it touches?** Yes. I reproduced the bug directly
  while setting up the project: `curl localhost:8000/health` returned 503 with
  `postgres: unhealthy` even though migrations and the seed script both connected
  to Postgres successfully, which matches the raw-SQL-string root cause.
- **Can I verify the fix?** Yes. I can re-hit `/health` and confirm Postgres now
  reports healthy, and add/adjust a unit test for the health route.
- **Conclusion:** Good fit for a first contribution — narrow, testable, and I've
  already seen it fail locally.
