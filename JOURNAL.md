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
