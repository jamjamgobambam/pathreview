# Reproducing Issue #155

## Steps to reproduce

1. Started the local dev environment via `docker compose up -d` and `make run`.
2. Temporarily reverted the Redis client construction in `api/routes/health.py`
   back to the original buggy version:
```python
   r = redis.Redis(
       host=settings.redis_host,
       port=settings.redis_port,
       db=0,
       decode_responses=True,
   )
```
3. Called the health endpoint:
```bash
   curl -s http://localhost:8000/health | python3 -m json.tool
```
4. Observed a 503 response with `"redis": "unhealthy"`, even though the Redis
   Docker container (`pathreview-redis-1`) was confirmed running and healthy
   via `docker compose ps`.
5. Confirmed the exact root cause in the server logs:
redis_health_check_failed error="'Settings' object has no attribute 'redis_host'"
This is a genuine `AttributeError` — `settings.redis_host` does not exist
   on the `Settings` model (`core/config.py` only defines `redis_url`). The
   broad `except Exception` block in `health.py` silently caught this and
   reported it as `"unhealthy"`, masking the real problem and making it look
   like a Redis outage instead of a config bug.
6. Reverted the file back to the working fix
   (`redis.Redis.from_url(settings.redis_url, decode_responses=True)`) and
   re-ran the same `curl` command, confirming `"redis": "healthy"` again.

## Confirmed root cause

`grep -rn "redis_host" .` showed the field was only ever referenced in
`api/routes/health.py`, never defined anywhere in `core/config.py`. The
`Settings` class only has `redis_url: str = Field(default="redis://localhost:6379/0")`.