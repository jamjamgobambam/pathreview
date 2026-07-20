## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The health check endpoint's database probe, in `api/routes/health.py`, runs the raw SQL string `"SELECT 1"` directly against the database session. SQLAlchemy 2.x no longer accepts bare strings for textual SQL — it requires them to be wrapped in `sqlalchemy.text()` — so the probe throws an `ArgumentError` and the `/health` endpoint reports the database as unreachable even when it's working fine. A successful fix wraps the query string in `text()` so the probe executes correctly and the health check accurately reflects the database's real status.

**Branch name:** fix/154-health-check-sql-text-wrap

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

"Is this issue right for me?" checklist:

Understanding the issue: The DB health check probe runs the raw SQL string "SELECT 1" directly. SQLAlchemy 2.x requires textual SQL to be wrapped in sqlalchemy.text(), so the probe throws an ArgumentError and /health reports the database as down even when it's reachable. "Done" means GET /health returns a healthy status instead of raising that error.
Affected area: api/routes/health.py (API layer).
Tier fit: Tier 1 / good first issue — appropriate scope for an early contribution.
Codebase readiness: Read the relevant function in api/routes/health.py in full. Located and read the corresponding test file end-to-end.
Scope and time: Checked issue comments and ledger Claims count for #154. Estimated at 3–6 hours, within the Tier 1 range. No stated blockers on the issue.