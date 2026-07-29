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

**Reproduction commit link:** https://github.com/smtanaka00/pathreview/commit/3790cd7d8114c46ec38d6c7db6d3b7faa0d80887

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

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
The one-line fix (`text("SELECT 1")` + import) was already committed in Week 8 (`ae88d0e`). This
week I completed the test sub-task from PLAN.md: added `tests/unit/test_health.py` with three
cases — `/health` returns 200 with `postgres: "healthy"` when the probe succeeds, raises
`HTTPException(503)` with `postgres: "unhealthy"` when it errors, and a regression guard
(`test_probe_uses_text_clause_not_raw_string`) that asserts the probe runs a SQLAlchemy
`TextClause` rather than a raw string. The first two cover the 200/503 branching; the third is
what actually catches issue #154 — I verified that reverting the fix to `db.execute("SELECT 1")`
fails *only* that third test. All three pass and the new file is ruff- and black-clean.

I also recorded the repo's pre-existing CI baseline before touching anything: `make test-unit` is
53 failed / 375 passed and `ruff check .` reports 179 errors — all unrelated to #154 (and mypy
can't run to completion locally on a numpy stub). After my change the suite is 53 failed / **378
passed**: my 3 tests added, zero new failures.

**Next steps:**
- Open a draft PR to `ascherj/pathreview` early this week, template fully filled, documenting the
  pre-existing baseline and the out-of-scope Redis bug in Notes for Reviewers.
- Request peer/mentor review in Slack; iterate on feedback.
- Mark the PR ready for review, then complete Check-in 2 with the PR link and submit the branch
  URL via the portal.

**Blockers:**
- Resolved the two open questions from Week 8: the out-of-scope Redis bug will be **mentioned in
  the PR, not fixed** (keeps the diff Tier-1); and `make check` cannot pass cleanly on this repo
  regardless of my change (documented pre-existing failures), so "passes" here means my changes
  introduce no new failures — which I've confirmed. No hard blockers.

---

### Check-in 2 (end of week)

**PR link:** _(to be added Sunday once the draft PR is marked ready for review)_

**Branch:** `fix/154-health-db-probe-text`

**What you built:**
_(fill Sunday)_

**Tests added or updated:**
`tests/unit/test_health.py` — three unit tests covering the 200 healthy path, the 503 probe-error
path, and a regression guard that the probe uses a SQLAlchemy `text()` clause.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes
_(Note: this repo has documented pre-existing failures — see PR "Notes for Reviewers." "Passes"
here means my changes introduce no new failures: unit suite 53 pre-existing fails unchanged,
+3 of my tests passing.)_

**Draft PR feedback received from:** _(fill Sunday)_
