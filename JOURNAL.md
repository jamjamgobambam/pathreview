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

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** _(this commit — see hash after push:
`https://github.com/smtanaka00/pathreview/commit/<REPRO_COMMIT>`)_

**Reproduction summary:**
Brought up the real stack (`docker compose up -d db redis`), temporarily reverted the one-line
fix back to `await db.execute("SELECT 1")`, ran the API, and hit `GET /health` against a fully
reachable Postgres. As the issue predicts, the endpoint returned **503** with
`dependencies.postgres: "unhealthy"`, and the uvicorn log showed the SQLAlchemy 2.x
`ArgumentError`. Restoring the `text()` wrap flipped `postgres` back to `"healthy"` and the log to
`postgres_health_check_passed` — confirming the fix addresses the reported behavior.

<details>
<summary>Captured evidence</summary>

**Before (buggy — raw string), `curl -i http://127.0.0.1:8000/health`:**
```
HTTP/1.1 503 Service Unavailable
{"detail":{"status":"unhealthy","dependencies":{"postgres":"unhealthy","redis":"unhealthy","vector_db":"healthy"},...}}
```
uvicorn log:
```
[error] postgres_health_check_failed  error="Textual SQL expression 'SELECT 1' should be explicitly declared as text('SELECT 1')"
```

**After (fixed — `text("SELECT 1")`), same request:**
```
HTTP/1.1 503 Service Unavailable
{"detail":{"status":"unhealthy","dependencies":{"postgres":"healthy","redis":"unhealthy","vector_db":"healthy"},...}}
```
uvicorn log:
```
[debug] postgres_health_check_passed
```
`postgres` flips `unhealthy → healthy`, which is the exact acceptance criterion for #154.
</details>

**PLAN.md link:** https://github.com/smtanaka00/pathreview/blob/fix/154-health-db-probe-text/PLAN.md

**Walkthrough video (recommended):** Skipped for now (recommended, not graded).

**Blockers or open questions:**
- **Discovered an adjacent, out-of-scope bug:** the Redis probe reads `settings.redis_host` /
  `settings.redis_port`, but `Settings` only defines `REDIS_URL` — so Redis always reports
  `"unhealthy"` (`'Settings' object has no attribute 'redis_host'`). This means overall `/health`
  still returns 503 even with my Postgres fix in place. It is **not** part of issue #154, so I'm
  scoping it out, but it prevents a clean end-to-end `200`. Open question for Week 9: mention it
  in the PR description, or leave it entirely alone?
- Before the Week 9 PR I still need to make `make check` pass (pre-existing `B008` lint + mypy
  `dict[str, object]` findings in `health.py`, documented in PLAN.md → Risks).
