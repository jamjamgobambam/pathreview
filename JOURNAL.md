## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
SQLAlchemy 2.x won't execute raw SQL without wrapping it in `text()`, but the health check endpoint in `api/routes/health.py` doesn't do that. It just passes "SELECT 1" directly, which breaks the `/health` endpoint even when the database is fine. That defeats the whole point of a health check—you can't verify database connectivity. Wrapping the SQL string in `text()` restores that functionality so the endpoint actually confirms the database is up.

**Why this one:** My first open source contribution, so I wanted something contained to one file rather than a sprawling change.

**Branch name:** fix/154-health-check-sql

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [will add once this JOURNAL.md update is pushed]

**Reproduction summary:**
Postgres and Redis were already running via `docker-compose`, so I just started the API with `make run` in one terminal window and ran `curl -i localhost:8000/health` in another terminal window. It came back `503`, postgres marked `unhealthy`. Server logs showed error: `Textual SQL expression 'SELECT 1' should be explicitly declared as text('SELECT 1')`, pointing straight at `api/routes/health.py:31`, where `db.execute("SELECT 1")` passes a bare string to an `AsyncSession`. SQLAlchemy 2.x won't coerce that automatically anymore — it needs `text("SELECT 1")` — so the check fails even though the database is perfectly healthy. Confirmed error was consistently reproducible.

Side note, not part of this issue: the same `/health` call also reported redis as unhealthy, but for an unrelated reason — `core/config.py` only defines `redis_url`, and `health.py` reads `settings.redis_host`/`settings.redis_port`, which don't exist. Leaving that alone since the issue I picked is scoped to the postgres/`text()` fix.

**PLAN\.md link:** [PLAN\.md](PLAN.md)

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
Should the `redis_host`/`redis_port` mismatch get filed as its own issue? It's a real bug but outside what I scoped for #154.