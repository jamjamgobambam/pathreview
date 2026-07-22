## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `/health` endpoint in `api/routes/health.py` checks Postgres connectivity by calling
`db.execute("SELECT 1")` with a plain Python string. SQLAlchemy 2.x no longer accepts raw
strings for textual SQL — they must be wrapped in `sqlalchemy.text()` — so the call raises
an `ArgumentError` instead of running the query. Because that exception is caught by the
surrounding `try/except`, the health check reports Postgres (and the overall service) as
unhealthy even when the database is up and reachable. A correct fix wraps the query string
in `text("SELECT 1")` so the probe actually executes and reflects the real DB status.

**Scope reasoning ("Is this right for me?"):**
Worked through the issue-selection checklist and confirmed this is a well-sized Tier 1 pick:

- **Appropriately scoped / bounded blast radius:** The fix is a single line in a single file
  (`api/routes/health.py:31`) — wrapping the existing `"SELECT 1"` string in `text(...)`. No
  schema changes, no migrations, no API-contract changes, and no new dependencies (`text` already
  ships with the SQLAlchemy version in use).
- **Well-understood root cause:** The failure mode is a known SQLAlchemy 2.x behavior change
  (raw strings are no longer accepted for textual SQL), so there is no open-ended investigation.
- **Clear, deterministic acceptance criteria:** With the DB up, `/health` should report Postgres
  (and overall status) as healthy instead of catching an `ArgumentError`. This is directly
  observable and testable via the existing `/health` endpoint.
- **Fits my skill level and available time:** Self-contained, isolated to the health probe's
  `try/except`, with no cross-subsystem coordination — completable within the Week 7 window.

This is why it maps to Tier 1 rather than a larger tier.

**Branch name:** fix/154-health-check-textual-sql

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger
