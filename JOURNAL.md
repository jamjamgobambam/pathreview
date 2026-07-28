# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The health check endpoint (`GET /health`) in `api/routes/health.py` runs a raw SQL string `"SELECT 1"` to verify the database is reachable. SQLAlchemy 2.x no longer accepts bare string SQL — it must be wrapped with `sqlalchemy.text()`. Because of this, the DB probe always raises an `ArgumentError` and reports the database as down even when it is perfectly healthy. A successful fix wraps the literal string in `text("SELECT 1")`, making the probe compliant with SQLAlchemy 2.x and accurately reflecting the database's actual status.

**"Is this right for me?" reasoning:**
This is a well-scoped, single-line change in one file (`api/routes/health.py`) with a clear error message pointing directly to the fix. The issue description includes exact reproduction steps and the expected outcome, making it easy to verify. It's a good Tier 1 issue — low risk, no complex logic, and a great way to get familiar with the codebase structure and contribution workflow.

**Branch name:** fix/154-health-db-probe-text-sql

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [test: add reproduction test and plan for issue #154](https://github.com/sudhiracodes/pathreview/commit/7ba97dc)

**Reproduction summary:**
Added a unit test (`tests/unit/test_health_db_probe.py`) that mocks the async DB session to raise the exact `ArgumentError` SQLAlchemy 2.x raises for a bare string. Running the test against the unfixed code confirms the route catches the error and returns HTTP 503 with `"postgres": "unhealthy"` — proving the bug is real and precisely located at `api/routes/health.py` line 31.

**PLAN.md link:** https://github.com/sudhiracodes/pathreview/blob/fix/154-health-db-probe-text-sql/PLAN.md


**Blockers or open questions:**
None — the fix is a one-line change. Will run the full test suite after applying the fix to confirm no regressions before opening the PR.
