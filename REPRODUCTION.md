# Reproducing Issue #155

## Steps to reproduce

1. Started the local dev environment via `docker compose up -d` and `make run`.
2. Called the health endpoint directly:
```bash
   curl -s http://localhost:8000/health | python3 -m json.tool
```
3. Observed a 503 response with `"redis": "unhealthy"`, even though the Redis
   Docker container (`pathreview-redis-1`) was confirmed running and healthy
   via `docker compose ps`.
4. Checked the server logs and found the root cause in `api/routes/health.py`:
   the Redis client was being constructed with `settings.redis_host` and
   `settings.redis_port`, neither of which exist on the `Settings` model
   (`core/config.py` only defines `redis_url`). This raised an
   `AttributeError` every time, which the broad `except Exception` block
   caught and reported as `"unhealthy"` — masking the real problem and making
   it look like a Redis outage instead of a config bug.

## Confirmed root cause

`grep -rn "redis_host" .` showed the field was only ever referenced in
`api/routes/health.py`, never defined anywhere in `core/config.py`. The
`Settings` class only has `redis_url: str = Field(default="redis://localhost:6379/0")`.