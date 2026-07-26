# Issue #155 — Reproduction and Solution Plan

## Issue

**Issue link:** https://github.com/ascherj/pathreview/issues/155

**Issue title:** Health check references `settings.redis_host`, which does not exist on Settings

**Tier:** Tier 1

**Branch:** `fix/155-health-check-redis-settings`

## Problem summary

The `/health` endpoint checks PostgreSQL, Redis, and vector database status. Its Redis check originally attempted to use `settings.redis_host` and `settings.redis_port`, but the application's `Settings` model only defines `redis_url`.

Because those attributes do not exist, the Redis check raises an `AttributeError`. The exception is caught by the health route, which marks Redis as unhealthy and causes the endpoint to return HTTP 503 even when the configured Redis URL may be valid.

A successful fix should make the health route use the existing `settings.redis_url` configuration and verify Redis connectivity without introducing duplicate host and port settings.

## Reproduction steps

1. Open `api/routes/health.py`.
2. Locate the Redis health-check block.
3. Confirm that the Redis client is created using:

```python
settings.redis_host
settings.redis_port
```

4. Open `core/config.py`.
5. Confirm that `Settings` defines:

```python
redis_url
```

but does not define `redis_host` or `redis_port`.

6. Run the focused health tests before applying the fix:

```powershell
.\.venv\Scripts\python -m pytest tests/unit/test_health.py -v
```

7. Observe that the tests fail because:

   * PostgreSQL is marked healthy by the mocked database.
   * Vector DB is marked healthy because a URL is configured.
   * Redis is marked unhealthy because `Settings` has no `redis_host` attribute.
   * The route raises HTTP 503.

## Observed behavior

Before the fix, the focused tests produced an error showing:

```text
'Settings' object has no attribute 'redis_host'
```

The route caught that exception, marked Redis as unhealthy, and raised an HTTP 503 response.

This is not an uncaught application crash. It is a caught configuration error that causes the health endpoint to incorrectly report an unhealthy Redis dependency.

## Expected behavior

The health route should use the application's existing Redis configuration source:

```python
settings.redis_url
```

When the Redis client successfully responds to `ping()`, the route should report Redis as healthy.

The fix should not require adding new `redis_host` or `redis_port` fields to `core/config.py`.

## Relevant files

### Production code

* `api/routes/health.py`

  * Contains the `/health` route and Redis health-check logic.

* `core/config.py`

  * Defines `redis_url`, `database_url`, and `vector_db_url`.

### Tests

* `tests/unit/test_health.py`

  * New focused tests for the health route.

* `tests/unit/test_review_service.py`

  * Existing example of using `AsyncMock` for database sessions.

* `tests/unit/test_rate_limiter.py`

  * Existing example of mocking Redis behavior.

## Known unknowns

During investigation, the main unknowns were:

1. Whether the Redis URL should be parsed manually or passed directly to a Redis URL-based constructor.
2. Whether the repository already had a FastAPI route-test pattern.
3. Whether Docker-backed PostgreSQL and Redis services were required to reproduce and validate the issue.
4. Whether introducing new host and port settings would be expected or would duplicate the existing `redis_url` configuration.

Investigation showed that:

* No existing FastAPI `TestClient` or health-route tests were present.
* Direct async testing of `health_check()` with mocked dependencies was sufficient.
* The existing full Redis URL is the clearest source of truth.
* Docker is not required for focused mocked unit tests.

## Proposed approach

1. Create focused tests in `tests/unit/test_health.py`.
2. Call `health_check()` directly instead of introducing a new `TestClient` setup.
3. Mock the async database session with `AsyncMock`.
4. Mock the Redis client and its `ping()` method.
5. Add a happy-path test where all dependencies are reported healthy.
6. Add a test confirming the health route uses `settings.redis_url`.
7. Update only the Redis client construction in `api/routes/health.py`.
8. Leave `core/config.py` unchanged.
9. Run the focused health tests.
10. Run nearby Redis-related unit tests to check for regressions.

## Tests added

### Happy-path test

`test_health_check_returns_healthy_when_dependencies_are_healthy`

This test:

* mocks `db.execute()` successfully;
* mocks Redis `ping()` successfully;
* provides a nonempty vector DB URL;
* calls `health_check()` directly;
* asserts the overall status is healthy;
* asserts PostgreSQL, Redis, and vector DB are each healthy.

### Redis configuration test

`test_health_check_uses_redis_url_from_settings`

This test:

* assigns a known sentinel value to `settings.redis_url`;
* patches the Redis URL-based client factory;
* calls `health_check()` directly;
* asserts the Redis client is created using the configured URL;
* asserts Redis `ping()` is called;
* asserts Redis is reported healthy.

## Smallest implementation change

I updated the Redis health-check block in `api/routes/health.py` to use the existing Redis URL configuration.

The implemented direction is:

```python
redis.from_url(
    settings.redis_url,
    decode_responses=True,
)
```

This keeps the change small and preserves the full configured Redis URL, including its host, port, and database number.

No new configuration fields were added to `core/config.py`.

## Risks

The main implementation risks were:

* accidentally ignoring the Redis database number included in the URL;
* introducing duplicate Redis configuration fields;
* changing unrelated health-route behavior;
* adding a new testing framework or route harness that was unnecessary for this Tier 1 issue.

Using the complete existing `redis_url` and limiting the code change to the Redis construction path minimized these risks.

## Scope estimate

Expected scope:

* one production file: `api/routes/health.py`;
* one new test file: `tests/unit/test_health.py`.

Estimated complexity:

* investigation: low;
* implementation: low;
* unit testing: low to moderate;
* full runtime validation: blocked by Docker image pull failures.

## Validation plan

Run the focused health tests:

```powershell
.\.venv\Scripts\python -m pytest tests/unit/test_health.py -v
```

Run the focused health tests together with nearby Redis-related tests:

```powershell
.\.venv\Scripts\python -m pytest tests/unit/test_health.py tests/unit/test_rate_limiter.py -v
```

Current result:

```text
21 passed
```

## Environment blocker

The normal Docker-backed setup could not be completed because image pulls repeatedly failed with EOF errors for:

* `postgres:16-alpine`;
* `redis:7-alpine`;
* `chromadb/chroma:0.4.22`.

Because of that, full local runtime validation with live PostgreSQL, Redis, and Chroma services was not possible.

The issue was still reproduced and validated through focused mocked unit tests that directly exercise the health route's behavior.

## Current status

* Issue claimed on GitHub
* Issue added to the cohort ledger
* Branch created and pushed
* `JOURNAL.md` updated
* `PLAN.md` created
* Focused tests added
* Fix implemented
* 21 relevant tests passing
* Pull request opened
