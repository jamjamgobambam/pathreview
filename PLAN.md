## Solution plan

**Issue:** [Health check references `settings.redis_host`, which does not exist on Settings](https://github.com/ascherj/pathreview/issues/155)

### Understand

The Redis probe in `GET /health` constructs a client with `settings.redis_host` and
`settings.redis_port`, but `core.config.Settings` does not define those fields. The resulting
`AttributeError` is caught by the probe, so Redis is reported as unhealthy and the endpoint
returns HTTP 503 even when Redis is running. The settings model should provide the host and port
values expected by the health endpoint so it can successfully ping a reachable Redis server and
continue to report a genuine connection failure as unhealthy.

### Map

Files and functions involved:

- `core/config.py`: add `redis_host` and `redis_port` settings with appropriate default values.
- `api/routes/health.py`: verify that `health_check` consumes the newly defined settings as
  intended; no functional change is expected in this file.
- `tests/unit/test_health.py`: add focused tests for healthy and unavailable Redis behavior (new
  file if no health-route test module exists).

### Plan

1. Add `redis_host: str` with a default value of `localhost` to `core.config.Settings`.
2. Add `redis_port: int` with a default value of `6379` to `core.config.Settings`.
3. Preserve the current `PING` check and error handling so a failed connection marks Redis and
   the overall response as unhealthy.
4. Add unit tests that mock the Redis client and verify successful and failed probes, including
   HTTP 200 and HTTP 503 behavior.
5. Convert the reproduction-only commented settings into active configuration and run the
   focused tests plus linting and type checks.

### Inputs & outputs

The fix takes `REDIS_HOST` and `REDIS_PORT` from the environment, defaulting to `localhost` and
`6379`. With a reachable Redis instance, `GET /health` should return HTTP 200 and report
`dependencies.redis` as `healthy`. If Redis cannot be reached, it should return HTTP 503 and
report Redis as `unhealthy` without exposing an unhandled exception.

### Risks & unknowns

- The Redis library is synchronous, so `ping()` briefly blocks the async health endpoint. This
  change will preserve existing behavior; adopting the async Redis client is outside this issue's
  scope unless tests reveal a requirement.
- Tests must isolate PostgreSQL and vector-store checks so they do not depend on local services.
- Invalid Redis host or port values and slow network failures must still follow the endpoint's
  existing 503 error path.

### Edge cases

- `REDIS_HOST` points to a remote host or Docker service name, or `REDIS_PORT` uses a non-default
  port.
- Redis is configured correctly but is stopped or unreachable.
- `REDIS_PORT` contains a non-numeric or out-of-range value.
- Redis responds successfully while another dependency is unhealthy; the overall endpoint must
  still return HTTP 503 and retain Redis's healthy status.
