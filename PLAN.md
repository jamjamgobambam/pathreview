## Solution plan

**Issue:** [Health check references settings.redis_host, which does not exist on Settings](https://github.com/ascherj/pathreview/issues/155)

### Understand

Calling `GET /health` runs the Redis probe in `api/routes/health.py`. The probe
constructs a Redis client with `settings.redis_host` and `settings.redis_port`,
but the `Settings` model in `core/config.py` defines only `redis_url`. Accessing
`settings.redis_host` therefore raises `AttributeError` before the Redis client
is created or `r.ping()` is called. The route catches that exception, logs
`redis_health_check_failed`, marks Redis and the overall service as unhealthy,
and returns HTTP 503.

The expected behavior is for the health check to use configuration fields that
are defined by `Settings`, attempt an actual Redis ping, and report Redis as
healthy when the configured Redis instance is reachable. A connection failure
should still be caught and reported as an unhealthy dependency rather than
causing an unhandled application error.

### Map

- `core/config.py`
  - `Settings`: defines the available application configuration.
  - `settings`: singleton read by the health-check route.
- `api/routes/health.py`
  - `health_check()`: reads the Redis configuration, creates the client, calls
    `ping()`, and builds the dependency-status response.
- `.env.example`
  - Documents the supported Redis environment variables and their local
    defaults. It may need updating if separate host and port settings are
    introduced.
- `tests/unit/` or `tests/integration/`
  - Add focused coverage for a successful Redis probe and a Redis connection
    failure. The exact test file will follow the repository's existing test
    organization.

### Plan

1. Confirm how `redis_url` is used elsewhere in the repository and choose one
   canonical Redis configuration format, avoiding conflicting URL and
   host/port settings.
2. Make the Redis probe consume fields that are actually defined by `Settings`.
   Prefer reusing `settings.redis_url` directly if supported by the Redis client;
   otherwise add typed `redis_host` and `redis_port` fields to `core/config.py`
   and document them in `.env.example`.
3. Update `health_check()` in `api/routes/health.py` so configuration is read
   consistently and `ping()` is reached when the configuration is valid.
4. Add tests that mock or control the Redis client and verify both success and
   connection-failure responses without requiring an uncontrolled external
   Redis service.
5. Run the relevant unit tests and manually call `GET /health` with the local
   Docker Redis container to confirm that the `AttributeError` is gone and the
   Redis status reflects the actual probe result.

### Inputs & outputs

**Inputs**

- Redis connection configuration loaded from `.env` through `Settings`.
- The result of the Redis client's `ping()` operation.
- Availability or unavailability of the configured Redis service.

**Outputs**

- When Redis is reachable, `GET /health` reports
  `dependencies.redis` as `healthy`.
- When Redis is unreachable or misconfigured, the route reports Redis as
  `unhealthy`, sets the overall status to `unhealthy`, and returns HTTP 503.
- Accessing the Redis configuration no longer raises an `AttributeError` for
  `redis_host` or `redis_port`.

### Risks & unknowns

- `core/config.py` currently exposes `redis_url`, while `health.py` expects
  separate host and port values. Adding both representations could allow them
  to disagree, so existing Redis consumers must be searched before selecting
  the final representation.
- `redis.Redis` is synchronous but is called from the asynchronous
  `health_check()` route. This issue may not require changing that design, but a
  slow Redis connection could block the event loop and should be noted.
- Redis URLs can contain authentication credentials, non-default databases,
  TLS (`rediss://`), or non-default ports. Manually extracting only a host and
  port could discard those settings.
- `api/routes/health.py` also reports PostgreSQL and vector-store health. Tests
  must isolate or override those checks so unrelated dependency failures do not
  hide the Redis behavior under test.
- The PostgreSQL probe currently passes `"SELECT 1"` directly to SQLAlchemy and
  may independently report PostgreSQL as unhealthy. That behavior is outside
  issue #155 and should not be mixed into this fix unless maintainers expand
  the scope.

### Edge cases

- Redis is running at the configured URL and responds successfully to `ping()`.
- Redis is stopped, refuses the connection, or times out.
- Redis uses a non-default port or database number.
- Redis requires a password or uses a `rediss://` TLS URL.
- The Redis URL is empty or malformed.
- PostgreSQL is unhealthy while Redis is healthy, so each dependency status
  remains independently accurate.
