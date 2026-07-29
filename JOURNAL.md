# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/158

**Issue title:** review_service unit tests misconfigure async mocks — 13 of 19 tests fail

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The unit tests for `core/services/review_service.py` are built on a mock database
session that doesn't match how SQLAlchemy's async API actually behaves. The service
awaits `db.execute(stmt)` and then calls `.scalars().first()` on what comes back —
`execute` is asynchronous, but the `Result` object it returns is an ordinary
synchronous one. The tests build that result as an `AsyncMock`, so `result.scalars()`
hands back a coroutine instead of a scalar accessor, and the service dies with
`AttributeError: 'coroutine' object has no attribute 'first'` before a single real
assertion runs. The practical damage is that 13 of the 19 tests in
`tests/unit/test_review_service.py` fail against service code that is itself correct,
which leaves the review CRUD paths (`get_review`, `list_reviews`) with effectively no
coverage — a genuine regression there would slip through unnoticed. A successful fix
reshapes the mock fixtures so the async/sync boundary is modelled correctly
(`AsyncMock` for `execute`, a synchronous mock for the result object), letting all 19
tests actually exercise the service and pass, with no change to the service code.

**Selection notes — "Is this issue right for me?"**

- *Tier fit.* This is labelled `tier-1` (also `bug`, `tests`). It's my first
  contribution to a codebase this size, so Tier 1 is the honest starting point — I
  wanted an issue where I'd spend my effort on understanding the project's
  conventions rather than fighting the problem itself.
- *Can I reproduce it?* Yes, before claiming it. `pytest tests/unit/test_review_service.py -q`
  gives exactly the 13 failed / 6 passed the issue reports, and the traceback lands on
  the line the issue describes. An issue I can reproduce on demand is one I can prove
  I've fixed.
- *Is the scope bounded?* The blast radius is one test file. The fix is in the
  fixtures and per-test mock setup, not in `core/services/review_service.py` — the
  issue is explicit that the service code is correct. That means no API contract to
  renegotiate and no migration to coordinate.
- *Do I have the skills?* The core of it is one specific idea: which parts of
  SQLAlchemy's async session are awaitable and which aren't, and how `AsyncMock`
  propagates to child attributes. That's a contained thing to learn properly, and it's
  knowledge that transfers to every other async test in this repo.
- *How will I know I'm done?* An unambiguous finish line — 19 passed — plus
  `make check` clean. No judgement call about whether the behaviour is "right".
- *What's the risk?* The main one is fixing the symptom the wrong way, by loosening
  assertions or making the service accommodate the mock, which would leave the tests
  green but worthless. The tests must keep asserting real behaviour; only the mock
  wiring should change.
- *Competition.* Roughly 16 people have commented on this issue, which is on the low
  end for Tier 1 in this tracker — several of the more approachable issues already
  have 40–50 claims.

**Branch name:** `fix/158-review-service-async-mocks`

**Setup confirmation:** [x] App runs locally at localhost:5173

Verified end to end rather than by eyeballing the page:

- `docker compose ps` — `db`, `redis`, and `vector-db` all healthy.
- `make setup` — migrations applied, database seeded with the three sample users.
- `make run` — frontend responds 200 at `localhost:5173` and Vite compiles the React
  entrypoint; API docs respond 200 at `localhost:8000/docs`.
- `POST /auth/login` with the seeded `user1@example.com` returns a JWT, which confirms
  the API is genuinely talking to the seeded database.

Two local setup notes, both environment-specific and kept out of the repo in an
ignored `docker-compose.override.yml`:

1. Port `6379` was already taken by another project's Redis, so this project's Redis
   is mapped to `6380` (with `REDIS_URL` in `.env` updated to match).
2. On Apple Silicon, the `chromadb/chroma:0.4.22` entrypoint reinstalls
   `chroma-hnswlib` on every start and pulls an unpinned NumPy 2.x, which breaks the
   image's own code (`np.float_` was removed in NumPy 2.0) and leaves the container in
   a crash loop. The override runs the same rebuild with NumPy held below 2.

`GET /health` currently reports `postgres` and `redis` as unhealthy, but that is not a
setup problem — it's two separate known bugs in `api/routes/health.py`, tracked as
issues #154 (passes a raw `"SELECT 1"` string, which SQLAlchemy 2.x rejects) and #155
(reads `settings.redis_host`, which doesn't exist on `Settings`). Both dependencies are
reachable directly: Postgres returns the 3 seeded users and Redis answers `PING`.

**Cohort ledger:** [ ] Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:**
https://github.com/thewildox/pathreview/commit/a7f98720c5f6399b8ca7b340c6d6b8c1f2e09ebb

**Reproduction summary:**
`pytest tests/unit/test_review_service.py -q` reproduces the issue exactly as reported —
13 failed, 6 passed — against unmodified service code. Every failure lands inside
`core/services/review_service.py` on `result.scalars()`, with
`AttributeError: 'coroutine' object has no attribute 'first'` (for `get_review`) or
`'all'` (for `list_reviews`), accompanied by
`RuntimeWarning: coroutine 'AsyncMockMixin._execute_mock_call' was never awaited`.

The cause is that the tests build the object returned by `db.execute(...)` as
`AsyncMock()` (13 occurrences in `tests/unit/test_review_service.py`). Because
`AsyncMock` propagates to its auto-created children, `mock_result.scalars` is itself an
`AsyncMock`, so `result.scalars()` returns a coroutine and the configured
`.first.return_value` chain is never reached. That does not match SQLAlchemy 2.x, where
`AsyncSession.execute()` is the only awaitable in the chain and the `Result` it returns
is synchronous.

The 6 passing tests are exactly the `create_review` ones, which only touch
`db.add`/`commit`/`refresh` and never call `execute` — so the failure boundary lines up
precisely with the diagnosis.

**Beyond the issue report:** I prototyped the mock-wiring fix in a scratch copy before
planning, and it yields **18 passed, 1 failed**, not the 19 the issue predicts.
`test_list_reviews_ordered_by_created_at` asserts
`mock_db_session.execute.assert_called_once()`, but `list_reviews` calls `execute` twice
by design — the count query at `review_service.py:64` and the paginated query at
`review_service.py:76` (`Expected 'execute' to have been called once. Called 2 times.`).
The broken async mocks were masking a second, independent defect: a wrong assertion.
Fixing only what the issue describes would leave the file red, so my plan covers both.

I also found three assertions that pass for any possible input and would stay green
against arbitrarily broken code — `test_list_reviews_returns_paginated_results:121`
(`len(reviews) > 0 or len(reviews) == 0`), `test_get_review_with_valid_uuid:326`
(`result is None or result is not None`), and
`test_list_reviews_ordered_by_created_at`, which asserts nothing about ordering at all.

**PLAN.md link:**
https://github.com/thewildox/pathreview/blob/fix/158-review-service-async-mocks/PLAN.md

**Walkthrough video (recommended):** not recorded

**Blockers or open questions:**
Going into Week 9, the open question is scope. Correcting the mock wiring and the
call-count assertion is required to get the file green. Rewriting the tautological
assertions is not strictly required by the issue text, but leaving them means shipping
tests that cannot fail — which is the same class of problem the issue is about. My plan
does both and flags the split, so a maintainer can ask me to cut the second half into a
follow-up PR.
