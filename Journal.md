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

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/ApoorvThite/pathreview/commit/4178537f88212fc7e0a5cbb87948c98a65590ad9

**Reproduction summary:**
Added `tests/integration/test_health_check.py`, which calls `health_check()` with a real, working in-memory SQLite `AsyncSession` and asserts the result. The test passes today because `dependencies.postgres` is reported `"unhealthy"` even though the session is fully functional — the bare-string `db.execute("SELECT 1")` call raises `ArgumentError` under SQLAlchemy 2.x, and that exception is swallowed and misreported as the database being down.

**PLAN.md link:** https://github.com/ApoorvThite/pathreview/blob/fix/154-health-check-sql-text-wrap/PLAN.md

**Walkthrough video (recommended):**

**Blockers or open questions:**
While reading `api/routes/health.py`, found a second, unrelated bug: the Redis probe references `settings.redis_host` / `settings.redis_port`, but `core/config.py`'s `Settings` only defines `redis_url` — so the Redis leg always raises `AttributeError` and reports unhealthy regardless of the Postgres fix. This means `/health` will likely still return 503 overall even after fixing #154, purely from the Redis leg. Planning to flag this as a separate follow-up issue rather than fold it into #154's scope — open to feedback on that call in Week 9.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md: wrapped the Postgres probe's raw SQL string in `sqlalchemy.text("SELECT 1")` in `api/routes/health.py` (plan step 1, one-line change plus the `sqlalchemy.text` import). Updated the reproduction test in `tests/integration/test_health_check.py` to assert `dependencies.postgres == "healthy"` instead of the old buggy `"unhealthy"` expectation (plan step 2), and added a second, narrower test asserting no `postgres_health_check_failed` log event fires, so a future regression back to a bare string is caught even if the string assertion is ever loosened (plan step 3).

**Next steps:**
Run the full local check suite (`make check`, `make test-unit`, and the integration tests) to confirm the fix doesn't introduce regressions, document any pre-existing failures, self-review against `docs/CONTRIBUTING.md`, open a draft PR, and get peer/mentor feedback before finalizing.

**Blockers:**
No Docker/Postgres stack available in this dev environment, so verification is against an in-memory SQLite `AsyncSession` (same approach as the Week 8 reproduction test) rather than real Postgres — flagged as a residual risk in `PLAN.md`.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/805

**Branch:** `fix/154-health-check-sql-text-wrap`

**What you built:**
Fixed the `/health` endpoint's false-negative Postgres probe by wrapping the raw SQL string in `sqlalchemy.text("SELECT 1")`, which SQLAlchemy 2.x's `AsyncSession.execute()` requires for textual SQL. The probe now actually executes and reports `dependencies.postgres` accurately instead of always reporting `"unhealthy"`.

**Tests added or updated:**
`tests/integration/test_health_check.py` — updated the existing reproduction test to assert `dependencies.postgres == "healthy"` against a live, working session, and added a new test asserting no `postgres_health_check_failed` log event fires, to catch any future regression back to a bare SQL string.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

Both commands surfaced pre-existing failures unrelated to this change (53 `test-unit` failures in modules like `test_review_service.py`, `test_pii_scrubber.py`, `test_resume_parser.py`; 183 pre-existing `ruff` errors; 11 pre-existing `mypy` errors, including the separate Redis config bug noted in Week 8). Confirmed via `git stash` that the exact same failure counts exist on the base commit, so none of these were introduced by this change — documented in the PR description.

**Draft PR feedback received from:** none yet — PR opened as draft, requesting peer/mentor review before finalizing.