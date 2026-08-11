# JOURNAL

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The database probe in `api/routes/health.py` calls `db.execute("SELECT 1")` with a plain Python string. SQLAlchemy 2.x requires textual SQL to be wrapped explicitly with `sqlalchemy.text()`, so this call raises an `ArgumentError` instead of running the query. Because the health check catches that exception and marks postgres as unhealthy, `GET /health` reports the database as down even when it's fully reachable, which would falsely trip alerting/monitoring on a healthy deployment. A successful fix wraps the raw string in `text()` so the probe executes correctly and only reports "unhealthy" when the database is actually unreachable.

**"Is this right for me?" checklist reasoning:**

*Part 1 — Understanding the issue:* The `/health` route calls `db.execute("SELECT 1")` with a bare string. SQLAlchemy 2.x only accepts raw SQL wrapped in `sqlalchemy.text()`, so the call raises `ArgumentError`, which the route's `except Exception` catches and reports as `postgres: "unhealthy"` — even when the database is completely reachable. A correct fix makes the probe run cleanly and report `"healthy"` when Postgres is actually up, `"unhealthy"` only when it's actually down. Affected area: `api/routes/health.py` (label `api`).

*Part 2 — Tier fit:* Labeled `tier-1` in the tracker, and it matches the Tier 1 description — the change lives in one file, is a one-line fix (`text("SELECT 1")`), and doesn't require understanding how modules interact. This is my first contribution to a codebase this size, so Tier 1 is the right level.

*Part 3 — Codebase readiness:* Found and read the exact line (`api/routes/health.py:31`) and the surrounding `try/except` blocks for redis and vector_db, which follow the same pattern. Confirmed `core/database.py` uses the async SQLAlchemy 2.x engine (`create_async_engine`/`AsyncSession`), which is why `text()` is required. There's no existing test file for the health route (`tests/unit` and `tests/integration` have no `health` or `api` test files), so I'll add one — `tests/unit/test_review_service.py` shows the project's pattern for mocking an async db session with `AsyncMock`, which I'll follow.

*Part 4 — Scope and time:* Several others have already commented on the issue and opened PRs against it (this is a practice repo, so duplicate work across the cohort is expected and fine). Scope is small — I already applied and verified the fix locally (confirmed via `GET /health` returning `postgres: "healthy"`), well within the Tier 1 3–6 hour estimate. No blockers or dependencies on other issues.

**Branch name:** fix/154-health-check-raw-sql

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [6fa94a0](https://github.com/heyz-hye/pathreview/commit/6fa94a0) (branch `fix/155-health-check-redis-host`)

**Reproduction summary:**
Switched issues this week to [#155](https://github.com/ascherj/pathreview/issues/155) — my Week 7 issue (#154) turned out to already be fully fixed and tested on `fix/154-health-check-raw-sql`, so there was no un-fixed bug left to reproduce on that branch. For #155, I called `health_check()` directly against the real (unmocked) `Settings` object and confirmed `settings.redis_host` raises `AttributeError: 'Settings' object has no attribute 'redis_host'`, since `Settings` only defines `redis_url`. The route's broad `except Exception` swallows this and reports `redis: "unhealthy"` (503 overall) without ever contacting Redis. I added a regression test (`TestHealthCheckRedisHost`) that exercises the real `Settings` instance instead of a mock — the existing tests mock `core.config.settings` entirely, which is exactly why they didn't catch this bug (a `MagicMock` silently satisfies any attribute access).

**PLAN.md link:** [PLAN.md](https://github.com/heyz-hye/pathreview/blob/fix/155-health-check-redis-host/PLAN.md)

**Walkthrough video (recommended):** [not recorded]

**Blockers or open questions:**
Need to double check whether `redis.Redis.from_url(settings.redis_url)` is a drop-in replacement everywhere Redis auth/TLS might matter (e.g. `rediss://` URLs with a password) before Week 9 — planning to grep for other `redis_host`/`redis_port` references to confirm this is the only call site.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Switched issues again this week, this time to [#89](https://github.com/ascherj/pathreview/issues/89) (`docs`/`good first issue`, tier-1) — the `#155` redis_host fix from Week 8 is still valid and unmerged on `fix/155-health-check-redis-host`, but I'm using this week's graded PR slot for #89 instead. `docs/API.md` documented one-line summaries for each endpoint but had no request body schemas at all. Read `api/routes/profiles.py`, `api/routes/reviews.py`, and their Pydantic schemas (`api/schemas/profile.py`, `api/schemas/review.py`) to confirm the real field types/constraints, then added a field table, auth requirement, and example request for both `POST /profiles` (multipart form + optional resume file) and `POST /reviews` (JSON body with `profile_id`) directly below their existing one-liners in `docs/API.md`.

**Next steps:**
Open the PR, request peer/mentor feedback on the draft, and address any feedback before marking it ready for review.

**Blockers:**
None. This is a docs-only change (no code paths touched), so there are no new unit tests to add — confirmed by diffing against `main` (`docs/API.md` is the only file changed). `make check` and `make test-unit` both show pre-existing, unrelated failures (182 pre-existing lint errors and 53 pre-existing test failures, mostly in `tests/unit/test_tech_detector.py`, `test_resume_parser.py`, `test_review_service.py`, etc.) that exist identically on `main` before my change and are untouched by it.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/720

**Branch:** `docs/89-profiles-reviews-request-schema`

**What you built:**
Added request body documentation to `docs/API.md` for `POST /profiles` and `POST /reviews`, the two endpoints flagged in #89. Each now has a field table (name, type, required, description), the auth requirement, and a runnable example request, sourced directly from the route handlers and Pydantic schemas so the docs match the real validation behavior (e.g. `POST /profiles` is `multipart/form-data` because of the resume file upload, not JSON like `POST /reviews`).

**Tests added or updated:**
Documentation-only change — no code paths were modified, so no test files were touched. Verified via `git diff main --stat` that `docs/API.md` is the only file changed.

**Self-review confirmation:** [x] make check passes (no new failures vs. `main`)  [x] make test-unit passes (no new failures vs. `main`)

**Draft PR feedback received from:** Peer review in Slack came back as feedback for issue #151 (bias detector patterns) rather than #89 — mismatched/misdirected, not applicable to this docs change. Re-requesting feedback on the correct PR.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No maintainer review came in on PR #720. Reviewer feedback is not a feature in Summer 2026, so no comments arrived during this window. The only peer feedback I received earlier (Week 9) was misdirected — it was review for issue #151, not my #89 docs PR — so there was nothing applicable to act on.

**How you responded:**
Nothing to respond to. I re-read the #720 diff one more time to confirm the request-body tables in `docs/API.md` still matched the current Pydantic schemas in `api/schemas/profile.py` and `api/schemas/review.py`, and left the PR as submitted.

---

### Reflection

**What was harder than you expected?**
Issue *selection* was harder than the actual work, every week. I picked #154 in Week 7, but by Week 8 discovered it was already fully fixed and tested on my branch, so I switched to #155 (the `redis_host` bug). Then in Week 9 I moved again to #89 (documenting request bodies). Each switch cost real time re-reading the codebase from scratch, and taught me that "is there actually un-done work left here?" is a question to answer *before* committing to an issue, not after. The #155 bug was the most technically interesting — the existing tests mocked `core.config.settings` entirely, so a `MagicMock` silently satisfied `settings.redis_host` and hid the very bug the tests should have caught. Realizing the tests were masking the bug, not missing it, was the least obvious thing I found all module.

**What did you learn about working in a large codebase?**
That documentation is only trustworthy if it's derived from the source, not written from memory. For #89 I couldn't just describe what `POST /profiles` "probably" accepts — I had to read the route handler and its Pydantic schema to find that it's `multipart/form-data` with an optional resume file, not JSON like `POST /reviews`. Getting that one distinction wrong would have made the docs actively misleading. In a codebase this size, the schema *is* the spec, and my job was to surface it accurately, not to invent it.

**How did AI tools help — and where did they fall short?**
AI was strong at explaining framework-level behavior fast — why SQLAlchemy 2.x rejects raw-string SQL (#154), and how `MagicMock` auto-satisfies attribute access (which is exactly why the #155 bug hid). Where it fell short was anything specific to *this* repo's wiring: it couldn't tell me #154 was already fixed on my branch, that `Settings` defines `redis_url` but not `redis_host`, or that `POST /profiles` uses multipart. Those all came from reading the actual source. The pattern held all module — AI for the general mechanism, me for the repo-specific truth.

**What would you do differently if you started over?**
I'd verify an issue still has real, un-done work *before* writing it into my journal — that alone would have saved two mid-module issue switches. I'd also request peer review on the correct PR earlier and more explicitly; the one review I got landed on the wrong issue (#151) and I only had time to re-request, not to actually receive usable feedback. And I'd record at least one walkthrough video — I marked it "not recorded" every week, and narrating the #155 mock-masking-the-bug story out loud would have sharpened my own understanding.

**What are you most proud of?**
The #155 regression test. Instead of mocking the whole settings object like the existing tests did, it exercises the real `Settings` instance — which is the only way to actually catch an `AttributeError` on `redis_host`. It's a small change, but it fixes the blind spot in the test suite that let the bug exist in the first place, not just the bug itself.

---
