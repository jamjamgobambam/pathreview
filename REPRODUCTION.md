# Reproduction — Issue #155

**Issue:** [Health check references `settings.redis_host`, which does not exist on Settings](https://github.com/ascherj/pathreview/issues/155)

## Steps to reproduce

The buggy code (pre-fix, commit `10d3713`) built the Redis client like this in
`api/routes/health.py`:

```python
r = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=0,
    decode_responses=True,
)
```

`Settings` (`core/config.py`) only defines `redis_url`, not `redis_host`/`redis_port`.

### 1. Reproduce the raw AttributeError in isolation

```bash
python -c "
from core.config import settings
import redis
r = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0, decode_responses=True)
"
```

Output:

```
AttributeError: 'Settings' object has no attribute 'redis_host'
```

### 2. Reproduce the user-facing symptom via the endpoint

Running the pre-fix `health_check()` function against a stubbed DB session shows the
`AttributeError` gets silently swallowed by the broad `except Exception` and reported as
a generic "unhealthy" status — masking the real bug behind what looks like an
infrastructure problem:

```
2026-07-26 21:26:27 [debug]  postgres_health_check_passed
2026-07-26 21:26:27 [error]  redis_health_check_failed  error="'Settings' object has no attribute 'redis_host'"
2026-07-26 21:26:27 [debug]  vector_db_health_check_passed
503 raised with detail: {'status': 'unhealthy', 'dependencies': {'postgres': 'healthy', 'redis': 'unhealthy', 'vector_db': 'healthy'}, 'safety_events_last_hour': 0, ...}
```

Postgres and vector DB report healthy, but Redis is always reported "unhealthy" —
even when Redis itself is running fine — because the check never actually reaches
`r.ping()`.

## Root cause

`api/routes/health.py` references config fields (`redis_host`, `redis_port`) that
don't exist on `Settings`. The fix builds the client from the field that does exist,
`settings.redis_url`, via `redis.Redis.from_url(...)`. See commit `c23239c` on this
branch for the fix and accompanying tests in `tests/unit/test_health_check.py`.
